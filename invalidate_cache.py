import boto3
import time

cloudfront = boto3.client('cloudfront')

print("Invalidating CloudFront cache...")
response = cloudfront.create_invalidation(
    DistributionId='E1TBYQ8YV78RKE',
    InvalidationBatch={
        'Paths': {
            'Quantity': 1,
            'Items': ['/*']
        },
        'CallerReference': str(time.time())
    }
)

print(f"✓ CloudFront cache invalidated")
print(f"  Invalidation ID: {response['Invalidation']['Id']}")
print(f"  Status: {response['Invalidation']['Status']}")
