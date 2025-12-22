#!/bin/bash

# ============================================
# CloudFront Distribution Setup with SSL
# ============================================

set -e

STAGE=${1:-dev}
REGION=${2:-ap-southeast-1}
BUCKET_NAME="debtor-portal-frontend-$STAGE"

echo "============================================"
echo "Setting up CloudFront Distribution"
echo "Stage: $STAGE"
echo "Region: $REGION"
echo "S3 Bucket: $BUCKET_NAME"
echo "============================================"

# Check if CloudFront distribution already exists
echo "Checking for existing CloudFront distribution..."
EXISTING_CF=$(aws cloudfront list-distributions --query "DistributionList.Items[?Origins.Items[?contains(DomainName,'${BUCKET_NAME}')]].{Id:Id,Domain:DomainName}" --output json 2>/dev/null)

if [ "$EXISTING_CF" != "[]" ] && [ "$EXISTING_CF" != "null" ] && [ -n "$EXISTING_CF" ]; then
    echo "CloudFront distribution already exists:"
    echo "$EXISTING_CF" | python3 -m json.tool
    CF_ID=$(echo "$EXISTING_CF" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0]['Id'])" 2>/dev/null)
    CF_DOMAIN=$(echo "$EXISTING_CF" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0]['Domain'])" 2>/dev/null)
    
    echo ""
    echo "Existing CloudFront Distribution:"
    echo "ID: $CF_ID"
    echo "Domain: https://$CF_DOMAIN"
    echo ""
    echo "Creating cache invalidation..."
    aws cloudfront create-invalidation --distribution-id "$CF_ID" --paths "/*" 2>/dev/null || echo "Note: Invalidation may require additional permissions"
    
    exit 0
fi

echo "No existing CloudFront distribution found. Creating new one..."

# Get S3 website endpoint
S3_WEBSITE_ENDPOINT="${BUCKET_NAME}.s3-website-${REGION}.amazonaws.com"

# Create CloudFront distribution config
cat > /tmp/cf-config-$$.json <<EOF
{
  "CallerReference": "debtor-portal-${STAGE}-$(date +%s)",
  "Comment": "Debtor Portal Frontend - ${STAGE}",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-${BUCKET_NAME}",
        "DomainName": "${S3_WEBSITE_ENDPOINT}",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only",
          "OriginSslProtocols": {
            "Quantity": 1,
            "Items": ["TLSv1.2"]
          }
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-${BUCKET_NAME}",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000,
    "Compress": true
  },
  "PriceClass": "PriceClass_All",
  "ViewerCertificate": {
    "CloudFrontDefaultCertificate": true,
    "MinimumProtocolVersion": "TLSv1.2_2021"
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      }
    ]
  }
}
EOF

echo "Creating CloudFront distribution..."
CF_RESULT=$(aws cloudfront create-distribution --distribution-config file:///tmp/cf-config-$$.json 2>&1)

if [ $? -eq 0 ]; then
    CF_ID=$(echo "$CF_RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['Distribution']['Id'])" 2>/dev/null)
    CF_DOMAIN=$(echo "$CF_RESULT" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['Distribution']['DomainName'])" 2>/dev/null)
    
    echo ""
    echo "============================================"
    echo "CloudFront Distribution Created!"
    echo "============================================"
    echo ""
    echo "Distribution ID: $CF_ID"
    echo "CloudFront URL: https://$CF_DOMAIN"
    echo ""
    echo "Note: It may take 15-20 minutes for the distribution to be fully deployed."
    echo "Status: Deploying..."
else
    echo "ERROR: Failed to create CloudFront distribution"
    echo "$CF_RESULT"
    exit 1
fi

# Cleanup
rm -f /tmp/cf-config-$$.json

echo ""
echo "S3 Bucket: $BUCKET_NAME"
echo "Region: $REGION"
