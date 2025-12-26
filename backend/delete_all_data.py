"""
Script to delete ALL data:
1. All debtors from MongoDB
2. All QR mappings from MongoDB  
3. All QR codes from S3

WARNING: This is a destructive operation!
"""

import pymongo
import boto3
from datetime import datetime

# MongoDB connection
MONGO_URI = "mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority"

# S3 configuration
S3_BUCKET = "power-amc-debtor-media-dev"
S3_QR_PREFIX = "debtor_images/"

def delete_all_data():
    print("=" * 60)
    print("DELETE ALL DATA SCRIPT")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    print()
    
    # Connect to MongoDB
    print("Connecting to MongoDB...")
    client = pymongo.MongoClient(MONGO_URI)
    db = client['debtor_portal']
    
    # Get current counts
    debtors_count = db.debtors.count_documents({})
    qr_mappings_count = db.qr_mappings.count_documents({})
    
    print(f"Current debtors: {debtors_count}")
    print(f"Current QR mappings: {qr_mappings_count}")
    print()
    
    # Auto-confirm for script execution
    print("Proceeding with deletion...")
    
    print()
    print("-" * 40)
    
    # 1. Delete all debtors
    print("Step 1: Deleting all debtors...")
    result = db.debtors.delete_many({})
    print(f"  Deleted {result.deleted_count} debtors")
    
    # 2. Delete all QR mappings
    print("Step 2: Deleting all QR mappings...")
    result = db.qr_mappings.delete_many({})
    print(f"  Deleted {result.deleted_count} QR mappings")
    
    # 3. Delete all QR codes from S3
    print("Step 3: Deleting all QR codes from S3...")
    s3_client = boto3.client('s3', region_name='ap-southeast-1')
    
    deleted_count = 0
    continuation_token = None
    
    while True:
        # List objects with pagination
        if continuation_token:
            response = s3_client.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=S3_QR_PREFIX,
                ContinuationToken=continuation_token
            )
        else:
            response = s3_client.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=S3_QR_PREFIX
            )
        
        if 'Contents' not in response:
            break
        
        # Delete objects in batches of 1000
        objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
        
        if objects_to_delete:
            delete_response = s3_client.delete_objects(
                Bucket=S3_BUCKET,
                Delete={'Objects': objects_to_delete}
            )
            deleted_count += len(delete_response.get('Deleted', []))
            print(f"  Deleted {deleted_count} QR files so far...")
        
        # Check for more objects
        if response.get('IsTruncated'):
            continuation_token = response.get('NextContinuationToken')
        else:
            break
    
    print(f"  Total S3 files deleted: {deleted_count}")
    
    # Close MongoDB connection
    client.close()
    
    print()
    print("-" * 40)
    print("DELETION COMPLETE!")
    print(f"Finished at: {datetime.now()}")
    print("=" * 60)

if __name__ == "__main__":
    delete_all_data()
