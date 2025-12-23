#!/usr/bin/env python3
import pymongo
import boto3
import os
from datetime import datetime

def fix_missing_qr_mappings():
    try:
        # MongoDB connection
        mongo_uri = "mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&appName=debtor-portal-cluster"
        client = pymongo.MongoClient(mongo_uri)
        
        # AWS S3 client
        s3_client = boto3.client('s3', region_name='ap-southeast-1')
        bucket_name = 'power-amc-debtor-media-dev'
        
        client.admin.command('ping')
        print("✅ MongoDB and AWS connections successful")
        print("=" * 80)
        
        db = client['debtor_portal']
        debtors_collection = db['debtors']
        debtor_images_collection = db['debtor_images']
        
        # Find debtors with QR images but no qr_code_url
        pipeline = [
            {
                '$lookup': {
                    'from': 'debtor_images',
                    'localField': 'account_number',
                    'foreignField': 'account_number',
                    'as': 'qr_image'
                }
            },
            {
                '$match': {
                    'qr_image': {'$ne': []},  # Has QR image
                    '$or': [
                        {'qr_code_url': {'$exists': False}},
                        {'qr_code_url': None},
                        {'qr_code_url': ''}
                    ]
                }
            }
        ]
        
        unmapped_debtors = list(debtors_collection.aggregate(pipeline))
        total_to_fix = len(unmapped_debtors)
        
        print(f"🔧 Found {total_to_fix} debtors to fix")
        
        if total_to_fix == 0:
            print("✅ No mappings to fix!")
            return
            
        print(f"🚀 Starting to fix {total_to_fix} QR mappings...")
        
        fixed_count = 0
        failed_count = 0
        
        for i, debtor in enumerate(unmapped_debtors):
            account_number = debtor.get('account_number')
            qr_image = debtor.get('qr_image', [{}])[0]
            storage_key = qr_image.get('storage_key')
            
            try:
                if not storage_key:
                    print(f"❌ {account_number}: No storage key found")
                    failed_count += 1
                    continue
                
                # Generate new presigned URL (7 days expiry)
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': storage_key},
                    ExpiresIn=604800  # 7 days
                )
                
                # Update debtors collection with qr_code_url
                result = debtors_collection.update_one(
                    {'account_number': account_number},
                    {
                        '$set': {
                            'qr_code_url': presigned_url,
                            'qr_code_storage_key': storage_key,
                            'qr_code_updated_at': datetime.utcnow()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    fixed_count += 1
                    if (i + 1) % 100 == 0:
                        print(f"   Progress: {i + 1}/{total_to_fix} ({fixed_count} fixed)")
                else:
                    failed_count += 1
                    print(f"❌ Failed to update {account_number}")
                    
            except Exception as e:
                failed_count += 1
                print(f"❌ Error fixing {account_number}: {e}")
        
        print("=" * 80)
        print(f"🎉 Mapping fix completed!")
        print(f"   ✅ Fixed: {fixed_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   📊 Success rate: {(fixed_count/total_to_fix)*100:.1f}%")
        
        # Verify the fix
        print(f"\n🔍 Verifying fix...")
        remaining_unmapped = debtors_collection.count_documents({
            '$or': [
                {'qr_code_url': {'$exists': False}},
                {'qr_code_url': None},
                {'qr_code_url': ''}
            ]
        })
        
        total_debtors = debtors_collection.count_documents({})
        mapped_debtors = total_debtors - remaining_unmapped
        coverage = (mapped_debtors / total_debtors) * 100
        
        print(f"   Total debtors: {total_debtors}")
        print(f"   Mapped debtors: {mapped_debtors}")
        print(f"   Coverage: {coverage:.1f}%")
        print(f"   Remaining unmapped: {remaining_unmapped}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_missing_qr_mappings()