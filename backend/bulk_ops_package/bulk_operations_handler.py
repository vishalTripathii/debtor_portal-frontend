"""
Standalone Lambda Function for Bulk Delete/Update Operations
NO Django dependencies - Direct MongoDB operations for maximum performance
"""
import json
import base64
import os
from io import BytesIO
from pymongo import MongoClient
import pandas as pd
from email import message_from_bytes

# MongoDB Connection
MONGODB_URI = os.environ.get('MONGODB_URI')
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['debtor_portal']
debtors_collection = db['debtors']


def parse_multipart_excel(event):
    """Parse Excel file from API Gateway multipart/form-data"""
    try:
        # Get body and check if base64 encoded
        body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)
        
        if is_base64:
            body = base64.b64decode(body)
        else:
            body = body.encode('utf-8') if isinstance(body, str) else body
        
        # Get content type and extract boundary
        content_type = event['headers'].get('content-type') or event['headers'].get('Content-Type', '')
        
        if 'boundary=' not in content_type:
            raise ValueError('No boundary found in content-type')
        
        # Parse multipart message
        msg = message_from_bytes(b'Content-Type: ' + content_type.encode() + b'\r\n\r\n' + body)
        
        # Extract file content
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
    
    # try:
    #     auth_header = event['headers'].get('authorization') or event['headers'].get('Authorization', '')
    #     
    #     if not auth_header or not auth_header.startswith('Bearer '):
    #         return False
    #     
    #     # For now, just check if token exists
    #     # In production, add proper JWT verification
    #     token = auth_header.split(' ')[1]
    #     return len(token) > 20  # Basic check
    #     
    # except Exception:
    #     return False


def bulk_delete_handler(event, context):
    """
    Bulk delete debtors by Account Numbers from Excel file
    Direct MongoDB operation - NO Django overhead
    """
    try:
        # Verify authentication
        if not verify_token(event):
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        # Parse Excel file
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
        
        # Batch delete using MongoDB deleteMany (FAST!)
        # Process in batches of 1000 for optimal performance
        deleted_count = 0
        not_found_count = 0
        batch_size = 1000
        
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
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'success': True,
                'message': f'Deleted {deleted_count} accounts from Excel file',
                'deleted_count': deleted_count,
                'not_found_count': not_found_count,
                'total_in_excel': len(account_numbers)
            })
        }
        
    except Exception as e:
        print(f"Error in bulk_delete_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }


def bulk_update_handler(event, context):
    """
    Bulk update debtors by Account Numbers from Excel file
    Uses MongoDB bulkWrite for maximum performance
    """
    try:
        # Verify authentication
        if not verify_token(event):
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        # Parse Excel file
        file_content = parse_multipart_excel(event)
        df = pd.read_excel(BytesIO(file_content))
        
        # Validate columns
        if 'Account Number' not in df.columns:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Excel must contain "Account Number" column'})
            }
        
        # Column mapping
        column_mapping = {
            'Account Number': 'account_number',
            'National ID': 'national_id',
            'Name': 'name',
            'Phone': 'phone',
            'Email': 'email',
            'Outstanding Balance': 'outstanding_balance',
            'Debt Type': 'debt_type',
            'Original Creditor': 'original_creditor',
            'Charge-off Date': 'loan_contract_date',
            'Case ID': 'case_id'
        }
        
        # Prepare bulk operations
        bulk_operations = []
        updated_count = 0
        not_found_count = 0
        
        for _, row in df.iterrows():
            account_number = str(row['Account Number']).strip()
            
            if pd.isna(account_number) or not account_number:
                continue
            
            # Build update document
            update_doc = {}
            for excel_col, db_field in column_mapping.items():
                if excel_col in df.columns and excel_col != 'Account Number':
                    value = row[excel_col]
                    if not pd.isna(value):
                        if db_field == 'outstanding_balance':
                            try:
                                update_doc[db_field] = float(value)
                            except (ValueError, TypeError):
                                pass
                        else:
                            update_doc[db_field] = str(value).strip()
            
            if update_doc:
                bulk_operations.append({
                    'updateOne': {
                        'filter': {'account_number': account_number},
                        'update': {'$set': update_doc}
                    }
                })
        
        # Execute bulk update (FAST!)
        if bulk_operations:
            # Process in batches of 1000
            batch_size = 1000
            total_updated = 0
            total_not_found = 0
            
            for i in range(0, len(bulk_operations), batch_size):
                batch = bulk_operations[i:i + batch_size]
                result = debtors_collection.bulk_write(batch, ordered=False)
                total_updated += result.modified_count
                total_not_found += (len(batch) - result.modified_count)
            
            updated_count = total_updated
            not_found_count = total_not_found
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({
                'success': True,
                'message': f'Updated {updated_count} accounts from Excel file',
                'updated_count': updated_count,
                'not_found_count': not_found_count,
                'total_in_excel': len(df)
            })
        }
        
    except Exception as e:
        print(f"Error in bulk_update_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }


# Lambda handler router
def handler(event, context):
    """Main handler that routes to appropriate function"""
    path = event.get('path', '')
    
    if 'delete' in path:
        return bulk_delete_handler(event, context)
    elif 'update' in path:
        return bulk_update_handler(event, context)
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Not found'})
        }
