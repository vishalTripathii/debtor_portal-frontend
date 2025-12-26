"""
Ultra-Optimized Bulk Delete Lambda
- Returns job ID immediately (< 3 seconds)
- Processes in background within same invocation
- Optimized batch processing with pymongo
- No external dependencies beyond pandas/pymongo
"""
import json
import base64
import os
import uuid
from datetime import datetime
from io import BytesIO
from pymongo import MongoClient
import pandas as pd
from email import message_from_bytes
from threading import Thread

# MongoDB Connection
MONGODB_URI = os.environ.get('MONGODB_URI')
mongo_client = MongoClient(MONGODB_URI, maxPoolSize=50)
db = mongo_client['debtor_portal']
debtors_collection = db['debtors']
jobs_collection = db['bulk_operation_jobs']

# Ensure index exists for performance
try:
    debtors_collection.create_index([('account_number', 1)])
except:
    pass


def parse_multipart_excel(event):
    """Parse Excel file from API Gateway multipart/form-data"""
    try:
        body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)
        
        if is_base64:
            body = base64.b64decode(body)
        else:
            body = body.encode('utf-8') if isinstance(body, str) else body
        
        content_type = event['headers'].get('content-type') or event['headers'].get('Content-Type', '')
        
        if 'boundary=' not in content_type:
            raise ValueError('No boundary found in content-type')
        
        msg = message_from_bytes(b'Content-Type: ' + content_type.encode() + b'\r\n\r\n' + body)
        
        for part in msg.walk():
            if part.get_content_disposition() == 'form-data':
                content_disposition = part.get('Content-Disposition', '')
                if 'filename' in content_disposition:
                    return part.get_payload(decode=True)
        
        raise ValueError('No file found in multipart data')
        
    except Exception as e:
        raise Exception(f'Error parsing multipart data: {str(e)}')


def process_deletions_background(job_id, account_numbers):
    """Background thread to process deletions"""
    try:
        deleted_count = 0
        not_found_count = 0
        batch_size = 2000  # Larger batches for speed
        total = len(account_numbers)
        
        print(f"Starting background processing for job {job_id}: {total} records")
        
        # Process in optimized batches
        for i in range(0, total, batch_size):
            batch = account_numbers[i:i + batch_size]
            
            # Single delete operation per batch (FAST!)
            result = debtors_collection.delete_many({
                'account_number': {'$in': batch}
            })
            
            deleted_count += result.deleted_count
            not_found_count += (len(batch) - result.deleted_count)
            
            # Update progress every batch
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {
                    'processed_records': min(i + batch_size, total),
                    'deleted_count': deleted_count,
                    'not_found_count': not_found_count
                }}
            )
            
            print(f"Job {job_id}: Processed {min(i + batch_size, total)}/{total}, Deleted: {deleted_count}")
        
        # Mark as completed
        jobs_collection.update_one(
            {'job_id': job_id},
            {'$set': {
                'status': 'completed',
                'processed_records': total,
                'deleted_count': deleted_count,
                'not_found_count': not_found_count,
                'completed_at': datetime.utcnow()
            }}
        )
        
        print(f"Job {job_id} completed: {deleted_count} deleted, {not_found_count} not found")
        
    except Exception as e:
        print(f"Error in background processing: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Mark as failed
        try:
            jobs_collection.update_one(
                {'job_id': job_id},
                {'$set': {
                    'status': 'failed',
                    'error': str(e),
                    'completed_at': datetime.utcnow()
                }}
            )
        except:
            pass


def bulk_delete_handler(event, context):
    """
    Fast bulk delete handler
    Returns immediately with job_id, processes in background thread
    """
    try:
        print("Bulk delete handler started")
        
        # Parse Excel file (optimized - should be < 2 seconds for 26K records)
        file_content = parse_multipart_excel(event)
        print(f"File parsed, size: {len(file_content)} bytes")
        
        df = pd.read_excel(BytesIO(file_content))
        print(f"Excel loaded: {len(df)} rows")
        
        # Validate columns
        if 'Account Number' not in df.columns:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Excel must contain "Account Number" column'})
            }
        
        # Extract account numbers (fast operation)
        account_numbers = df['Account Number'].dropna().astype(str).tolist()
        total_records = len(account_numbers)
        
        if not account_numbers:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'No account numbers found in Excel'})
            }
        
        print(f"Extracted {total_records} account numbers")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job record
        job_record = {
            'job_id': job_id,
            'operation': 'bulk_delete',
            'status': 'processing',
            'total_records': total_records,
            'processed_records': 0,
            'deleted_count': 0,
            'not_found_count': 0,
            'started_at': datetime.utcnow(),
            'completed_at': None,
            'error': None
        }
        jobs_collection.insert_one(job_record)
        print(f"Job created: {job_id}")
        
        # Start background processing thread
        thread = Thread(target=process_deletions_background, args=(job_id, account_numbers))
        thread.daemon = True  # Daemon thread continues after response
        thread.start()
        
        print(f"Background thread started, returning response")
        
        # Return immediately (< 3 seconds total)
        return {
            'statusCode': 202,  # Accepted
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'job_id': job_id,
                'total_records': total_records,
                'message': f'Processing {total_records} deletions in background',
                'status_url': f'/bulk/job-status/{job_id}'
            })
        }
        
    except Exception as e:
        print(f"Error in bulk_delete_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }


def job_status_handler(event, context):
    """Get status of a bulk operation job"""
    try:
        # Extract job_id from path
        path_params = event.get('pathParameters', {})
        job_id = path_params.get('job_id')
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'job_id required'})
            }
        
        # Get job from MongoDB
        job = jobs_collection.find_one({'job_id': job_id}, {'_id': 0})
        
        if not job:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Job not found'})
            }
        
        # Convert datetime to ISO format
        if job.get('started_at'):
            job['started_at'] = job['started_at'].isoformat()
        if job.get('completed_at'):
            job['completed_at'] = job['completed_at'].isoformat()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
            },
            'body': json.dumps(job)
        }
        
    except Exception as e:
        print(f"Error in job_status_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }


def lambda_handler(event, context):
    """Main Lambda handler - Route to appropriate function"""
    try:
        # Get HTTP method and path
        http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', ''))
        path = event.get('path', event.get('requestContext', {}).get('http', {}).get('path', ''))
        
        print(f"=== Lambda Invocation ===")
        print(f"Method: {http_method}")
        print(f"Path: {path}")
        print(f"Headers: {event.get('headers', {})}")
        
        # Handle OPTIONS for CORS preflight
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({'message': 'OK'})
            }
        
        # Route to handlers
        if path and '/bulk/delete-excel' in path:
            return bulk_delete_handler(event, context)
        elif path and '/bulk/job-status/' in path:
            return job_status_handler(event, context)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Not found',
                    'path': path,
                    'method': http_method
                })
            }
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e), 'type': 'lambda_handler_error'})
        }
