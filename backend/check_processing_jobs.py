import pymongo

client = pymongo.MongoClient('mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority')
db = client['debtor_portal']

print("=== Processing Jobs (excel_upload) ===")
docs = list(db.processing_jobs.find({'type': 'excel_upload'}).sort('created_at', -1).limit(5))
print(f"Found {len(docs)} records\n")

for doc in docs:
    print(f"job_id: {doc.get('job_id')}")
    print(f"  file_size: {doc.get('file_size')}")
    print(f"  total_records: {doc.get('total_records')}")
    print(f"  inserted_count: {doc.get('inserted_count')}")
    print(f"  updated_count: {doc.get('updated_count')}")
    print(f"  status: {doc.get('status')}")
    print()

client.close()
