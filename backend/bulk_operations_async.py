"""
Async Bulk Operations Lambda with Job Tracking
Solves API Gateway 30-second timeout by returning immediately
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
import boto3

# MongoDB Connection
MONGODB_URI = os.environ.get('MONGODB_URI')
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['debtor_portal']
debtors_collection = db['debtors']
jobs_collection = db['bulk_operation_jobs']

# Lambda client for async invocation
lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
FUNCTION_NAME = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'debtor-portal-bulk-operations-dev')


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


def verify_token(event):
    """Verify JWT token from Authorization header"""
    # Temporarily disable auth for testing
    return True


def bulk_delete_async_handler(event, context):
    """
    ASYNC: Immediately return job ID, process in background
    Solves API Gateway 30-second timeout
    """
    try:
        # Check if this is the initial request or background processing
        if event.get('background_processing'):
            return process_delete_background(event, context)
        
        # Verify authentication
        if not verify_token(event):
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        # Parse Excel file (should be fast < 5 seconds)
        file_content = parse_multipart_excel(event)
        df = pd.read_excel(BytesIO(file_content))
        
        # Validate columns
        if 'Account Number' not in df.columns:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Excel must contain "Account Number" column'})
            }
        
        # Extract account numbers
        account_numbers = df['Account Number'].dropna().astype(str).tolist()
        
        if not account_numbers:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'No account numbers found in Excel'})
            }
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job record in MongoDB
        job_record = {
            'job_id': job_id,
            'operation': 'bulk_delete',
            'status': 'processing',
            'total_records': len(account_numbers),
            'processed_records': 0,
            'deleted_count': 0,
            'not_found_count': 0,
            'started_at': datetime.utcnow(),
            'completed_at': None,
            'error': None
        }
        jobs_collection.insert_one(job_record)
        
        # Invoke Lambda asynchronously for background processing
        lambda_client.invoke(
            FunctionName=FUNCTION_NAME,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps({
                'background_processing': True,
                'job_id': job_id,
                'account_numbers': account_numbers
            })
        )
        
        # Return immediately (< 5 seconds)
        return {
            'statusCode': 202,  # Accepted
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'success': True,
                'job_id': job_id,
                'total_records': len(account_numbers),
                'message': f'Processing {len(account_numbers)} deletions in background. Use job_id to check status.',
                'status_url': f'/bulk/job-status/{job_id}'
            })
        }
        
    except Exception as e:
        print(f"Error in bulk_delete_async_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }


def process_delete_background(event, context):
    """Background processing of bulk delete"""
    try:
        job_id = event['job_id']
        account_numbers = event['account_numbers']
        
        deleted_count = 0
        not_found_count = 0
        batch_size = 1000
        
        # Process in batches with progress updates
        for i in range(0, len(account_numbers), batch_size):
            batch = account_numbers[i:i + batch_size]
            
            # Check how many exist
            existing_count = debtors_collection.count_documents({
                'account_number': {'$in': batch}
            })
            
            # Delete batch
            result = debtors_collection.delete_many({
                'account_number': {'$in': batch}
            })
            
            deleted_count += result.deleted_count
            not_found_count += (len(batch) - existing_count)
            
            # Update job progress every batch
            jobs_collection.update_one(
                {'job_id': job_id},
                {
                    '$set': {
                        'processed_records': i + len(batch),
                        'deleted_count': deleted_count,
                        'not_found_count': not_found_count
                    }
                }
            )
        
        # Mark job as completed
        jobs_collection.update_one(
            {'job_id': job_id},
            {
                '$set': {
                    'status': 'completed',
                    'processed_records': len(account_numbers),
                    'deleted_count': deleted_count,
                    'not_found_count': not_found_count,
                    'completed_at': datetime.utcnow()
                }
            }
        )
        
        print(f"Job {job_id} completed: {deleted_count} deleted, {not_found_count} not found")
        return {'statusCode': 200, 'body': json.dumps({'success': True})}
        
    except Exception as e:
        # Mark job as failed
        jobs_collection.update_one(
            {'job_id': event['job_id']},
            {
                '$set': {
                    'status': 'failed',
                    'error': str(e),
                    'completed_at': datetime.utcnow()
                }
            }
        )
        print(f"Job {event['job_id']} failed: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def job_status_handler(event, context):
    """Get status of a bulk operation job"""
    try:
        # Extract job_id from path
        path_params = event.get('pathParameters', {})
        job_id = path_params.get('job_id')
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'job_id required'})
            }
        
        # Get job from MongoDB
        job = jobs_collection.find_one({'job_id': job_id}, {'_id': 0})
        
        if not job:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
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
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps(job)
        }
        
    except Exception as e:
        print(f"Error in job_status_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }


def lambda_handler(event, context):
    """Main Lambda handler - Route to appropriate function"""
    try:
        # Check if background processing
        if event.get('background_processing'):
            return process_delete_background(event, context)
        
        # Get HTTP method and path
        http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', ''))
        path = event.get('path', event.get('requestContext', {}).get('http', {}).get('path', ''))
        
        print(f"Request: {http_method} {path}")
        
        # Route to handlers
        if path.startswith('/bulk/delete-excel'):
            return bulk_delete_async_handler(event, context)
        elif path.startswith('/bulk/job-status/'):
            return job_status_handler(event, context)
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
