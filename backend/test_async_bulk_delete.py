"""
Test Async Bulk Delete with Job Status Polling
"""
import requests
import pandas as pd
import time
from pathlib import Path

# Configuration
API_BASE_URL = "https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev"
DELETE_ENDPOINT = f"{API_BASE_URL}/bulk/delete-excel"
STATUS_ENDPOINT = f"{API_BASE_URL}/bulk/job-status"

# Test file
TEST_FILE = r"C:\Users\tripa\Downloads\debtor_upload_template (3).xlsx"

def test_async_bulk_delete():
    """Test async bulk delete with real-time status updates"""
    print("\n" + "="*80)
    print("ASYNC BULK DELETE TEST")
    print("="*80)
    
    # Read Excel file
    print(f"\n📁 Reading Excel file: {TEST_FILE}")
    df = pd.read_excel(TEST_FILE)
    account_numbers = df['Account Number'].dropna().astype(str).tolist()
    print(f"✓ Found {len(account_numbers)} account numbers")
    print(f"   First 5: {account_numbers[:5]}")
    
    # Send delete request
    print(f"\n🚀 Sending async delete request...")
    start_time = time.time()
    
    with open(TEST_FILE, 'rb') as f:
        files = {'file': ('test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        
        response = requests.post(
            DELETE_ENDPOINT,
            files=files,
            timeout=30  # Should return in < 5 seconds
        )
    
    request_time = time.time() - start_time
    print(f"✓ Initial response received in {request_time:.2f} seconds")
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code != 202:
        print(f"❌ Expected 202 Accepted, got {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    # Parse response
    result = response.json()
    print(f"\n✓ Response:")
    print(f"   Job ID: {result['job_id']}")
    print(f"   Total Records: {result['total_records']}")
    print(f"   Message: {result['message']}")
    print(f"   Status URL: {result['status_url']}")
    
    job_id = result['job_id']
    
    # Poll for status
    print(f"\n🔄 Polling job status (checking every 2 seconds)...")
    print("-" * 80)
    
    poll_count = 0
    max_polls = 300  # 10 minutes max
    
    while poll_count < max_polls:
        poll_count += 1
        time.sleep(2)
        
        # Get job status
        status_response = requests.get(f"{STATUS_ENDPOINT}/{job_id}")
        
        if status_response.status_code != 200:
            print(f"❌ Status check failed: {status_response.status_code}")
            print(f"Response: {status_response.text}")
            break
        
        status = status_response.json()
        
        # Calculate progress
        progress_pct = (status['processed_records'] / status['total_records'] * 100) if status['total_records'] > 0 else 0
        
        # Display progress
        print(f"[{poll_count:3d}] Status: {status['status']:12s} | "
              f"Progress: {status['processed_records']:6d} / {status['total_records']:6d} ({progress_pct:5.1f}%) | "
              f"Deleted: {status['deleted_count']:6d} | "
              f"Not Found: {status['not_found_count']:6d}")
        
        # Check if completed or failed
        if status['status'] == 'completed':
            print("\n" + "="*80)
            print("✅ JOB COMPLETED SUCCESSFULLY!")
            print("="*80)
            print(f"\n📈 Final Results:")
            print(f"   Total Records: {status['total_records']}")
            print(f"   Deleted: {status['deleted_count']}")
            print(f"   Not Found: {status['not_found_count']}")
            print(f"   Started: {status['started_at']}")
            print(f"   Completed: {status['completed_at']}")
            
            # Calculate processing time
            from datetime import datetime
            start = datetime.fromisoformat(status['started_at'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(status['completed_at'].replace('Z', '+00:00'))
            processing_time = (end - start).total_seconds()
            print(f"   Processing Time: {processing_time:.2f} seconds")
            print(f"   Rate: {status['total_records'] / processing_time:.0f} records/second")
            break
        
        elif status['status'] == 'failed':
            print("\n" + "="*80)
            print("❌ JOB FAILED")
            print("="*80)
            print(f"Error: {status.get('error', 'Unknown error')}")
            break
    
    if poll_count >= max_polls:
        print("\n⚠️ Maximum polling time reached (10 minutes)")


if __name__ == "__main__":
    try:
        test_async_bulk_delete()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
