#!/usr/bin/env python3
"""
Direct Database & S3 Cleanup Script
===================================
Directly connects to MongoDB and AWS S3 to delete all data.
No Django or virtual environment required.
"""

import os
import json
import shutil
from datetime import datetime

try:
    import pymongo
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


def clear_mongodb_direct():
    """Clear MongoDB collections directly."""
    print("🗑️  Clearing MongoDB Collections...")
    
    if not PYMONGO_AVAILABLE:
        print("   ❌ pymongo not available, skipping MongoDB cleanup")
        return
    
    try:
        # MongoDB connection - using same settings as Django
        MONGO_URI = "mongodb+srv://naveenkumar:naveenkumar@cluster0.3v2gs.mongodb.net/"
        DB_NAME = "debtor_portal"
        
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        collections_to_clear = [
            'debtors',
            'debtor_images', 
            'processing_jobs',
            'activity_logs'
        ]
        
        for collection_name in collections_to_clear:
            try:
                collection = db[collection_name]
                count = collection.count_documents({})
                
                if count > 0:
                    result = collection.delete_many({})
                    print(f"   ✅ {collection_name}: Deleted {result.deleted_count} documents")
                else:
                    print(f"   ✅ {collection_name}: Already empty")
            except Exception as e:
                print(f"   ❌ {collection_name}: Error - {str(e)}")
        
        # Create default admin
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
            
            db['debtors'].insert_one(admin_user)
            print("   ✅ Default admin created (admin/admin123)")
            
        except Exception as e:
            print(f"   ❌ Error creating admin: {str(e)}")
        
        client.close()
        
    except Exception as e:
        print(f"   ❌ MongoDB connection error: {str(e)}")


def clear_s3_direct():
    """Clear S3 storage directly."""
    print("\n🗑️  Clearing S3 Storage...")
    
    if not BOTO3_AVAILABLE:
        print("   ❌ boto3 not available, skipping S3 cleanup")
        return
    
    try:
        # AWS S3 connection
        s3 = boto3.client(
            's3',
            region_name='ap-southeast-1',
            aws_access_key_id='AKIA5AVHM4VQTQMQAWLU',
            aws_secret_access_key='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'
        )
        
        bucket_name = 'debtor-portal-storage'
        
        folders_to_clear = [
            'debtor_images/',
            'pdf_staging/',
            'uploads/', 
            'payment_receipts/',
            'media/'
        ]
        
        for folder in folders_to_clear:
            try:
                # List objects in folder
                response = s3.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix=folder.rstrip('/')
                )
                
                objects = response.get('Contents', [])
                
                if objects:
                    print(f"   📂 {folder}: Found {len(objects)} files")
                    
                    # Delete objects in batches
                    objects_to_delete = [{'Key': obj['Key']} for obj in objects]
                    
                    if objects_to_delete:
                        s3.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': objects_to_delete}
                        )
                        print(f"   ✅ {folder}: Deleted {len(objects_to_delete)} files")
                else:
                    print(f"   ✅ {folder}: Already empty")
                    
            except Exception as e:
                print(f"   ❌ {folder}: Error - {str(e)}")
                
    except Exception as e:
        print(f"   ❌ S3 connection error: {str(e)}")


def clear_local_media():
    """Clear local media files."""
    print("\n🗑️  Clearing Local Media...")
    
    base_path = os.path.dirname(os.path.dirname(__file__))  # Go up to project root
    
    media_dirs = [
        'media/debtor_images',
        'media/uploads',
        'media/payment_receipts', 
        'media/pdf_staging'
    ]
    
    for media_dir in media_dirs:
        try:
            full_path = os.path.join(base_path, media_dir)
            
            if os.path.exists(full_path):
                files = [f for f in os.listdir(full_path) 
                        if os.path.isfile(os.path.join(full_path, f))]
                
                if files:
                    for filename in files:
                        file_path = os.path.join(full_path, filename)
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print(f"      ❌ Failed to delete {filename}: {str(e)}")
                    
                    print(f"   ✅ {media_dir}: Deleted {len(files)} files")
                else:
                    print(f"   ✅ {media_dir}: Already empty")
            else:
                print(f"   ✅ {media_dir}: Directory doesn't exist")
                
        except Exception as e:
            print(f"   ❌ {media_dir}: Error - {str(e)}")


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
    
    # Check dependencies
    if not PYMONGO_AVAILABLE:
        print("⚠️  Warning: pymongo not installed - MongoDB cleanup will be skipped")
    if not BOTO3_AVAILABLE:
        print("⚠️  Warning: boto3 not installed - S3 cleanup will be skipped")
    
    # Confirm deletion
    confirm = input("\n⚠️  Are you sure? Type 'DELETE ALL' to confirm: ")
    if confirm != "DELETE ALL":
        print("❌ Cleanup cancelled.")
        return
    
    print(f"\n🚀 Starting cleanup at {datetime.utcnow()}")
    
    # Clear all data
    clear_mongodb_direct()
    clear_s3_direct()
    clear_local_media()
    
    print(f"\n✅ Cleanup completed at {datetime.utcnow()}")
    print("\n🎯 System Reset Summary:")
    print("   - All collections cleared")
    print("   - All S3 files removed")
    print("   - Local media cleaned") 
    print("   - Default admin restored")
    print("\n🚀 Ready for fresh data upload!")


if __name__ == "__main__":
    main()