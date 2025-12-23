# DEPLOYMENT GUIDE - Debtor Portal
## Complete Deployment to AWS

### Prerequisites Completed ✓
- AWS Credentials: AKIA3W57UCLYC72TWKBX
- S3 Buckets created: power-amc-debtor-media-dev (with 999+ QR codes)
- MongoDB Atlas connected

---

## STEP-BY-STEP DEPLOYMENT

### Step 1: Configure AWS Credentials (5 minutes)

Open Command Prompt and run:
```cmd
aws configure
```

When prompted, enter:
- **AWS Access Key ID**: `AKIA3W57UCLYC72TWKBX`
- **AWS Secret Access Key**: `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`
- **Default region name**: `ap-southeast-1`
- **Default output format**: `json`

Verify it works:
```cmd
aws s3 ls s3://power-amc-debtor-media-dev/debtor_images/ --max-items 5
```
You should see your QR code files listed.

---

### Step 2: Deploy Backend (10-15 minutes)

```cmd
cd E:\Collections_Debtor_page\Collections_Debtor_page\backend

# Install Serverless Framework (if not installed)
npm install -g serverless

# Install dependencies
npm install

# Deploy to AWS Lambda
serverless deploy --stage dev --region ap-southeast-1
```

**SAVE the API Gateway URL** that appears at the end! It will look like:
```
https://xxxxxxxxxx.execute-api.ap-southeast-1.amazonaws.com/dev
```

---

### Step 3: Build & Deploy Frontend (5-10 minutes)

```cmd
cd E:\Collections_Debtor_page\Collections_Debtor_page

# Create .env file with API URL (replace with YOUR URL from Step 2)
echo VITE_API_BASE_URL=https://YOUR-API-URL.execute-api.ap-southeast-1.amazonaws.com/dev/api > .env
echo VITE_S3_MEDIA_URL=https://power-amc-debtor-media-dev.s3.amazonaws.com >> .env

# Install dependencies
npm install

# Build frontend
npm run build

# Deploy to S3
aws s3 sync dist/ s3://power-amc-debtor-portal-frontend-dev/ --delete --acl public-read

# Configure S3 for website hosting
aws s3 website s3://power-amc-debtor-portal-frontend-dev/ --index-document index.html --error-document index.html
```

---

### Step 4: Set Bucket Policy for Frontend

Create `bucket-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::power-amc-debtor-portal-frontend-dev/*"
    }
  ]
}
```

Apply it:
```cmd
aws s3api put-bucket-policy --bucket power-amc-debtor-portal-frontend-dev --policy file://bucket-policy.json
```

---

### Step 5: Access Your Deployed Application

**Frontend URL (Public):**
```
http://power-amc-debtor-portal-frontend-dev.s3-website-ap-southeast-1.amazonaws.com
```

**Backend API URL:**
```
https://YOUR-API-URL.execute-api.ap-southeast-1.amazonaws.com/dev/api
```

**QR Codes URL (Verified Working):**
```
https://power-amc-debtor-media-dev.s3.amazonaws.com/debtor_images/202203000242631.png
```

---

## TROUBLESHOOTING

### QR Codes Not Showing?
1. Check browser console for errors
2. Verify S3 bucket permissions:
   ```cmd
   aws s3api get-bucket-acl --bucket power-amc-debtor-media-dev
   ```
3. Test direct QR image access:
   ```
   https://power-amc-debtor-media-dev.s3.amazonaws.com/debtor_images/202203000242631.png
   ```

### Backend Errors?
Check Lambda logs:
```cmd
serverless logs -f api --stage dev --tail
```

---

## QUICK DEPLOY SCRIPT

I've created `deploy-complete.bat` - just double-click it to deploy everything automatically!

Location: `E:\Collections_Debtor_page\Collections_Debtor_page\deploy-complete.bat`

---

## Your Configuration Summary

✓ **Backend Bucket**: debtor-portal-api-dev-serverlessdeploymentbucket-rhgfzohvfm57
✓ **Media Bucket**: power-amc-debtor-media-dev (999+ QR codes stored)
✓ **Frontend Bucket**: power-amc-debtor-portal-frontend-dev
✓ **Region**: Asia Pacific (Singapore) ap-southeast-1
✓ **MongoDB**: Connected to debtor-portal-cluster
✓ **AWS Credentials**: Configured and working

---

## After Deployment

1. Test QR code display in production
2. Test payment flow
3. Test file uploads
4. Verify all features work

The QR codes WILL work in production because:
- They're already in S3 (power-amc-debtor-media-dev)
- Lambda has automatic AWS credentials
- The code correctly fetches from debtors collection → qr_code_storage_key
