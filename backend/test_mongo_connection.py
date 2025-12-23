#!/usr/bin/env python3
import os
from pymongo import MongoClient
from urllib.parse import quote_plus

# Try different connection string formats
username = "debtorportal"
password = "CyQfePqgUKMDvebF"

# URL encode the password in case of special characters
encoded_password = quote_plus(password)

connection_strings = [
    f"mongodb+srv://{username}:{password}@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority",
    f"mongodb+srv://{username}:{encoded_password}@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority",
    f"mongodb+srv://{username}:{password}@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&appName=debtor-portal-cluster",
]

for i, uri in enumerate(connection_strings, 1):
    print(f"\n--- Testing connection {i} ---")
    print(f"URI: {uri[:50]}...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Try to get database info
        db = client.debtor_portal
        collections = db.list_collection_names()
        print(f"✓ SUCCESS! Connected to database")
        print(f"  Collections found: {len(collections)}")
        if collections:
            print(f"  Sample collections: {collections[:3]}")
        client.close()
        break
    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        if "authentication failed" in str(e).lower():
            print("  → Authentication error - check username/password in MongoDB Atlas")
        elif "timeout" in str(e).lower():
            print("  → Connection timeout - check network/firewall")
