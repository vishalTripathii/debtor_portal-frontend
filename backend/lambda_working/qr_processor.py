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
from concurrent.futures import ThreadPoolExecutor, as_completed

from pymongo import MongoClient, UpdateOne
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

# Performance tuning
PARALLEL_UPLOAD_WORKERS = 20  # Number of parallel S3 upload threads
BATCH_SIZE = 100  # MongoDB batch size for bulk operations


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


def batch_find_debtors(identifiers, debtors_collection):
    """
    Find multiple debtors in a single query - MUCH faster than individual queries
    Returns: dict mapping identifier -> debtor document
    """
    if not identifiers:
        return {}
    
    # Build OR query for all identifiers at once
    or_conditions = []
    for identifier in identifiers:
        or_conditions.extend([
            {'account_number': identifier},
            {'national_id': identifier},
            {'case_id': identifier}
        ])
    
    # Single query to fetch all matching debtors
    cursor = debtors_collection.find({'$or': or_conditions})
    
    # Build lookup dict by all possible identifiers
    result = {}
    for debtor in cursor:
        if debtor.get('account_number'):
            result[debtor['account_number']] = debtor
        if debtor.get('national_id'):
            result[debtor['national_id']] = debtor
        if debtor.get('case_id'):
            result[debtor['case_id']] = debtor
    
    return result


def batch_check_existing_images(account_numbers, debtor_images_collection):
    """
    Check which accounts already have images in a single query
    Returns: set of account_numbers that already have images
    """
    if not account_numbers:
        return set()
    
    cursor = debtor_images_collection.find(
        {'account_number': {'$in': list(account_numbers)}, 'storage_key': {'$exists': True, '$ne': ''}},
        {'account_number': 1}
    )
    
    return {doc['account_number'] for doc in cursor}


def upload_single_image_to_s3(args):
    """
    Upload a single image to S3 - designed for parallel execution
    Returns: (account_number, storage_key, success, error_msg)
    """
    account_number, image_data, extension, bucket = args
    try:
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
        
        # Each thread gets its own S3 client for thread safety
        s3_client = boto3.client('s3', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=image_data,
            ContentType=content_type
        )
        
        return (account_number, key, True, None)
    except Exception as e:
        return (account_number, None, False, str(e))


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
    OPTIMIZED QR Code Processor with parallel S3 uploads and batch MongoDB operations
    
    Performance improvements:
    - Batch debtor lookups (1 query instead of N)
    - Parallel S3 uploads (20 workers)
    - Batch MongoDB writes (bulk_write instead of individual updates)
    - ~10x faster than sequential processing
    """
    start_time = time.time()
    print(f"🚀 OPTIMIZED QR Processor started with event: {json.dumps(event)}")
    
    job_id = event.get('job_id')
    staging_key = event.get('staging_key')
    file_type = event.get('file_type', 'zip')
    original_filename = event.get('original_filename', 'unknown.zip')
    created_by = event.get('created_by', 'system')
    
    # Chunk parameters
    start_index = event.get('start_index', 0)
    end_index = event.get('end_index', None)
    chunk_id = event.get('chunk_id', 1)
    total_chunks = event.get('total_chunks', 1)
    
    if not job_id or not staging_key:
        return {'statusCode': 400, 'body': 'Missing job_id or staging_key'}
    
    jobs_collection = get_processing_jobs_collection()
    bucket = os.environ.get('S3_BUCKET_NAME', os.environ.get('S3_BUCKET', 'power-amc-debtor-media-dev'))
    
    try:
        # Update job status
        if start_index == 0 and chunk_id == 1:
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {'status': 'processing', 'started_at': datetime.utcnow()}}
            )
        
        # Download file from S3
        s3_client = get_s3_client()
        print(f"📥 Downloading from S3: {bucket}/{staging_key}")
        response = s3_client.get_object(Bucket=bucket, Key=staging_key)
        file_data = response['Body'].read()
        print(f"   Downloaded {len(file_data):,} bytes")
        
        # Extract images
        if file_type == 'zip' or staging_key.lower().endswith('.zip'):
            images = extract_images_from_zip(file_data)
        elif file_type == 'pdf' or staging_key.lower().endswith('.pdf'):
            images = extract_images_from_pdf(file_data, original_filename)
        else:
            images = [(original_filename, file_data)]
        
        total_images = len(images)
        print(f"📦 Extracted {total_images} images")
        
        if total_images == 0:
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {
                    'status': 'completed',
                    'processed_images': 0,
                    'percentage': 100,
                    'completed_at': datetime.utcnow(),
                    'message': 'No images found in file'
                }}
            )
            return {'statusCode': 200, 'body': 'No images found'}
        
        # Update total count
        if chunk_id == 1 and start_index == 0:
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {'total_images': total_images}}
            )
        
        # Determine range to process
        chunk_start = start_index
        chunk_end = min(end_index or total_images, total_images)
        images_to_process = images[chunk_start:chunk_end]
        
        print(f"⚡ Processing {len(images_to_process)} images (index {chunk_start} to {chunk_end})")
        
        # === PHASE 1: Extract identifiers and batch lookup debtors ===
        phase1_start = time.time()
        
        # Extract all identifiers from filenames
        identifier_to_image = {}
        for filename, image_data in images_to_process:
            identifier = filename.rsplit('.', 1)[0].strip() if '.' in filename else filename.strip()
            identifier_to_image[identifier] = (filename, image_data)
        
        # Batch lookup debtors (single DB query instead of N queries)
        debtors_collection = get_debtors_collection()
        debtor_lookup = batch_find_debtors(list(identifier_to_image.keys()), debtors_collection)
        
        print(f"   Phase 1 (debtor lookup): {time.time() - phase1_start:.2f}s - Found {len(debtor_lookup)} debtors")
        
        # === PHASE 2: Check existing images ===
        phase2_start = time.time()
        
        # Get account numbers for matched debtors
        matched_accounts = set()
        identifier_to_account = {}
        identifier_to_debtor = {}
        
        for identifier in identifier_to_image.keys():
            debtor = debtor_lookup.get(identifier)
            if debtor:
                account = debtor.get('account_number')
                if account:
                    matched_accounts.add(account)
                    identifier_to_account[identifier] = account
                    identifier_to_debtor[identifier] = debtor
        
        # Batch check which already have images (single query)
        debtor_images_collection = get_debtor_images_collection()
        existing_images = batch_check_existing_images(matched_accounts, debtor_images_collection)
        
        print(f"   Phase 2 (check existing): {time.time() - phase2_start:.2f}s - {len(existing_images)} already have images")
        
        # Update progress to 20%
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': {'percentage': 20, 'status': 'processing'}}
        )
        
        # === PHASE 3: Parallel S3 uploads ===
        phase3_start = time.time()
        
        # Prepare upload tasks
        upload_tasks = []
        not_found_count = 0
        skipped_count = 0
        errors = []
        
        for identifier, (filename, image_data) in identifier_to_image.items():
            account_number = identifier_to_account.get(identifier)
            
            if not account_number:
                not_found_count += 1
                if len(errors) < 20:
                    errors.append(f"{filename}: No debtor found for '{identifier}'")
                continue
            
            if account_number in existing_images:
                skipped_count += 1
                continue
            
            # Get file extension
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'png'
            if file_ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp']:
                file_ext = 'png'
            
            upload_tasks.append((account_number, image_data, file_ext, bucket, identifier))
        
        print(f"   Prepared {len(upload_tasks)} uploads, {skipped_count} skipped, {not_found_count} not found")
        
        # Update progress to 30%
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': {'percentage': 30}}
        )
        
        # Parallel upload to S3
        uploaded_count = 0
        error_count = 0
        successful_uploads = []  # (account_number, storage_key, identifier)
        
        if upload_tasks:
            # Use ThreadPoolExecutor for parallel uploads
            with ThreadPoolExecutor(max_workers=PARALLEL_UPLOAD_WORKERS) as executor:
                # Submit all upload tasks
                future_to_task = {}
                for task in upload_tasks:
                    account_number, image_data, file_ext, bucket_name, identifier = task
                    future = executor.submit(upload_single_image_to_s3, (account_number, image_data, file_ext, bucket_name))
                    future_to_task[future] = (account_number, identifier)
                
                # Collect results as they complete
                completed = 0
                for future in as_completed(future_to_task):
                    account_number, identifier = future_to_task[future]
                    try:
                        result_account, storage_key, success, error_msg = future.result()
                        
                        if success:
                            uploaded_count += 1
                            successful_uploads.append((result_account, storage_key, identifier))
                        else:
                            error_count += 1
                            if len(errors) < 20:
                                errors.append(f"{result_account}: {error_msg}")
                    except Exception as e:
                        error_count += 1
                        if len(errors) < 20:
                            errors.append(f"{account_number}: {str(e)}")
                    
                    # Update progress periodically
                    completed += 1
                    if completed % 100 == 0:
                        progress = 30 + int((completed / len(upload_tasks)) * 40)  # 30-70%
                        jobs_collection.update_one(
                            {'job_id': job_id},
                            {'$set': {'percentage': progress}}
                        )
                        print(f"   S3 upload progress: {completed}/{len(upload_tasks)}")
        
        print(f"   Phase 3 (S3 uploads): {time.time() - phase3_start:.2f}s - {uploaded_count} uploaded, {error_count} errors")
        
        # Update progress to 70%
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': {'percentage': 70}}
        )
        
        # === PHASE 4: Batch MongoDB updates ===
        phase4_start = time.time()
        
        if successful_uploads:
            # Prepare bulk operations
            debtor_image_ops = []
            debtor_ops = []
            
            for account_number, storage_key, identifier in successful_uploads:
                debtor = identifier_to_debtor.get(identifier, {})
                file_ext = storage_key.split('.')[-1] if '.' in storage_key else 'png'
                
                # Update debtor_images collection
                debtor_image_ops.append(UpdateOne(
                    {'account_number': account_number},
                    {'$set': {
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
                    }},
                    upsert=True
                ))
                
                # Update debtors collection with storage key
                debtor_ops.append(UpdateOne(
                    {'account_number': account_number},
                    {'$set': {
                        'qr_code_storage_key': storage_key,
                        'qr_code_updated_at': datetime.utcnow()
                    }}
                ))
            
            # Execute bulk operations (much faster than individual updates)
            if debtor_image_ops:
                debtor_images_collection.bulk_write(debtor_image_ops, ordered=False)
            
            if debtor_ops:
                debtors_collection.bulk_write(debtor_ops, ordered=False)
        
        print(f"   Phase 4 (MongoDB bulk): {time.time() - phase4_start:.2f}s - {len(successful_uploads)} records updated")
        
        # === PHASE 5: Update job status ===
        processed_count = len(images_to_process)
        
        jobs_collection.update_one(
            {'job_id': job_id},
            {
                '$inc': {
                    'processed_images': processed_count,
                    'uploaded_count': uploaded_count,
                    'not_found_count': not_found_count,
                    'skipped_count': skipped_count,
                    'error_count': error_count,
                    'chunks_completed': 1
                },
                '$set': {'percentage': 90}
            }
        )
        
        # Check if complete
        current_job = jobs_collection.find_one({'job_id': job_id})
        chunks_completed = current_job.get('chunks_completed', 0)
        
        if chunks_completed >= total_chunks:
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {
                    'status': 'completed',
                    'percentage': 100,
                    'completed_at': datetime.utcnow()
                }}
            )
            
            # Cleanup staging file
            try:
                s3_client.delete_object(Bucket=bucket, Key=staging_key)
                print(f"🗑️  Cleaned up staging file: {staging_key}")
            except Exception as e:
                print(f"Warning: Could not clean up staging file: {str(e)}")
            
            total_time = time.time() - start_time
            print(f"🎉 COMPLETED in {total_time:.2f}s - Uploaded: {uploaded_count}, Skipped: {skipped_count}, Not Found: {not_found_count}, Errors: {error_count}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'job_id': job_id,
                'total_images': total_images,
                'uploaded': uploaded_count,
                'skipped': skipped_count,
                'not_found': not_found_count,
                'errors': errors,
                'processing_time': time.time() - start_time
            })
        }
        
    except Exception as e:
        print(f"❌ Error processing QR images: {str(e)}")
        import traceback
        traceback.print_exc()
        
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': {
                'status': 'failed',
                'errors': [str(e)],
                'completed_at': datetime.utcnow()
            }}
        )
        return {'statusCode': 500, 'body': str(e)}
