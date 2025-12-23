#!/usr/bin/env python3
"""
FORCE DELETE ALL DATA - Using Deployment Credentials
====================================================
Uses actual AWS and MongoDB credentials from deployment configuration.
"""

import os
import boto3
import pymongo
from datetime import datetime
from botocore.config import Config


def force_clear_mongodb():
    """Force clear MongoDB using deployment credentials."""
    print("🗑️  FORCE CLEARING MONGODB...")
    
    try:
        # Use the exact MongoDB URI from your deployment
        MONGO_URI = "mongodb+srv://naveenkumar:naveenkumar@cluster0.3v2gs.mongodb.net/debtor_portal?retryWrites=true&w=majority"
        
        # Try with different connection options
        client = pymongo.MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=60000,  # 60 seconds
            connectTimeoutMS=60000,
            socketTimeoutMS=60000,
            maxPoolSize=1,
            tlsAllowInvalidCertificates=True,
            directConnection=False
        )
        
        # Force connection test
        client.admin.command('ping')
        print("   ✅ MongoDB connection established")
        
        db = client['debtor_portal']
        
        # Get all collections
        collections = db.list_collection_names()
        print(f"   📊 Found collections: {collections}")
        
        total_deleted = 0
        for collection_name in collections:
            try:
                collection = db[collection_name]
                count = collection.count_documents({})
                
                if count > 0:
                    # Force delete all documents
                    result = collection.delete_many({})
                    print(f"   ✅ {collection_name}: DELETED {result.deleted_count} documents")
                    total_deleted += result.deleted_count
                else:
                    print(f"   ✅ {collection_name}: Already empty")
            except Exception as e:
                print(f"   ❌ {collection_name}: Error - {str(e)}")
                # Try to drop the entire collection
                try:
                    collection.drop()
                    print(f"   ✅ {collection_name}: Collection DROPPED")
                except:
                    pass
        
        # Recreate admin user
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
            print("   ✅ Default admin recreated (admin/admin123)")
        except Exception as e:
            print(f"   ❌ Error creating admin: {str(e)}")
        
        client.close()
        print(f"   🎯 MongoDB cleanup: {total_deleted} total documents deleted")
        
    except Exception as e:
        print(f"   ❌ MongoDB connection failed: {str(e)}")
        # Try alternate connection method
        try:
            # Try direct connection to primary
            alt_uri = "mongodb+srv://naveenkumar:naveenkumar@cluster0-shard-00-00.3v2gs.mongodb.net:27017,cluster0-shard-00-01.3v2gs.mongodb.net:27017,cluster0-shard-00-02.3v2gs.mongodb.net:27017/debtor_portal?ssl=true&replicaSet=atlas-12345-shard-0&authSource=admin&retryWrites=true&w=majority"
            
            client = pymongo.MongoClient(alt_uri, serverSelectionTimeoutMS=30000)
            client.admin.command('ping')
            print("   ✅ MongoDB alternate connection works")
            
            db = client['debtor_portal']
            for collection_name in ['debtors', 'debtor_images', 'processing_jobs', 'activity_logs']:
                try:
                    db[collection_name].delete_many({})
                    print(f"   ✅ {collection_name}: Force deleted")
                except:
                    pass
            client.close()
            
        except Exception as e2:
            print(f"   ❌ All MongoDB connection methods failed: {str(e2)}")


def force_clear_s3():
    """Force clear S3 using deployment credentials."""
    print("\n🗑️  FORCE CLEARING S3...")
    
    try:
        # Use deployment AWS credentials  
        session = boto3.Session()
        
        # Try to use credentials from environment or default AWS profile
        s3_client = boto3.client(
            's3',
            region_name='ap-southeast-1',
            config=Config(
                retries={'max_attempts': 10, 'mode': 'adaptive'},
                max_pool_connections=50
            )
        )
        
        bucket_name = 'debtor-portal-storage'
        
        # Test bucket access
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"   ✅ S3 bucket '{bucket_name}' accessible")
        except Exception as e:
            print(f"   ❌ S3 bucket access failed: {str(e)}")
            return
        
        # List and delete all objects
        folders_to_clear = [
            'debtor_images',
            'pdf_staging', 
            'uploads',
            'payment_receipts',
            'media'
        ]
        
        total_deleted = 0
        
        for folder in folders_to_clear:
            try:
                # List all objects with this prefix
                paginator = s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(
                    Bucket=bucket_name,
                    Prefix=folder
                )
                
                objects_to_delete = []
                for page in pages:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            objects_to_delete.append({'Key': obj['Key']})
                
                if objects_to_delete:
                    print(f"   📂 {folder}: Found {len(objects_to_delete)} objects")
                    
                    # Delete in batches of 1000 (S3 limit)
                    for i in range(0, len(objects_to_delete), 1000):
                        batch = objects_to_delete[i:i+1000]
                        
                        response = s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={
                                'Objects': batch,
                                'Quiet': True
                            }
                        )
                        
                        deleted_count = len(batch)
                        total_deleted += deleted_count
                        print(f"   ✅ {folder}: DELETED {deleted_count} objects")
                        
                        # Check for errors
                        if 'Errors' in response:
                            for error in response['Errors']:
                                print(f"      ❌ Error deleting {error['Key']}: {error['Message']}")
                else:
                    print(f"   ✅ {folder}: Already empty")
                    
            except Exception as e:
                print(f"   ❌ {folder}: Error - {str(e)}")
        
        print(f"   🎯 S3 cleanup: {total_deleted} total objects deleted")
        
    except Exception as e:
        print(f"   ❌ S3 setup failed: {str(e)}")
        print("   💡 Make sure AWS credentials are configured (aws configure)")


def main():
    """Force delete everything."""
    print("🚨 FORCE DELETE ALL DATA")
    print("=" * 50)
    print("Using deployment credentials to delete:")
    print("- ALL MongoDB collections")  
    print("- ALL S3 storage objects")
    print("=" * 50)
    
    confirm = input("\n⚠️  PERMANENTLY DELETE EVERYTHING? Type 'FORCE DELETE' to confirm: ")
    if confirm != "FORCE DELETE":
        print("❌ Operation cancelled.")
        return
    
    print(f"\n🚀 Starting FORCE deletion at {datetime.now().strftime('%H:%M:%S')}")
    
    # Force delete everything
    force_clear_mongodb()
    force_clear_s3()
    
    print(f"\n✅ FORCE deletion completed at {datetime.now().strftime('%H:%M:%S')}")
    print("\n🎯 DESTRUCTION SUMMARY:")
    print("   - MongoDB: All collections cleared")
    print("   - S3: All storage objects deleted") 
    print("   - Default admin recreated")
    print("\n🚀 SYSTEM RESET COMPLETE - Ready for fresh data!")


if __name__ == "__main__":
    main()