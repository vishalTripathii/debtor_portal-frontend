#!/bin/bash

# Test Production Email Service
echo "🧪 Testing Production Email Service"
echo "============================================================"
echo "API Gateway URL: https://29o7gp9n8l.execute-api.ap-southeast-1.amazonaws.com/dev"
echo "National ID: 1100100051224"
echo "Email: tilakagrawal7777@gmail.com"
echo ""

# Test OTP sending
echo "📧 Sending OTP via production API..."
echo ""

RESPONSE=$(curl -s -X POST \
  "https://29o7gp9n8l.execute-api.ap-southeast-1.amazonaws.com/dev/email/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "send-otp",
    "email": "tilakagrawal7777@gmail.com",
    "otp": "789012",
    "name": "ศราวุธ ชัยมงคล"
  }')

echo "📋 Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Check if successful
if echo "$RESPONSE" | grep -q '"success": true'; then
    echo "✅ EMAIL SENT SUCCESSFULLY via Production API!"
    echo "📧 Check email at: tilakagrawal7777@gmail.com"
    echo "🔢 OTP Code: 789012"
    echo ""
    echo "🎉 Production email service is working!"
    exit 0
else
    echo "❌ EMAIL FAILED!"
    echo "Check the error message above"
    exit 1
fi
