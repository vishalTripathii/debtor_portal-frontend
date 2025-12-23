#!/usr/bin/env python3
"""
Fix missing debtor_images records in MongoDB
This script finds all QR images in S3 that don't have corresponding debtor_images records
and creates them to ensure proper API functionality.
"""

import os
import boto3
from datetime import datetime
from pymongo import MongoClient

# MongoDB connection
MONGODB_URI = 'mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&appName=debtor-portal-cluster'

def main():
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    
    # Connect to S3
    s3_client = boto3.client('s3', region_name='ap-southeast-1')
    bucket_name = 'power-amc-debtor-media-dev'
    
    print("🔍 Analyzing missing debtor_images records...")
    
    # Get all S3 QR images
    print("📁 Fetching S3 QR image list...")
    s3_images = {}  # account_number -> storage_key
    paginator = s3_client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket_name, Prefix='debtor_images/'):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    # Extract account number from filename
                    filename = key.split('/')[-1]  # Get filename only
                    account_num = filename.rsplit('.', 1)[0]  # Remove extension
                    s3_images[account_num] = key
    
    print(f"📊 Found {len(s3_images)} QR images in S3")
    
    # Get existing debtor_images records
    print("💼 Fetching existing debtor_images records...")
    existing_image_records = set()
    for record in db.debtor_images.find({}, {'account_number': 1}):
        existing_image_records.add(record['account_number'])
    
    print(f"📷 Found {len(existing_image_records)} existing image records")
    
    # Get all debtors to validate account numbers
    print("👥 Fetching debtors...")
    valid_debtors = set()
    for debtor in db.debtors.find({}, {'account_number': 1}):
        valid_debtors.add(debtor['account_number'])
    
    print(f"✅ Found {len(valid_debtors)} valid debtors")
    
    # Find missing debtor_images records
    missing_records = []
    for account_num, storage_key in s3_images.items():
        if account_num in valid_debtors and account_num not in existing_image_records:
            missing_records.append({
                'account_number': account_num,
                'storage_key': storage_key
            })
    
    print(f"❌ Found {len(missing_records)} missing debtor_images records")
    
    if not missing_records:
        print("✅ All QR images already have corresponding debtor_images records!")
        return
    
    # Create missing records
    print(f"\n🔧 Creating {len(missing_records)} missing debtor_images records...")
    
    current_time = datetime.utcnow()
    batch_records = []
    
    for i, record in enumerate(missing_records):
        account_num = record['account_number']
        storage_key = record['storage_key']
        filename = storage_key.split('/')[-1]
        
        # Determine content type
        ext = filename.split('.')[-1].lower()
        content_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        content_type = content_type_map.get(ext, 'image/png')
        
        debtor_image_record = {
            'account_number': account_num,
            'filename': filename,
            'content_type': content_type,
            'storage_key': storage_key,
            'uploaded_by': 'system_repair',
            'uploaded_at': current_time,
            'source': 'bulk_upload_repair'
        }
        
        batch_records.append(debtor_image_record)
        
        # Insert in batches of 1000
        if len(batch_records) >= 1000:
            db.debtor_images.insert_many(batch_records)
            print(f"   ✅ Inserted batch {i//1000 + 1}: {len(batch_records)} records")
            batch_records = []
    
    # Insert remaining records
    if batch_records:
        db.debtor_images.insert_many(batch_records)
        print(f"   ✅ Inserted final batch: {len(batch_records)} records")
    
    print(f"\n🎉 Successfully created {len(missing_records)} debtor_images records!")
    
    # Verify the fix
    print("\n🔍 Verifying the fix...")
    final_image_count = db.debtor_images.count_documents({})
    final_debtor_count = db.debtors.count_documents({})
    
    print(f"📊 Final counts:")
    print(f"   - Debtors: {final_debtor_count}")
    print(f"   - QR Images in S3: {len(s3_images)}")
    print(f"   - debtor_images records: {final_image_count}")
    
    if final_image_count == len(s3_images):
        print("✅ Perfect! All QR images now have debtor_images records")
    else:
        print(f"⚠️  Still missing {len(s3_images) - final_image_count} records")
    
    client.close()

if __name__ == "__main__":
    main()