# ============================================
# Deploy Frontend to S3 & CloudFront
# ============================================

$BUCKET_NAME = "power-amc-debtor-portal-frontend-dev"
$CLOUDFRONT_ID = "E1TBYQ8YV78RKE"
$REGION = "ap-southeast-1"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Deploying Frontend to S3 & CloudFront" -ForegroundColor Cyan
Write-Host "Bucket: $BUCKET_NAME" -ForegroundColor Cyan
Write-Host "CloudFront: $CLOUDFRONT_ID" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Check if dist folder exists
if (-not (Test-Path "dist")) {
    Write-Host "`nERROR: dist folder not found!" -ForegroundColor Red
    Write-Host "Please run 'npm run build' first" -ForegroundColor Yellow
    exit 1
}

# Upload to S3
Write-Host "`nUploading files to S3..." -ForegroundColor Yellow
aws s3 sync dist/ s3://$BUCKET_NAME --delete --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to upload to S3" -ForegroundColor Red
    exit 1
}

Write-Host "Files uploaded successfully!" -ForegroundColor Green

# Invalidate CloudFront cache
Write-Host "`nInvalidating CloudFront cache..." -ForegroundColor Yellow
$invalidation = aws cloudfront create-invalidation `
    --distribution-id $CLOUDFRONT_ID `
    --paths "/*" `
    --query 'Invalidation.Id' `
    --output text

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Failed to create CloudFront invalidation" -ForegroundColor Yellow
    Write-Host "You may need to manually invalidate the cache" -ForegroundColor Yellow
} else {
    Write-Host "CloudFront invalidation created: $invalidation" -ForegroundColor Green
    Write-Host "Cache will be cleared in 1-5 minutes" -ForegroundColor Yellow
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "FRONTEND DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "`nFrontend URL: https://d1hmzuewg6k3ss.cloudfront.net" -ForegroundColor Cyan
Write-Host "`nWait 2-5 minutes for CloudFront cache to clear, then test!" -ForegroundColor Yellow
