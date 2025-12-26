# ============================================
# Deploy Bulk Operations Lambda Function
# ============================================

$FUNCTION_NAME = "debtor-portal-bulk-operations-dev"
$REGION = "ap-southeast-1"
$ROLE_ARN = "arn:aws:iam::211125310334:role/debtor-portal-api-dev-ap-southeast-1-lambdaRole"
$ZIP_FILE = "bulk_operations_lambda.zip"
$MONGODB_URI = $env:MONGODB_URI

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Deploying Bulk Operations Lambda" -ForegroundColor Cyan
Write-Host "Function: $FUNCTION_NAME" -ForegroundColor Cyan
Write-Host "Region: $REGION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Check if Lambda function exists
Write-Host "`nChecking if function exists..." -ForegroundColor Yellow
$functionExists = $false
try {
    aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>$null
    $functionExists = $LASTEXITCODE -eq 0
} catch {
    $functionExists = $false
}

if ($functionExists) {
    Write-Host "Function exists. Updating code..." -ForegroundColor Green
    
    # Update function code
    aws lambda update-function-code `
        --function-name $FUNCTION_NAME `
        --zip-file fileb://$ZIP_FILE `
        --region $REGION
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to update function code" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`nWaiting for update to complete..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Update function configuration
    Write-Host "Updating function configuration..." -ForegroundColor Yellow
    $envVars = "{MONGODB_URI=`"$MONGODB_URI`"}"
    aws lambda update-function-configuration `
        --function-name $FUNCTION_NAME `
        --runtime python3.12 `
        --handler bulk_operations_handler.handler `
        --timeout 900 `
        --memory-size 10240 `
        --environment "Variables=$envVars" `
        --layers "arn:aws:lambda:ap-southeast-1:336392948345:layer:AWSSDKPandas-Python312:13" `
        --region $REGION
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to update function configuration" -ForegroundColor Red
        exit 1
    }
    
} else {
    Write-Host "Function does not exist. Creating new function..." -ForegroundColor Green
    
    # Create new function
    $envVars = "{MONGODB_URI=`"$MONGODB_URI`"}"
    aws lambda create-function `
        --function-name $FUNCTION_NAME `
        --runtime python3.12 `
        --role $ROLE_ARN `
        --handler bulk_operations_handler.handler `
        --zip-file fileb://$ZIP_FILE `
        --timeout 900 `
        --memory-size 10240 `
        --environment "Variables=$envVars" `
        --layers "arn:aws:lambda:ap-southeast-1:336392948345:layer:AWSSDKPandas-Python312:13" `
        --region $REGION
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create function" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "Lambda function deployed successfully!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

# Get API Gateway ID
Write-Host "`nGetting API Gateway information..." -ForegroundColor Yellow
$API_ID = "jxnu8wrip2"
$ROOT_RESOURCE_ID = (aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/'].id" --output text)

if (-not $ROOT_RESOURCE_ID) {
    Write-Host "ERROR: Could not get root resource ID" -ForegroundColor Red
    exit 1
}

Write-Host "API Gateway ID: $API_ID" -ForegroundColor Green
Write-Host "Root Resource ID: $ROOT_RESOURCE_ID" -ForegroundColor Green

# Check if /bulk resource exists
Write-Host "`nChecking for /bulk resource..." -ForegroundColor Yellow
$BULK_RESOURCE_ID = (aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/bulk'].id" --output text)

if (-not $BULK_RESOURCE_ID) {
    Write-Host "Creating /bulk resource..." -ForegroundColor Yellow
    $BULK_RESOURCE_ID = (aws apigateway create-resource `
        --rest-api-id $API_ID `
        --parent-id $ROOT_RESOURCE_ID `
        --path-part "bulk" `
        --region $REGION `
        --query 'id' --output text)
    
    if (-not $BULK_RESOURCE_ID) {
        Write-Host "ERROR: Failed to create /bulk resource" -ForegroundColor Red
        exit 1
    }
    Write-Host "Created /bulk resource: $BULK_RESOURCE_ID" -ForegroundColor Green
} else {
    Write-Host "/bulk resource already exists: $BULK_RESOURCE_ID" -ForegroundColor Green
}

# Function to create endpoint
function Create-BulkEndpoint {
    param(
        [string]$PathPart,
        [string]$ParentId
    )
    
    Write-Host "`nSetting up /$PathPart endpoint..." -ForegroundColor Yellow
    
    # Check if resource exists
    $resourceId = (aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/bulk/$PathPart'].id" --output text)
    
    if (-not $resourceId) {
        Write-Host "Creating /bulk/$PathPart resource..." -ForegroundColor Yellow
        $resourceId = (aws apigateway create-resource `
            --rest-api-id $API_ID `
            --parent-id $ParentId `
            --path-part $PathPart `
            --region $REGION `
            --query 'id' --output text)
        
        if (-not $resourceId) {
            Write-Host "ERROR: Failed to create resource" -ForegroundColor Red
            return $false
        }
        Write-Host "Created resource: $resourceId" -ForegroundColor Green
    } else {
        Write-Host "Resource already exists: $resourceId" -ForegroundColor Green
    }
    
    # Create OPTIONS method for CORS
    Write-Host "Setting up OPTIONS method..." -ForegroundColor Yellow
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --authorization-type NONE `
        --region $REGION 2>$null
    
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --type MOCK `
        --request-templates '{"application/json":"{\"statusCode\": 200}"}' `
        --region $REGION 2>$null
    
    aws apigateway put-method-response `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" `
        --region $REGION 2>$null
    
    aws apigateway put-integration-response `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method OPTIONS `
        --status-code 200 `
        --response-parameters '{\"method.response.header.Access-Control-Allow-Headers\":\"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'\",\"method.response.header.Access-Control-Allow-Methods\":\"'"'"'POST,OPTIONS'"'"'\",\"method.response.header.Access-Control-Allow-Origin\":\"'"'"'*'"'"'\"}' `
        --region $REGION 2>$null
    
    # Create POST method
    Write-Host "Setting up POST method..." -ForegroundColor Yellow
    aws apigateway put-method `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method POST `
        --authorization-type NONE `
        --region $REGION 2>$null
    
    # Create Lambda integration
    $LAMBDA_ARN = "arn:aws:lambda:${REGION}:211125310334:function:${FUNCTION_NAME}"
    $SOURCE_ARN = "arn:aws:execute-api:${REGION}:211125310334:${API_ID}/*/*"
    
    aws apigateway put-integration `
        --rest-api-id $API_ID `
        --resource-id $resourceId `
        --http-method POST `
        --type AWS_PROXY `
        --integration-http-method POST `
        --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" `
        --region $REGION 2>$null
    
    # Add Lambda permission
    Write-Host "Adding Lambda invoke permission..." -ForegroundColor Yellow
    aws lambda add-permission `
        --function-name $FUNCTION_NAME `
        --statement-id "apigateway-bulk-${PathPart}-$(Get-Date -Format 'yyyyMMddHHmmss')" `
        --action lambda:InvokeFunction `
        --principal apigateway.amazonaws.com `
        --source-arn $SOURCE_ARN `
        --region $REGION 2>$null
    
    Write-Host "Endpoint /bulk/$PathPart configured successfully!" -ForegroundColor Green
    return $true
}

# Create both endpoints
Create-BulkEndpoint -PathPart "delete-excel" -ParentId $BULK_RESOURCE_ID
Create-BulkEndpoint -PathPart "update-excel" -ParentId $BULK_RESOURCE_ID

# Deploy API
Write-Host "`nDeploying API Gateway changes..." -ForegroundColor Yellow
aws apigateway create-deployment `
    --rest-api-id $API_ID `
    --stage-name dev `
    --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to deploy API Gateway" -ForegroundColor Red
    exit 1
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "`nAPI Endpoints:" -ForegroundColor Yellow
Write-Host "  DELETE: https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/bulk/delete-excel" -ForegroundColor Cyan
Write-Host "  UPDATE: https://${API_ID}.execute-api.${REGION}.amazonaws.com/dev/bulk/update-excel" -ForegroundColor Cyan
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Test bulk delete with Excel file" -ForegroundColor White
Write-Host "  2. Test bulk update with Excel file" -ForegroundColor White
Write-Host "  3. Deploy frontend if not already done" -ForegroundColor White
