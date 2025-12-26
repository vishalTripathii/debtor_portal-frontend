"""Check specific QR job status"""
from pymongo import MongoClient

client = MongoClient('mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal')
db = client['debtor_portal']

job = db.processing_jobs.find_one({'job_id': 'QR-20251224165033-9987'})
if job:
    print('Job ID:', job.get('job_id'))
    print('Status:', job.get('status'))
    print('Total:', job.get('total_images'))
    print('Processed:', job.get('processed_images'))
    print('Uploaded:', job.get('uploaded_count'))
    print('NotFound:', job.get('not_found_count'))
    print('Errors:', job.get('error_count'))
    print('Created:', job.get('created_at'))
    print('Started:', job.get('started_at'))
    print('Completed:', job.get('completed_at'))
else:
    print('Job not found')

client.close()
