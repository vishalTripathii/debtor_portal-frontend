from api.database import get_debtor_images_collection

debtor_images = get_debtor_images_collection()

# Get one sample document to see structure
sample = debtor_images.find_one()

if sample:
    print("Sample debtor_images document structure:")
    print(f"Fields: {list(sample.keys())}")
    print(f"\nFull document:")
    for key, value in sample.items():
        if key == '_id':
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")
else:
    print("No documents found in debtor_images collection")
    
# Check total count
count = debtor_images.count_documents({})
print(f"\nTotal documents in debtor_images: {count}")
