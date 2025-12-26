import pymongo

client = pymongo.MongoClient('mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority')
db = client['debtor_portal']

print('Deleting debtor_images...')
result = db.debtor_images.delete_many({})
print(f'Deleted {result.deleted_count} records')

print(f'debtor_images now: {db.debtor_images.count_documents({})}')
client.close()
