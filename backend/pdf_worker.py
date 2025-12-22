"""
AWS Lambda PDF Processing Worker

This module handles PDF processing jobs triggered by SQS messages.
It extracts QR codes from PDFs and stores them as images.

The worker:
1. Receives SQS message with job_id
2. Lists PDF files from S3 staging
3. Processes each PDF to extract QR codes
4. Stores extracted images to S3
5. Updates job status in MongoDB
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from io import BytesIO
from typing import Optional, Dict, Any, Tuple

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'debtorportal.settings')

# Initialize Django
import django
django.setup()

import boto3
from botocore.exceptions import ClientError

# Import PDF processing libraries
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Import database connections
from api.database import (
    get_processing_jobs_collection,
    get_debtor_images_collection,
    get_debtors_collection
)

# Import storage utilities
from api.aws_storage import storage

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3 prefixes
PDF_STAGING_PREFIX = 'pdf_staging'
IMAGES_PREFIX = 'debtor_images'


def extract_ref1_from_barcode(barcode_data: str) -> Optional[str]:
    """
    Extracts Ref1 number from barcode data string.

    Barcode format: |010556503082900 202111000201554 3820100052883 0
    The second number (15 digits) is the Ref1 (account number).
    """
    if not barcode_data:
        return None

    # Remove leading pipe if present
    if barcode_data.startswith('|'):
        barcode_data = barcode_data[1:]

    # Split by spaces
    parts = barcode_data.split()

    if len(parts) >= 2:
        ref1 = parts[1]
        # Ref1 should be 15 digits
        if len(ref1) == 15 and ref1.isdigit():
            return ref1

    return None


def process_pdf_qr_extraction(pdf_content: bytes, filename: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """
    Process a PDF and extract QR code from bottom-left quadrant.
    Fallback to text extraction if image processing libraries aren't available.

    Args:
        pdf_content: PDF file content as bytes
        filename: Original filename for account number extraction

    Returns:
        Tuple of (qr_image_bytes, account_number, error_message)
    """
    if not PYMUPDF_AVAILABLE:
        return None, None, "PyMuPDF library not available"

    account_number = None
    qr_image_bytes = None
    error_message = None

    try:
        # Extract account number from filename first
        base_name = os.path.splitext(filename)[0]
        potential_account = base_name.strip()
        if potential_account:
            account_number = potential_account

        # Open PDF
        pdf_document = fitz.open(stream=pdf_content, filetype='pdf')

        if pdf_document.page_count == 0:
            return None, account_number, "PDF has no pages"

        # Get first page
        page = pdf_document[0]

        # If we have full image processing libraries, do QR extraction
        if all([PYZBAR_AVAILABLE, OPENCV_AVAILABLE, PIL_AVAILABLE]):
            # Render page to image (higher resolution for better QR detection)
            mat = fitz.Matrix(2, 2)  # 2x zoom
            pix = page.get_pixmap(matrix=mat)

            # Convert to numpy array
            img_data = pix.tobytes("png")
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return None, account_number, "Failed to decode PDF page image"

            height, width = img.shape[:2]

            # Focus on bottom-left quadrant (where QR code usually is)
            bottom_left = img[height // 2:, :width // 2]

            # Detect barcodes/QR codes
            decoded_objects = pyzbar.decode(bottom_left)

            if decoded_objects:
                for obj in decoded_objects:
                    barcode_data = obj.data.decode('utf-8')

                    # Try to extract Ref1 from barcode
                    ref1 = extract_ref1_from_barcode(barcode_data)
                    if ref1:
                        account_number = ref1
                        break

                    # If it's a QR code with direct account number
                    if obj.type == 'QRCODE' and barcode_data.isdigit():
                        account_number = barcode_data
                        break

                # Extract the QR code region
                obj = decoded_objects[0]
                points = obj.polygon
                if points:
                    # Get bounding box
                    x_coords = [p.x for p in points]
                    y_coords = [p.y for p in points]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)

                    # Add padding
                    padding = 20
                    x_min = max(0, x_min - padding)
                    y_min = max(0, y_min - padding)
                    x_max = min(bottom_left.shape[1], x_max + padding)
                    y_max = min(bottom_left.shape[0], y_max + padding)

                    # Extract QR region
                    qr_region = bottom_left[y_min:y_max, x_min:x_max]

                    # Convert to PNG bytes
                    success, buffer = cv2.imencode('.png', qr_region)
                    if success:
                        qr_image_bytes = buffer.tobytes()
        else:
            # Fallback: Basic text extraction to find account numbers
            try:
                text_content = page.get_text()
                
                # Look for account number patterns in text
                import re
                
                # Pattern for 15-digit account numbers
                account_pattern = r'\b\d{15}\b'
                matches = re.findall(account_pattern, text_content)
                
                if matches:
                    account_number = matches[0]  # Use first 15-digit number found
                    logger.info(f"Found account number via text extraction: {account_number}")
                
                # Create a simple placeholder QR image if we found an account
                if account_number and PIL_AVAILABLE:
                    from PIL import Image, ImageDraw, ImageFont
                    
                    # Create simple placeholder image
                    img = Image.new('RGB', (200, 200), 'white')
                    draw = ImageDraw.Draw(img)
                    
                    # Draw simple text
                    try:
                        draw.text((10, 90), f"ACC: {account_number}", fill='black')
                    except:
                        pass
                    
                    # Convert to bytes
                    from io import BytesIO
                    buffer = BytesIO()
                    img.save(buffer, format='PNG')
                    qr_image_bytes = buffer.getvalue()
                    
            except Exception as text_error:
                logger.warning(f"Text extraction fallback failed: {str(text_error)}")

        pdf_document.close()

        if not account_number:
            return None, None, f"No account number found in PDF: {filename}"

        # Return success even if no QR image (text extraction mode)
        return qr_image_bytes, account_number, None

    except Exception as e:
        logger.error(f"Error processing PDF {filename}: {str(e)}")
        return None, account_number, str(e)


def update_job_status(
    job_id: str,
    status: str = None,
    processed: int = None,
    successful: int = None,
    failed: int = None,
    not_found: int = None,
    error: str = None,
    percentage: int = None
):
    """Update job status in MongoDB."""
    jobs_collection = get_processing_jobs_collection()

    update_data = {'updated_at': datetime.utcnow()}

    if status:
        update_data['status'] = status
    if processed is not None:
        update_data['processed'] = processed
    if successful is not None:
        update_data['successful'] = successful
    if failed is not None:
        update_data['failed'] = failed
    if not_found is not None:
        update_data['not_found'] = not_found
    if percentage is not None:
        update_data['percentage'] = percentage

    if error:
        jobs_collection.update_one(
            {'job_id': job_id},
            {
                '$set': update_data,
                '$push': {'processing_errors': error}
            }
        )
    else:
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': update_data}
        )


def process_job(job_id: str) -> Dict[str, Any]:
    """
    Process a PDF extraction job.

    Args:
        job_id: The job ID to process

    Returns:
        Dict with processing results
    """
    logger.info(f"Starting job processing: {job_id}")

    jobs_collection = get_processing_jobs_collection()
    debtor_images = get_debtor_images_collection()
    debtors = get_debtors_collection()

    # Get job info
    job = jobs_collection.find_one({'job_id': job_id})
    if not job:
        logger.error(f"Job not found: {job_id}")
        return {'error': 'Job not found'}

    # Update status to processing
    update_job_status(job_id, status='processing')

    # List PDF files from S3 staging
    staging_prefix = f"{PDF_STAGING_PREFIX}/{job_id}/"
    pdf_files = storage.list_files(staging_prefix)

    if not pdf_files:
        update_job_status(job_id, status='failed', error='No PDF files found in staging')
        return {'error': 'No PDF files found'}

    total_files = len(pdf_files)
    processed = 0
    successful = 0
    failed = 0
    not_found = 0

    logger.info(f"Processing {total_files} PDF files for job {job_id}")

    for file_info in pdf_files:
        try:
            key = file_info['key']
            filename = os.path.basename(key)

            if not filename.lower().endswith('.pdf'):
                continue

            # Download PDF from S3
            pdf_content = storage.download_file(key)

            # Process PDF
            qr_image_bytes, account_number, error = process_pdf_qr_extraction(pdf_content, filename)

            if error:
                logger.warning(f"PDF processing error for {filename}: {error}")
                update_job_status(job_id, error=f"{filename}: {error}")
                failed += 1
            elif account_number and qr_image_bytes:
                # Check if debtor exists (try both with and without leading zeros)
                debtor = debtors.find_one({'account_number': account_number})
                
                # If not found and account starts with 0, try without leading zero
                if not debtor and account_number.startswith('0'):
                    account_number_no_zero = account_number.lstrip('0')
                    if account_number_no_zero:  # Ensure it's not empty after removing zeros
                        debtor = debtors.find_one({'account_number': account_number_no_zero})
                        if debtor:
                            account_number = account_number_no_zero  # Use the matched format
                
                # If still not found, try adding a leading zero to account
                if not debtor and not account_number.startswith('0'):
                    account_number_with_zero = '0' + account_number
                    debtor = debtors.find_one({'account_number': account_number_with_zero})
                    if debtor:
                        account_number = account_number_with_zero  # Use the matched format

                if debtor:
                    # Save image to S3
                    image_key = f"{IMAGES_PREFIX}/{account_number}.png"
                    storage.upload_file(qr_image_bytes, image_key, 'image/png')

                    # Update database
                    debtor_images.update_one(
                        {'account_number': account_number},
                        {
                            '$set': {
                                'account_number': account_number,
                                'image_key': image_key,
                                'has_image': True,
                                'source': 'pdf_extraction',
                                'job_id': job_id,
                                'updated_at': datetime.utcnow()
                            }
                        },
                        upsert=True
                    )
                    successful += 1
                    logger.info(f"Successfully extracted QR for account {account_number}")
                else:
                    not_found += 1
                    update_job_status(job_id, error=f"Account not found: {account_number}")
            else:
                failed += 1

            processed += 1

            # Update progress every 10 files or at the end
            if processed % 10 == 0 or processed == total_files:
                percentage = int((processed / total_files) * 100)
                update_job_status(
                    job_id,
                    processed=processed,
                    successful=successful,
                    failed=failed,
                    not_found=not_found,
                    percentage=percentage
                )

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            failed += 1
            processed += 1
            update_job_status(job_id, error=f"Error: {str(e)}")

    # Final status update
    final_status = 'completed' if failed < total_files else 'failed'
    update_job_status(
        job_id,
        status=final_status,
        processed=processed,
        successful=successful,
        failed=failed,
        not_found=not_found,
        percentage=100
    )

    # Clean up staging files
    try:
        storage.delete_folder(staging_prefix)
        logger.info(f"Cleaned up staging folder for job {job_id}")
    except Exception as e:
        logger.warning(f"Failed to clean up staging folder: {str(e)}")

    result = {
        'job_id': job_id,
        'status': final_status,
        'total_files': total_files,
        'processed': processed,
        'successful': successful,
        'failed': failed,
        'not_found': not_found
    }

    logger.info(f"Job completed: {result}")
    return result


def handler(event, context):
    """
    AWS Lambda handler for SQS events.

    Event structure from SQS:
    {
        "Records": [
            {
                "body": "{\"job_id\": \"abc123\"}",
                "messageId": "...",
                ...
            }
        ]
    }
    """
    logger.info(f"PDF Worker received event: {json.dumps(event)}")

    results = []

    for record in event.get('Records', []):
        try:
            # Parse message body
            body = json.loads(record.get('body', '{}'))
            job_id = body.get('job_id')

            if not job_id:
                logger.error("No job_id in message")
                continue

            # Process the job
            result = process_job(job_id)
            results.append(result)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SQS message: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing SQS message: {str(e)}")
            logger.error(traceback.format_exc())

    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': len(results),
            'results': results
        })
    }


# For local testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        test_job_id = sys.argv[1]
        print(f"Testing with job_id: {test_job_id}")
        result = process_job(test_job_id)
        print(f"Result: {result}")
    else:
        print("Usage: python pdf_worker.py <job_id>")
