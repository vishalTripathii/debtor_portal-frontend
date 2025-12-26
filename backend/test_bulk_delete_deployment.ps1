# ============================================
# COMPREHENSIVE BULK DELETE DEPLOYMENT TEST
# ============================================

$API_BASE = "https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev"
$DELETE_ENDPOINT = "$API_BASE/bulk/delete-excel"
$UPDATE_ENDPOINT = "$API_BASE/bulk/update-excel"

Write-Host "============================================" -ForegroundColor Magenta
Write-Host "   DEPLOYMENT VERIFICATION TEST" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

# Test 1: Lambda Function Status
Write-Host "`n[TEST 1] Checking Lambda Function..." -ForegroundColor Cyan
$lambdaInfo = aws lambda get-function --function-name debtor-portal-bulk-operations-dev --region ap-southeast-1 --query 'Configuration.[FunctionName,Runtime,MemorySize,Timeout,State]' --output text
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Lambda exists: $lambdaInfo" -ForegroundColor Green
} else {
    Write-Host "  ✗ Lambda NOT found!" -ForegroundColor Red
}

# Test 2: Lambda Environment Variables
Write-Host "`n[TEST 2] Checking Lambda Environment..." -ForegroundColor Cyan
$mongoUri = aws lambda get-function-configuration --function-name debtor-portal-bulk-operations-dev --region ap-southeast-1 --query 'Environment.Variables.MONGODB_URI' --output text
if ($mongoUri -match "mongodb") {
    Write-Host "  ✓ MongoDB URI configured" -ForegroundColor Green
} else {
    Write-Host "  ✗ MongoDB URI NOT configured!" -ForegroundColor Red
}

# Test 3: Lambda Layers
Write-Host "`n[TEST 3] Checking Lambda Layers..." -ForegroundColor Cyan
$layers = aws lambda get-function-configuration --function-name debtor-portal-bulk-operations-dev --region ap-southeast-1 --query 'Layers[*].Arn' --output text
if ($layers -match "AWSSDKPandas") {
    Write-Host "  ✓ Pandas layer attached: $layers" -ForegroundColor Green
} else {
    Write-Host "  ✗ Pandas layer NOT attached!" -ForegroundColor Red
}

# Test 4: API Gateway Resources
Write-Host "`n[TEST 4] Checking API Gateway Resources..." -ForegroundColor Cyan
$resources = aws apigateway get-resources --rest-api-id jxnu8wrip2 --region ap-southeast-1 --query 'items[?path==`/bulk/delete-excel` || path==`/bulk/update-excel`].[path,id]' --output text
if ($resources -match "/bulk/delete-excel" -and $resources -match "/bulk/update-excel") {
    Write-Host "  ✓ API Gateway resources exist" -ForegroundColor Green
    Write-Host "    $($resources -replace "`t", " - ")" -ForegroundColor Gray
} else {
    Write-Host "  ✗ API Gateway resources NOT found!" -ForegroundColor Red
}

# Test 5: Lambda Invocation Permission
Write-Host "`n[TEST 5] Checking Lambda Permissions..." -ForegroundColor Cyan
$policy = aws lambda get-policy --function-name debtor-portal-bulk-operations-dev --region ap-southeast-1 --query 'Policy' --output text 2>$null
if ($policy -match "apigateway") {
    Write-Host "  ✓ API Gateway invoke permission exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ API Gateway invoke permission NOT found!" -ForegroundColor Red
}

# Test 6: Direct Lambda Invocation
Write-Host "`n[TEST 6] Testing Direct Lambda Invocation..." -ForegroundColor Cyan
$testPayload = @{
    path = "/delete"
    httpMethod = "POST"
    headers = @{
        "Content-Type" = "multipart/form-data; boundary=----WebKitFormBoundary"
    }
    body = ""
} | ConvertTo-Json -Compress

$testPayload | Out-File -Encoding utf8 test_payload.json
$invokeResult = aws lambda invoke --function-name debtor-portal-bulk-operations-dev --region ap-southeast-1 --payload file://test_payload.json response.json 2>&1
if ($LASTEXITCODE -eq 0) {
    $response = Get-Content response.json | ConvertFrom-Json
    Write-Host "  Lambda invocation successful!" -ForegroundColor Green
    Write-Host "  Status Code: $($response.statusCode)" -ForegroundColor Gray
    if ($response.statusCode -eq 401) {
        Write-Host "  ✓ Lambda returns 401 (auth required) - Expected behavior" -ForegroundColor Green
    }
} else {
    Write-Host "  ✗ Lambda invocation FAILED!" -ForegroundColor Red
    Write-Host "  Error: $invokeResult" -ForegroundColor Red
}

# Test 7: CloudWatch Logs
Write-Host "`n[TEST 7] Checking CloudWatch Logs..." -ForegroundColor Cyan
$logGroup = "/aws/lambda/debtor-portal-bulk-operations-dev"
$logStreams = aws logs describe-log-streams --log-group-name $logGroup --region ap-southeast-1 --order-by LastEventTime --descending --max-items 1 --query 'logStreams[0].logStreamName' --output text 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ CloudWatch logs exist: $logStreams" -ForegroundColor Green
} else {
    Write-Host "  ! CloudWatch logs not yet created (normal for first deploy)" -ForegroundColor Yellow
}

# Test 8: Test MongoDB Connection from Lambda
Write-Host "`n[TEST 8] Testing MongoDB Connection..." -ForegroundColor Cyan
$testMongo = @{
    path = "/delete"
    httpMethod = "POST"
    headers = @{
        "Content-Type" = "application/json"
    }
    body = '{"test": true}'
} | ConvertTo-Json -Compress

$testMongo | Out-File -Encoding utf8 test_mongo.json
aws lambda invoke --function-name debtor-portal-bulk-operations-dev --region ap-southeast-1 --payload file://test_mongo.json mongo_response.json --log-type Tail --query 'LogResult' --output text 2>$null | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) } | Select-String -Pattern "MongoDB|Error|Exception" | ForEach-Object {
    if ($_ -match "Error|Exception") {
        Write-Host "  ⚠ $($_.Line)" -ForegroundColor Yellow
    } else {
        Write-Host "  ✓ $($_.Line)" -ForegroundColor Green
    }
}

# Test 9: Frontend Deployment
Write-Host "`n[TEST 9] Checking Frontend Deployment..." -ForegroundColor Cyan
$s3Files = aws s3 ls s3://power-amc-debtor-portal-frontend-dev/ --region ap-southeast-1 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Frontend deployed to S3" -ForegroundColor Green
    $indexExists = $s3Files -match "index.html"
    if ($indexExists) {
        Write-Host "  ✓ index.html found" -ForegroundColor Green
    }
} else {
    Write-Host "  ✗ Frontend NOT deployed!" -ForegroundColor Red
}

# Test 10: API Endpoint Accessibility
Write-Host "`n[TEST 10] Testing API Endpoint Accessibility..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri $DELETE_ENDPOINT -Method POST -ContentType "application/json" -Body '{"test":true}' -ErrorAction Stop
    Write-Host "  ✓ DELETE endpoint accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 401 -or $_.Exception.Response.StatusCode -eq 400) {
        Write-Host "  ✓ DELETE endpoint accessible (returned expected error)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ DELETE endpoint error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

try {
    $response = Invoke-WebRequest -Uri $UPDATE_ENDPOINT -Method POST -ContentType "application/json" -Body '{"test":true}' -ErrorAction Stop
    Write-Host "  ✓ UPDATE endpoint accessible (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 401 -or $_.Exception.Response.StatusCode -eq 400) {
        Write-Host "  ✓ UPDATE endpoint accessible (returned expected error)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ UPDATE endpoint error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Cleanup
Remove-Item -Path test_payload.json, test_mongo.json, response.json, mongo_response.json -ErrorAction SilentlyContinue

Write-Host "`n============================================" -ForegroundColor Magenta
Write-Host "   TEST SUMMARY" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
Write-Host "`nDeployment URLs:" -ForegroundColor Yellow
Write-Host "  Frontend: https://d1hmzuewg6k3ss.cloudfront.net" -ForegroundColor Cyan
Write-Host "  API Base: $API_BASE" -ForegroundColor Cyan
Write-Host "  DELETE: $DELETE_ENDPOINT" -ForegroundColor Cyan
Write-Host "  UPDATE: $UPDATE_ENDPOINT" -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Open browser: https://d1hmzuewg6k3ss.cloudfront.net" -ForegroundColor White
Write-Host "  2. Login as admin" -ForegroundColor White
Write-Host "  3. Select 'bulkDelete' mode" -ForegroundColor White
Write-Host "  4. Upload Excel with Account Numbers" -ForegroundColor White
Write-Host "  5. Check CloudWatch logs for execution details" -ForegroundColor White
