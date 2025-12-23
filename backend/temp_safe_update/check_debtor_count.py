#!/usr/bin/env python3
import os
import sys
sys.path.append('/Users/apple/Desktop/Collections_Debtor_page/backend')

from pymongo import MongoClient

def get_debtor_count():
    try:
        # MongoDB connection
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb+srv://poweramc:poweramc123@cluster0.n9w9d.mongodb.net/debtor_portal?retryWrites=true&w=majority')
        client = MongoClient(mongo_uri)
        db = client['debtor_portal']
        debtors_collection = db['debtors']
        
        # Get total count
        total_count = debtors_collection.count_documents({})
        print(f"Total debtors in MongoDB: {total_count}")
        
        # Get some sample account numbers to verify
        sample_debtors = list(debtors_collection.find({}, {'account_number': 1, 'name': 1}).limit(5))
        print("\nSample debtors:")
        for debtor in sample_debtors:
            print(f"  {debtor.get('account_number')} - {debtor.get('name', 'No name')}")
            
        return total_count
        
    except Exception as e:
        print(f"Error checking debtor count: {e}")
        return None

if __name__ == "__main__":
    count = get_debtor_count()
    if count:
        print(f"\n✅ MongoDB has {count} debtors")
    else:
        print("❌ Failed to get debtor count")