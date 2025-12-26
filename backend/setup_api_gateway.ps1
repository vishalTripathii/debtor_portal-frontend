# Setup API Gateway for Bulk Operations
$API_ID = "jxnu8wrip2"
$REGION = "ap-southeast-1"
$LAMBDA_ARN = "arn:aws:lambda:ap-southeast-1:805171368688:function:debtor-portal-bulk-operations-dev"

Write-Host "Setting up API Gateway endpoints..." -ForegroundColor Cyan

# Get root resource
$rootId = (aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/'].id" --output text)
Write-Host "Root resource ID: $rootId" -ForegroundColor Green

# Create /bulk resource
Write-Host "`nCreating /bulk resource..." -ForegroundColor Yellow
$bulkId = (aws apigateway create-resource --rest-api-id $API_ID --parent-id $rootId --path-part "bulk" --region $REGION --query 'id' --output text 2>$null)
if (!$bulkId) {
    $bulkId = (aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/bulk'].id" --output text)
}
Write-Host "/bulk resource ID: $bulkId" -ForegroundColor Green

# Create /bulk/delete-excel
Write-Host "`nCreating /bulk/delete-excel..." -ForegroundColor Yellow
$deleteId = (aws apigateway create-resource --rest-api-id $API_ID --parent-id $bulkId --path-part "delete-excel" --region $REGION --query 'id' --output text 2>$null)
if (!$deleteId) {
    $deleteId = (aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/bulk/delete-excel'].id" --output text)
}

# Setup POST method for delete-excel
aws apigateway put-method --rest-api-id $API_ID --resource-id $deleteId --http-method POST --authorization-type NONE --region $REGION 2>$null
aws apigateway put-integration --rest-api-id $API_ID --resource-id $deleteId --http-method POST --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" --region $REGION 2>$null

# Create /bulk/update-excel
Write-Host "Creating /bulk/update-excel..." -ForegroundColor Yellow
$updateId = (aws apigateway create-resource --rest-api-id $API_ID --parent-id $bulkId --path-part "update-excel" --region $REGION --query 'id' --output text 2>$null)
if (!$updateId) {
    $updateId = (aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/bulk/update-excel'].id" --output text)
}

# Setup POST method for update-excel
aws apigateway put-method --rest-api-id $API_ID --resource-id $updateId --http-method POST --authorization-type NONE --region $REGION 2>$null
aws apigateway put-integration --rest-api-id $API_ID --resource-id $updateId --http-method POST --type AWS_PROXY --integration-http-method POST --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" --region $REGION 2>$null

# Add Lambda permissions
Write-Host "`nAdding Lambda permissions..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
aws lambda add-permission --function-name debtor-portal-bulk-operations-dev --statement-id "apigateway-delete-$timestamp" --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${REGION}:805171368688:${API_ID}/*/*" --region $REGION 2>$null

# Deploy API
Write-Host "`nDeploying API..." -ForegroundColor Yellow
aws apigateway create-deployment --rest-api-id $API_ID --stage-name dev --region $REGION

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "API Gateway Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "`nEndpoints:" -ForegroundColor Yellow
Write-Host "  DELETE: https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/bulk/delete-excel" -ForegroundColor Cyan
Write-Host "  UPDATE: https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/bulk/update-excel" -ForegroundColor Cyan
