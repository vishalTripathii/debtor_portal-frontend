"""
Excel Processor Lambda - Dedicated for large file processing
This runs WITHOUT API Gateway attachment, so it can run for full 900 seconds (15 min max AWS limit)

For files larger than what can be processed in 15 minutes, this processor:
1. Processes as many records as possible within the time limit
2. Re-invokes itself to continue processing from where it left off
3. Continues until all records are processed (unlimited time total)
"""
import json
import os
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
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


def get_db():
    """Get MongoDB database connection (cached)"""
    global _mongo_client, _db
    if _db is None:
        _mongo_client = MongoClient(MONGODB_URI)
        _db = _mongo_client.get_default_database()
    return _db


def get_debtors_collection():
    return get_db()['debtors']


def get_processing_jobs_collection():
    return get_db()['processing_jobs']


def get_upload_history_collection():
    return get_db()['upload_history']


def parse_currency_value(value):
    """Parse currency values handling Thai Baht and other formats"""
    if pd.isna(value) or value is None:
        return 0.0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    # Convert to string and clean
    value_str = str(value).strip()
    
    # Remove currency symbols and formatting
    value_str = value_str.replace('฿', '').replace('$', '').replace(',', '').replace(' ', '')
    
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return 0.0


def handler(event, context):
    """
    Process Excel file from S3 staging
    This function is invoked asynchronously and can run for full 900 seconds
    
    For very large files, it will:
    1. Process as many records as possible
    2. Save progress to database
    3. Re-invoke itself to continue from where it left off
    """
    start_time = time.time()
    print(f"Excel Processor started with event: {json.dumps(event)}")
    
    job_id = event.get('job_id')
    staging_key = event.get('staging_key')
    file_ext = event.get('file_extension', '.xlsx')
    original_filename = event.get('original_filename', 'unknown')
    created_by = event.get('created_by', 'admin')
    start_index = event.get('start_index', 0)  # For continuation
    
    if not job_id or not staging_key:
        print("Missing job_id or staging_key")
        return {'statusCode': 400, 'body': 'Missing job_id or staging_key'}
    
    jobs_collection = get_processing_jobs_collection()
    
    # Get remaining time from Lambda context (in milliseconds)
    def get_remaining_time_ms():
        if context and hasattr(context, 'get_remaining_time_in_millis'):
            return context.get_remaining_time_in_millis()
        return (LAMBDA_TIMEOUT - (time.time() - start_time)) * 1000
    
    try:
        # Update job status to processing
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': {'status': 'processing', 'started_at': datetime.utcnow()}}
        )
        
        # Import storage and download file from S3
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'power-amc-debtor-media-dev')
        
        print(f"Downloading file from s3://{bucket_name}/{staging_key}")
        
        response = s3_client.get_object(Bucket=bucket_name, Key=staging_key)
        file_content = response['Body'].read()
        
        # Read file into pandas - read ALL rows including empty ones
        file_bytes = BytesIO(file_content)
        
        if file_ext == '.csv':
            df = pd.read_csv(file_bytes)
        else:  # .xlsx or .xls
            # Use openpyxl to get actual row count, then force pandas to read all rows
            import openpyxl
            wb = openpyxl.load_workbook(file_bytes, read_only=True)
            sheet = wb.active
            actual_rows = sheet.max_row - 1  # Exclude header
            wb.close()
            
            # Re-read with pandas, but this time we know the true row count
            file_bytes.seek(0)
            df = pd.read_excel(file_bytes, engine='openpyxl')
            
            # If pandas didn't read all rows, pad with empty rows
            if len(df) < actual_rows:
                print(f"⚠️ Pandas read {len(df)} rows, but file has {actual_rows} rows. Reading all rows...")
                empty_rows = pd.DataFrame([[None] * len(df.columns)] * (actual_rows - len(df)), columns=df.columns)
                df = pd.concat([df, empty_rows], ignore_index=True)
        
        print(f"File loaded with {len(df)} rows, starting from index {start_index}")
        
        # Process the data
        column_mapping = {
            'Account Number': 'account_number',
            'National ID': 'national_id',
            'Original Creditor': 'original_creditor',
            'Outstanding Balance': 'outstanding_balance',
            'Debt Type': 'debt_type',
            'Loan CONTRACT DATE': 'loan_contract_date',
            'Name': 'name',
            'Phone': 'phone',
            'Email': 'email'
        }
        
        # Validate required columns
        required_columns = list(column_mapping.keys())
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            error_msg = f'Missing required columns: {", ".join(missing_columns)}'
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {
                    'status': 'failed',
                    'errors': [error_msg],
                    'completed_at': datetime.utcnow()
                }}
            )
            return {'statusCode': 400, 'body': error_msg}
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # **SKIP EMPTY ROWS** - drop rows where all required fields are empty
        df = df.dropna(subset=['account_number'], how='all')  # Drop if account_number is empty
        df = df[df['account_number'].notna()]  # Keep only rows with account_number
        
        records = df.to_dict('records')
        total_records = len(records)
        
        # Update total records (only on first run)
        if start_index == 0:
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {'total_records': total_records}}
            )
        
        print(f"Processing {total_records} records, starting from index {start_index}...")
        
        # Get current counts from previous runs (for continuation)
        current_job = jobs_collection.find_one({'job_id': job_id})
        inserted_count = current_job.get('inserted_count', 0) if start_index > 0 else 0
        updated_count = current_job.get('updated_count', 0) if start_index > 0 else 0
        error_count = current_job.get('error_count', 0) if start_index > 0 else 0
        errors = current_job.get('errors', []) if start_index > 0 else []
        
        # Process each record
        debtors = get_debtors_collection()
        last_processed_index = start_index
        
        for idx in range(start_index, total_records):
            record = records[idx]
            
            # Check if we're running out of time (leave 60s buffer)
            remaining_ms = get_remaining_time_ms()
            if remaining_ms < SAFETY_BUFFER_SECONDS * 1000:
                print(f"Running low on time ({remaining_ms}ms remaining), will continue in next invocation from index {idx}")
                
                # Save progress
                percentage = int(idx / total_records * 100)
                jobs_collection.update_one(
                    {'job_id': job_id},
                    {'$set': {
                        'processed_records': idx,
                        'inserted_count': inserted_count,
                        'updated_count': updated_count,
                        'error_count': error_count,
                        'percentage': percentage,
                        'status': 'processing',
                        'continuation_index': idx
                    }}
                )
                
                # Re-invoke self to continue processing
                lambda_client = boto3.client('lambda', region_name=os.environ.get('S3_REGION', 'ap-southeast-1'))
                stage = os.environ.get('STAGE', 'dev')
                processor_function_name = f"debtor-portal-api-{stage}-excelProcessor"
                
                continuation_payload = {
                    'job_id': job_id,
                    'staging_key': staging_key,
                    'file_extension': file_ext,
                    'original_filename': original_filename,
                    'created_by': created_by,
                    'start_index': idx  # Continue from current index
                }
                
                lambda_client.invoke(
                    FunctionName=processor_function_name,
                    InvocationType='Event',  # Async
                    Payload=json.dumps(continuation_payload)
                )
                
                print(f"Continuation invoked for index {idx}. Processed so far: {idx}/{total_records}")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'continuing',
                        'processed_so_far': idx,
                        'total_records': total_records,
                        'next_start_index': idx
                    })
                }
            
            try:
                # Clean and format data
                account_number = str(record.get('account_number', '')).strip()
                
                if not account_number:
                    continue
                
                # Check if debtor already exists
                existing_debtor = debtors.find_one({'account_number': account_number})
                
                debtor_data = {
                    'account_number': account_number,
                    'national_id': str(record.get('national_id', '')).strip(),
                    'original_creditor': str(record.get('original_creditor', '')).strip(),
                    'outstanding_balance': parse_currency_value(record.get('outstanding_balance', 0)),
                    'debt_type': str(record.get('debt_type', '')).strip(),
                    'loan_contract_date': str(record.get('loan_contract_date', '')).strip(),
                    'name': str(record.get('name', '')).strip(),
                    'phone': str(record.get('phone', '')).strip(),
                    'email': str(record.get('email', '')).strip(),
                }
                
                if existing_debtor:
                    debtors.update_one(
                        {'account_number': account_number},
                        {'$set': debtor_data}
                    )
                    updated_count += 1
                else:
                    debtors.insert_one(debtor_data)
                    inserted_count += 1
                
                last_processed_index = idx + 1
                
                # Update progress every 100 records
                if (idx + 1) % 100 == 0:
                    percentage = int((idx + 1) / total_records * 100)
                    jobs_collection.update_one(
                        {'job_id': job_id},
                        {'$set': {
                            'processed_records': idx + 1,
                            'inserted_count': inserted_count,
                            'updated_count': updated_count,
                            'percentage': percentage
                        }}
                    )
                    print(f"Progress: {idx + 1}/{total_records} ({percentage}%)")
            
            except Exception as e:
                error_count += 1
                if len(errors) < 10:  # Only store first 10 errors
                    errors.append(f"Row {idx + 1}: {str(e)}")
        
        # Mark job as completed
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': {
                'status': 'completed',
                'processed_records': total_records,
                'inserted_count': inserted_count,
                'updated_count': updated_count,
                'error_count': error_count,
                'errors': errors,
                'percentage': 100,
                'completed_at': datetime.utcnow()
            }}
        )
        
        # Save to upload history
        upload_history = get_upload_history_collection()
        upload_id = f"UPLOAD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        history_record = {
            'upload_id': upload_id,
            'job_id': job_id,
            'filename': original_filename,
            'total_records': total_records,
            'inserted': inserted_count,
            'updated': updated_count,
            'uploaded_by': created_by,
            'uploaded_at': datetime.utcnow(),
            'status': 'success'
        }
        upload_history.insert_one(history_record)
        
        print(f"Completed! Inserted: {inserted_count}, Updated: {updated_count}, Errors: {error_count}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'job_id': job_id,
                'upload_id': upload_id,
                'total_records': total_records,
                'inserted': inserted_count,
                'updated': updated_count,
                'errors': error_count
            })
        }
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
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
