"""
Check MongoDB records and create test file for bulk delete
"""
from pymongo import MongoClient
import pandas as pd

# MongoDB Connection
MONGODB_URI = "mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority"

print("="*80)
print("         MONGODB RECORDS CHECK & TEST FILE CREATION")
print("="*80)

# Connect to MongoDB
print("\n1️⃣  Connecting to MongoDB...")
client = MongoClient(MONGODB_URI)
db = client['debtor_portal']
debtors = db['debtors']

# Count total records
total_count = debtors.count_documents({})
print(f"   ✓ Total records in 'debtors' collection: {total_count:,}")

if total_count == 0:
    print("\n❌ No records found in MongoDB!")
    print("   Cannot create test file without existing records.")
    exit()

# Get sample records
print("\n2️⃣  Fetching sample records...")
sample_size = min(100, total_count)  # Get up to 100 records for testing
records = list(debtors.find({}, {'account_number': 1, 'name': 1, '_id': 0}).limit(sample_size))

print(f"   ✓ Fetched {len(records)} records")

# Display first 5
print("\n   Sample account numbers:")
for i, record in enumerate(records[:5]):
    print(f"      {i+1}. {record.get('account_number', 'N/A')} - {record.get('name', 'N/A')}")

# Create test Excel file
print("\n3️⃣  Creating test Excel file...")
account_numbers = [r.get('account_number') for r in records if r.get('account_number')]

if not account_numbers:
    print("❌ No account numbers found in records!")
    exit()

# Create DataFrame
df = pd.DataFrame({'Account Number': account_numbers})

# Save to Excel
test_file_path = r"E:\Collections_Debtor_page\Collections_Debtor_page\test_bulk_delete_real_accounts.xlsx"
df.to_excel(test_file_path, index=False)

print(f"   ✓ Test file created: {test_file_path}")
print(f"   ✓ Contains {len(account_numbers)} account numbers")

# Summary
print("\n" + "="*80)
print("                       SUMMARY")
print("="*80)
print(f"\n📊 MongoDB Status:")
print(f"   Total Records: {total_count:,}")
print(f"   Test Records: {len(account_numbers)}")
print(f"\n📁 Test File Created:")
print(f"   Path: {test_file_path}")
print(f"   Records: {len(account_numbers)}")
print(f"\n🎯 Next Steps:")
print(f"   1. Use this test file for bulk delete")
print(f"   2. After delete, records should reduce by {len(account_numbers)}")
print(f"   3. Expected final count: {total_count - len(account_numbers):,}")
print("\n" + "="*80)

client.close()
