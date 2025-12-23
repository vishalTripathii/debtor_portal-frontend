@echo off
echo ============================================
echo Deploying Debtor Portal - Simple Method
echo ============================================

REM Set AWS credentials
set AWS_ACCESS_KEY_ID=AKIA3W57UCLYC72TWKBX
set AWS_SECRET_ACCESS_KEY=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
set AWS_DEFAULT_REGION=ap-southeast-1

echo.
echo Step 1: Verifying AWS Connection...
aws sts get-caller-identity
if errorlevel 1 (
    echo ERROR: AWS connection failed
    exit /b 1
)

echo.
echo Step 2: Installing Python dependencies...
cd backend
pip install -r requirements.txt -t ./package
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

echo.
echo Step 3: Creating deployment package...
cd package
powershell -command "Compress-Archive -Path * -DestinationPath ../lambda-deployment.zip -Force"
cd ..
powershell -command "Compress-Archive -Path api,debtorportal,manage.py,lambda_handler.py -Update -DestinationPath lambda-deployment.zip"

echo.
echo Step 4: Uploading to S3...
aws s3 cp lambda-deployment.zip s3://debtor-portal-api-dev-serverlessdeploymentbucket-rhgfzohvfm57/lambda-deployment.zip

echo.
echo Step 5: Updating Lambda function...
aws lambda update-function-code ^
    --function-name debtor-portal-api-dev-api ^
    --s3-bucket debtor-portal-api-dev-serverlessdeploymentbucket-rhgfzohvfm57 ^
    --s3-key lambda-deployment.zip ^
    --region ap-southeast-1

echo.
echo ============================================
echo Backend deployment complete!
echo ============================================

cd ..

echo.
echo Step 6: Building frontend...
call npm install
if errorlevel 1 (
    echo ERROR: Frontend npm install failed
    exit /b 1
)

call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed
    exit /b 1
)

echo.
echo Step 7: Deploying frontend to S3...
aws s3 sync dist/ s3://power-amc-debtor-portal-frontend-dev/ --delete --acl public-read

echo.
echo Step 8: Setting S3 website configuration...
aws s3 website s3://power-amc-debtor-portal-frontend-dev/ ^
    --index-document index.html ^
    --error-document index.html

echo.
echo ============================================
echo DEPLOYMENT COMPLETE!
echo ============================================
echo.
echo Frontend URL: http://power-amc-debtor-portal-frontend-dev.s3-website-ap-southeast-1.amazonaws.com
echo Backend API: https://YOUR-API-GATEWAY-URL.execute-api.ap-southeast-1.amazonaws.com/dev/api
echo.
echo QR codes should now be visible in the deployed version!
echo ============================================

pause
