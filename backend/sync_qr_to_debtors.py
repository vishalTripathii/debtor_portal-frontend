"""
Sync QR mappings from debtor_images to debtors.qr_code_storage_key
"""
from pymongo import MongoClient

MONGODB_URI = "mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal"

client = MongoClient(MONGODB_URI)
db = client['debtor_portal']

# Get all debtor_images mappings
mappings = list(db.debtor_images.find({}, {'account_number': 1, 'storage_key': 1}))
print(f'Found {len(mappings)} QR mappings')

# Update debtors with qr_code_storage_key
updated = 0
not_found = 0
for m in mappings:
    acc = m.get('account_number')
    key = m.get('storage_key')
    if acc and key:
        result = db.debtors.update_one(
            {'account_number': acc}, 
            {'$set': {'qr_code_storage_key': key}}
        )
        if result.modified_count > 0:
            updated += 1
        else:
            not_found += 1

print(f'Updated: {updated}')
print(f'Not found (no matching debtor): {not_found}')

# Verify
linked = db.debtors.count_documents({'qr_code_storage_key': {'$exists': True, '$ne': None, '$ne': ''}})
print(f'Debtors with QR linked: {linked}')

client.close()
