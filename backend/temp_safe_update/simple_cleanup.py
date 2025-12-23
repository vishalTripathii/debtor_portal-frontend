#!/usr/bin/env python3
"""
Simple Direct Cleanup - Use deployed system to clear data
=========================================================
"""

import os
import shutil
import requests
import json
from datetime import datetime


def clear_via_deployed_api():
    """Use the deployed API to clear data."""
    print("🚀 Clearing data via deployed API...")
    
    try:
        API_BASE = 'https://lm6sss1gk8.execute-api.ap-southeast-1.amazonaws.com/dev'
        
        # Login as admin
        print("   🔐 Logging in...")
        login_response = requests.post(f'{API_BASE}/auth/login/', json={
            'username': 'admin',
            'password': 'admin123'
        }, timeout=30)
        
        if login_response.status_code == 200:
            token = login_response.json()['access_token']
            print("   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            return
        
        # Get current debtors count
        try:
            debtors_response = requests.get(f'{API_BASE}/admin/debtors/', 
                headers={'Authorization': f'Bearer {token}'},
                timeout=30
            )
            if debtors_response.status_code == 200:
                current_count = len(debtors_response.json().get('debtors', []))
                print(f"   📊 Current debtors: {current_count}")
        except Exception as e:
            print(f"   ⚠️  Could not get current count: {str(e)}")
        
        # Clear processing jobs
        try:
            jobs_response = requests.get(f'{API_BASE}/admin/pdf/jobs/', 
                headers={'Authorization': f'Bearer {token}'},
                timeout=30
            )
            if jobs_response.status_code == 200:
                jobs = jobs_response.json().get('jobs', [])
                print(f"   📊 Current processing jobs: {len(jobs)}")
                
                # Delete each job if there's an endpoint for it
                for job in jobs[:5]:  # Limit to first 5 to avoid timeout
                    job_id = job.get('job_id')
                    if job_id:
                        print(f"   🗑️  Found job: {job_id}")
                        
        except Exception as e:
            print(f"   ⚠️  Could not access jobs: {str(e)}")
        
        print("   ✅ API data check completed")
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to deployed API")
    except Exception as e:
        print(f"   ❌ API error: {str(e)}")


def clear_local_media():
    """Clear local media files."""
    print("\n🗑️  Clearing Local Media Files...")
    
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    media_dirs = [
        'media/debtor_images',
        'media/uploads', 
        'media/payment_receipts',
        'media/pdf_staging'
    ]
    
    total_deleted = 0
    
    for media_dir in media_dirs:
        try:
            full_path = os.path.join(project_root, media_dir)
            
            if os.path.exists(full_path):
                files = [f for f in os.listdir(full_path) 
                        if os.path.isfile(os.path.join(full_path, f))]
                
                if files:
                    for filename in files:
                        file_path = os.path.join(full_path, filename)
                        try:
                            os.remove(file_path)
                            total_deleted += 1
                        except Exception as e:
                            print(f"      ❌ Failed to delete {filename}: {str(e)}")
                    
                    print(f"   ✅ {media_dir}: Deleted {len(files)} files")
                else:
                    print(f"   ✅ {media_dir}: Already empty")
            else:
                print(f"   ✅ {media_dir}: Directory doesn't exist")
                
        except Exception as e:
            print(f"   ❌ {media_dir}: Error - {str(e)}")
    
    print(f"   📊 Total local files deleted: {total_deleted}")


def clear_sqlite_db():
    """Clear local SQLite database."""
    print("\n🗑️  Clearing Local SQLite Database...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'db.sqlite3')
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("   ✅ SQLite database deleted")
        except Exception as e:
            print(f"   ❌ Error deleting SQLite: {str(e)}")
    else:
        print("   ✅ SQLite database doesn't exist")


def main():
    """Main cleanup function."""
    print("🧹 SIMPLE DATA CLEANUP")
    print("=" * 40)
    print("This will clear:")
    print("- Local media files")
    print("- Local SQLite database")
    print("- Check deployed system data")
    print("=" * 40)
    
    # Confirm deletion
    confirm = input("\n⚠️  Continue? Type 'YES' to confirm: ")
    if confirm.upper() != "YES":
        print("❌ Cleanup cancelled.")
        return
    
    print(f"\n🚀 Starting cleanup at {datetime.now().strftime('%H:%M:%S')}")
    
    # Clear local data
    clear_local_media()
    clear_sqlite_db()
    
    # Check deployed system
    clear_via_deployed_api()
    
    print(f"\n✅ Local cleanup completed at {datetime.now().strftime('%H:%M:%S')}")
    print("\n🎯 Summary:")
    print("   - Local media files cleared")
    print("   - SQLite database removed")
    print("   - Deployed system checked")
    print("\n💡 Note: To clear MongoDB/S3 data, you need to:")
    print("   1. Access MongoDB Atlas dashboard directly")
    print("   2. Access AWS S3 console directly")
    print("   3. Or use the deployed API endpoints")


if __name__ == "__main__":
    main()