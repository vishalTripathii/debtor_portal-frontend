"""
Quick test of async bulk delete endpoint
"""
import requests
import pandas as pd

API_BASE_URL = "https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev"
DELETE_ENDPOINT = f"{API_BASE_URL}/bulk/delete-excel"
TEST_FILE = r"C:\Users\tripa\Downloads\debtor_upload_template (3).xlsx"

print("Testing async bulk delete...")
print(f"Reading file: {TEST_FILE}")

# Read file
df = pd.read_excel(TEST_FILE)
account_numbers = df['Account Number'].dropna().astype(str).tolist()
print(f"Found {len(account_numbers)} account numbers")

# Send request
print("\nSending request...")
with open(TEST_FILE, 'rb') as f:
    files = {'file': ('test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = requests.post(DELETE_ENDPOINT, files=files, timeout=30)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 202:
    result = response.json()
    print(f"\n✅ SUCCESS!")
    print(f"Job ID: {result['job_id']}")
    print(f"Total Records: {result['total_records']}")
    print(f"\nYou can check status at:")
    print(f"{API_BASE_URL}/bulk/job-status/{result['job_id']}")
else:
    print(f"\n❌ FAILED!")
