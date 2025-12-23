#!/usr/bin/env python3
"""
Clear MongoDB Database Script
Removes all data from all collections
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'debtorportal.settings')
import django
django.setup()

from api.database import (
    get_database,
    get_debtors_collection,
    get_admins_collection,
    get_notifications_collection,
    get_settings_collection,
    get_upload_history_collection,
    get_system_settings_collection,
    get_debtor_images_collection,
    get_otp_collection,
    get_processing_jobs_collection
)

def clear_all_collections():
    """Clear all collections in the database"""
    
    collections_to_clear = [
        ('debtors', get_debtors_collection),
        ('notifications', get_notifications_collection),
        ('settings', get_settings_collection),
        ('upload_history', get_upload_history_collection),
        ('system_settings', get_system_settings_collection),
        ('debtor_images', get_debtor_images_collection),
        ('otp', get_otp_collection),
        ('processing_jobs', get_processing_jobs_collection)
    ]
    
    print("🗑️  Clearing MongoDB Database...")
    print("=" * 50)
    
    total_deleted = 0
    
    for collection_name, get_collection_func in collections_to_clear:
        try:
            collection = get_collection_func()
            count = collection.count_documents({})
            
            if count > 0:
                result = collection.delete_many({})
                print(f"✅ {collection_name}: Deleted {result.deleted_count} documents")
                total_deleted += result.deleted_count
            else:
                print(f"ℹ️  {collection_name}: Already empty")
                
        except Exception as e:
            print(f"❌ {collection_name}: Error - {str(e)}")
    
    # Also clear admins collection but preserve one admin user
    try:
        admins = get_admins_collection()
        admin_count = admins.count_documents({})
        if admin_count > 0:
            # Delete all admins
            result = admins.delete_many({})
            print(f"✅ admins: Deleted {result.deleted_count} documents")
            total_deleted += result.deleted_count
            
            # Recreate default admin
            from api.views import hash_password
            default_admin = {
                'username': 'admin',
                'password': hash_password('admin123'),
                'role': 'super_admin',
                'created_at': '2025-12-12T00:00:00Z'
            }
            admins.insert_one(default_admin)
            print(f"✅ admins: Created default admin (username: admin, password: admin123)")
        else:
            print(f"ℹ️  admins: Already empty")
    except Exception as e:
        print(f"❌ admins: Error - {str(e)}")
    
    print("=" * 50)
    print(f"🎉 Database cleared! Total documents deleted: {total_deleted}")
    print("🔑 Default admin created: username=admin, password=admin123")
    print("💾 Ready for fresh data upload!")

if __name__ == "__main__":
    try:
        clear_all_collections()
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        sys.exit(1)