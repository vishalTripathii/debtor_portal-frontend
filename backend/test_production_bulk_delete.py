"""
Production Test: Async Bulk Delete with Real Data
Tests with 26,883 records from actual Excel file
"""
import requests
import pandas as pd
import time
import json
from datetime import datetime
from pathlib import Path

# Configuration
API_BASE_URL = "https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev"
DELETE_ENDPOINT = f"{API_BASE_URL}/bulk/delete-excel"
STATUS_ENDPOINT = f"{API_BASE_URL}/bulk/job-status"

# Test file with 26,883 records
TEST_FILE = r"C:\Users\tripa\Downloads\debtor_upload_template (3).xlsx"

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*100)
    print(text.center(100))
    print("="*100)

def print_section(text):
    """Print section divider"""
    print("\n" + "-"*100)
    print(text)
    print("-"*100)

def read_excel_file():
    """Read and validate Excel file"""
    print_section("📁 STEP 1: Reading Excel File")
    
    if not Path(TEST_FILE).exists():
        print(f"❌ File not found: {TEST_FILE}")
        return None
    
    print(f"File: {TEST_FILE}")
    file_size_mb = Path(TEST_FILE).stat().st_size / (1024 * 1024)
    print(f"Size: {file_size_mb:.2f} MB")
    
    # Read Excel
    df = pd.read_excel(TEST_FILE)
    print(f"✓ Excel loaded successfully")
    print(f"Total rows: {len(df):,}")
    print(f"Columns: {', '.join(df.columns.tolist())}")
    
    # Extract account numbers
    if 'Account Number' not in df.columns:
        print(f"❌ 'Account Number' column not found!")
        return None
    
    account_numbers = df['Account Number'].dropna().astype(str).tolist()
    print(f"\n✓ Found {len(account_numbers):,} account numbers")
    print(f"First 5: {account_numbers[:5]}")
    print(f"Last 5: {account_numbers[-5:]}")
    
    return account_numbers

def send_delete_request():
    """Send async bulk delete request"""
    print_section("🚀 STEP 2: Sending Delete Request")
    
    print(f"Endpoint: {DELETE_ENDPOINT}")
    print(f"Method: POST (multipart/form-data)")
    print(f"Timeout: 30 seconds")
    
    start_time = time.time()
    
    try:
        with open(TEST_FILE, 'rb') as f:
            files = {
                'file': ('debtor_upload_template.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            }
            
            print(f"\n⏳ Sending request... (waiting for response)")
            
            response = requests.post(
                DELETE_ENDPOINT,
                files=files,
                timeout=30
            )
        
        request_time = time.time() - start_time
        
        print(f"\n✓ Response received in {request_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 202:
            print(f"✓ Status: 202 Accepted (Async processing started)")
            
            try:
                result = response.json()
                print(f"\n📊 Response Data:")
                print(json.dumps(result, indent=2))
                return result
                
            except json.JSONDecodeError:
                print(f"❌ Failed to parse JSON response")
                print(f"Response text: {response.text}")
                return None
        
        elif response.status_code == 504:
            print(f"❌ 504 Gateway Timeout - Old synchronous endpoint still responding")
            print(f"Response: {response.text}")
            return None
        
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out after 30 seconds")
        print(f"This should NOT happen with async processing!")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")
        return None

def poll_job_status(job_id, total_records):
    """Poll job status until completion"""
    print_section(f"🔄 STEP 3: Polling Job Status (Job ID: {job_id})")
    
    status_url = f"{STATUS_ENDPOINT}/{job_id}"
    print(f"Status URL: {status_url}")
    print(f"Polling interval: 2 seconds")
    print(f"Maximum wait time: 10 minutes")
    
    poll_count = 0
    max_polls = 300  # 10 minutes (300 x 2 seconds)
    
    print("\n" + "="*100)
    print(f"{'Poll':>5} | {'Status':^12} | {'Progress':^30} | {'Deleted':>8} | {'Not Found':>10} | {'Time':>8}")
    print("="*100)
    
    start_poll_time = time.time()
    last_processed = 0
    
    while poll_count < max_polls:
        poll_count += 1
        time.sleep(2)
        
        try:
            response = requests.get(status_url, timeout=10)
            
            if response.status_code != 200:
                print(f"\n❌ Status check failed: {response.status_code}")
                print(f"Response: {response.text}")
                time.sleep(5)  # Wait longer before retry
                continue
            
            status = response.json()
            
            # Calculate progress
            processed = status.get('processed_records', 0)
            deleted = status.get('deleted_count', 0)
            not_found = status.get('not_found_count', 0)
            job_status = status.get('status', 'unknown')
            
            progress_pct = (processed / total_records * 100) if total_records > 0 else 0
            progress_bar = '█' * int(progress_pct / 5) + '░' * (20 - int(progress_pct / 5))
            
            elapsed = time.time() - start_poll_time
            
            # Calculate speed
            records_per_sec = (processed - last_processed) / 2 if processed > last_processed else 0
            last_processed = processed
            
            print(f"{poll_count:>5} | {job_status:^12} | [{progress_bar}] {progress_pct:5.1f}% | {deleted:>8,} | {not_found:>10,} | {elapsed:>7.1f}s")
            
            if records_per_sec > 0:
                eta_seconds = (total_records - processed) / records_per_sec if processed < total_records else 0
                print(f"       | Speed: {records_per_sec:,.0f} rec/sec | ETA: {eta_seconds:.0f}s", end='\r')
            
            # Check completion
            if job_status == 'completed':
                print("\n" + "="*100)
                print_header("✅ JOB COMPLETED SUCCESSFULLY!")
                
                print(f"\n📈 Final Results:")
                print(f"   Job ID: {job_id}")
                print(f"   Status: {job_status}")
                print(f"   Total Records: {total_records:,}")
                print(f"   Processed: {processed:,}")
                print(f"   Deleted: {deleted:,}")
                print(f"   Not Found: {not_found:,}")
                print(f"   Started: {status.get('started_at', 'N/A')}")
                print(f"   Completed: {status.get('completed_at', 'N/A')}")
                
                # Calculate metrics
                total_time = time.time() - start_poll_time
                print(f"\n⚡ Performance Metrics:")
                print(f"   Total Processing Time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
                print(f"   Average Speed: {processed / total_time:.0f} records/second")
                print(f"   Success Rate: {(deleted / processed * 100):.2f}% deleted")
                print(f"   Not Found Rate: {(not_found / processed * 100):.2f}%")
                
                return status
            
            elif job_status == 'failed':
                print("\n" + "="*100)
                print_header("❌ JOB FAILED")
                print(f"\n⚠️ Error: {status.get('error', 'Unknown error')}")
                print(f"   Processed before failure: {processed:,} / {total_records:,}")
                print(f"   Deleted before failure: {deleted:,}")
                return status
            
        except requests.exceptions.RequestException as e:
            print(f"\n⚠️ Poll {poll_count} failed: {str(e)}")
            time.sleep(5)  # Wait longer before retry
            continue
        
        except Exception as e:
            print(f"\n⚠️ Unexpected error: {str(e)}")
            time.sleep(5)
            continue
    
    # Timeout
    print("\n" + "="*100)
    print_header("⚠️ MAXIMUM POLLING TIME REACHED")
    print(f"\nJob may still be processing. Check status manually:")
    print(f"{status_url}")
    return None

def main():
    """Main test execution"""
    print_header("🧪 PRODUCTION BULK DELETE TEST - ASYNC VERSION")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    overall_start = time.time()
    
    # Step 1: Read Excel
    account_numbers = read_excel_file()
    if not account_numbers:
        print("\n❌ Failed to read Excel file. Aborting test.")
        return
    
    total_records = len(account_numbers)
    
    # Step 2: Send delete request
    result = send_delete_request()
    if not result:
        print("\n❌ Failed to initiate delete request. Aborting test.")
        return
    
    job_id = result.get('job_id')
    if not job_id:
        print("\n❌ No job_id in response. Aborting test.")
        return
    
    # Step 3: Poll status
    final_status = poll_job_status(job_id, total_records)
    
    # Summary
    overall_time = time.time() - overall_start
    print_header("📊 TEST SUMMARY")
    print(f"\n⏱️ Total Test Duration: {overall_time:.2f} seconds ({overall_time/60:.2f} minutes)")
    
    if final_status and final_status.get('status') == 'completed':
        print(f"✅ Result: SUCCESS")
        print(f"   {final_status['deleted_count']:,} accounts deleted")
        print(f"   {final_status['not_found_count']:,} accounts not found")
    elif final_status and final_status.get('status') == 'failed':
        print(f"❌ Result: FAILED")
        print(f"   Error: {final_status.get('error', 'Unknown')}")
    else:
        print(f"⚠️ Result: INCOMPLETE")
        print(f"   Job may still be running")
    
    print("\n" + "="*100)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
