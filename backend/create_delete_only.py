"""Create delete-only Excel with just account_number column"""
import pandas as pd

# Create delete-only Excel with just account_number column
account_numbers = [f'TEST_DELETE_{i:04d}' for i in range(1, 101)]
df = pd.DataFrame({'account_number': account_numbers})

output_path = r'E:\Collections_Debtor_page\Collections_Debtor_page\backend\delete_only_100.xlsx'
df.to_excel(output_path, index=False)

print(f'Created: {output_path}')
print(f'Entries: {len(df)}')
print('\nPreview:')
print(df.head(5).to_string())
print('...')
print(df.tail(3).to_string())
