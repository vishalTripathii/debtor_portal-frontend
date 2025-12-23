#!/usr/bin/env python3
"""
Direct MongoDB Clear Script
Clears all collections without Django dependencies
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = "mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtorportal?retryWrites=true&w=majority&appName=debtor-portal-cluster"
MONGODB_NAME = "debtorportal"

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def clear_database():
    """Clear all MongoDB collections"""
    
    print("🗑️  Clearing MongoDB Database...")
    print("=" * 50)
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_NAME]
        
        # List all collections
        collections = db.list_collection_names()
        print(f"📋 Found collections: {collections}")
        
        if not collections:
            print("ℹ️  No collections found")
            # But let's try to clear common collections anyway
            common_collections = ['debtors', 'admins', 'notifications', 'settings', 
                                'upload_history', 'system_settings', 'debtor_images', 
                                'otp', 'processing_jobs']
            
            print("🔍 Checking common collections...")
            any_found = False
            for coll_name in common_collections:
                try:
                    coll = db[coll_name]
                    count = coll.count_documents({})
                    if count > 0:
                        result = coll.delete_many({})
                        print(f"✅ {coll_name}: Deleted {result.deleted_count} documents")
                        any_found = True
                    else:
                        print(f"ℹ️  {coll_name}: Empty")
                except Exception as e:
                    print(f"❌ {coll_name}: {str(e)}")
                    
            if not any_found:
                print("✅ Database is completely clean")
        else:
            total_deleted = 0
            
            for collection_name in collections:
                collection = db[collection_name]
                count = collection.count_documents({})
                
                if count > 0:
                    result = collection.delete_many({})
                    print(f"✅ {collection_name}: Deleted {result.deleted_count} documents")
                    total_deleted += result.deleted_count
                else:
                    print(f"ℹ️  {collection_name}: Already empty")
            
            print(f"🎉 Total documents deleted: {total_deleted}")
        
        # Always recreate default admin
        admins_collection = db['admins']
        default_admin = {
            'username': 'admin',
            'password': hash_password('admin123'),
            'role': 'super_admin',
            'created_at': '2025-12-12T00:00:00Z'
        }
        admins_collection.insert_one(default_admin)
        print(f"✅ admins: Created default admin (username: admin, password: admin123)")
        
        print("=" * 50)
        print("🔑 Default admin ready: username=admin, password=admin123")
        print("💾 Database ready for fresh data upload!")
        
        client.close()
        
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = clear_database()
    if not success:
        exit(1)