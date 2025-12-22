#!/usr/bin/env python3
"""
Test PDF Processing Functionality
"""

import requests
import json

def test_pdf_staging():
    """Test PDF staging endpoint"""
    
    base_url = "https://29o7gp9n8l.execute-api.ap-southeast-1.amazonaws.com/dev"
    
    print("🔍 Testing PDF Processing")
    print("=" * 40)
    
    # Step 1: Test admin login
    print("1. Testing admin login...")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/admin/login/", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✅ Login successful, token: {token[:20]}...")
            
            # Step 2: Test PDF staging endpoint structure
            print("\n2. Testing PDF staging endpoint (no files)...")
            
            headers = {
                'Authorization': f'Bearer {token}',
            }
            
            # Test with no files
            response = requests.post(f"{base_url}/api/admin/pdf/stage/", headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code == 400:
                data = response.json()
                if data.get('error') == 'No files uploaded':
                    print("✅ PDF staging endpoint is working (expects files)")
                else:
                    print(f"❌ Unexpected error: {data.get('error')}")
            else:
                print("❌ Unexpected status code")
                
            # Step 3: Test with real PDF file
            print("\n3. Testing with real PDF file (ACC-10001.pdf)...")
            
            # Try to read the actual PDF file
            possible_paths = [
                "/Users/apple/Downloads/Collections_Debtor_page/ACC-10001.pdf",
                "/Users/apple/Downloads/ACC-10001.pdf", 
                "/Users/apple/Desktop/ACC-10001.pdf",
                "./ACC-10001.pdf"
            ]
            
            pdf_content = None
            pdf_path = None
            
            for path in possible_paths:
                try:
                    with open(path, 'rb') as f:
                        pdf_content = f.read()
                        pdf_path = path
                        break
                except FileNotFoundError:
                    continue
            
            if pdf_content:
                print(f"✅ Found PDF file at: {pdf_path}")
                print(f"   File size: {len(pdf_content)} bytes")
                
                # Test 1: Multipart upload (might not work in Lambda)
                print("\n   Testing multipart upload...")
                files = {
                    'files': ('ACC-10001.pdf', pdf_content, 'application/pdf')
                }
                
                response = requests.post(f"{base_url}/api/admin/pdf/stage/", 
                                       headers=headers, 
                                       files=files)
                
                print(f"   Multipart Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ Multipart upload works!")
                else:
                    print("   ❌ Multipart failed, trying base64...")
                    
                    # Test 2: Base64 upload (Lambda-compatible)
                    import base64
                    pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                    
                    base64_data = {
                        "files": [
                            {
                                "filename": "ACC-10001.pdf",
                                "content": pdf_base64
                            }
                        ]
                    }
                    
                    headers_json = {
                        'Authorization': headers['Authorization'],
                        'Content-Type': 'application/json'
                    }
                    
                    response = requests.post(f"{base_url}/api/admin/pdf/stage-base64/", 
                                           headers=headers_json, 
                                           json=base64_data)
                    
                    print(f"   Base64 Status: {response.status_code}")
                    print(f"   Response: {response.text[:300]}...")
                    
                    if response.status_code == 200:
                        print("   ✅ Base64 upload works!")
                        data = response.json()
                        print(f"   Job ID: {data.get('job_id')}")
                        print(f"   Staged: {data.get('staged')} files")
                    else:
                        print("   ❌ Both uploads failed")
                        
            else:
                print("❌ ACC-10001.pdf not found in any common location")
                
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health():
    """Test basic API health"""
    
    base_url = "https://29o7gp9n8l.execute-api.ap-southeast-1.amazonaws.com/dev"
    
    print("\n🔍 Testing API Health")
    print("=" * 40)
    
    try:
        response = requests.get(f"{base_url}/api/health/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print("❌ API health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    # Test API health first
    if test_health():
        # Test PDF functionality
        test_pdf_staging()
    else:
        print("💥 API is not responding, cannot test PDF processing")