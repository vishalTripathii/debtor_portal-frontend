@echo off
REM ============================================
REM Complete Deployment Script for Windows
REM ============================================

echo ============================================
echo Debtor Portal - Complete Deployment
echo ============================================
echo.

REM Set AWS Credentials
set AWS_ACCESS_KEY_ID=AKIA3W57UCLYC72TWKBX
set AWS_SECRET_ACCESS_KEY=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
set AWS_DEFAULT_REGION=ap-southeast-1

REM Configuration
set STAGE=dev
set REGION=ap-southeast-1
set MEDIA_BUCKET=power-amc-debtor-media-dev
set FRONTEND_BUCKET=power-amc-debtor-portal-frontend-dev
set API_DEPLOYMENT_BUCKET=debtor-portal-api-dev-serverlessdeploymentbucket-rhgfzohvfm57

echo Step 1: Deploying Backend to AWS Lambda...
echo ============================================
cd backend

REM Install serverless if not installed
where serverless >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing Serverless Framework...
    npm install -g serverless
)

REM Install dependencies
echo Installing backend dependencies...
call npm install

REM Deploy backend
echo Deploying backend with Serverless...
call serverless deploy --stage %STAGE% --region %REGION%

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Backend deployment failed!
    pause
    exit /b 1
)

REM Get API Gateway URL
echo Getting API Gateway URL...
for /f "tokens=*" %%i in ('serverless info --stage %STAGE% --region %REGION% ^| findstr "https://.*execute-api"') do set API_LINE=%%i
for /f "tokens=2" %%i in ("%API_LINE%") do set API_URL=%%i

echo API Gateway URL: %API_URL%

cd ..

echo.
echo Step 2: Building Frontend...
echo ============================================

REM Create/Update .env file with API URL
echo VITE_API_BASE_URL=%API_URL%/api > .env
echo VITE_S3_MEDIA_URL=https://%MEDIA_BUCKET%.s3.amazonaws.com >> .env

REM Install frontend dependencies
echo Installing frontend dependencies...
call npm install

REM Build frontend
echo Building frontend...
call npm run build

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Frontend build failed!
    pause
    exit /b 1
)

echo.
echo Step 3: Deploying Frontend to S3...
echo ============================================

REM Create S3 bucket if it doesn't exist
aws s3 ls s3://%FRONTEND_BUCKET% >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Creating S3 bucket: %FRONTEND_BUCKET%...
    aws s3 mb s3://%FRONTEND_BUCKET% --region %REGION%
    
    REM Configure bucket for static website hosting
    aws s3 website s3://%FRONTEND_BUCKET% --index-document index.html --error-document index.html
    
    REM Set public access policy
    echo { > bucket-policy.json
    echo   "Version": "2012-10-17", >> bucket-policy.json
    echo   "Statement": [ >> bucket-policy.json
    echo     { >> bucket-policy.json
    echo       "Sid": "PublicReadGetObject", >> bucket-policy.json
    echo       "Effect": "Allow", >> bucket-policy.json
    echo       "Principal": "*", >> bucket-policy.json
    echo       "Action": "s3:GetObject", >> bucket-policy.json
    echo       "Resource": "arn:aws:s3:::%FRONTEND_BUCKET%/*" >> bucket-policy.json
    echo     } >> bucket-policy.json
    echo   ] >> bucket-policy.json
    echo } >> bucket-policy.json
    
    aws s3api put-bucket-policy --bucket %FRONTEND_BUCKET% --policy file://bucket-policy.json
    del bucket-policy.json
)

REM Upload built files to S3
echo Uploading frontend files to S3...
aws s3 sync dist/ s3://%FRONTEND_BUCKET%/ --delete --cache-control "no-cache" --acl public-read

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Frontend deployment failed!
    pause
    exit /b 1
)

REM Get website URL
set WEBSITE_URL=http://%FRONTEND_BUCKET%.s3-website-%REGION%.amazonaws.com

echo.
echo ============================================
echo DEPLOYMENT SUCCESSFUL!
echo ============================================
echo.
echo Backend API URL: %API_URL%
echo Frontend URL: %WEBSITE_URL%
echo Media Bucket: https://%MEDIA_BUCKET%.s3.amazonaws.com
echo.
echo QR codes will be loaded from: https://%MEDIA_BUCKET%.s3.amazonaws.com/debtor_images/
echo.
echo ============================================
echo.

pause
