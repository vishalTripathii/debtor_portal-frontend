from api.database import get_debtors_collection

debtors = get_debtors_collection()
count = debtors.count_documents({})
print(f'Total debtors in database: {count}')

if count > 0:
    sample = debtors.find_one()
    print(f'\nSample debtor:')
    print(f'  National ID: {sample.get("national_id")}')
    print(f'  Account: {sample.get("account_number")}')
    print(f'  Email: {sample.get("email")}')
else:
    print('\nNo debtors found. You need to upload debtor data first.')
