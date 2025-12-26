import pymongo
import pandas as pd

# Connect to MongoDB - correct URI from Lambda
mongo_uri = "mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority"
client = pymongo.MongoClient(mongo_uri)
db = client['debtor_portal']

# Get 250 account numbers - field is 'account_number' (lowercase with underscore)
debtors = list(db.debtors.find({}, {'account_number': 1}).limit(250))
account_numbers = [d.get('account_number') for d in debtors if d.get('account_number')]

print(f'Found {len(account_numbers)} account numbers')

if account_numbers:
    print(f'\nFirst 5 accounts:')
    for acc in account_numbers[:5]:
        print(f'  - {acc}')

# Create Excel file with correct column name
df = pd.DataFrame({'account_number': account_numbers})
output_path = r'E:\Collections_Debtor_page\Collections_Debtor_page\test_bulk_delete_250_accounts.xlsx'
df.to_excel(output_path, index=False)
print(f'\nCreated: {output_path}')
print(f'Contains {len(account_numbers)} accounts for bulk delete testing')

client.close()
