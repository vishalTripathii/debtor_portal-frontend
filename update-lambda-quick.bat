@echo off
echo ============================================
echo Quick Lambda Update - Source Files Only
echo ============================================

set AWS_ACCESS_KEY_ID=AKIA3W57UCLYC72TWKBX
set AWS_SECRET_ACCESS_KEY=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
set AWS_DEFAULT_REGION=ap-southeast-1

echo Creating deployment package with updated code...
cd backend

REM Create a zip with just the Python source files
powershell -command "if (Test-Path lambda-update.zip) { Remove-Item lambda-update.zip }"
powershell -command "Compress-Archive -Path api\*.py,api\migrations,debtorportal\*.py,lambda_handler.py,excel_processor.py,qr_processor.py -DestinationPath lambda-update.zip -Force"

echo.
echo Uploading to Lambda function: debtor-portal-api-dev-api...
aws lambda update-function-code ^
    --function-name debtor-portal-api-dev-api ^
    --zip-file fileb://lambda-update.zip ^
    --region ap-southeast-1

echo.
echo Waiting for Lambda to finish updating...
timeout /t 5 /nobreak

echo.
echo Updating Excel Processor Lambda...
aws lambda update-function-code ^
    --function-name debtor-portal-api-dev-excelProcessor ^
    --zip-file fileb://lambda-update.zip ^
    --region ap-southeast-1

echo.
echo ============================================
echo Lambda functions updated with QR code fix!
echo ============================================
echo.
echo Your API URL: https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev
echo.

cd ..
pause
