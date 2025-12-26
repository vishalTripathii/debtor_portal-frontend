"""
Test with minimal Excel file (5 records)
"""
import requests
import pandas as pd
import io

API_BASE_URL = "https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev"
DELETE_ENDPOINT = f"{API_BASE_URL}/bulk/delete-excel"

# Create small test file in memory
df = pd.DataFrame({
    'Account Number': ['TEST001', 'TEST002', 'TEST003', 'TEST004', 'TEST005']
})

# Save to bytes
excel_bytes = io.BytesIO()
df.to_excel(excel_bytes, index=False)
excel_bytes.seek(0)

print("Testing async bulk delete with 5 records...")
print("Sending request...")

try:
    files = {'file': ('test.xlsx', excel_bytes.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = requests.post(DELETE_ENDPOINT, files=files, timeout=30)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 202:
        result = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"Job ID: {result['job_id']}")
        
        # Test status endpoint
        print(f"\nChecking job status...")
        import time
        time.sleep(2)
        
        status_url = f"{API_BASE_URL}/bulk/job-status/{result['job_id']}"
        status_response = requests.get(status_url, timeout=10)
        print(f"Status Code: {status_response.status_code}")
        print(f"Status: {status_response.text}")
        
except requests.exceptions.Timeout:
    print("\n❌ Request timed out after 30 seconds")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
