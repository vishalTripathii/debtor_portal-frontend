"""
Check QR image status in new S3 bucket and MongoDB mappings
"""
import os
from pymongo import MongoClient

# MongoDB Atlas URI (production)
MONGODB_URI = 'mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&appName=debtor-portal-cluster'

print("Connecting to MongoDB Atlas...")
client = MongoClient(MONGODB_URI)
db = client['debtor_portal']

# Get collections
debtors = db['debtors']
debtor_images = db['debtor_images']

print("\n=== MongoDB Status ===")
total_debtors = debtors.count_documents({})
debtors_with_qr_url = debtors.count_documents({'qr_code_url': {'$exists': True, '$ne': None, '$ne': ''}})
debtors_with_storage_key = debtors.count_documents({'qr_code_storage_key': {'$exists': True, '$ne': None, '$ne': ''}})
total_debtor_images = debtor_images.count_documents({})
debtor_images_with_storage = debtor_images.count_documents({'storage_key': {'$exists': True, '$ne': None, '$ne': ''}})

print(f"Total debtors: {total_debtors:,}")
print(f"Debtors with qr_code_url: {debtors_with_qr_url:,}")
print(f"Debtors with qr_code_storage_key: {debtors_with_storage_key:,}")
print(f"Debtor images documents: {total_debtor_images:,}")
print(f"Debtor images with storage_key: {debtor_images_with_storage:,}")

# Sample a few records to see the data
if debtors_with_qr_url > 0:
    print("\n=== Sample Debtor with QR ===")
    sample = debtors.find_one({'qr_code_url': {'$exists': True, '$ne': None}})
    if sample:
        print(f"  Account: {sample.get('account_number')}")
        print(f"  QR URL: {sample.get('qr_code_url', 'N/A')[:100]}...")
        print(f"  Storage Key: {sample.get('qr_code_storage_key', 'N/A')}")

if total_debtor_images > 0:
    print("\n=== Sample Debtor Image ===")
    sample = debtor_images.find_one({})
    if sample:
        print(f"  Account: {sample.get('account_number')}")
        print(f"  Storage Key: {sample.get('storage_key', 'N/A')}")
        print(f"  Uploaded At: {sample.get('uploaded_at', 'N/A')}")

client.close()
print("\n✅ Check complete")
