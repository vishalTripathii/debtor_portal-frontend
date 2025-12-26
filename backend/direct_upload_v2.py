"""
FAST Direct MongoDB Upload Script with retry
Uses bulk operations with smaller batches and retry logic
"""

import pymongo
from pymongo import UpdateOne
import pandas as pd
from datetime import datetime, timezone
import time

# MongoDB connection with longer timeout
MONGO_URI = "mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&serverSelectionTimeoutMS=60000&socketTimeoutMS=120000&connectTimeoutMS=60000"

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
    if value is None or pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        str_val = str(value).replace(',', '').replace('฿', '').replace('$', '').strip()
        return float(str_val) if str_val else 0.0
    except:
        return 0.0

def bulk_write_with_retry(collection, operations, max_retries=3):
    """Execute bulk write with retry logic"""
    for attempt in range(max_retries):
        try:
            result = collection.bulk_write(operations, ordered=False)
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"      Retry {attempt + 1}/{max_retries} after error: {str(e)[:50]}...")
                time.sleep(2)
            else:
                raise

def upload_file_bulk(filepath, collection, file_num):
    """Upload a single Excel file using bulk operations"""
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
    
    # Prepare bulk operations
    now = datetime.now(timezone.utc)
    operations = []
    
    for _, row in df.iterrows():
        account_number = str(row.get('account_number', '')).strip()
        if not account_number:
            continue
        
        clean_record = {
            'account_number': account_number,
            'national_id': str(row.get('national_id', '')).strip() if pd.notna(row.get('national_id')) else '',
            'original_creditor': str(row.get('original_creditor', '')).strip() if pd.notna(row.get('original_creditor')) else '',
            'outstanding_balance': parse_currency(row.get('outstanding_balance')),
            'debt_type': str(row.get('debt_type', '')).strip() if pd.notna(row.get('debt_type')) else '',
            'loan_contract_date': str(row.get('loan_contract_date', '')).strip() if pd.notna(row.get('loan_contract_date')) else '',
            'name': str(row.get('name', '')).strip() if pd.notna(row.get('name')) else '',
            'phone': str(row.get('phone', '')).strip() if pd.notna(row.get('phone')) else '',
            'email': str(row.get('email', '')).strip() if pd.notna(row.get('email')) else '',
            'updated_at': now,
        }
        
        operations.append(UpdateOne(
            {'account_number': account_number},
            {'$set': clean_record, '$setOnInsert': {'created_at': now}},
            upsert=True
        ))
    
    print(f"    Executing bulk write ({len(operations)} operations)...")
    
    # Execute bulk write in smaller batches of 1000
    batch_size = 1000
    total_inserted = 0
    total_updated = 0
    
    for i in range(0, len(operations), batch_size):
        batch = operations[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(operations) + batch_size - 1) // batch_size
        
        try:
            result = bulk_write_with_retry(collection, batch)
            total_inserted += result.upserted_count
            total_updated += result.modified_count
            print(f"    Batch {batch_num}/{total_batches}: +{result.upserted_count} inserted, {result.modified_count} updated")
        except Exception as e:
            print(f"    Batch {batch_num} FAILED: {str(e)[:100]}")
    
    print(f"    File complete: {total_inserted} inserted, {total_updated} updated")
    return total_inserted, total_updated

def main():
    print("=" * 60)
    print("FAST DIRECT MONGODB UPLOAD (BULK)")
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
            inserted, updated = upload_file_bulk(filepath, collection, i)
            total_inserted += inserted
            total_updated += updated
        except Exception as e:
            print(f"    ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
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
