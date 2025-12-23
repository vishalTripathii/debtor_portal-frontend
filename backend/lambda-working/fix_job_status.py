#!/usr/bin/env python3

import pymongo
import os
from datetime import datetime

# MongoDB connection
MONGODB_URI = "mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal"

def fix_job_status():
    try:
        client = pymongo.MongoClient(MONGODB_URI)
        db = client.debtor_portal
        jobs_collection = db.processing_jobs
        
        # Find the job
        job_id = "QR-20251216192054-6689"
        job = jobs_collection.find_one({"job_id": job_id})
        
        if job:
            print(f"Current job status: {job.get('status')}")
            print(f"Total images: {job.get('total_images')}")
            print(f"Processed images: {job.get('processed_images')}")
            print(f"Percentage: {job.get('percentage')}")
            
            # Update the job status to completed
            update_result = jobs_collection.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "status": "completed",
                        "percentage": 100,
                        "processed_images": job.get('total_images', 1266),
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            if update_result.modified_count > 0:
                print("✅ Job status updated to 'completed'")
            else:
                print("❌ Failed to update job status")
                
        else:
            print("❌ Job not found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_job_status()