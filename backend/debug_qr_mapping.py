"""Check what's in debtor_images and sample debtors"""
from pymongo import MongoClient

client = MongoClient('mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal')
db = client['debtor_portal']

# Check a sample debtor_image mapping
print("=== Sample debtor_images records ===")
for img in db.debtor_images.find().limit(3):
    print(f"Account: {img.get('account_number')}")
    print(f"Storage Key: {img.get('storage_key')}")
    print()

# Check if those debtors exist and have qr_code_storage_key
print("=== Checking corresponding debtors ===")
sample_accounts = [img.get('account_number') for img in db.debtor_images.find().limit(3)]
for acc in sample_accounts:
    debtor = db.debtors.find_one({'account_number': acc})
    if debtor:
        print(f"Debtor {acc}:")
        print(f"  qr_code_storage_key: {debtor.get('qr_code_storage_key')}")
        print(f"  qr_code_updated_at: {debtor.get('qr_code_updated_at')}")
    else:
        print(f"Debtor {acc}: NOT FOUND in debtors collection!")
    print()

# Check total counts
print("=== Counts ===")
print(f"debtor_images: {db.debtor_images.count_documents({})}")
print(f"debtors total: {db.debtors.count_documents({})}")
print(f"debtors with qr_code_storage_key: {db.debtors.count_documents({'qr_code_storage_key': {'$exists': True, '$ne': None, '$ne': ''}})}")

client.close()
