"""
Test optimized bulk delete with small dataset first
"""
import requests
import pandas as pd
import time
import openpyxl

API_BASE_URL = "https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev"
DELETE_ENDPOINT = f"{API_BASE_URL}/bulk/delete-excel"
STATUS_ENDPOINT = f"{API_BASE_URL}/bulk/job-status"

# Create small test file
print("Creating small test file with 5 records...")
test_data = {
    'Account Number': ['TEST001', 'TEST002', 'TEST003', 'TEST004', 'TEST005']
}
df = pd.DataFrame(test_data)
test_file = 'test_small_delete.xlsx'
df.to_excel(test_file, index=False)
print(f"✓ Created {test_file}")

# Test 1: Small file
print("\n" + "="*80)
print("TEST 1: Small file (5 records)")
print("="*80)

with open(test_file, 'rb') as f:
    files = {'file': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    
    print("\nSending request...")
    start_time = time.time()
    response = requests.post(DELETE_ENDPOINT, files=files, timeout=60)
    elapsed = time.time() - start_time

print(f"\n📊 Response Time: {elapsed:.2f} seconds")
print(f"📊 Status Code: {response.status_code}")
print(f"📊 Response: {response.text}")

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ SUCCESS!")
    print(f"Job ID: {result.get('job_id', 'N/A')}")
    
    # Check status
    if 'job_id' in result:
        job_id = result['job_id']
        print(f"\n🔄 Checking job status...")
        
        for i in range(30):  # Check for 30 seconds
            time.sleep(1)
            status_response = requests.get(f"{STATUS_ENDPOINT}/{job_id}")
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"[{i+1:2d}] Status: {status['status']:12s} | "
                      f"Processed: {status['processed_records']:4d}/{status['total_records']:4d} | "
                      f"Deleted: {status['deleted_count']:4d}")
                
                if status['status'] in ['completed', 'failed']:
                    print(f"\n✅ Final Status: {status['status']}")
                    if status['status'] == 'completed':
                        print(f"   Deleted: {status['deleted_count']}")
                        print(f"   Not Found: {status['not_found_count']}")
                    break
else:
    print(f"\n❌ FAILED with status {response.status_code}")

# Test 2: Large file
print("\n\n" + "="*80)
print("TEST 2: Large file (26,883 records)")
print("="*80)

large_file = r"C:\Users\tripa\Downloads\debtor_upload_template (3).xlsx"
print(f"Using file: {large_file}")

with open(large_file, 'rb') as f:
    files = {'file': ('large_test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    
    print("\nSending request...")
    start_time = time.time()
    
    try:
        response = requests.post(DELETE_ENDPOINT, files=files, timeout=60)
        elapsed = time.time() - start_time
        
        print(f"\n📊 Response Time: {elapsed:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Request accepted!")
            print(f"Job ID: {result.get('job_id', 'N/A')}")
            
            if 'job_id' in result:
                job_id = result['job_id']
                print(f"\n🔄 Monitoring progress (will check for up to 5 minutes)...")
                
                for i in range(300):  # Check for 5 minutes
                    time.sleep(2)
                    status_response = requests.get(f"{STATUS_ENDPOINT}/{job_id}")
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        progress = (status['processed_records'] / status['total_records'] * 100) if status['total_records'] > 0 else 0
                        
                        print(f"[{i+1:3d}] Status: {status['status']:12s} | "
                              f"Progress: {status['processed_records']:6d}/{status['total_records']:6d} ({progress:5.1f}%) | "
                              f"Deleted: {status['deleted_count']:6d} | "
                              f"Not Found: {status['not_found_count']:6d}")
                        
                        if status['status'] in ['completed', 'failed', 'partial']:
                            print(f"\n✅ Final Status: {status['status']}")
                            print(f"   Total Records: {status['total_records']}")
                            print(f"   Processed: {status['processed_records']}")
                            print(f"   Deleted: {status['deleted_count']}")
                            print(f"   Not Found: {status['not_found_count']}")
                            
                            if status.get('started_at') and status.get('completed_at'):
                                from datetime import datetime
                                start = datetime.fromisoformat(status['started_at'].replace('Z', '+00:00'))
                                end = datetime.fromisoformat(status['completed_at'].replace('Z', '+00:00'))
                                duration = (end - start).total_seconds()
                                rate = status['processed_records'] / duration if duration > 0 else 0
                                print(f"   Duration: {duration:.2f} seconds")
                                print(f"   Rate: {rate:.0f} records/second")
                            break
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"\n⚠️ Request timed out after 60 seconds")
        print("This is OK - the Lambda is still processing in background")
        print("Note: API Gateway might timeout but Lambda continues for up to 15 minutes")
