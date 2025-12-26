"""
Direct MongoDB Upload Script
Uploads debtor data from Excel files directly to MongoDB (bypasses frontend)
"""

import pymongo
import pandas as pd
from datetime import datetime

# MongoDB connection
MONGO_URI = "mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority"

# Excel files to upload
FILES = [
    r"C:\Users\tripa\Downloads\debtor_upload_template (3).xlsx",
    r"C:\Users\tripa\Downloads\debtor_upload_template_Live(1).xlsx",
    r"C:\Users\tripa\Downloads\debtor_upload_template (2).xlsx",
]

# Column mapping from Excel to MongoDB
COLUMN_MAPPING = {
    'Account Number': 'account_number',
    'National ID': 'national_id',
    'Original Creditor': 'original_creditor',
    'Outstanding Balance': 'outstanding_balance',
    'Debt Type': 'debt_type',
    'Loan CONTRACT DATE': 'loan_contract_date',
    'Name': 'name',
    'Phone': 'phone',
    'Email': 'email'
}

def parse_currency(value):
    """Parse currency/number values"""
    if value is None or pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        str_val = str(value).replace(',', '').replace('฿', '').replace('$', '').strip()
        return float(str_val) if str_val else 0.0
    except:
        return 0.0

def upload_file(filepath, collection, file_num):
    """Upload a single Excel file to MongoDB"""
    print(f"\n[{file_num}] Processing: {filepath}")
    
    # Read Excel file
    df = pd.read_excel(filepath, engine='openpyxl')
    print(f"    Rows in file: {len(df)}")
    
    # Rename columns
    df = df.rename(columns=COLUMN_MAPPING)
    
    # Drop rows with empty account_number
    df = df.dropna(subset=['account_number'])
    df = df[df['account_number'].notna()]
    print(f"    Valid rows: {len(df)}")
    
    # Convert to records
    records = df.to_dict('records')
    
    inserted = 0
    updated = 0
    
    for record in records:
        # Clean up the record
        clean_record = {
            'account_number': str(record.get('account_number', '')).strip(),
            'national_id': str(record.get('national_id', '')).strip() if pd.notna(record.get('national_id')) else '',
            'original_creditor': str(record.get('original_creditor', '')).strip() if pd.notna(record.get('original_creditor')) else '',
            'outstanding_balance': parse_currency(record.get('outstanding_balance')),
            'debt_type': str(record.get('debt_type', '')).strip() if pd.notna(record.get('debt_type')) else '',
            'loan_contract_date': str(record.get('loan_contract_date', '')).strip() if pd.notna(record.get('loan_contract_date')) else '',
            'name': str(record.get('name', '')).strip() if pd.notna(record.get('name')) else '',
            'phone': str(record.get('phone', '')).strip() if pd.notna(record.get('phone')) else '',
            'email': str(record.get('email', '')).strip() if pd.notna(record.get('email')) else '',
            'updated_at': datetime.utcnow(),
        }
        
        # Skip if account_number is empty
        if not clean_record['account_number']:
            continue
        
        # Upsert (insert or update)
        result = collection.update_one(
            {'account_number': clean_record['account_number']},
            {'$set': clean_record, '$setOnInsert': {'created_at': datetime.utcnow()}},
            upsert=True
        )
        
        if result.upserted_id:
            inserted += 1
        elif result.modified_count > 0:
            updated += 1
    
    print(f"    Inserted: {inserted}, Updated: {updated}")
    return inserted, updated

def main():
    print("=" * 60)
    print("DIRECT MONGODB UPLOAD")
    print("=" * 60)
    print(f"Started: {datetime.now()}")
    
    # Connect to MongoDB
    print("\nConnecting to MongoDB...")
    client = pymongo.MongoClient(MONGO_URI)
    db = client['debtor_portal']
    collection = db['debtors']
    
    # Get initial count
    initial_count = collection.count_documents({})
    print(f"Current debtors in DB: {initial_count}")
    
    total_inserted = 0
    total_updated = 0
    
    # Process each file
    for i, filepath in enumerate(FILES, 1):
        try:
            inserted, updated = upload_file(filepath, collection, i)
            total_inserted += inserted
            total_updated += updated
        except Exception as e:
            print(f"    ERROR: {str(e)}")
    
    # Get final count
    final_count = collection.count_documents({})
    
    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE")
    print("=" * 60)
    print(f"Total Inserted: {total_inserted}")
    print(f"Total Updated: {total_updated}")
    print(f"Debtors before: {initial_count}")
    print(f"Debtors after: {final_count}")
    print(f"Net change: +{final_count - initial_count}")
    print(f"Finished: {datetime.now()}")
    
    client.close()

if __name__ == "__main__":
    main()
