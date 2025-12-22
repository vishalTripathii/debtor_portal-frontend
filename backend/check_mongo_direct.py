#!/usr/bin/env python3
import pymongo
import os

def check_mongo_direct():
    try:
        # Direct MongoDB connection
        mongo_uri = "mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&appName=debtor-portal-cluster"
        client = pymongo.MongoClient(mongo_uri)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Get database and collection
        db = client['debtor_portal']
        debtors_collection = db['debtors']
        jobs_collection = db['processing_jobs']
        
        # Get total debtor count
        total_debtors = debtors_collection.count_documents({})
        print(f"📊 Total Debtors: {total_debtors}")
        
        # Check the specific upload job
        job = jobs_collection.find_one({'job_id': 'UPLOAD-20251216214740-8023'})
        if job:
            print(f"\n📋 Excel Upload Job Status:")
            print(f"  Status: {job.get('status', 'unknown')}")
            print(f"  Total Records: {job.get('total_records', 0)}")
            print(f"  Processed: {job.get('processed_records', 0)}")
            print(f"  Inserted: {job.get('inserted_count', 0)}")
            print(f"  Updated: {job.get('updated_count', 0)}")
            print(f"  Failed: {job.get('failed_count', 0)}")
            
            if job.get('total_records', 0) > 0:
                progress = (job.get('processed_records', 0) / job.get('total_records', 0)) * 100
                print(f"  Progress: {progress:.1f}%")
                
            # Check if it's still running
            if job.get('status') == 'processing':
                print("  🔄 Job is still processing...")
            elif job.get('status') == 'completed':
                print("  ✅ Job completed!")
            else:
                print(f"  ⚠️  Job status: {job.get('status')}")
        else:
            print("❌ Upload job not found")
            
        # Get recent debtors to see if new ones are being added
        recent_debtors = list(debtors_collection.find({}).sort('_id', -1).limit(5))
        print(f"\n📝 Last 5 debtors added:")
        for debtor in recent_debtors:
            print(f"  {debtor.get('account_number')} - {debtor.get('name', 'No name')}")
            
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_mongo_direct()