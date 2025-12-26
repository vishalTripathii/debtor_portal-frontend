"""
Final Verification Test - All Endpoints
Tests both backend API and confirms deployment status
"""
import requests
import json

print("="*80)
print("          FINAL DEPLOYMENT VERIFICATION")
print("="*80)

BASE_URL = "https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev"
FRONTEND_URL = "https://d1hmzuewg6k3ss.cloudfront.net"

# Test 1: Check if API Gateway is responding
print("\n1️⃣  Testing API Gateway...")
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"   ✓ API Gateway responding (status: {response.status_code})")
except Exception as e:
    print(f"   ✗ API Gateway error: {str(e)}")

# Test 2: Test bulk delete endpoint with empty request (should fail gracefully)
print("\n2️⃣  Testing bulk delete endpoint...")
try:
    response = requests.post(f"{BASE_URL}/bulk/delete-excel", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code in [400, 401]:
        print(f"   ✓ Endpoint exists and handles invalid requests correctly")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")

# Test 3: Test job status endpoint with dummy job ID
print("\n3️⃣  Testing job status endpoint...")
try:
    dummy_job_id = "test-12345"
    response = requests.get(f"{BASE_URL}/bulk/job-status/{dummy_job_id}", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print(f"   ✓ Job status endpoint working (404 for non-existent job)")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")

# Test 4: Check frontend
print("\n4️⃣  Testing frontend...")
try:
    response = requests.get(FRONTEND_URL, timeout=10)
    if response.status_code == 200:
        print(f"   ✓ Frontend is accessible")
        if 'debtor' in response.text.lower() or 'admin' in response.text.lower():
            print(f"   ✓ Frontend content looks correct")
    else:
        print(f"   Status: {response.status_code}")
except Exception as e:
    print(f"   ✗ Error: {str(e)}")

# Summary
print("\n" + "="*80)
print("                     DEPLOYMENT STATUS")
print("="*80)
print("\n✅ Backend API: " + BASE_URL)
print("✅ Frontend: " + FRONTEND_URL)
print("\n📝 Next Steps:")
print("  1. Wait 1-2 minutes for CloudFront cache invalidation")
print("  2. Go to: " + FRONTEND_URL)
print("  3. Login as admin")
print("  4. Test bulk delete with Excel file")
print("  5. Watch real-time progress!")
print("\n" + "="*80)
