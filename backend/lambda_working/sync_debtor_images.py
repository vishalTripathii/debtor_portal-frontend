#!/usr/bin/env python3
"""
Debtor Image Sync Script
========================
Ensures perfect mapping between:
1. S3 images (power-amc-debtor-media-dev/debtor_images/)
2. Debtors in MongoDB (debtors collection)
3. Image mappings in MongoDB (debtor_images collection)

Rule: If a debtor exists AND an S3 image exists for that debtor,
      then a mapping MUST exist in debtor_images collection.
"""

import os
import boto3
from pymongo import MongoClient
from datetime import datetime
from botocore.config import Config

# Configuration
MONGODB_URI = os.environ.get(
    'MONGODB_URI',
    'mongodb+srv://debtorportal:Welleazy2025DB@debtor-portal-cluster.m6wcxqm.mongodb.net/debtor_portal'
)
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'power-amc-debtor-media-dev')
S3_REGION = os.environ.get('S3_REGION', 'ap-southeast-1')
S3_PREFIX = 'debtor_images/'

def get_s3_client():
    """Create S3 client"""
    config = Config(
        region_name=S3_REGION,
        signature_version='s3v4'
    )
    return boto3.client('s3', config=config)

def get_mongodb():
    """Create MongoDB connection"""
    client = MongoClient(MONGODB_URI)
    return client['debtor_portal']

def extract_account_from_filename(filename):
    """Extract account number from image filename"""
    # Remove extension and path
    basename = os.path.basename(filename)
    account = os.path.splitext(basename)[0]
    return account

def list_s3_images(s3_client):
    """List all images in S3 bucket"""
    print(f"\n📂 Listing S3 images from s3://{S3_BUCKET}/{S3_PREFIX}")
    
    images = {}
    paginator = s3_client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                account = extract_account_from_filename(key)
                images[account] = {
                    'key': key,
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                }
    
    print(f"   Found {len(images)} images in S3")
    return images

def get_all_debtors(db):
    """Get all debtors from MongoDB"""
    print(f"\n👥 Loading debtors from MongoDB")
    
    debtors = {}
    cursor = db.debtors.find({}, {'account_number': 1, 'national_id': 1, 'case_id': 1})
    
    for doc in cursor:
        account = doc.get('account_number')
        if account:
            debtors[account] = {
                'national_id': doc.get('national_id', ''),
                'case_id': doc.get('case_id', '')
            }
    
    print(f"   Found {len(debtors)} debtors")
    return debtors

def get_existing_mappings(db):
    """Get existing image mappings from MongoDB"""
    print(f"\n🔗 Loading existing mappings from debtor_images collection")
    
    mappings = {}
    cursor = db.debtor_images.find({}, {'account_number': 1, 'storage_key': 1})
    
    for doc in cursor:
        account = doc.get('account_number')
        if account:
            mappings[account] = doc.get('storage_key', '')
    
    print(f"   Found {len(mappings)} existing mappings")
    return mappings

def sync_mappings(db, s3_images, debtors, existing_mappings, dry_run=False):
    """Sync mappings to ensure consistency"""
    print(f"\n🔄 Syncing mappings...")
    
    stats = {
        'created': 0,
        'updated': 0,
        'orphan_mappings': 0,
        'orphan_images': 0,
        'already_synced': 0
    }
    
    # Find accounts that have BOTH debtor AND S3 image
    accounts_with_both = set(s3_images.keys()) & set(debtors.keys())
    print(f"   Accounts with both debtor AND image: {len(accounts_with_both)}")
    
    # Find orphan images (S3 image but no debtor)
    orphan_images = set(s3_images.keys()) - set(debtors.keys())
    stats['orphan_images'] = len(orphan_images)
    if orphan_images:
        print(f"   ⚠️  Orphan images (no matching debtor): {len(orphan_images)}")
        # Show first 5
        for acc in list(orphan_images)[:5]:
            print(f"      - {acc}")
        if len(orphan_images) > 5:
            print(f"      ... and {len(orphan_images) - 5} more")
    
    # Find orphan mappings (mapping exists but no S3 image)
    orphan_mappings = set(existing_mappings.keys()) - set(s3_images.keys())
    stats['orphan_mappings'] = len(orphan_mappings)
    if orphan_mappings:
        print(f"   ⚠️  Orphan mappings (no S3 image): {len(orphan_mappings)}")
    
    # Create/Update mappings for accounts with both debtor and image
    mappings_to_create = []
    mappings_to_update = []
    
    for account in accounts_with_both:
        s3_info = s3_images[account]
        debtor_info = debtors[account]
        expected_key = s3_info['key']
        
        if account not in existing_mappings:
            # Need to create mapping
            mappings_to_create.append({
                'account_number': account,
                'national_id': debtor_info.get('national_id', ''),
                'case_id': debtor_info.get('case_id', ''),
                'storage_key': expected_key,
                'filename': os.path.basename(expected_key),
                'content_type': 'image/png' if expected_key.endswith('.png') else 'image/jpeg',
                'source': 'sync_script',
                'uploaded_at': datetime.utcnow(),
                'uploaded_by': 'system',
                'original_identifier': account,
                'source_file': 'sync_debtor_images.py'
            })
        elif existing_mappings[account] != expected_key:
            # Need to update mapping
            mappings_to_update.append({
                'account': account,
                'old_key': existing_mappings[account],
                'new_key': expected_key
            })
        else:
            stats['already_synced'] += 1
    
    print(f"\n📊 Sync Plan:")
    print(f"   - Mappings to CREATE: {len(mappings_to_create)}")
    print(f"   - Mappings to UPDATE: {len(mappings_to_update)}")
    print(f"   - Already synced: {stats['already_synced']}")
    
    if dry_run:
        print(f"\n🔍 DRY RUN - No changes made")
        if mappings_to_create:
            print(f"   Would create mappings for:")
            for m in mappings_to_create[:5]:
                print(f"      - {m['account_number']}: {m['storage_key']}")
            if len(mappings_to_create) > 5:
                print(f"      ... and {len(mappings_to_create) - 5} more")
        return stats
    
    # Execute creates
    if mappings_to_create:
        print(f"\n✅ Creating {len(mappings_to_create)} new mappings...")
        result = db.debtor_images.insert_many(mappings_to_create)
        stats['created'] = len(result.inserted_ids)
        print(f"   Created {stats['created']} mappings")
    
    # Execute updates
    if mappings_to_update:
        print(f"\n✅ Updating {len(mappings_to_update)} mappings...")
        for update in mappings_to_update:
            db.debtor_images.update_one(
                {'account_number': update['account']},
                {'$set': {'storage_key': update['new_key']}}
            )
            stats['updated'] += 1
        print(f"   Updated {stats['updated']} mappings")
    
    # Clean orphan mappings (optional - mappings without S3 images)
    if orphan_mappings:
        print(f"\n🗑️  Removing {len(orphan_mappings)} orphan mappings...")
        result = db.debtor_images.delete_many({
            'account_number': {'$in': list(orphan_mappings)}
        })
        print(f"   Removed {result.deleted_count} orphan mappings")
    
    return stats

def verify_sync(db, s3_images, debtors):
    """Verify the sync was successful"""
    print(f"\n✅ Verifying sync...")
    
    # Re-fetch mappings
    mappings = get_existing_mappings(db)
    
    # Accounts that should have mappings (both debtor and image exist)
    expected = set(s3_images.keys()) & set(debtors.keys())
    actual = set(mappings.keys())
    
    missing = expected - actual
    extra = actual - expected
    
    print(f"\n📊 Final Verification:")
    print(f"   S3 Images: {len(s3_images)}")
    print(f"   Debtors: {len(debtors)}")
    print(f"   Expected Mappings (debtor+image): {len(expected)}")
    print(f"   Actual Mappings: {len(actual)}")
    print(f"   Missing Mappings: {len(missing)}")
    print(f"   Extra Mappings: {len(extra)}")
    
    if len(missing) == 0 and len(extra) == 0:
        print(f"\n🎉 SUCCESS! All mappings are perfectly synced!")
        return True
    else:
        print(f"\n⚠️  Sync incomplete!")
        if missing:
            print(f"   Missing mappings for: {list(missing)[:5]}")
        if extra:
            print(f"   Extra mappings for: {list(extra)[:5]}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sync debtor images between S3 and MongoDB')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--verify-only', action='store_true', help='Only verify current state, do not sync')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔄 DEBTOR IMAGE SYNC SCRIPT")
    print("=" * 60)
    print(f"S3 Bucket: {S3_BUCKET}")
    print(f"S3 Prefix: {S3_PREFIX}")
    print(f"MongoDB: {MONGODB_URI.split('@')[1] if '@' in MONGODB_URI else 'local'}")
    
    # Initialize clients
    s3_client = get_s3_client()
    db = get_mongodb()
    
    # Gather data
    s3_images = list_s3_images(s3_client)
    debtors = get_all_debtors(db)
    existing_mappings = get_existing_mappings(db)
    
    if args.verify_only:
        verify_sync(db, s3_images, debtors)
        return
    
    # Sync
    stats = sync_mappings(db, s3_images, debtors, existing_mappings, dry_run=args.dry_run)
    
    if not args.dry_run:
        # Verify
        verify_sync(db, s3_images, debtors)
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"   Created: {stats['created']}")
    print(f"   Updated: {stats['updated']}")
    print(f"   Already Synced: {stats['already_synced']}")
    print(f"   Orphan Images (no debtor): {stats['orphan_images']}")
    print(f"   Orphan Mappings (removed): {stats['orphan_mappings']}")

if __name__ == '__main__':
    main()
