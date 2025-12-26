# ============================================
# COMPLETE DEPLOYMENT SCRIPT
# Deploys Backend Lambda + Frontend
# ============================================

Write-Host "============================================" -ForegroundColor Magenta
Write-Host "   DEBTOR PORTAL - COMPLETE DEPLOYMENT" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta

# Step 1: Build Frontend
Write-Host "`n[1/4] Building Frontend..." -ForegroundColor Cyan
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Frontend build failed" -ForegroundColor Red
    exit 1
}
Write-Host "Frontend build complete!" -ForegroundColor Green

# Step 2: Deploy Backend Lambda
Write-Host "`n[2/4] Deploying Bulk Operations Lambda..." -ForegroundColor Cyan
Set-Location backend
.\deploy_bulk_ops_lambda.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Backend deployment failed" -ForegroundColor Red
    exit 1
}
Set-Location ..
Write-Host "Backend deployment complete!" -ForegroundColor Green

# Step 3: Deploy Frontend
Write-Host "`n[3/4] Deploying Frontend to S3..." -ForegroundColor Cyan
.\deploy_frontend.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Frontend deployment failed" -ForegroundColor Red
    exit 1
}
Write-Host "Frontend deployment complete!" -ForegroundColor Green

# Step 4: Summary
Write-Host "`n============================================" -ForegroundColor Magenta
Write-Host "   DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Magenta

Write-Host "`nAPI Endpoints:" -ForegroundColor Yellow
Write-Host "  Base URL: https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev/api" -ForegroundColor White
Write-Host "  Bulk Delete: https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev/bulk/delete-excel" -ForegroundColor White
Write-Host "  Bulk Update: https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev/bulk/update-excel" -ForegroundColor White

Write-Host "`nFrontend:" -ForegroundColor Yellow
Write-Host "  URL: https://d1hmzuewg6k3ss.cloudfront.net" -ForegroundColor White

Write-Host "`nTesting Instructions:" -ForegroundColor Yellow
Write-Host "  1. Wait 2-5 minutes for CloudFront cache to clear" -ForegroundColor White
Write-Host "  2. Login to https://d1hmzuewg6k3ss.cloudfront.net" -ForegroundColor White
Write-Host "  3. Select 'bulkDelete' from dropdown" -ForegroundColor White
Write-Host "  4. Upload Excel with Account Numbers" -ForegroundColor White
Write-Host "  5. Verify records are deleted from MongoDB" -ForegroundColor White
Write-Host "  6. Test 'bulkUpdate' with Excel containing Account Numbers + data" -ForegroundColor White

Write-Host "`n============================================" -ForegroundColor Magenta
