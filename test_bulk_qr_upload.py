#!/usr/bin/env python3
"""
Test script for bulk QR upload functionality
"""
import requests
import base64
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# API Configuration
API_URL = "https://29o7gp9n8l.execute-api.ap-southeast-1.amazonaws.com/dev/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def login_admin():
    """Login as admin and get JWT token"""
    print("🔐 Logging in as admin...")
    response = requests.post(
        f"{API_URL}/admin/login/",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ Login successful! Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def get_debtors(token):
    """Get list of debtors to use for testing"""
    print("\n📋 Fetching debtors...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/admin/debtors/", headers=headers)
    
    if response.status_code == 200:
        debtors = response.json().get('debtors', [])
        print(f"✅ Found {len(debtors)} debtors")
        return debtors[:3]  # Return first 3 for testing
    else:
        print(f"❌ Failed to fetch debtors: {response.text}")
        return []

def create_test_qr_image(account_number):
    """Create a simple test QR image"""
    # Create a simple image with account number as text
    img = Image.new('RGB', (200, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple QR-like pattern
    draw.rectangle([20, 20, 180, 180], outline='black', width=2)
    draw.text((100, 100), account_number, fill='black', anchor='mm')
    
    # Convert to bytes
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

def test_single_image_upload(token, account_number):
    """Test uploading a single QR image"""
    print(f"\n📤 Test 1: Single image upload for account {account_number}")
    
    # Create test image
    image_data = create_test_qr_image(account_number)
    
    # Upload as multipart
    headers = {"Authorization": f"Bearer {token}"}
    files = {
        'files': (f'{account_number}.png', image_data, 'image/png')
    }
    
    response = requests.post(
        f"{API_URL}/admin/qr/bulk-upload/",
        headers=headers,
        files=files
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_base64_upload(token, account_number):
    """Test uploading QR image via base64"""
    print(f"\n📤 Test 2: Base64 upload for account {account_number}")
    
    # Create test image
    image_data = create_test_qr_image(account_number)
    base64_content = base64.b64encode(image_data).decode('utf-8')
    
    # Upload as base64
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "files": [
            {
                "filename": f"{account_number}.png",
                "content": base64_content
            }
        ]
    }
    
    response = requests.post(
        f"{API_URL}/admin/qr/bulk-upload-base64/",
        headers=headers,
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_zip_upload(token, debtors):
    """Test uploading a ZIP file with multiple QR images"""
    print(f"\n📤 Test 3: ZIP file upload with {len(debtors)} images")
    
    import zipfile
    
    # Create a ZIP file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for debtor in debtors:
            account_number = debtor.get('account_number')
            image_data = create_test_qr_image(account_number)
            zip_file.writestr(f"{account_number}.png", image_data)
    
    zip_buffer.seek(0)
    
    # Upload ZIP file
    headers = {"Authorization": f"Bearer {token}"}
    files = {
        'files': ('qr_codes.zip', zip_buffer.getvalue(), 'application/zip')
    }
    
    response = requests.post(
        f"{API_URL}/admin/qr/bulk-upload/",
        headers=headers,
        files=files
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def verify_qr_upload(token, account_number):
    """Verify QR image was uploaded successfully"""
    print(f"\n🔍 Verifying upload for account {account_number}")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_URL}/admin/images/{account_number}/",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('image'):
            print(f"✅ QR image found for account {account_number}")
            print(f"   Filename: {data['image'].get('filename')}")
            print(f"   Content-Type: {data['image'].get('content_type')}")
            return True
        else:
            print(f"⚠️  No image found for account {account_number}")
            return False
    else:
        print(f"❌ Failed to verify: {response.text}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Bulk QR Upload Testing")
    print("=" * 60)
    
    # Login
    token = login_admin()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    # Get test debtors
    debtors = get_debtors(token)
    if len(debtors) < 1:
        print("\n❌ Need at least 1 debtor for testing")
        return
    
    results = []
    
    # Test 1: Single image upload
    if len(debtors) >= 1:
        account1 = debtors[0].get('account_number')
        success = test_single_image_upload(token, account1)
        results.append(("Single Image Upload", success))
        if success:
            verify_qr_upload(token, account1)
    
    # Test 2: Base64 upload
    if len(debtors) >= 2:
        account2 = debtors[1].get('account_number')
        success = test_base64_upload(token, account2)
        results.append(("Base64 Upload", success))
        if success:
            verify_qr_upload(token, account2)
    
    # Test 3: ZIP upload
    if len(debtors) >= 3:
        success = test_zip_upload(token, debtors)
        results.append(("ZIP Upload", success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")

if __name__ == "__main__":
    main()
