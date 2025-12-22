#!/bin/bash

# ============================================
# AWS S3/CloudFront Frontend Deployment Script
# ============================================

set -e

# Configuration
STAGE=${1:-dev}
REGION=${2:-ap-southeast-1}
BUCKET_NAME="power-amc-debtor-portal-frontend-$STAGE"

echo "============================================"
echo "Deploying Debtor Portal Frontend"
echo "Stage: $STAGE"
echo "Region: $REGION"
echo "Bucket: $BUCKET_NAME"
echo "============================================"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check for AWS CLI
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI not found. Please install it first."
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS credentials not configured."
    echo "Please run: aws configure"
    exit 1
fi

# Get API Gateway URL from serverless deployment
echo "Getting API Gateway URL..."
cd backend
API_URL=$(serverless info --stage $STAGE --region $REGION 2>/dev/null | grep -o 'https://[^[:space:]]*execute-api[^[:space:]]*' | head -1)
cd ..

if [ -z "$API_URL" ]; then
    echo "WARNING: Could not automatically detect API Gateway URL."
    echo "Please ensure VITE_API_BASE_URL is set in .env"
else
    echo "API Gateway URL: $API_URL"
    # Update .env file
    if [ -f .env ]; then
        sed -i.bak "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=${API_URL}/api|" .env
        rm -f .env.bak
    else
        echo "VITE_API_BASE_URL=${API_URL}/api" > .env
    fi
fi

# Install dependencies
echo "Installing dependencies..."
npm install

# Build frontend
echo "Building frontend..."
npm run build

# Check if build succeeded
if [ ! -d "dist" ]; then
    echo "ERROR: Build failed. dist directory not found."
    exit 1
fi

# Check if bucket exists
if ! aws s3 ls "s3://$BUCKET_NAME" --region $REGION &> /dev/null; then
    echo "WARNING: S3 bucket $BUCKET_NAME not found."
    echo "The bucket should be created by the serverless deployment."
    echo "If deploying separately, create it with:"
    echo "aws s3 mb s3://$BUCKET_NAME --region $REGION"
    exit 1
fi

# Sync to S3
echo "Uploading to S3..."
aws s3 sync dist/ "s3://$BUCKET_NAME" \
    --region $REGION \
    --delete \
    --cache-control "max-age=31536000" \
    --exclude "index.html" \
    --exclude "*.json"

# Upload index.html and JSON with shorter cache
aws s3 cp dist/index.html "s3://$BUCKET_NAME/index.html" \
    --region $REGION \
    --cache-control "max-age=0, no-cache, no-store, must-revalidate"

# Upload JSON files (if any)
if ls dist/*.json 1> /dev/null 2>&1; then
    for file in dist/*.json; do
        aws s3 cp "$file" "s3://$BUCKET_NAME/$(basename $file)" \
            --region $REGION \
            --cache-control "max-age=0, no-cache"
    done
fi

# Get CloudFront distribution
echo "Looking for CloudFront distribution..."
CLOUDFRONT_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Origins.Items[?DomainName=='${BUCKET_NAME}.s3.${REGION}.amazonaws.com']].Id" --output text 2>/dev/null)

if [ -n "$CLOUDFRONT_ID" ] && [ "$CLOUDFRONT_ID" != "None" ]; then
    echo "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --distribution-id $CLOUDFRONT_ID \
        --paths "/*" \
        --region $REGION

    # Get CloudFront URL
    CLOUDFRONT_URL=$(aws cloudfront get-distribution --id $CLOUDFRONT_ID --query "Distribution.DomainName" --output text)
    echo ""
    echo "============================================"
    echo "Deployment Complete!"
    echo "============================================"
    echo ""
    echo "CloudFront URL: https://$CLOUDFRONT_URL"
else
    echo ""
    echo "============================================"
    echo "Deployment Complete!"
    echo "============================================"
    echo ""
    echo "S3 Website URL: http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
    echo ""
    echo "Note: CloudFront distribution not found."
    echo "For HTTPS, set up CloudFront manually or via serverless.yml"
fi

echo ""
echo "API Gateway URL: $API_URL"
