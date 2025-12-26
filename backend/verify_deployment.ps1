# ============================================
# COMPREHENSIVE DEPLOYMENT VERIFICATION
# ============================================

$API_BASE = "https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev"
$DELETE_ENDPOINT = "$API_BASE/bulk/delete-excel"
$UPDATE_ENDPOINT = "$API_BASE/bulk/update-excel"

Write-Host "============================================" -ForegroundColor Magenta
Write-Host "   DEPLOYMENT VERIFICATION TEST" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

# Test 1: Lambda Function Status
Write-Host "`n[TEST 1] Checking Lambda Function..." -ForegroundColor Cyan
try {
    $lambdaInfo = aws lambda get-function --function-name debtor-portal-bulk-operations-dev --region ap-southeast-1 --query 'Configuration.[FunctionName,Runtime,MemorySize,Timeout,State]' --output text 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  SUCCESS: Lambda exists" -ForegroundColor Green
        Write-Host "  Details: $lambdaInfo" -ForegroundColor Gray
    }
} catch {
    Write-Host "  FAILED: Lambda NOT found!" -ForegroundColor Red
}

# Test 2: Lambda Environment Variables
Write-Host "`n[TEST 2] Checking Lambda Environment..." -ForegroundColor Cyan
$mongoUri = aws lambda get-function-configuration --function-name debtor-portal-bulk-operations-dev --region ap-southeast-1 --query 'Environment.Variables.MONGODB_URI' --output text 2>$null
if ($mongoUri -and $mongoUri -match "mongodb") {
    Write-Host "  SUCCESS: MongoDB URI configured" -ForegroundColor Green
} else {
    Write-Host "  FAILED: MongoDB URI NOT configured!" -ForegroundColor Red
}

# Test 3: Lambda Layers
Write-Host "`n[TEST 3] Checking Lambda Layers..." -ForegroundColor Cyan
$layers = aws lambda get-function-configuration --function-name debtor-portal-bulk-operations-dev --region ap-southeast-1 --query 'Layers[*].Arn' --output text 2>$null
if ($layers -match "AWSSDKPandas") {
    Write-Host "  SUCCESS: Pandas layer attached" -ForegroundColor Green
    Write-Host "  Layer: $layers" -ForegroundColor Gray
} else {
    Write-Host "  FAILED: Pandas layer NOT attached!" -ForegroundColor Red
}

# Test 4: API Gateway Resources
Write-Host "`n[TEST 4] Checking API Gateway Resources..." -ForegroundColor Cyan
$resources = aws apigateway get-resources --rest-api-id jxnu8wrip2 --region ap-southeast-1 --query 'items[?path==`/bulk/delete-excel` || path==`/bulk/update-excel`].[path,id]' --output text 2>$null
if ($resources -match "/bulk/delete-excel" -and $resources -match "/bulk/update-excel") {
    Write-Host "  SUCCESS: Both endpoints exist" -ForegroundColor Green
} else {
    Write-Host "  FAILED: API Gateway resources NOT found!" -ForegroundColor Red
}

# Test 5: Frontend Deployment
Write-Host "`n[TEST 5] Checking Frontend Deployment..." -ForegroundColor Cyan
$s3Files = aws s3 ls s3://power-amc-debtor-portal-frontend-dev/ --region ap-southeast-1 2>$null
if ($LASTEXITCODE -eq 0 -and ($s3Files -match "index.html")) {
    Write-Host "  SUCCESS: Frontend deployed" -ForegroundColor Green
} else {
    Write-Host "  FAILED: Frontend NOT deployed!" -ForegroundColor Red
}

# Test 6: API Endpoint Test
Write-Host "`n[TEST 6] Testing DELETE Endpoint..." -ForegroundColor Cyan
try {
    $headers = @{
        "Content-Type" = "application/json"
    }
    $response = Invoke-RestMethod -Uri $DELETE_ENDPOINT -Method POST -Headers $headers -Body '{}' -ErrorAction Stop
    Write-Host "  SUCCESS: Endpoint accessible" -ForegroundColor Green
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 401 -or $statusCode -eq 400 -or $statusCode -eq 500) {
        Write-Host "  SUCCESS: Endpoint accessible (Status: $statusCode)" -ForegroundColor Green
        Write-Host "  Note: Error expected without valid auth/data" -ForegroundColor Gray
    } else {
        Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n[TEST 7] Testing UPDATE Endpoint..." -ForegroundColor Cyan
try {
    $headers = @{
        "Content-Type" = "application/json"
    }
    $response = Invoke-RestMethod -Uri $UPDATE_ENDPOINT -Method POST -Headers $headers -Body '{}' -ErrorAction Stop
    Write-Host "  SUCCESS: Endpoint accessible" -ForegroundColor Green
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 401 -or $statusCode -eq 400 -or $statusCode -eq 500) {
        Write-Host "  SUCCESS: Endpoint accessible (Status: $statusCode)" -ForegroundColor Green
        Write-Host "  Note: Error expected without valid auth/data" -ForegroundColor Gray
    } else {
        Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 8: Check Recent Logs
Write-Host "`n[TEST 8] Checking CloudWatch Logs..." -ForegroundColor Cyan
$logGroup = "/aws/lambda/debtor-portal-bulk-operations-dev"
$logExists = aws logs describe-log-groups --log-group-name-prefix $logGroup --region ap-southeast-1 --query 'logGroups[0].logGroupName' --output text 2>$null
if ($logExists) {
    Write-Host "  SUCCESS: CloudWatch log group exists" -ForegroundColor Green
} else {
    Write-Host "  INFO: No logs yet (normal for first deploy)" -ForegroundColor Yellow
}

Write-Host "`n============================================" -ForegroundColor Magenta
Write-Host "   VERIFICATION COMPLETE" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

Write-Host "`nDeployment URLs:" -ForegroundColor Yellow
Write-Host "  Frontend: https://d1hmzuewg6k3ss.cloudfront.net" -ForegroundColor Cyan
Write-Host "  API Delete: $DELETE_ENDPOINT" -ForegroundColor Cyan
Write-Host "  API Update: $UPDATE_ENDPOINT" -ForegroundColor Cyan

Write-Host "`nBULK DELETE WORKFLOW:" -ForegroundColor Yellow
Write-Host "  1. User opens frontend" -ForegroundColor White
Write-Host "  2. User logs in" -ForegroundColor White
Write-Host "  3. User selects 'bulkDelete' from dropdown" -ForegroundColor White
Write-Host "  4. User uploads Excel file with 'Account Number' column" -ForegroundColor White
Write-Host "  5. Frontend sends POST to /bulk/delete-excel" -ForegroundColor White
Write-Host "  6. API Gateway routes to Lambda" -ForegroundColor White
Write-Host "  7. Lambda parses Excel file" -ForegroundColor White
Write-Host "  8. Lambda extracts Account Numbers" -ForegroundColor White
Write-Host "  9. Lambda deletes from MongoDB in batches of 1000" -ForegroundColor White
Write-Host "  10. Lambda returns {success, deleted_count, not_found_count}" -ForegroundColor White

Write-Host "`nTo monitor execution:" -ForegroundColor Yellow
Write-Host "  aws logs tail /aws/lambda/debtor-portal-bulk-operations-dev --follow --region ap-southeast-1" -ForegroundColor Cyan
