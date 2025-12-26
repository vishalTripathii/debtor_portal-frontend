"""
Test Bulk Delete in Production
Sends Excel file to deployed API Gateway endpoint
"""
import requests
import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
EXCEL_FILE = r"C:\Users\tripa\Downloads\debtor_upload_template_Live(1).xlsx"
API_ENDPOINT = "https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev/bulk/delete-excel"
MONGODB_URI = os.getenv('MONGODB_URI')

print("=" * 60)
print("BULK DELETE PRODUCTION TEST")
print("=" * 60)

# Step 1: Read Excel and show what will be deleted
print("\n[STEP 1] Reading Excel file...")
try:
    df = pd.read_excel(EXCEL_FILE)
    print(f"✓ Excel loaded: {len(df)} rows")
    
    if 'Account Number' in df.columns:
        account_numbers = df['Account Number'].dropna().astype(str).tolist()
        print(f"✓ Found {len(account_numbers)} Account Numbers")
        print(f"\nFirst 10 Account Numbers:")
        for i, acc in enumerate(account_numbers[:10], 1):
            print(f"  {i}. {acc}")
        if len(account_numbers) > 10:
            print(f"  ... and {len(account_numbers) - 10} more")
    else:
        print("✗ ERROR: 'Account Number' column not found!")
        print(f"Available columns: {list(df.columns)}")
        exit(1)
except Exception as e:
    print(f"✗ ERROR reading Excel: {e}")
    exit(1)

# Step 2: Check MongoDB - count existing records
print(f"\n[STEP 2] Checking MongoDB before deletion...")
try:
    client = MongoClient(MONGODB_URI)
    db = client.get_database()
    debtors = db.debtors
    
    existing_count = debtors.count_documents({
        'account_number': {'$in': account_numbers}
    })
    print(f"✓ MongoDB connected")
    print(f"✓ Records that will be deleted: {existing_count}")
    print(f"✓ Records NOT in DB: {len(account_numbers) - existing_count}")
    
    # Show some existing records
    if existing_count > 0:
        sample_records = list(debtors.find(
            {'account_number': {'$in': account_numbers[:5]}},
            {'account_number': 1, 'name': 1, '_id': 0}
        ))
        print(f"\nSample records to be deleted:")
        for rec in sample_records:
            print(f"  - {rec.get('account_number')}: {rec.get('name', 'N/A')}")
    
    total_before = debtors.count_documents({})
    print(f"\nTotal records in DB before: {total_before}")
    
except Exception as e:
    print(f"✗ ERROR connecting to MongoDB: {e}")
    exit(1)

# Step 3: Send to API Gateway
print(f"\n[STEP 3] Sending DELETE request to API Gateway...")
print(f"Endpoint: {API_ENDPOINT}")

try:
    # Read file as binary
    with open(EXCEL_FILE, 'rb') as f:
        files = {'file': ('test_delete.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        
        # You can add Authorization header if needed
        headers = {
            # 'Authorization': 'Bearer YOUR_TOKEN_HERE'  # Add if required
        }
        
        print("Uploading file...")
        response = requests.post(API_ENDPOINT, files=files, headers=headers, timeout=120)
        
        print(f"\n✓ Response received")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ SUCCESS!")
            print(f"Response: {result}")
            print(f"\nDeletion Summary:")
            print(f"  - Deleted: {result.get('deleted_count', 0)}")
            print(f"  - Not Found: {result.get('not_found_count', 0)}")
            print(f"  - Total in Excel: {result.get('total_in_excel', 0)}")
        else:
            print(f"\n✗ ERROR Response")
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text}")
            
except requests.exceptions.Timeout:
    print("✗ Request timed out (Lambda may still be processing)")
except Exception as e:
    print(f"✗ ERROR sending request: {e}")
    exit(1)

# Step 4: Verify MongoDB after deletion
print(f"\n[STEP 4] Verifying MongoDB after deletion...")
try:
    remaining_count = debtors.count_documents({
        'account_number': {'$in': account_numbers}
    })
    
    total_after = debtors.count_documents({})
    deleted = existing_count - remaining_count
    
    print(f"✓ Verification complete")
    print(f"\nResults:")
    print(f"  - Records deleted: {deleted}")
    print(f"  - Records remaining (from Excel): {remaining_count}")
    print(f"  - Total DB records before: {total_before}")
    print(f"  - Total DB records after: {total_after}")
    print(f"  - Net change: -{total_before - total_after}")
    
    if deleted > 0:
        print(f"\n✓✓✓ BULK DELETE SUCCESSFUL! ✓✓✓")
    else:
        print(f"\n⚠ WARNING: No records were deleted")
        print(f"Possible reasons:")
        print(f"  - Account numbers don't exist in database")
        print(f"  - Account number format mismatch")
        print(f"  - API error occurred")
    
    client.close()
    
except Exception as e:
    print(f"✗ ERROR verifying MongoDB: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
