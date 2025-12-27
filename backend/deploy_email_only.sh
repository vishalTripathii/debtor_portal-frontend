#!/bin/bash

# ============================================
# SAFE EMAIL LAMBDA DEPLOYMENT
# Updates ONLY email Lambda with new GoDaddy Welleazy credentials
# Does NOT affect any other working deployments
# ============================================

set -e

FUNCTION_NAME="debtor-portal-api-dev-email"
REGION="ap-southeast-1"
BACKEND_DIR="/Users/apple/debtor_portal-frontend/backend"
DEPLOY_DIR="$BACKEND_DIR/.email_deploy"

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║               📧 EMAIL LAMBDA SAFE DEPLOYMENT                              ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Function:     $FUNCTION_NAME"
echo "Region:       $REGION"
echo "Date:         $(date)"
echo "Deployment:   Email configuration update only"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# ============================================
# STEP 1: Verify AWS Credentials
# ============================================
echo "🔐 STEP 1: Verifying AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ ERROR: AWS credentials not configured"
    echo "Please run: aws configure"
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
echo "✅ Authenticated"
echo "   User: $AWS_USER"
echo "   Account: $AWS_ACCOUNT"
echo ""

# ============================================
# STEP 2: Verify Lambda Function Exists
# ============================================
echo "🔍 STEP 2: Checking if Lambda function exists..."
if ! aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
    echo "❌ ERROR: Lambda function '$FUNCTION_NAME' not found"
    echo ""
    echo "Available Lambda functions:"
    aws lambda list-functions --region $REGION --query "Functions[?contains(FunctionName, 'debtor-portal')].FunctionName" --output table
    exit 1
fi
echo "✅ Lambda function found: $FUNCTION_NAME"
echo ""

# ============================================
# STEP 3: Create Backup
# ============================================
echo "💾 STEP 3: Creating backup of current Lambda..."
BACKUP_DIR="$BACKEND_DIR/.lambda_backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/email_lambda_backup_$(date +%Y%m%d_%H%M%S).json"

aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > "$BACKUP_FILE"
echo "✅ Backup saved: $BACKUP_FILE"

# Also backup current code
echo "   Downloading current code..."
CODE_LOCATION=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Code.Location' --output text)
curl -s "$CODE_LOCATION" -o "$BACKUP_DIR/email_lambda_code_$(date +%Y%m%d_%H%M%S).zip"
echo "✅ Current code backed up"
echo ""

# ============================================
# STEP 4: Display Current Configuration
# ============================================
echo "📋 STEP 4: Current Lambda configuration..."
CURRENT_CONFIG=$(aws lambda get-function-configuration --function-name $FUNCTION_NAME --region $REGION)
CURRENT_RUNTIME=$(echo $CURRENT_CONFIG | jq -r '.Runtime')
CURRENT_TIMEOUT=$(echo $CURRENT_CONFIG | jq -r '.Timeout')
CURRENT_MEMORY=$(echo $CURRENT_CONFIG | jq -r '.MemorySize')
CURRENT_HANDLER=$(echo $CURRENT_CONFIG | jq -r '.Handler')
CURRENT_EMAIL_USER=$(echo $CURRENT_CONFIG | jq -r '.Environment.Variables.EMAIL_HOST_USER // "N/A"')
CURRENT_EMAIL_HOST=$(echo $CURRENT_CONFIG | jq -r '.Environment.Variables.EMAIL_HOST // "N/A"')

echo "   Runtime:         $CURRENT_RUNTIME"
echo "   Timeout:         $CURRENT_TIMEOUT seconds"
echo "   Memory:          $CURRENT_MEMORY MB"
echo "   Handler:         $CURRENT_HANDLER"
echo "   Current Email:   $CURRENT_EMAIL_USER"
echo "   Current SMTP:    $CURRENT_EMAIL_HOST"
echo ""

# ============================================
# STEP 5: Create Deployment Package
# ============================================
echo "📦 STEP 5: Creating deployment package..."
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Copy updated email_lambda.js
echo "   - Copying email_lambda.js..."
cp "$BACKEND_DIR/email_lambda.js" .

# Copy package.json
echo "   - Copying package.json..."
cp "$BACKEND_DIR/package.json" .

# Install dependencies (production only)
echo "   - Installing node_modules..."
npm install --production --quiet --no-audit --no-fund

if [ ! -d "node_modules" ]; then
    echo "❌ ERROR: npm install failed"
    exit 1
fi

# Create ZIP package
echo "   - Creating ZIP archive..."
zip -r email-lambda.zip . -q

if [ ! -f "email-lambda.zip" ]; then
    echo "❌ ERROR: Failed to create ZIP file"
    exit 1
fi

PACKAGE_SIZE=$(du -h email-lambda.zip | cut -f1)
FILE_COUNT=$(unzip -l email-lambda.zip | tail -1 | awk '{print $2}')
echo "✅ Package created"
echo "   Size: $PACKAGE_SIZE"
echo "   Files: $FILE_COUNT"
echo ""

# ============================================
# STEP 6: Update Environment Variables
# ============================================
echo "🔧 STEP 6: Updating environment variables with new email config..."

# Get current environment variables
CURRENT_ENV=$(aws lambda get-function-configuration \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'Environment.Variables' \
    --output json)

# Update email-related variables
NEW_ENV=$(echo "$CURRENT_ENV" | jq -c '. + {
    "EMAIL_HOST": "smtpout.secureserver.net",
    "EMAIL_PORT": "587",
    "EMAIL_USE_TLS": "True",
    "EMAIL_USE_SSL": "False",
    "EMAIL_HOST_USER": "digital.marketing@welleazy.in",
    "EMAIL_HOST_PASSWORD": "Welcome@123",
    "DEFAULT_FROM_EMAIL": "digital.marketing@welleazy.in"
}')

aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --environment Variables="$NEW_ENV" \
    > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Environment variables updated"
    echo "   New SMTP:      smtpout.secureserver.net:587"
    echo "   New Email:     digital.marketing@welleazy.in"
    echo "   Security:      STARTTLS (TLS on port 587)"
else
    echo "⚠️  Warning: Could not update environment variables"
    echo "   Will continue with code deployment"
fi
echo ""

# Wait for update to complete
echo "   Waiting for configuration update..."
sleep 8

# ============================================
# STEP 7: Deploy Updated Code
# ============================================
echo "🚀 STEP 7: Deploying updated Lambda code..."
echo "   Uploading email-lambda.zip..."

UPDATE_RESPONSE=$(aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://email-lambda.zip \
    --region $REGION \
    --output json)

if [ $? -eq 0 ]; then
    echo "✅ Code deployed successfully"
    
    NEW_SIZE=$(echo $UPDATE_RESPONSE | jq -r '.CodeSize')
    NEW_SHA=$(echo $UPDATE_RESPONSE | jq -r '.CodeSha256')
    LAST_MODIFIED=$(echo $UPDATE_RESPONSE | jq -r '.LastModified')
    
    echo "   Code Size:      $(echo "scale=2; $NEW_SIZE/1024/1024" | bc) MB"
    echo "   SHA256:         ${NEW_SHA:0:20}..."
    echo "   Last Modified:  $LAST_MODIFIED"
else
    echo "❌ ERROR: Failed to deploy code"
    exit 1
fi
echo ""

# ============================================
# STEP 8: Wait for Lambda to be Active
# ============================================
echo "⏳ STEP 8: Waiting for Lambda to be active..."
MAX_WAIT=60
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    STATE=$(aws lambda get-function-configuration \
        --function-name $FUNCTION_NAME \
        --region $REGION \
        --query 'State' \
        --output text)
    
    if [ "$STATE" = "Active" ]; then
        echo "✅ Lambda is Active and ready"
        break
    fi
    
    echo "   State: $STATE (waiting... $WAIT_COUNT/$MAX_WAIT)"
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT+1))
done

if [ "$STATE" != "Active" ]; then
    echo "⚠️  WARNING: Lambda state is $STATE"
    echo "   Check AWS Console for details"
fi
echo ""

# ============================================
# STEP 9: Test the Deployment
# ============================================
echo "🧪 STEP 9: Testing deployed Lambda..."

# Test 1: SMTP Connection Test
echo "   Test 1: SMTP Connection..."
TEST_PAYLOAD='{"httpMethod":"POST","body":"{\"action\":\"test\"}"}'

TEST_RESULT=$(aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --payload "$TEST_PAYLOAD" \
    --cli-binary-format raw-in-base64-out \
    /tmp/lambda_test_response.json 2>&1)

if grep -q "200" /tmp/lambda_test_response.json 2>/dev/null; then
    echo "   ✅ SMTP connection test passed"
else
    echo "   ⚠️  Test response: $(cat /tmp/lambda_test_response.json 2>/dev/null || echo 'No response')"
fi

# Test 2: OTP Email Test (optional - comment out to skip)
echo "   Test 2: OTP Email Send Test..."
OTP_PAYLOAD='{
    "httpMethod":"POST",
    "body":"{\"action\":\"send-otp\",\"email\":\"tilakagrawal7777@gmail.com\",\"otp\":\"999888\",\"name\":\"Test User\"}"
}'

OTP_RESULT=$(aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --payload "$OTP_PAYLOAD" \
    --cli-binary-format raw-in-base64-out \
    /tmp/lambda_otp_response.json 2>&1)

if grep -q "success.*true" /tmp/lambda_otp_response.json 2>/dev/null; then
    MESSAGE_ID=$(cat /tmp/lambda_otp_response.json | jq -r '.body' | jq -r '.messageId')
    echo "   ✅ OTP email sent successfully"
    echo "   Message ID: $MESSAGE_ID"
    echo "   Check: tilakagrawal7777@gmail.com"
else
    echo "   ⚠️  OTP test: $(cat /tmp/lambda_otp_response.json 2>/dev/null | jq -r '.body' || echo 'Check AWS Console logs')"
fi

echo ""

# ============================================
# STEP 10: Verify New Configuration
# ============================================
echo "✅ STEP 10: Verifying deployed configuration..."
DEPLOYED_CONFIG=$(aws lambda get-function-configuration \
    --function-name $FUNCTION_NAME \
    --region $REGION)

DEPLOYED_EMAIL=$(echo $DEPLOYED_CONFIG | jq -r '.Environment.Variables.EMAIL_HOST_USER')
DEPLOYED_SMTP=$(echo $DEPLOYED_CONFIG | jq -r '.Environment.Variables.EMAIL_HOST')
DEPLOYED_PORT=$(echo $DEPLOYED_CONFIG | jq -r '.Environment.Variables.EMAIL_PORT')
DEPLOYED_HANDLER=$(echo $DEPLOYED_CONFIG | jq -r '.Handler')

echo "   Email:       $DEPLOYED_EMAIL"
echo "   SMTP:        $DEPLOYED_SMTP:$DEPLOYED_PORT"
echo "   Handler:     $DEPLOYED_HANDLER"
echo ""

# ============================================
# STEP 11: Cleanup
# ============================================
echo "🧹 STEP 11: Cleaning up temporary files..."
rm -rf "$DEPLOY_DIR"
rm -f /tmp/lambda_test_response.json
rm -f /tmp/lambda_otp_response.json
echo "✅ Cleanup complete"
echo ""

# ============================================
# DEPLOYMENT SUMMARY
# ============================================
echo "════════════════════════════════════════════════════════════════════════════"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📋 Summary:"
echo "   Function:           $FUNCTION_NAME"
echo "   Region:             $REGION"
echo "   Status:             ✅ DEPLOYED"
echo ""
echo "📧 Email Configuration:"
echo "   Old Email:          hello@poweramc.co"
echo "   New Email:          digital.marketing@welleazy.in"
echo "   SMTP:               smtpout.secureserver.net:587"
echo "   Security:           STARTTLS"
echo ""
echo "✅ Updated Features:"
echo "   1. OTP Emails           → Debtors (dynamic recipients)"
echo "   2. Payment Notifications → hello@poweramc.com"
echo "   3. Support Requests     → hello@poweramc.com"
echo ""
echo "📂 Backup Location:"
echo "   $BACKUP_FILE"
echo ""
echo "🔗 AWS Console:"
echo "   https://ap-southeast-1.console.aws.amazon.com/lambda/home?region=ap-southeast-1#/functions/$FUNCTION_NAME"
echo ""
echo "⚠️  Important:"
echo "   - Other Lambda functions NOT modified"
echo "   - Django backend still needs deployment"
echo "   - Test all email flows in production"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
