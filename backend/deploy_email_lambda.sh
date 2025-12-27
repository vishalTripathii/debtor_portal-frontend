#!/bin/bash

# ============================================
# SAFE EMAIL LAMBDA DEPLOYMENT SCRIPT
# ============================================
# This script ONLY updates the email Lambda function
# WITHOUT affecting any other working deployments
# ============================================

set -e

FUNCTION_NAME="debtor-portal-api-dev-email"
REGION="ap-southeast-1"
BACKEND_DIR="/Users/apple/debtor_portal-frontend/backend"
DEPLOY_DIR="$BACKEND_DIR/email_deploy_package"

echo "============================================"
echo "📧 EMAIL LAMBDA DEPLOYMENT"
echo "============================================"
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo "Date: $(date)"
echo "============================================"
echo ""

# Step 1: Verify AWS credentials
echo "🔐 Step 1: Verifying AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ ERROR: AWS credentials not configured"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
echo "✅ Authenticated as: $AWS_USER"
echo "✅ Account: $AWS_ACCOUNT"
echo ""

# Step 2: Verify the Lambda function exists
echo "🔍 Step 2: Checking if Lambda function exists..."
if ! aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
    echo "❌ ERROR: Lambda function '$FUNCTION_NAME' not found"
    echo "Available functions:"
    aws lambda list-functions --region $REGION --query "Functions[?contains(FunctionName, 'debtor-portal')].FunctionName" --output table
    exit 1
fi
echo "✅ Lambda function found: $FUNCTION_NAME"
echo ""

# Step 3: Create deployment package directory
echo "📦 Step 3: Creating deployment package..."
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Copy email Lambda files
echo "   - Copying email_lambda.js..."
cp "$BACKEND_DIR/email_lambda.js" .

echo "   - Copying package.json..."
cp "$BACKEND_DIR/package.json" .

# Install production dependencies
echo "   - Installing node_modules (production only)..."
npm install --production --quiet

# Create ZIP package
echo "   - Creating ZIP archive..."
zip -r email-lambda.zip . -q

PACKAGE_SIZE=$(du -h email-lambda.zip | cut -f1)
echo "✅ Package created: email-lambda.zip ($PACKAGE_SIZE)"
echo ""

# Step 4: Backup current Lambda function
echo "💾 Step 4: Creating backup of current Lambda..."
BACKUP_FILE="$BACKEND_DIR/email_lambda_backup_$(date +%Y%m%d_%H%M%S).json"
aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > "$BACKUP_FILE"
echo "✅ Backup saved: $BACKUP_FILE"
echo ""

# Step 5: Get current configuration
echo "📋 Step 5: Reading current Lambda configuration..."
CURRENT_CONFIG=$(aws lambda get-function-configuration --function-name $FUNCTION_NAME --region $REGION)
CURRENT_RUNTIME=$(echo $CURRENT_CONFIG | jq -r '.Runtime')
CURRENT_TIMEOUT=$(echo $CURRENT_CONFIG | jq -r '.Timeout')
CURRENT_MEMORY=$(echo $CURRENT_CONFIG | jq -r '.MemorySize')
CURRENT_HANDLER=$(echo $CURRENT_CONFIG | jq -r '.Handler')

echo "   Current Runtime: $CURRENT_RUNTIME"
echo "   Current Timeout: $CURRENT_TIMEOUT seconds"
echo "   Current Memory: $CURRENT_MEMORY MB"
echo "   Current Handler: $CURRENT_HANDLER"
echo ""

# Step 6: Deploy the updated code
echo "🚀 Step 6: Deploying updated email Lambda..."
echo "   Uploading email-lambda.zip..."

UPDATE_RESPONSE=$(aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://email-lambda.zip \
    --region $REGION \
    --output json)

if [ $? -eq 0 ]; then
    echo "✅ Code updated successfully!"
    
    # Extract details
    NEW_SIZE=$(echo $UPDATE_RESPONSE | jq -r '.CodeSize')
    NEW_SHA=$(echo $UPDATE_RESPONSE | jq -r '.CodeSha256')
    LAST_MODIFIED=$(echo $UPDATE_RESPONSE | jq -r '.LastModified')
    
    echo "   Code Size: $(echo "scale=2; $NEW_SIZE/1024/1024" | bc) MB"
    echo "   Code SHA256: ${NEW_SHA:0:20}..."
    echo "   Last Modified: $LAST_MODIFIED"
else
    echo "❌ ERROR: Failed to update Lambda function"
    exit 1
fi
echo ""

# Step 7: Wait for function to be ready
echo "⏳ Step 7: Waiting for Lambda to be active..."
for i in {1..30}; do
    STATE=$(aws lambda get-function-configuration \
        --function-name $FUNCTION_NAME \
        --region $REGION \
        --query 'State' \
        --output text)
    
    if [ "$STATE" = "Active" ]; then
        echo "✅ Lambda is Active"
        break
    fi
    
    echo "   State: $STATE (waiting... $i/30)"
    sleep 2
done

if [ "$STATE" != "Active" ]; then
    echo "⚠️  WARNING: Lambda state is $STATE (not Active)"
    echo "   This may be normal during update. Check AWS Console."
fi
echo ""

# Step 8: Test the updated Lambda
echo "🧪 Step 8: Testing updated Lambda function..."
TEST_PAYLOAD='{"httpMethod":"POST","body":"{\"action\":\"test\"}"}'

echo "   Invoking test action..."
TEST_RESPONSE=$(aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --payload "$TEST_PAYLOAD" \
    --cli-binary-format raw-in-base64-out \
    /tmp/lambda-response.json 2>&1)

if [ $? -eq 0 ]; then
    RESPONSE_BODY=$(cat /tmp/lambda-response.json)
    echo "✅ Lambda test invocation successful"
    echo "   Response: $RESPONSE_BODY"
    
    # Check if response indicates success
    if echo "$RESPONSE_BODY" | grep -q '"success":true'; then
        echo "✅ Email service is working correctly"
    else
        echo "⚠️  WARNING: Response may indicate an issue"
    fi
else
    echo "❌ ERROR: Lambda test invocation failed"
    echo "$TEST_RESPONSE"
fi
echo ""

# Step 9: Verify configuration
echo "✅ Step 9: Verifying final configuration..."
FINAL_CONFIG=$(aws lambda get-function-configuration --function-name $FUNCTION_NAME --region $REGION)
echo "$FINAL_CONFIG" | jq '{
    FunctionName: .FunctionName,
    Runtime: .Runtime,
    Handler: .Handler,
    Timeout: .Timeout,
    MemorySize: .MemorySize,
    LastModified: .LastModified,
    State: .State,
    CodeSize: .CodeSize
}'
echo ""

# Step 10: Cleanup
echo "🧹 Step 10: Cleaning up..."
cd "$BACKEND_DIR"
# Keep the backup but remove the deployment directory
# rm -rf "$DEPLOY_DIR"
echo "✅ Deployment package kept at: $DEPLOY_DIR"
echo "✅ Backup kept at: $BACKUP_FILE"
echo ""

# Final Summary
echo "============================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "============================================"
echo ""
echo "📧 Email Configuration Updated:"
echo "   From: digital.marketing@welleazy.in"
echo "   SMTP: smtpout.secureserver.net:587"
echo ""
echo "📋 Email Flows Configured:"
echo "   1. OTP Emails → Debtor's email"
echo "   2. Payment Notifications → hello@poweramc.com"
echo "   3. Support Requests → hello@poweramc.com"
echo ""
echo "🔄 Other Lambda Functions:"
echo "   ✅ UNCHANGED - All working code preserved"
echo ""
echo "📝 What was deployed:"
echo "   - backend/email_lambda.js (updated SMTP config)"
echo "   - Added payment notification handler"
echo "   - Added support request handler"
echo ""
echo "🧪 Next Steps:"
echo "   1. Test OTP login in production"
echo "   2. Test payment submission"
echo "   3. Test support request"
echo "   4. Check email delivery"
echo ""
echo "📞 Support:"
echo "   Backup: $BACKUP_FILE"
echo "   To rollback: Use AWS Console or restore from backup"
echo ""
echo "============================================"
echo "Deployment completed: $(date)"
echo "============================================"
