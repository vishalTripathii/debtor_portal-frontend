#!/usr/bin/env python3
"""
Lambda-Based Data Deletion
===========================
Use the deployed Lambda function to clear data since it has direct access.
"""

import json
import base64


def create_lambda_cleanup_function():
    """Create a Lambda function for data cleanup."""
    
    lambda_code = '''
import json
import os
from datetime import datetime

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'debtorportal.settings')
import django
django.setup()

from api.database import (
    get_debtors_collection,
    get_debtor_images_collection,
    get_processing_jobs_collection,
    get_activity_logs_collection
)
from api.aws_storage import storage

def cleanup_all_data():
    """Cleanup all data from MongoDB and S3."""
    results = {
        'mongodb': {},
        's3': {},
        'admin_created': False
    }
    
    # Clear MongoDB
    collections = [
        ('debtors', get_debtors_collection()),
        ('debtor_images', get_debtor_images_collection()),
        ('processing_jobs', get_processing_jobs_collection()),
        ('activity_logs', get_activity_logs_collection())
    ]
    
    for name, collection in collections:
        try:
            count = collection.count_documents({})
            if count > 0:
                result = collection.delete_many({})
                results['mongodb'][name] = f"Deleted {result.deleted_count} documents"
            else:
                results['mongodb'][name] = "Already empty"
        except Exception as e:
            results['mongodb'][name] = f"Error: {str(e)}"
    
    # Clear S3
    folders = ['debtor_images/', 'pdf_staging/', 'uploads/', 'payment_receipts/', 'media/']
    
    for folder in folders:
        try:
            files = storage.list_files(folder.rstrip('/'))
            if files:
                deleted = 0
                for file_info in files:
                    storage.delete_file(file_info['key'])
                    deleted += 1
                results['s3'][folder] = f"Deleted {deleted} files"
            else:
                results['s3'][folder] = "Already empty"
        except Exception as e:
            results['s3'][folder] = f"Error: {str(e)}"
    
    # Create admin
    try:
        admin_user = {
            "account_number": "admin",
            "name": "System Administrator",
            "role": "admin", 
            "password": "admin123",
            "email": "admin@poweramc.co",
            "phone": "+1234567890",
            "address": "System Admin",
            "outstanding_amount": 0,
            "payment_status": "admin",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        get_debtors_collection().insert_one(admin_user)
        results['admin_created'] = True
    except Exception as e:
        results['admin_error'] = str(e)
    
    return results

def lambda_handler(event, context):
    """Lambda handler for cleanup."""
    try:
        results = cleanup_all_data()
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': True,
                'message': 'Data cleanup completed',
                'results': results
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
'''
    
    return lambda_code


def main():
    """Create cleanup function."""
    print("🔧 LAMBDA CLEANUP FUNCTION")
    print("=" * 30)
    
    # Create the Lambda cleanup code
    cleanup_code = create_lambda_cleanup_function()
    
    # Save to file
    with open('lambda_cleanup.py', 'w') as f:
        f.write(cleanup_code)
    
    print("✅ Lambda cleanup function created: lambda_cleanup.py")
    print("\n📋 DEPLOYMENT OPTIONS:")
    print("1. Deploy as new Lambda function")
    print("2. Add to existing API as endpoint")
    print("3. Execute via serverless invoke")
    
    print("\n🚀 QUICK DEPLOY:")
    print("Add this to your serverless.yml functions:")
    print("""
  cleanup:
    handler: lambda_cleanup.lambda_handler
    events:
      - http:
          path: admin/cleanup
          method: post
          cors: true
""")
    
    print("\n💡 Then call: POST /admin/cleanup")
    print("Or run: serverless invoke -f cleanup")


if __name__ == "__main__":
    main()