#!/usr/bin/env python3
import pymongo
import os

def check_complete_status():
    try:
        # Direct MongoDB connection
        mongo_uri = "mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal?retryWrites=true&w=majority&appName=debtor-portal-cluster"
        client = pymongo.MongoClient(mongo_uri)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        print("=" * 60)
        
        # Get database and collections
        db = client['debtor_portal']
        debtors_collection = db['debtors']
        debtor_images_collection = db['debtor_images']
        
        # 1. Total Debtors Count
        total_debtors = debtors_collection.count_documents({})
        print(f"👥 Total Debtors: {total_debtors:,}")
        
        # 2. Total QR Images Count
        total_qr_images = debtor_images_collection.count_documents({})
        print(f"🏷️  Total QR Images: {total_qr_images:,}")
        
        # 3. Debtors with QR images (mapped)
        debtors_with_qr = debtors_collection.count_documents({
            'qr_code_url': {'$exists': True, '$ne': None, '$ne': ''}
        })
        print(f"🔗 Debtors with QR mapping: {debtors_with_qr:,}")
        
        # 4. Alternative count - check debtor_images collection for mapped debtors
        mapped_via_images = debtor_images_collection.count_documents({
            'storage_key': {'$exists': True, '$ne': None, '$ne': ''}
        })
        print(f"🗃️  Mapped via debtor_images: {mapped_via_images:,}")
        
        print("=" * 60)
        
        # 5. Calculate coverage percentages
        if total_debtors > 0:
            qr_coverage = (debtors_with_qr / total_debtors) * 100
            print(f"📊 QR Coverage: {qr_coverage:.1f}% ({debtors_with_qr:,}/{total_debtors:,})")
            
            unmapped_debtors = total_debtors - debtors_with_qr
            print(f"❌ Debtors without QR: {unmapped_debtors:,}")
        
        # 6. Sample of debtors with QR codes
        print("\n🔍 Sample Debtors with QR codes:")
        sample_with_qr = list(debtors_collection.find(
            {'qr_code_url': {'$exists': True, '$ne': None, '$ne': ''}},
            {'account_number': 1, 'name': 1, 'qr_code_url': 1}
        ).limit(3))
        
        for debtor in sample_with_qr:
            qr_url = debtor.get('qr_code_url', '')
            qr_status = "✅ Has QR" if qr_url else "❌ No QR"
            print(f"  {debtor.get('account_number')} - {debtor.get('name', 'No name')} - {qr_status}")
        
        # 7. Sample of debtors without QR codes
        print("\n❌ Sample Debtors WITHOUT QR codes:")
        sample_without_qr = list(debtors_collection.find(
            {'$or': [
                {'qr_code_url': {'$exists': False}},
                {'qr_code_url': None},
                {'qr_code_url': ''}
            ]},
            {'account_number': 1, 'name': 1}
        ).limit(3))
        
        for debtor in sample_without_qr:
            print(f"  {debtor.get('account_number')} - {debtor.get('name', 'No name')} - ❌ No QR")
            
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_complete_status()