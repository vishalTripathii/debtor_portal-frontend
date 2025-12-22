# AWS Serverless Deployment Guide

This guide explains how to deploy the Debtor Portal application to AWS using serverless architecture.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                                   │
│                                                                          │
│  ┌──────────────┐     ┌─────────────────┐     ┌──────────────────────┐  │
│  │  CloudFront  │────▶│   S3 (Frontend) │     │   MongoDB Atlas      │  │
│  │     CDN      │     │   React SPA     │     │   (Database)         │  │
│  └──────────────┘     └─────────────────┘     └──────────────────────┘  │
│         │                                              ▲                 │
│         ▼                                              │                 │
│  ┌──────────────┐     ┌─────────────────┐              │                 │
│  │ API Gateway  │────▶│  Lambda (API)   │──────────────┘                 │
│  │   REST API   │     │  Django/Mangum  │                                │
│  └──────────────┘     └─────────────────┘                                │
│                              │                                           │
│                              ▼                                           │
│                       ┌─────────────────┐     ┌──────────────────────┐  │
│                       │   S3 (Media)    │     │   SES (Email)        │  │
│                       │ uploads/receipts│     │   OTP & Notifications│  │
│                       └─────────────────┘     └──────────────────────┘  │
│                              ▲                                           │
│                              │                                           │
│  ┌──────────────┐     ┌─────────────────┐                               │
│  │  SQS Queue   │────▶│ Lambda (Worker) │                               │
│  │  PDF Jobs    │     │ PDF Processing  │                               │
│  └──────────────┘     └─────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Node.js** (v18+) and npm
4. **Python** (3.11+)
5. **Serverless Framework** (`npm install -g serverless`)
6. **MongoDB Atlas** account (free tier works)

## Quick Start

### 1. Clone and Configure

```bash
# Navigate to project directory
cd Collections_Debtor_page

# Install serverless plugins
cd backend
npm init -y
npm install --save-dev serverless-python-requirements serverless-offline
cd ..

# Install frontend dependencies
npm install
```

### 2. Set Up MongoDB Atlas

1. Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a database user
3. Whitelist AWS Lambda IPs (or allow access from anywhere for testing)
4. Get your connection string: `mongodb+srv://user:pass@cluster.mongodb.net/debtor_portal`

### 3. Configure AWS Parameter Store

```bash
# Run the setup script
chmod +x deploy/setup-aws-params.sh
./deploy/setup-aws-params.sh dev ap-southeast-1
```

Or manually create parameters:

```bash
# MongoDB URI (SecureString)
aws ssm put-parameter \
    --name "/debtor-portal/dev/mongodb-uri" \
    --value "mongodb+srv://user:pass@cluster.mongodb.net/debtor_portal" \
    --type SecureString \
    --region ap-southeast-1

# Django Secret Key (SecureString)
aws ssm put-parameter \
    --name "/debtor-portal/dev/django-secret-key" \
    --value "your-random-secret-key-here" \
    --type SecureString \
    --region ap-southeast-1

# SES Sender Email (Optional)
aws ssm put-parameter \
    --name "/debtor-portal/dev/ses-sender-email" \
    --value "noreply@yourdomain.com" \
    --type String \
    --region ap-southeast-1
```

### 4. Deploy Backend

```bash
chmod +x deploy/deploy-backend.sh
./deploy/deploy-backend.sh dev ap-southeast-1
```

This will:
- Create S3 buckets for media and frontend
- Create SQS queue for PDF processing
- Deploy Lambda functions
- Set up API Gateway
- Create CloudFront distribution

### 5. Deploy Frontend

```bash
chmod +x deploy/deploy-frontend.sh
./deploy/deploy-frontend.sh dev ap-southeast-1
```

This will:
- Build the React app with production settings
- Upload to S3
- Invalidate CloudFront cache

## Configuration Files

### Backend (`backend/serverless.yml`)

Key configurations:
- `provider.region`: AWS region
- `provider.stage`: Deployment stage (dev/staging/prod)
- `custom.s3BucketName`: Media bucket name
- `functions.api.memorySize`: Lambda memory (affects performance)
- `functions.pdfWorker.timeout`: PDF processing timeout (max 15 min)

### Frontend (`.env`)

```env
# For production, use the API Gateway URL
VITE_API_BASE_URL=https://xxxxxxxxxx.execute-api.ap-southeast-1.amazonaws.com/dev/api
```

## AWS Services Used

| Service | Purpose | Estimated Cost |
|---------|---------|----------------|
| Lambda | API & PDF processing | ~$2-5/month |
| API Gateway | REST API | ~$3-4/month |
| S3 | Media & frontend hosting | ~$0.50/month |
| CloudFront | CDN | ~$4-5/month |
| SQS | Job queue | ~$0.01/month |
| SES | Email (optional) | ~$0.10/1000 emails |
| **Total** | | **~$10-15/month** |

*Costs based on light usage. Free tier may reduce costs further.*

## Environment Variables

### Backend (via Parameter Store & serverless.yml)

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB connection string | Yes |
| `DJANGO_SECRET_KEY` | Django secret key | Yes |
| `S3_BUCKET_NAME` | Media bucket name | Auto |
| `PDF_QUEUE_URL` | SQS queue URL | Auto |
| `SES_SENDER_EMAIL` | Verified sender email | No |

### Frontend (`.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_BASE_URL` | API Gateway URL | Yes |
| `VITE_BASE_URL` | Base path for assets | No |

## Deployment Stages

### Development
```bash
./deploy/deploy-backend.sh dev ap-southeast-1
./deploy/deploy-frontend.sh dev ap-southeast-1
```

### Staging
```bash
./deploy/deploy-backend.sh staging ap-southeast-1
./deploy/deploy-frontend.sh staging ap-southeast-1
```

### Production
```bash
./deploy/deploy-backend.sh prod ap-southeast-1
./deploy/deploy-frontend.sh prod ap-southeast-1
```

## Monitoring & Logs

### View Lambda Logs
```bash
# API logs
serverless logs -f api --stage dev

# PDF worker logs
serverless logs -f pdfWorker --stage dev

# Tail logs in real-time
serverless logs -f api --stage dev --tail
```

### CloudWatch Metrics
- Lambda invocations, errors, duration
- API Gateway requests, latency, 4xx/5xx errors
- SQS messages in flight, age

## Troubleshooting

### Lambda Cold Starts
If API responses are slow on first request:
1. Increase Lambda memory (also increases CPU)
2. Enable Provisioned Concurrency for production
3. Use Lambda warming (CloudWatch scheduled event)

### MongoDB Connection Issues
1. Check MongoDB Atlas IP whitelist (allow 0.0.0.0/0 for Lambda)
2. Verify connection string in Parameter Store
3. Check Lambda security group outbound rules

### File Upload Failures
1. Check S3 bucket permissions
2. Verify Lambda IAM role has s3:PutObject permission
3. Check file size limits (API Gateway: 10MB, increase via binary media types)

### PDF Processing Failures
1. Check SQS dead letter queue for failed messages
2. Review CloudWatch logs for pdf worker
3. Ensure Lambda has sufficient memory (2GB recommended)

## Updating the Application

### Backend Update
```bash
cd backend
serverless deploy --stage dev
```

### Frontend Update
```bash
npm run build
./deploy/deploy-frontend.sh dev ap-southeast-1
```

### Full Redeployment
```bash
./deploy/deploy-backend.sh dev ap-southeast-1
./deploy/deploy-frontend.sh dev ap-southeast-1
```

## Cleanup

To remove all AWS resources:

```bash
cd backend
serverless remove --stage dev --region ap-southeast-1
```

**Warning:** This will delete:
- Lambda functions
- API Gateway
- S3 buckets (including all files)
- SQS queues
- CloudFront distribution

## Local Development

You can still run locally for development:

```bash
# Backend
cd backend
python manage.py runserver 8000

# Frontend
cd ..
npm run dev
```

Set `USE_S3_STORAGE=False` in backend `.env` for local file storage.

## Security Best Practices

1. **Never commit `.env` files** - use Parameter Store for secrets
2. **Enable AWS WAF** on API Gateway for production
3. **Set up CloudTrail** for audit logging
4. **Use least privilege** IAM policies
5. **Enable S3 bucket versioning** for media files
6. **Set up CloudWatch alarms** for error rates

## Support

For issues:
1. Check CloudWatch logs
2. Review this documentation
3. Open an issue on the repository
