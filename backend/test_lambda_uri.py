#!/usr/bin/env python3
from pymongo import MongoClient

# Test the exact URI that Lambda has
lambda_uri = "mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&appName=debtor-portal-cluster"

print("Testing Lambda's exact MongoDB URI...")
print(f"URI: {lambda_uri[:60]}...")

try:
    client = MongoClient(lambda_uri, serverSelectionTimeoutMS=10000)
    db = client.debtor_portal
    collections = db.list_collection_names()
    print(f"✓ SUCCESS! Connected to database")
    print(f"  Collections found: {len(collections)}")
    
    # Try to count debtors to verify full access
    debtors_count = db.debtors.count_documents({})
    print(f"  Debtors in database: {debtors_count}")
    client.close()
except Exception as e:
    print(f"✗ FAILED: {str(e)}")
    print(f"\nFull error: {repr(e)}")
