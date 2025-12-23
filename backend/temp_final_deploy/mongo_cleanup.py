#!/usr/bin/env python3
"""
MongoDB Atlas Direct Cleanup
============================
Direct connection to MongoDB Atlas to clear all collections.
"""

import pymongo
from datetime import datetime


def clear_mongodb_atlas():
    """Clear MongoDB Atlas collections directly."""
    print("🚀 Connecting to MongoDB Atlas...")
    
    # MongoDB Atlas connection string (from your serverless.yml env vars)
    MONGO_URI = "mongodb+srv://naveenkumar:naveenkumar@cluster0.3v2gs.mongodb.net/"
    DB_NAME = "debtor_portal"
    
    try:
        # Connect with proper DNS resolution
        client = pymongo.MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=30000,  # 30 second timeout
            tlsAllowInvalidCertificates=True,
            retryWrites=True
        )
        
        # Test connection
        client.admin.command('ping')
        print("   ✅ Connected to MongoDB Atlas")
        
        db = client[DB_NAME]
        
        # Get all collection names
        collections = db.list_collection_names()
        print(f"   📊 Found collections: {collections}")
        
        # Clear each collection
        total_deleted = 0
        for collection_name in collections:
            try:
                collection = db[collection_name]
                count = collection.count_documents({})
                
                if count > 0:
                    result = collection.delete_many({})
                    print(f"   ✅ {collection_name}: Deleted {result.deleted_count} documents")
                    total_deleted += result.deleted_count
                else:
                    print(f"   ✅ {collection_name}: Already empty")
                    
            except Exception as e:
                print(f"   ❌ {collection_name}: Error - {str(e)}")
        
        # Create default admin user
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
        print(f"\n✅ MongoDB cleanup completed - {total_deleted} total documents deleted")
        
    except pymongo.errors.ServerSelectionTimeoutError:
        print("   ❌ Could not connect to MongoDB Atlas - timeout")
        print("   💡 Make sure you have internet connection")
    except Exception as e:
        print(f"   ❌ MongoDB error: {str(e)}")


def main():
    """Main function."""
    print("🗑️  MONGODB ATLAS CLEANUP")
    print("=" * 30)
    
    # Confirm deletion
    confirm = input("⚠️  Delete ALL MongoDB data? Type 'DELETE' to confirm: ")
    if confirm != "DELETE":
        print("❌ Cleanup cancelled.")
        return
    
    clear_mongodb_atlas()


if __name__ == "__main__":
    main()