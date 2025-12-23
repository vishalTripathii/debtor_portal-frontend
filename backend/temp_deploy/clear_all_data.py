#!/usr/bin/env python3
"""
Complete Data Cleanup Script
============================
Removes ALL data from:
- MongoDB collections (debtors, debtor_images, processing_jobs, activity_logs)
- S3 storage (debtor_images/, pdf_staging/, uploads/, payment_receipts/)
- Local media files
"""

import os
import sys
import shutil
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'debtorportal.settings')

# Initialize Django
import django
django.setup()

from api.database import (
    get_debtors_collection,
    get_debtor_images_collection, 
    get_processing_jobs_collection,
    get_activity_logs_collection
)
from api.aws_storage import storage


def clear_mongodb_collections():
    """Clear all MongoDB collections."""
    print("🗑️  Clearing MongoDB Collections...")
    
    collections = [
        ("debtors", get_debtors_collection()),
        ("debtor_images", get_debtor_images_collection()),
        ("processing_jobs", get_processing_jobs_collection()),
        ("activity_logs", get_activity_logs_collection())
    ]
    
    for name, collection in collections:
        try:
            count = collection.count_documents({})
            if count > 0:
                result = collection.delete_many({})
                print(f"   ✅ {name}: Deleted {result.deleted_count} documents")
            else:
                print(f"   ✅ {name}: Already empty")
        except Exception as e:
            print(f"   ❌ {name}: Error - {str(e)}")


def clear_s3_storage():
    """Clear all S3 storage folders."""
    print("\n🗑️  Clearing S3 Storage...")
    
    folders_to_clear = [
        'debtor_images/',
        'pdf_staging/', 
        'uploads/',
        'payment_receipts/',
        'media/'
    ]
    
    for folder in folders_to_clear:
        try:
            # List all files in the folder
            files = storage.list_files(folder.rstrip('/'))
            
            if files:
                print(f"   📂 {folder}: Found {len(files)} files")
                
                # Delete each file
                deleted_count = 0
                for file_info in files:
                    try:
                        storage.delete_file(file_info['key'])
                        deleted_count += 1
                    except Exception as e:
                        print(f"      ❌ Failed to delete {file_info['key']}: {str(e)}")
                
                print(f"   ✅ {folder}: Deleted {deleted_count} files")
            else:
                print(f"   ✅ {folder}: Already empty")
                
        except Exception as e:
            print(f"   ❌ {folder}: Error - {str(e)}")


def clear_local_media():
    """Clear local media directories."""
    print("\n🗑️  Clearing Local Media...")
    
    media_dirs = [
        'media/debtor_images/',
        'media/uploads/', 
        'media/payment_receipts/',
        'media/pdf_staging/'
    ]
    
    for media_dir in media_dirs:
        try:
            full_path = os.path.join(os.path.dirname(__file__), '..', media_dir)
            
            if os.path.exists(full_path):
                file_count = len([f for f in os.listdir(full_path) 
                                if os.path.isfile(os.path.join(full_path, f))])
                
                if file_count > 0:
                    # Remove all files in directory
                    for filename in os.listdir(full_path):
                        file_path = os.path.join(full_path, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    
                    print(f"   ✅ {media_dir}: Deleted {file_count} files")
                else:
                    print(f"   ✅ {media_dir}: Already empty")
            else:
                print(f"   ✅ {media_dir}: Directory doesn't exist")
                
        except Exception as e:
            print(f"   ❌ {media_dir}: Error - {str(e)}")


def create_default_admin():
    """Create default admin user."""
    print("\n👤 Creating Default Admin...")
    
    try:
        debtors = get_debtors_collection()
        
        # Create default admin
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
        
        debtors.insert_one(admin_user)
        print("   ✅ Default admin created (admin/admin123)")
        
    except Exception as e:
        print(f"   ❌ Error creating admin: {str(e)}")


def main():
    """Main cleanup function."""
    print("🚨 COMPLETE DATA CLEANUP SCRIPT")
    print("=" * 50)
    print("This will DELETE ALL DATA including:")
    print("- All debtor records")
    print("- All QR images") 
    print("- All PDF files")
    print("- All processing jobs")
    print("- All activity logs")
    print("- All uploaded files")
    print("=" * 50)
    
    # Confirm deletion
    confirm = input("\n⚠️  Are you sure? Type 'DELETE ALL' to confirm: ")
    if confirm != "DELETE ALL":
        print("❌ Cleanup cancelled.")
        return
    
    print(f"\n🚀 Starting cleanup at {datetime.utcnow()}")
    
    # Clear all data
    clear_mongodb_collections()
    clear_s3_storage() 
    clear_local_media()
    create_default_admin()
    
    print(f"\n✅ Cleanup completed at {datetime.utcnow()}")
    print("\n🎯 System Reset Summary:")
    print("   - All collections cleared")
    print("   - All S3 files removed") 
    print("   - Local media cleaned")
    print("   - Default admin restored")
    print("\n🚀 Ready for fresh data upload!")


if __name__ == "__main__":
    main()