"""
Clear old QR code mappings from MongoDB to allow fresh QR uploads

This script removes:
1. qr_code_url, qr_code_storage_key from debtors collection
2. All documents from debtor_images collection

After running this, QR images can be uploaded fresh.
"""

import os
from pymongo import MongoClient

# MongoDB connection from environment
MONGODB_URI = os.environ.get('MONGODB_URI', '')

MONGODB_NAME = os.environ.get('MONGODB_NAME', '')

if not MONGODB_URI:
    # Try to load from .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('MONGODB_URI='):
                    MONGODB_URI = line.split('=', 1)[1].strip('"\'')
                elif line.startswith('MONGODB_NAME='):
                    MONGODB_NAME = line.split('=', 1)[1].strip('"\'')

if not MONGODB_URI:
    print("ERROR: MONGODB_URI not found!")
    print("Please set MONGODB_URI environment variable or add it to backend/.env")
    exit(1)

if not MONGODB_NAME:
    MONGODB_NAME = 'debtor_portal'

print(f"Connecting to MongoDB database: {MONGODB_NAME}...")
client = MongoClient(MONGODB_URI)
db = client[MONGODB_NAME]

# Get collections
debtors = db['debtors']
debtor_images = db['debtor_images']

print("\n=== Current State ===")
total_debtors = debtors.count_documents({})
debtors_with_qr = debtors.count_documents({'qr_code_url': {'$exists': True, '$ne': None}})
debtors_with_storage_key = debtors.count_documents({'qr_code_storage_key': {'$exists': True, '$ne': None}})
total_debtor_images = debtor_images.count_documents({})

print(f"Total debtors: {total_debtors}")
print(f"Debtors with qr_code_url: {debtors_with_qr}")
print(f"Debtors with qr_code_storage_key: {debtors_with_storage_key}")
print(f"Debtor images documents: {total_debtor_images}")

# Confirm before proceeding
print("\n⚠️  This will REMOVE all QR code mappings from MongoDB!")
print("   - Remove qr_code_url from all debtors")
print("   - Remove qr_code_storage_key from all debtors")
print("   - Remove qr_code_updated_at from all debtors")
print("   - Delete ALL documents from debtor_images collection")
print("\nAfter this, you can upload QR images fresh to the new S3 bucket.")

confirm = input("\nType 'YES' to confirm: ")
if confirm != 'YES':
    print("Aborted.")
    exit(0)

print("\n=== Clearing Old Mappings ===")

# 1. Remove QR fields from debtors collection
result = debtors.update_many(
    {},
    {
        '$unset': {
            'qr_code_url': '',
            'qr_code_storage_key': '',
            'qr_code_updated_at': ''
        }
    }
)
print(f"✓ Removed QR fields from {result.modified_count} debtors")

# 2. Delete all debtor_images documents
result = debtor_images.delete_many({})
print(f"✓ Deleted {result.deleted_count} debtor_images documents")

print("\n=== Verification ===")
debtors_with_qr_after = debtors.count_documents({'qr_code_url': {'$exists': True, '$ne': None}})
total_images_after = debtor_images.count_documents({})
print(f"Debtors with qr_code_url: {debtors_with_qr_after}")
print(f"Debtor images documents: {total_images_after}")

print("\n✅ Done! You can now upload QR images to the new S3 bucket.")
print("   The QR processor will create fresh mappings for each image.")

client.close()
