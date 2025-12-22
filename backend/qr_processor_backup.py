"""
QR Code Processor Lambda - Dedicated for bulk QR image processing
This runs WITHOUT API Gateway attachment, so it can run for full 900 seconds (15 min max AWS limit)

For large ZIP files or many images:
1. Processes as many QR images as possible within the time limit
2. Re-invokes itself to continue processing from where it left off
3. Continues until all images are processed (unlimited time total)

Supported formats:
- Individual images: PNG, JPG, JPEG, GIF, WEBP
- ZIP files containing images
- PDF files with embedded images

Filename matching:
- filename.png -> matches debtor with account_number=filename OR national_id=filename OR case_id=filename
"""
import json
import os
import time
import base64
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from pymongo import MongoClient
import boto3

# MongoDB connection
MONGODB_URI = os.environ.get('MONGODB_URI', '')

_mongo_client = None
_db = None

# Reserve 60 seconds before Lambda timeout to save state and re-invoke
SAFETY_BUFFER_SECONDS = 60
# Lambda timeout from environment or default 900s
LAMBDA_TIMEOUT = int(os.environ.get('AWS_LAMBDA_TIMEOUT', 900))

# Valid image extensions
VALID_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']


def get_db():
    """Get MongoDB database connection (cached)"""
    global _mongo_client, _db
    if _db is None:
        _mongo_client = MongoClient(MONGODB_URI)
        _db = _mongo_client.get_default_database()
    return _db


def get_debtors_collection():
    return get_db()['debtors']


def get_debtor_images_collection():
    return get_db()['debtor_images']


def get_processing_jobs_collection():
    return get_db()['processing_jobs']


def get_s3_client():
    """Get S3 client"""
    return boto3.client('s3', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))


def save_image_to_s3(account_number, image_data, extension):
    """Save image to S3 and return storage key"""
    bucket = os.environ.get('S3_BUCKET_NAME', os.environ.get('S3_BUCKET', 'power-amc-debtor-media-dev'))
    print(f"[DEBUG] save_image_to_s3 - S3_BUCKET_NAME env: {os.environ.get('S3_BUCKET_NAME')}")
    print(f"[DEBUG] save_image_to_s3 - S3_BUCKET env: {os.environ.get('S3_BUCKET')}")
    print(f"[DEBUG] save_image_to_s3 - Using bucket: {bucket}")
    key = f"debtor_images/{account_number}.{extension}"
    
    content_type_map = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp'
    }
    content_type = content_type_map.get(extension.lower(), 'image/png')
    
    s3_client = get_s3_client()
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=image_data,
        ContentType=content_type
    )
    
    return key


def find_debtor_by_identifier(identifier, debtors_collection):
    """
    Find debtor by account_number, national_id, or case_id
    Returns the debtor document or None
    """
    identifier = str(identifier).strip()
    
    # Try exact match on account_number, national_id, or case_id
    debtor = debtors_collection.find_one({
        '$or': [
            {'account_number': identifier},
            {'national_id': identifier},
            {'case_id': identifier}
        ]
    })
    
    return debtor


def extract_images_from_zip(zip_data):
    """
    Extract all images from a ZIP file
    Returns list of tuples: [(filename, image_bytes), ...]
    """
    images = []
    try:
        zip_buffer = BytesIO(zip_data)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            for zip_info in zip_ref.namelist():
                # Skip directories and hidden files
                if zip_info.endswith('/') or os.path.basename(zip_info).startswith('.'):
                    continue
                
                # Check if it's an image
                zip_file_lower = zip_info.lower()
                if any(zip_file_lower.endswith(ext) for ext in VALID_IMAGE_EXTENSIONS):
                    filename = os.path.basename(zip_info)
                    image_data = zip_ref.read(zip_info)
                    images.append((filename, image_data))
    except Exception as e:
        print(f"Error extracting ZIP: {str(e)}")
    
    return images


def extract_images_from_pdf(pdf_data, pdf_filename):
    """
    Extract all images from a PDF file
    Returns list of tuples: [(filename, image_bytes), ...]
    """
    images = []
    try:
        import fitz  # PyMuPDF
        
        pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
        base_name = pdf_filename.rsplit('.', 1)[0] if '.' in pdf_filename else pdf_filename
        
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                base_image = pdf_doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image.get("ext", "png")
                
                # Generate filename: for single image use base_name, else add page/index
                if len(pdf_doc) == 1 and len(image_list) == 1:
                    filename = f"{base_name}.{image_ext}"
                else:
                    filename = f"{base_name}_p{page_num+1}_i{img_index+1}.{image_ext}"
                
                images.append((filename, image_bytes))
        
        pdf_doc.close()
    except ImportError:
        print("PyMuPDF not installed - PDF processing disabled")
    except Exception as e:
        print(f"Error extracting PDF images: {str(e)}")
    
    return images


def handler(event, context):
    """
    Process QR code images from S3 staging with parallel chunk support
    
    This function now supports parallel processing:
    - start_index: Starting image index for this chunk
    - end_index: Ending image index for this chunk (exclusive)
    - chunk_id: Chunk identifier (1, 2, 3, ...)
    - total_chunks: Total number of parallel chunks
    
    Multiple Lambdas can process different chunks of the same ZIP file simultaneously
    """
    start_time = time.time()
    print(f"QR Processor started with event: {json.dumps(event)}")
    
    job_id = event.get('job_id')
    staging_key = event.get('staging_key')
    file_type = event.get('file_type', 'zip')
    original_filename = event.get('original_filename', 'unknown.zip')
    created_by = event.get('created_by', 'system')
    
    # Chunk parameters for parallel processing
    start_index = event.get('start_index', 0)
    end_index = event.get('end_index', None)  # None = process all from start_index
    chunk_id = event.get('chunk_id', 1)
    total_chunks = event.get('total_chunks', 1)
    
    if not job_id or not staging_key:
        print("Missing job_id or staging_key")
        return {'statusCode': 400, 'body': 'Missing job_id or staging_key'}
    
    print(f"Processing chunk {chunk_id}/{total_chunks}: images {start_index} to {end_index or 'end'}")
    
    jobs_collection = get_processing_jobs_collection()
    
    # Get remaining time from Lambda context (in milliseconds)
    def get_remaining_time_ms():
        if context and hasattr(context, 'get_remaining_time_in_millis'):
            return context.get_remaining_time_in_millis()
        # Fallback: calculate from start time
        elapsed = time.time() - start_time
        remaining = (LAMBDA_TIMEOUT - elapsed) * 1000
        return max(0, remaining)
    
    try:
        # Update job status (use atomic operations for parallel chunks)
        if start_index == 0 and chunk_id == 1:
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {'status': 'processing', 'started_at': datetime.utcnow()}}
            )
        else:
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {'status': 'processing', 'continuation_count': {'$inc': 1}}}
            )
        
        # Download file from S3 and extract images (on every invocation)
        s3_client = get_s3_client()
        bucket = os.environ.get('S3_BUCKET_NAME', os.environ.get('S3_BUCKET', 'power-amc-debtor-media-dev'))
        
        print(f"Downloading from S3: {bucket}/{staging_key}")
        response = s3_client.get_object(Bucket=bucket, Key=staging_key)
        file_data = response['Body'].read()
        print(f"Downloaded {len(file_data)} bytes")
        
        # Extract images based on file type
        if file_type == 'zip' or staging_key.lower().endswith('.zip'):
            images = extract_images_from_zip(file_data)
        elif file_type == 'pdf' or staging_key.lower().endswith('.pdf'):
            images = extract_images_from_pdf(file_data, original_filename)
        else:
            # Single image file
            images = [(original_filename, file_data)]
        
        print(f"Extracted {len(images)} images")
        
        total_images = len(images)
        
        if total_images == 0:
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {
                    'status': 'completed',
                    'processed_images': 0,
                    'uploaded_count': 0,
                    'not_found_count': 0,
                    'error_count': 0,
                    'percentage': 100,
                    'completed_at': datetime.utcnow(),
                    'message': 'No images found in file'
                }}
            )
            return {'statusCode': 200, 'body': 'No images found'}
        
        # Update total count (only first chunk sets this)
        if chunk_id == 1 and start_index == 0:
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {'total_images': total_images}}
            )
        
        # Determine the range to process for this chunk
        chunk_start = start_index
        chunk_end = end_index if end_index is not None else total_images
        chunk_end = min(chunk_end, total_images)  # Don't exceed total
        
        print(f"Chunk {chunk_id}: Processing images {chunk_start} to {chunk_end} (total: {total_images})")
        
        # Track counts for this chunk
        uploaded_count = 0
        not_found_count = 0
        skipped_count = 0  # Already have QR image
        error_count = 0
        errors = []
        
        # Process each image in this chunk's range
        debtors = get_debtors_collection()
        debtor_images = get_debtor_images_collection()
        
        # Track progress for this chunk
        last_progress_update = 0
        
        for idx in range(chunk_start, chunk_end):
            filename, image_data = images[idx]
            
            try:
                # Extract identifier from filename (remove extension)
                identifier = filename.rsplit('.', 1)[0].strip() if '.' in filename else filename.strip()
                
                # Find debtor by account_number, national_id, or case_id
                debtor = find_debtor_by_identifier(identifier, debtors)
                
                if not debtor:
                    not_found_count += 1
                    if len(errors) < 20:
                        errors.append(f"{filename}: No debtor found for identifier '{identifier}'")
                    continue
                
                account_number = debtor.get('account_number')
                
                # Check if already processed (prevent duplicates)
                existing = debtor_images.find_one({'account_number': account_number})
                if existing and existing.get('storage_key'):
                    # Already has QR image - skip to avoid duplicate upload
                    print(f"Skipping {account_number} - already has QR image")
                    skipped_count += 1  # Count as skipped
                else:
                    # Process new QR image
                    try:
                        # Get file extension
                        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'png'
                        if file_ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp']:
                            file_ext = 'png'
                        
                        # Save image to S3
                        storage_key = save_image_to_s3(account_number, image_data, file_ext)
                        
                        # Generate presigned URL (valid for 7 days)
                        s3_client = get_s3_client()
                        bucket = os.environ.get('S3_BUCKET_NAME', os.environ.get('S3_BUCKET', 'power-amc-debtor-media-dev'))
                        presigned_url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': bucket, 'Key': storage_key},
                            ExpiresIn=604800  # 7 days
                        )
                        
                        # SIMULTANEOUSLY update both collections for one-to-one mapping
                        # 1. Update debtor_images collection (tracking metadata)
                        debtor_images.update_one(
                            {'account_number': account_number},
                            {
                                '$set': {
                                    'account_number': account_number,
                                    'national_id': debtor.get('national_id', ''),
                                    'case_id': debtor.get('case_id', ''),
                                    'filename': f"{account_number}.{file_ext}",
                                    'content_type': f'image/{file_ext}',
                                    'storage_key': storage_key,
                                    'uploaded_by': created_by,
                                    'uploaded_at': datetime.utcnow(),
                                    'source': 'bulk_qr_async',
                                    'source_file': original_filename,
                                    'original_identifier': identifier
                                }
                            },
                            upsert=True
                        )
                        
                        # 2. Update debtors collection with qr_code_url (for frontend access)
                        debtors.update_one(
                            {'account_number': account_number},
                            {
                                '$set': {
                                    'qr_code_url': presigned_url,
                                    'qr_code_storage_key': storage_key,
                                    'qr_code_updated_at': datetime.utcnow()
                                }
                            }
                        )
                        
                        uploaded_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        if len(errors) < 20:
                            errors.append(f"{filename}: {str(e)}")
            
            except Exception as e:
                not_found_count += 1
                if len(errors) < 20:
                    errors.append(f"{filename}: No debtor found for identifier '{identifier}'")
            
            # Update progress every 50 images using atomic operations for parallel safety
            if (idx + 1) % 50 == 0:
                # Calculate how many images processed since last update  
                current_position = (idx + 1) - chunk_start
                images_processed_since_last = current_position - last_progress_update
                
                # Update database with incremental progress
                jobs_collection.update_one(
                    {'job_id': job_id},
                    {
                        '$inc': {
                            'processed_images': images_processed_since_last,
                        },
                        '$set': {
                            'status': 'processing'
                        }
                    }
                )
                
                # Get updated count and calculate percentage
                current_job = jobs_collection.find_one({'job_id': job_id})
                total_processed = current_job.get('processed_images', 0)
                percentage = int(total_processed / total_images * 100) if total_images > 0 else 0
                
                # Update percentage separately
                jobs_collection.update_one(
                    {'job_id': job_id},
                    {'$set': {'percentage': percentage}}
                )
                
                last_progress_update = current_position
                print(f"Progress update: Processed {images_processed_since_last} images (total: {total_processed}/{total_images}, {percentage}%)")
                
                print(f"Chunk {chunk_id} Progress: {current_position}/{chunk_end - chunk_start} (Overall: {total_processed}/{total_images} - {percentage}%) - Uploaded: {uploaded_count}, Not Found: {not_found_count}")
        
        # Chunk completed - add any remaining images not caught by 50-batch updates
        current_position = chunk_end - chunk_start
        remaining_images = current_position - last_progress_update
        print(f"Chunk {chunk_id} completing: final position {current_position}, last update at {last_progress_update}, remaining: {remaining_images}")
        if remaining_images > 0:
            # Calculate final percentage for this chunk
            current_job = jobs_collection.find_one({'job_id': job_id})
            total_processed_after_final = current_job.get('processed_images', 0) + remaining_images
            final_percentage = int(total_processed_after_final / total_images * 100) if total_images > 0 else 0
            
            jobs_collection.update_one(
                {'job_id': job_id},
                {
                    '$inc': {
                        'processed_images': remaining_images,
                        'uploaded_count': uploaded_count,
                        'not_found_count': not_found_count,
                        'skipped_count': skipped_count,
                        'error_count': error_count,
                        'chunks_completed': 1
                    },
                    '$set': {
                        'percentage': final_percentage
                    }
                }
            )
        else:
            jobs_collection.update_one(
                {'job_id': job_id},
                {
                    '$inc': {
                        'uploaded_count': uploaded_count,
                        'not_found_count': not_found_count,
                        'skipped_count': skipped_count,
                        'error_count': error_count,
                        'chunks_completed': 1
                    }
                }
            )
        
        # Check if all chunks are complete
        current_job = jobs_collection.find_one({'job_id': job_id})
        chunks_completed = current_job.get('chunks_completed', 0)
        
        if chunks_completed >= total_chunks:
            # All chunks done - mark as completed
            total_uploaded = current_job.get('uploaded_count', 0)
            total_not_found = current_job.get('not_found_count', 0)
            total_errors = current_job.get('error_count', 0)
            
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {
                    'status': 'completed',
                    'processed_images': total_images,
                    'percentage': 100,
                    'completed_at': datetime.utcnow()
                }}
            )
            print(f"🎉 All {total_chunks} chunks completed! Total uploaded: {total_uploaded}, Not found: {total_not_found}, Errors: {total_errors}")
            
            # Clean up staging file from S3 (only by last chunk)
            try:
                s3_client = get_s3_client()
                bucket = os.environ.get('S3_BUCKET_NAME', os.environ.get('S3_BUCKET', 'power-amc-debtor-media-dev'))
                s3_client.delete_object(Bucket=bucket, Key=staging_key)
                print(f"Cleaned up staging file: {staging_key}")
            except Exception as e:
                print(f"Warning: Could not clean up staging file: {str(e)}")
        else:
            print(f"Chunk {chunk_id}/{total_chunks} completed ({chunks_completed} total chunks done). Uploaded: {uploaded_count}, Not Found: {not_found_count}, Errors: {error_count}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'job_id': job_id,
                'total_images': total_images,
                'uploaded': uploaded_count,
                'not_found': not_found_count,
                'errors': errors  # Return the errors array, not the count
            })
        }
        
    except Exception as e:
        print(f"Error processing QR images: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Mark job as failed
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': {
                'status': 'failed',
                'errors': [str(e)],
                'completed_at': datetime.utcnow()
            }}
        )
        return {'statusCode': 500, 'body': str(e)}
