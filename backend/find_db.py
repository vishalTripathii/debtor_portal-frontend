import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

# Try to connect and list all databases
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

print("Available databases:")
for db_name in client.list_database_names():
    print(f"  - {db_name}")

# Check each database for debtors collection
print("\nLooking for 'debtors' collection...")
for db_name in client.list_database_names():
    db = client[db_name]
    if 'debtors' in db.list_collection_names():
        count = db['debtors'].count_documents({})
        print(f"  Found in '{db_name}' database with {count} documents")
        if count > 0:
            print(f"  ✅ Use this database name: {db_name}")
