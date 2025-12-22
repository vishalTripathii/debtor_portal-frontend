from api.database import get_debtors_collection

debtors = get_debtors_collection()

# Create a test debtor
test_debtor = {
    'national_id': '1100200120741',
    'account_number': 'TEST001',
    'name': 'Test Debtor',
    'email': 'test@example.com',
    'phone': '0812345678',
    'principal_amount': 100000,
    'interest_amount': 10000,
    'total_amount': 110000,
    'created_at': '2025-12-22',
    'pdpa_accepted': False,
    'payment_consent': False
}

result = debtors.insert_one(test_debtor)
print(f'Test debtor created successfully!')
print(f'National ID: {test_debtor["national_id"]}')
print(f'Email: {test_debtor["email"]}')
print(f'\nYou can now login with National ID: 1100200120741')
