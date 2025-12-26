"""
Comprehensive API Endpoint Test
Tests all endpoints to verify complete system functionality
"""
import requests
import json

BASE_URL = "https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev"

print("="*80)
print("           COMPREHENSIVE API ENDPOINT TEST")
print("="*80)

results = []

# Test 1: Admin Login
print("\n1️⃣  Testing Admin Login...")
try:
    r = requests.post(f"{BASE_URL}/api/admin/login/", 
        json={"username": "admin", "password": "admin123"}, 
        timeout=30)
    if r.status_code == 200:
        data = r.json()
        token = data.get('token')
        print(f"   ✅ Login SUCCESS - Token received")
        results.append(("Admin Login", "✅ PASS"))
    else:
        print(f"   ❌ Login FAILED - Status: {r.status_code}")
        results.append(("Admin Login", f"❌ FAIL ({r.status_code})"))
        token = None
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    results.append(("Admin Login", f"❌ ERROR"))
    token = None

# Test 2: Get Debtors List (with auth)
print("\n2️⃣  Testing Get Debtors List...")
try:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{BASE_URL}/api/admin/debtors/", 
        headers=headers, timeout=30)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = data.get('count', len(data.get('results', [])))
        print(f"   ✅ SUCCESS - Found {count} debtors")
        results.append(("Get Debtors", "✅ PASS"))
    else:
        print(f"   ❌ FAILED - {r.text[:100]}")
        results.append(("Get Debtors", f"❌ FAIL ({r.status_code})"))
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    results.append(("Get Debtors", "❌ ERROR"))

# Test 3: Bulk Delete Endpoint
print("\n3️⃣  Testing Bulk Delete Endpoint (OPTIONS)...")
try:
    r = requests.options(f"{BASE_URL}/bulk/delete-excel", timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        print(f"   ✅ CORS preflight SUCCESS")
        results.append(("Bulk Delete CORS", "✅ PASS"))
    else:
        results.append(("Bulk Delete CORS", f"❌ FAIL ({r.status_code})"))
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    results.append(("Bulk Delete CORS", "❌ ERROR"))

# Test 4: Job Status Endpoint
print("\n4️⃣  Testing Job Status Endpoint...")
try:
    r = requests.get(f"{BASE_URL}/bulk/job-status/test-nonexistent", timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 404:
        print(f"   ✅ SUCCESS - Returns 404 for non-existent job")
        results.append(("Job Status", "✅ PASS"))
    else:
        print(f"   Response: {r.text[:100]}")
        results.append(("Job Status", f"⚠️ {r.status_code}"))
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    results.append(("Job Status", "❌ ERROR"))

# Test 5: Email Endpoint (OPTIONS)
print("\n5️⃣  Testing Email Endpoint (OPTIONS)...")
try:
    r = requests.options(f"{BASE_URL}/email/send-otp", timeout=10)
    print(f"   Status: {r.status_code}")
    results.append(("Email CORS", f"{'✅ PASS' if r.status_code == 200 else '⚠️ ' + str(r.status_code)}"))
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    results.append(("Email CORS", "❌ ERROR"))

# Test 6: Debtor Portal Access
print("\n6️⃣  Testing Debtor Portal Access...")
try:
    r = requests.post(f"{BASE_URL}/api/debtor/access/", 
        json={"account_number": "TEST123", "national_id": "TEST123"},
        timeout=10)
    print(f"   Status: {r.status_code}")
    # 404 or 400 is expected for non-existent debtor
    if r.status_code in [200, 400, 404]:
        print(f"   ✅ Endpoint responding")
        results.append(("Debtor Access", "✅ PASS"))
    else:
        results.append(("Debtor Access", f"⚠️ {r.status_code}"))
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    results.append(("Debtor Access", "❌ ERROR"))

# Summary
print("\n" + "="*80)
print("                         RESULTS SUMMARY")
print("="*80)
for name, status in results:
    print(f"  {name:25s} {status}")

passed = sum(1 for _, s in results if "PASS" in s)
total = len(results)
print("\n" + "-"*80)
print(f"  TOTAL: {passed}/{total} tests passed")
print("="*80)
