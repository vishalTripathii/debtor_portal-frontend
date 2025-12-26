"""Get debtor structure and create 100 dummy entries Excel"""
from pymongo import MongoClient
import pandas as pd

client = MongoClient('mongodb+srv://debtorportal:CyQfePqgUKMDvebF@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal')
db = client['debtor_portal']

# Get sample debtor structure
sample = db.debtors.find_one()
print("=== Debtor Structure ===")
for k, v in sample.items():
    print(f"  {k}: {type(v).__name__} = {repr(v)[:60]}")

client.close()
