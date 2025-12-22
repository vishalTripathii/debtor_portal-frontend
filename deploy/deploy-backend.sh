#!/bin/bash

# ============================================
# AWS Serverless Backend Deployment Script
# ============================================

set -e

# Configuration
STAGE=${1:-dev}
REGION=${2:-ap-southeast-1}

echo "============================================"
echo "Deploying Debtor Portal Backend"
echo "Stage: $STAGE"
echo "Region: $REGION"
echo "============================================"

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

# Check for serverless framework
if ! command -v serverless &> /dev/null; then
    echo "Serverless Framework not found. Installing..."
    npm install -g serverless
fi

# Install serverless plugins
echo "Installing serverless plugins..."
npm install --save-dev serverless-python-requirements serverless-offline

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "ERROR: AWS credentials not configured."
    echo "Please run: aws configure"
    exit 1
fi

# Create AWS Parameter Store entries if they don't exist
echo "Checking AWS Parameter Store entries..."

# Check MongoDB URI
if ! aws ssm get-parameter --name "/debtor-portal/$STAGE/mongodb-uri" --region $REGION &> /dev/null; then
    echo "WARNING: MongoDB URI not found in Parameter Store."
    echo "Please create: /debtor-portal/$STAGE/mongodb-uri"
    echo "Example: aws ssm put-parameter --name '/debtor-portal/$STAGE/mongodb-uri' --value 'mongodb+srv://...' --type SecureString --region $REGION"
fi

# Check Django Secret Key
if ! aws ssm get-parameter --name "/debtor-portal/$STAGE/django-secret-key" --region $REGION &> /dev/null; then
    echo "WARNING: Django Secret Key not found in Parameter Store."
    echo "Generating a new secret key..."
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    aws ssm put-parameter \
        --name "/debtor-portal/$STAGE/django-secret-key" \
        --value "$SECRET_KEY" \
        --type SecureString \
        --region $REGION
    echo "Django Secret Key created."
fi

# Deploy with Serverless Framework
echo "Deploying with Serverless Framework..."
serverless deploy --stage $STAGE --region $REGION

# Get deployment outputs
echo ""
echo "============================================"
echo "Deployment Complete!"
echo "============================================"
echo ""
serverless info --stage $STAGE --region $REGION

echo ""
echo "Next steps:"
echo "1. Update frontend .env with the API Gateway URL"
echo "2. Run: npm run build"
echo "3. Deploy frontend with: ./deploy-frontend.sh $STAGE $REGION"
