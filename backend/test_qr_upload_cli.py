#!/usr/bin/env python3
"""
CLI Test Script for QR Upload
This script uploads QR codes directly to the backend API for testing purposes.
"""

import os
import sys
import json
import zipfile
import tempfile
import requests
from io import BytesIO

# Configuration
API_BASE_URL = "https://29o7gp9n8l.execute-api.ap-southeast-1.amazonaws.com/dev"
QR_FOLDER = "/Users/apple/Downloads/qr_codes"
MAX_FILES = 100  # Number of files to upload

def get_admin_token():
    """Login as admin and get JWT token"""
    print("Logging in as admin...")
    
    response = requests.post(
        f"{API_BASE_URL}/api/admin/login/",
        json={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    data = response.json()
    token = data.get("token")
    print(f"Login successful! Token: {token[:20]}...")
    return token

def create_zip_from_qr_files(folder_path, max_files=100):
    """Create a ZIP file from QR images in the specified folder"""
    print(f"\nCollecting up to {max_files} QR images from {folder_path}...")
    
    # Get list of image files
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')
    files = [f for f in os.listdir(folder_path) 
             if f.lower().endswith(image_extensions)]
    
    # Limit to max_files
    files = files[:max_files]
    
    print(f"Found {len(files)} QR images to upload")
    
    # Create ZIP in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in files:
            file_path = os.path.join(folder_path, filename)
            zip_file.write(file_path, filename)
            print(f"  Added: {filename}")
    
    zip_buffer.seek(0)
    return zip_buffer, len(files)

def upload_qr_codes(token, zip_buffer, filename="test_qr_upload.zip"):
    """Upload QR codes using presigned URL method"""
    print(f"\n1. Requesting presigned URL for {filename}...")
    
    # Get file size
    zip_buffer.seek(0, 2)  # Seek to end
    file_size = zip_buffer.tell()
    zip_buffer.seek(0)  # Reset to beginning
    
    print(f"   File size: {file_size} bytes ({file_size / 1024:.1f} KB)")
    
    # Step 1: Get presigned URL
    presigned_response = requests.post(
        f"{API_BASE_URL}/api/admin/qr/upload-presigned/",
        json={
            "filename": filename,
            "file_size": file_size,
            "content_type": "application/zip"
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if presigned_response.status_code != 200:
        print(f"Failed to get presigned URL: {presigned_response.status_code}")
        print(f"Response: {presigned_response.text}")
        return None
    
    presigned_data = presigned_response.json()
    print(f"   Presigned response: {json.dumps(presigned_data, indent=2)}")
    
    presigned_url = presigned_data.get("presigned_url") or presigned_data.get("upload_url")
    job_id = presigned_data.get("job_id")
    
    if not presigned_url:
        print(f"   ERROR: No presigned URL in response!")
        print(f"   Response keys: {list(presigned_data.keys())}")
        return None
    
    print(f"   Got presigned URL for job: {job_id}")
    
    # Step 2: Upload directly to S3
    print(f"\n2. Uploading file to S3...")
    
    s3_response = requests.put(
        presigned_url,
        data=zip_buffer.read(),
        headers={"Content-Type": "application/zip"}
    )
    
    if s3_response.status_code not in (200, 204):
        print(f"S3 upload failed: {s3_response.status_code}")
        print(f"Response: {s3_response.text}")
        return None
    
    print(f"   S3 upload successful!")
    
    # Step 3: Start processing
    print(f"\n3. Starting QR processing...")
    
    process_response = requests.post(
        f"{API_BASE_URL}/api/admin/qr/start-processing/",
        json={"job_id": job_id},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if process_response.status_code != 200:
        print(f"Failed to start processing: {process_response.status_code}")
        print(f"Response: {process_response.text}")
        return None
    
    print(f"   Processing started!")
    
    return job_id

def poll_status(token, job_id, max_polls=60):
    """Poll for upload status until complete"""
    import time
    
    print(f"\n4. Polling for status (job: {job_id})...")
    
    for i in range(max_polls):
        response = requests.get(
            f"{API_BASE_URL}/api/admin/qr/upload-status/{job_id}/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            print(f"   Poll {i+1}: Failed with status {response.status_code}")
            time.sleep(3)
            continue
        
        data = response.json()
        status = data.get("status")
        total = data.get("total_images", 0)
        processed = data.get("processed_images", 0)
        percentage = data.get("percentage", 0)
        uploaded = data.get("uploaded_count", 0)
        not_found = data.get("not_found_count", 0)
        errors = data.get("errors", [])
        
        print(f"   Poll {i+1}: {status} - {processed}/{total} images ({percentage}%)")
        
        if status == "completed":
            print(f"\n✅ UPLOAD COMPLETED SUCCESSFULLY!")
            print(f"   Total images: {total}")
            print(f"   Uploaded: {uploaded}")
            print(f"   Not found (no matching debtor): {not_found}")
            print(f"   Errors: {len(errors) if isinstance(errors, list) else errors}")
            return data
        
        if status == "failed":
            print(f"\n❌ UPLOAD FAILED!")
            print(f"   Errors: {errors}")
            return data
        
        time.sleep(3)
    
    print(f"\n⚠️ Polling timeout after {max_polls * 3} seconds")
    return None

def main():
    print("=" * 60)
    print("QR Upload CLI Test Script")
    print("=" * 60)
    
    # Step 1: Login
    token = get_admin_token()
    if not token:
        print("Failed to login. Exiting.")
        sys.exit(1)
    
    # Step 2: Create ZIP from QR files
    try:
        zip_buffer, file_count = create_zip_from_qr_files(QR_FOLDER, MAX_FILES)
    except Exception as e:
        print(f"Failed to create ZIP: {e}")
        sys.exit(1)
    
    if file_count == 0:
        print("No files found to upload. Exiting.")
        sys.exit(1)
    
    # Step 3: Upload
    job_id = upload_qr_codes(token, zip_buffer, f"cli_test_{file_count}_images.zip")
    if not job_id:
        print("Failed to upload. Exiting.")
        sys.exit(1)
    
    # Step 4: Poll for completion
    result = poll_status(token, job_id)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    
    if result and result.get("status") == "completed":
        print("\n✅ SUCCESS! The QR upload system is working correctly.")
        print("\nSummary:")
        print(f"  - Job ID: {job_id}")
        print(f"  - Total images processed: {result.get('total_images', 0)}")
        print(f"  - Uploaded to debtors: {result.get('uploaded_count', 0)}")
        print(f"  - No matching debtor: {result.get('not_found_count', 0)}")
        return 0
    else:
        print("\n❌ FAILED! Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
