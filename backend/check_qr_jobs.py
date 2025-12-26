"""Check QR job status"""
from pymongo import MongoClient

client = MongoClient('mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal')
db = client['debtor_portal']

jobs = list(db.processing_jobs.find({'type': 'qr_upload'}).sort('created_at', -1).limit(5))
for j in jobs:
    print(f"Job: {j.get('job_id')}")
    print(f"  Status: {j.get('status')}")
    print(f"  Total: {j.get('total_images')}, Processed: {j.get('processed_images')}")
    print(f"  Uploaded: {j.get('uploaded_count')}, NotFound: {j.get('not_found_count')}")
    print(f"  Errors: {j.get('error_count')}")
    print(f"  Created: {j.get('created_at')}")
    print(f"  Completed: {j.get('completed_at')}")
    print()

client.close()
