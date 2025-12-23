#!/usr/bin/env python3
import os
import sys
sys.path.append('/Users/apple/Desktop/Collections_Debtor_page/backend')

from api.database import get_processing_jobs_collection, get_debtors_collection

def check_upload_status():
    try:
        # Check the processing job
        jobs_collection = get_processing_jobs_collection()
        job = jobs_collection.find_one({'job_id': 'UPLOAD-20251216214740-8023'})
        
        if job:
            print("📊 Excel Upload Status:")
            print(f"  Job ID: {job.get('job_id')}")
            print(f"  Status: {job.get('status')}")
            print(f"  Total Records: {job.get('total_records', 0)}")
            print(f"  Processed: {job.get('processed_records', 0)}")
            print(f"  Inserted: {job.get('inserted_count', 0)}")
            print(f"  Updated: {job.get('updated_count', 0)}")
            print(f"  Failed: {job.get('failed_count', 0)}")
            print(f"  Current Chunk: {job.get('current_chunk', 0)}")
            print(f"  Total Chunks: {job.get('total_chunks', 0)}")
            
            # Calculate progress
            if job.get('total_records', 0) > 0:
                progress = (job.get('processed_records', 0) / job.get('total_records', 0)) * 100
                print(f"  Progress: {progress:.1f}%")
        else:
            print("❌ Job not found")
            
        # Check total debtors
        debtors_collection = get_debtors_collection()
        total_debtors = debtors_collection.count_documents({})
        print(f"\n📈 Total Debtors in Database: {total_debtors}")
        
        return job
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    check_upload_status()