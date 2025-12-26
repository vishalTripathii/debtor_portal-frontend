"""Create 100 dummy debtor entries Excel matching DB structure"""
import pandas as pd
from datetime import datetime

# Create 100 dummy entries with unique test account numbers
dummy_data = []

for i in range(1, 101):
    dummy_data.append({
        'account_number': f'TEST_DELETE_{i:04d}',  # TEST_DELETE_0001 to TEST_DELETE_0100
        'name': f'Test Debtor {i}',
        'email': f'testdebtor{i}@test.com',
        'phone': f'080000{i:04d}',
        'national_id': f'1111111{i:06d}',
        'debt_type': 'TEST_LOAN',
        'original_creditor': 'Test Creditor',
        'outstanding_balance': 1000.00 + i,
        'loan_contract_date': '2025-01-01 00:00:00'
    })

# Create DataFrame
df = pd.DataFrame(dummy_data)

# Save to Excel
output_path = r'E:\Collections_Debtor_page\Collections_Debtor_page\backend\test_bulk_delete_100.xlsx'
df.to_excel(output_path, index=False)

print(f"Created Excel with {len(df)} dummy entries")
print(f"File saved to: {output_path}")
print("\nSample entries:")
print(df.head(5).to_string())
print("\n...")
print(df.tail(3).to_string())
