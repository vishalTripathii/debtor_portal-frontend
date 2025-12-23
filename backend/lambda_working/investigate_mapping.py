#!/usr/bin/env python3
import pymongo
import os

def investigate_mapping_issue():
    try:
        # Direct MongoDB connection
        mongo_uri = "mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&appName=debtor-portal-cluster"
        client = pymongo.MongoClient(mongo_uri)
        
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        print("=" * 80)
        
        db = client['debtor_portal']
        debtors_collection = db['debtors']
        debtor_images_collection = db['debtor_images']
        
        # 1. Check a specific unmapped debtor
        unmapped_debtor = debtors_collection.find_one({
            '$or': [
                {'qr_code_url': {'$exists': False}},
                {'qr_code_url': None},
                {'qr_code_url': ''}
            ]
        })
        
        if unmapped_debtor:
            account_number = unmapped_debtor.get('account_number')
            print(f"🔍 Investigating unmapped debtor: {account_number}")
            print(f"   Name: {unmapped_debtor.get('name', 'N/A')}")
            print(f"   QR URL field: {unmapped_debtor.get('qr_code_url', 'MISSING')}")
            
            # Check if this debtor has a QR image in debtor_images
            qr_image = debtor_images_collection.find_one({'account_number': account_number})
            if qr_image:
                print(f"   ✅ QR Image exists in debtor_images:")
                print(f"      Storage Key: {qr_image.get('storage_key', 'N/A')}")
                print(f"      Filename: {qr_image.get('filename', 'N/A')}")
                print(f"      Uploaded At: {qr_image.get('uploaded_at', 'N/A')}")
                print(f"   ❌ BUT qr_code_url is missing in debtors collection!")
            else:
                print(f"   ❌ No QR image found in debtor_images")
        
        print("\n" + "=" * 80)
        
        # 2. Check if there's a pattern in unmapped vs mapped
        print("🔍 Analyzing mapping patterns...")
        
        # Sample of mapped debtors
        mapped_sample = list(debtors_collection.find(
            {'qr_code_url': {'$exists': True, '$ne': None, '$ne': ''}},
            {'account_number': 1, 'qr_code_url': 1, 'qr_code_storage_key': 1}
        ).limit(2))
        
        print(f"\n📋 Sample MAPPED debtors:")
        for debtor in mapped_sample:
            account = debtor.get('account_number')
            print(f"   {account}:")
            print(f"      qr_code_url: {debtor.get('qr_code_url', 'N/A')[:60]}...")
            print(f"      qr_code_storage_key: {debtor.get('qr_code_storage_key', 'N/A')}")
            
            # Check corresponding debtor_images entry
            img = debtor_images_collection.find_one({'account_number': account})
            if img:
                print(f"      debtor_images storage_key: {img.get('storage_key', 'N/A')}")
            print()
        
        # 3. Find discrepancies
        print("🔍 Finding discrepancies...")
        
        # Debtors with images but no URL
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
            },
            {'$limit': 5}
        ]
        
        discrepancies = list(debtors_collection.aggregate(pipeline))
        print(f"\n❌ Found {len(discrepancies)} debtors with QR images but no qr_code_url:")
        
        for debtor in discrepancies:
            account = debtor.get('account_number')
            qr_image = debtor.get('qr_image', [{}])[0]
            print(f"   {account} - Has storage_key: {qr_image.get('storage_key', 'N/A')}")
        
        # 4. Check when QR URLs are supposed to be set
        print(f"\n🔍 Checking QR processor logic...")
        print("The qr_code_url should be set in qr_processor.py around line 370:")
        print("   debtors.update_one({'account_number': account_number}, {'$set': {'qr_code_url': presigned_url}})")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    investigate_mapping_issue()