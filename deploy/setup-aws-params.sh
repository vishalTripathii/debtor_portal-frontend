#!/bin/bash

# ============================================
# AWS Parameter Store Setup Script
# ============================================
# This script helps set up required AWS Parameter Store entries
# for the Debtor Portal serverless deployment.

set -e

STAGE=${1:-dev}
REGION=${2:-ap-southeast-1}

echo "============================================"
echo "AWS Parameter Store Setup"
echo "Stage: $STAGE"
echo "Region: $REGION"
echo "============================================"

# Function to create parameter
create_param() {
    local name=$1
    local description=$2
    local is_secure=$3

    echo ""
    echo "Parameter: $name"
    echo "Description: $description"

    # Check if parameter exists
    if aws ssm get-parameter --name "$name" --region $REGION &> /dev/null; then
        echo "Status: Already exists"
        read -p "Do you want to update it? (y/N): " update
        if [ "$update" != "y" ] && [ "$update" != "Y" ]; then
            return
        fi
    fi

    read -p "Enter value: " value

    if [ -z "$value" ]; then
        echo "Skipped (empty value)"
        return
    fi

    if [ "$is_secure" = "true" ]; then
        aws ssm put-parameter \
            --name "$name" \
            --value "$value" \
            --type SecureString \
            --overwrite \
            --region $REGION
    else
        aws ssm put-parameter \
            --name "$name" \
            --value "$value" \
            --type String \
            --overwrite \
            --region $REGION
    fi

    echo "Created/Updated successfully"
}

echo ""
echo "This script will help you set up the required AWS Parameter Store entries."
echo "You can skip any parameter by pressing Enter without a value."
echo ""

# MongoDB URI (Required)
create_param \
    "/debtor-portal/$STAGE/mongodb-uri" \
    "MongoDB connection URI (e.g., mongodb+srv://user:pass@cluster.mongodb.net/)" \
    "true"

# Django Secret Key (Required - can auto-generate)
echo ""
echo "Parameter: /debtor-portal/$STAGE/django-secret-key"
echo "Description: Django secret key for session security"

if aws ssm get-parameter --name "/debtor-portal/$STAGE/django-secret-key" --region $REGION &> /dev/null; then
    echo "Status: Already exists"
    read -p "Do you want to regenerate it? (y/N): " regen
    if [ "$regen" = "y" ] || [ "$regen" = "Y" ]; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 50)
        aws ssm put-parameter \
            --name "/debtor-portal/$STAGE/django-secret-key" \
            --value "$SECRET_KEY" \
            --type SecureString \
            --overwrite \
            --region $REGION
        echo "Regenerated successfully"
    fi
else
    read -p "Generate a random secret key? (Y/n): " generate
    if [ "$generate" != "n" ] && [ "$generate" != "N" ]; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 50)
        aws ssm put-parameter \
            --name "/debtor-portal/$STAGE/django-secret-key" \
            --value "$SECRET_KEY" \
            --type SecureString \
            --region $REGION
        echo "Created successfully"
    else
        create_param \
            "/debtor-portal/$STAGE/django-secret-key" \
            "Django secret key" \
            "true"
    fi
fi

# SES Sender Email (Optional)
create_param \
    "/debtor-portal/$STAGE/ses-sender-email" \
    "AWS SES verified sender email address" \
    "false"

echo ""
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo ""
echo "Parameter Store entries created/updated:"
aws ssm describe-parameters \
    --parameter-filters "Key=Name,Values=/debtor-portal/$STAGE/" \
    --region $REGION \
    --query "Parameters[].Name" \
    --output table

echo ""
echo "Next steps:"
echo "1. Verify MongoDB Atlas allows connections from AWS Lambda IPs"
echo "2. If using SES, verify your sender email in AWS SES console"
echo "3. Run: ./deploy-backend.sh $STAGE $REGION"
