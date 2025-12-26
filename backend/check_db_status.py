import pymongo

client = pymongo.MongoClient('mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority')
db = client['debtor_portal']

print('=== MongoDB Collections Status ===')
print(f'debtors: {db.debtors.count_documents({})}')
print(f'debtor_images: {db.debtor_images.count_documents({})}')
print(f'qr_mappings: {db.qr_mappings.count_documents({})}')
print(f'processing_jobs: {db.processing_jobs.count_documents({})}')

print()
print('=== Sample from debtor_images ===')
sample = db.debtor_images.find_one()
if sample:
    sample['_id'] = str(sample['_id'])
    for k, v in sample.items():
        print(f'  {k}: {v}')
else:
    print('  No records')

client.close()
