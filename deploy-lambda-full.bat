@echo off
echo ============================================
echo Creating Full Lambda Deployment Package
echo ============================================

cd /d E:\Collections_Debtor_page\Collections_Debtor_page\backend

echo Step 1: Cleaning up old packages...
if exist lambda_deploy rmdir /s /q lambda_deploy
mkdir lambda_deploy

echo Step 2: Installing Python dependencies...
pip install -r requirements.txt -t lambda_deploy --no-cache-dir --upgrade

echo Step 3: Copying application code...
xcopy /E /I /Y api lambda_deploy\api
xcopy /E /I /Y debtorportal lambda_deploy\debtorportal
copy /Y lambda_handler.py lambda_deploy\
copy /Y excel_processor.py lambda_deploy\
copy /Y qr_processor.py lambda_deploy\
copy /Y manage.py lambda_deploy\

echo Step 4: Creating deployment zip...
cd lambda_deploy
powershell -command "Compress-Archive -Path * -DestinationPath ../lambda-full.zip -Force"
cd ..

echo Step 5: Deploying to Lambda...
set AWS_ACCESS_KEY_ID=AKIA3W57UCLYC72TWKBX
set AWS_SECRET_ACCESS_KEY=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
set AWS_DEFAULT_REGION=ap-southeast-1

aws lambda update-function-code ^
    --function-name debtor-portal-api-dev-api ^
    --zip-file fileb://lambda-full.zip ^
    --region ap-southeast-1

echo.
echo Waiting for deployment to complete...
timeout /t 10 /nobreak

echo.
echo ============================================
echo Deployment Complete!
echo ============================================

cd ..
pause
