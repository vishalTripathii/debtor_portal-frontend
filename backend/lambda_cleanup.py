
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
