#!/bin/bash

# ============================================
# SAFE EMAIL LAMBDA DEPLOYMENT via Serverless
# ============================================
# Deploys ONLY the email Lambda function
# WITHOUT affecting other working Lambda functions
# ============================================

set -e

STAGE="dev"
REGION="ap-southeast-1"
BACKEND_DIR="/Users/apple/debtor_portal-frontend/backend"

echo "============================================"
echo "📧 EMAIL LAMBDA DEPLOYMENT (via Serverless)"
echo "============================================"
echo "Stage: $STAGE"
echo "Region: $REGION"
echo "Date: $(date)"
echo "============================================"
echo ""

# Navigate to backend directory
cd "$BACKEND_DIR"

# Step 1: Verify AWS credentials
echo "🔐 Step 1: Verifying AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ ERROR: AWS credentials not configured"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_USER=$(aws sts get-caller-identity --query Arn --output text | awk -F'/' '{print $NF}')
echo "✅ Authenticated as: $AWS_USER"
echo "✅ Account: $AWS_ACCOUNT"
echo ""

# Step 2: Check Serverless installation
echo "🔍 Step 2: Checking Serverless Framework..."
if ! command -v serverless &> /dev/null; then
    echo "Installing Serverless Framework..."
    npm install -g serverless
fi
SERVERLESS_VERSION=$(serverless --version | head -1)
echo "✅ $SERVERLESS_VERSION"
echo ""

# Step 3: Verify node_modules for email Lambda
echo "📦 Step 3: Checking node_modules..."
if [ ! -d "node_modules/nodemailer" ]; then
    echo "   Installing nodemailer..."
    npm install
else
    echo "✅ nodemailer is installed"
fi
echo ""

# Step 4: Create backup
echo "💾 Step 4: Creating backup..."
BACKUP_FILE="email_lambda_backup_$(date +%Y%m%d_%H%M%S).js"
cp email_lambda.js "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"
echo ""

# Step 5: Show what will be deployed
echo "📋 Step 5: Deployment Summary..."
echo ""
echo "   File to deploy: email_lambda.js"
echo "   Changes:"
echo "   ✅ SMTP credentials updated to digital.marketing@welleazy.in"
echo "   ✅ Added payment notification handler (send-payment-notification)"
echo "   ✅ Added support request handler (send-support-request)"
echo "   ✅ All emails go to hello@poweramc.com"
echo ""
echo "   Other Lambda functions:"
echo "   ✅ api (Django) - NOT MODIFIED"
echo "   ✅ excelProcessor - NOT MODIFIED"
echo "   ✅ qrProcessor - NOT MODIFIED"
echo "   ✅ bulkOperations - NOT MODIFIED"
echo ""

# Step 6: Deploy only the email function
echo "🚀 Step 6: Deploying email Lambda function..."
echo ""
echo "Running: serverless deploy function -f email --stage $STAGE --region $REGION"
echo ""

serverless deploy function -f email --stage $STAGE --region $REGION --verbose

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Email Lambda deployed successfully!"
else
    echo ""
    echo "❌ ERROR: Deployment failed"
    echo "Restoring backup..."
    cp "$BACKUP_FILE" email_lambda.js
    exit 1
fi
echo ""

# Step 7: Wait for function to be ready
echo "⏳ Step 7: Waiting for Lambda to be active..."
sleep 5

FUNCTION_NAME="debtor-portal-api-$STAGE-email"
STATE=$(aws lambda get-function-configuration \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'State' \
    --output text)

echo "✅ Lambda state: $STATE"
echo ""

# Step 8: Get deployed function info
echo "📊 Step 8: Deployed Function Info..."
aws lambda get-function-configuration \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query '{
        Name: FunctionName,
        Runtime: Runtime,
        Handler: Handler,
        Timeout: Timeout,
        Memory: MemorySize,
        Modified: LastModified,
        Size: CodeSize
    }' \
    --output json | jq .
echo ""

# Step 9: Test the deployed function
echo "🧪 Step 9: Testing email Lambda..."
TEST_PAYLOAD='{"httpMethod":"POST","body":"{\"action\":\"test\"}"}'

echo "   Invoking test action..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --payload "$TEST_PAYLOAD" \
    --cli-binary-format raw-in-base64-out \
    /tmp/lambda-test-response.json > /dev/null 2>&1

if [ $? -eq 0 ]; then
    RESPONSE=$(cat /tmp/lambda-test-response.json)
    echo "✅ Test invocation successful"
    echo "   Response: $RESPONSE"
    
    if echo "$RESPONSE" | grep -q '"success":true'; then
        echo "✅ Email service is operational"
    fi
else
    echo "⚠️  WARNING: Test invocation failed (may need manual verification)"
fi
echo ""

# Final Summary
echo "============================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "============================================"
echo ""
echo "📧 Email Configuration:"
echo "   Sender: digital.marketing@welleazy.in"
echo "   Password: Welcome@123"
echo "   SMTP: smtpout.secureserver.net:587"
echo ""
echo "📋 Email Flows:"
echo "   1️⃣  OTP Emails → Debtor's email (dynamic)"
echo "   2️⃣  Payment Notifications → hello@poweramc.com"
echo "   3️⃣  Support Requests → hello@poweramc.com"
echo ""
echo "✅ Deployed Lambda: debtor-portal-api-$STAGE-email"
echo "✅ Region: $REGION"
echo "✅ Backup: $BACKUP_FILE"
echo ""
echo "🔄 Other Lambda Functions: UNCHANGED ✅"
echo "   - api (Django backend)"
echo "   - excelProcessor"
echo "   - qrProcessor"
echo "   - bulkOperations"
echo ""
echo "🧪 Testing Checklist:"
echo "   [ ] Test OTP login in production"
echo "   [ ] Test payment submission → Check hello@poweramc.com"
echo "   [ ] Test support request → Check hello@poweramc.com"
echo "   [ ] Verify email templates render correctly"
echo ""
echo "📞 Need to rollback?"
echo "   cp $BACKUP_FILE email_lambda.js"
echo "   serverless deploy function -f email --stage $STAGE --region $REGION"
echo ""
echo "============================================"
echo "Deployment completed: $(date)"
echo "============================================"
