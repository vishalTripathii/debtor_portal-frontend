#!/bin/bash
echo "=========================================="
echo "  Deploying Bulk Operations Lambda"
echo "=========================================="
echo ""

# Navigate to backend directory
cd "$(dirname "$0")"

echo "[1/3] Deploying backend with new Lambda function..."
serverless deploy --stage dev --region ap-southeast-1

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Backend deployed successfully!"
    echo ""
    
    # Get the API Gateway endpoint
    ENDPOINT=$(serverless info --stage dev --region ap-southeast-1| grep "endpoint:" | awk '{print $2}')
    
    echo "API Endpoints:"
    echo "  - Bulk Delete: $ENDPOINT/bulk/delete-excel"
    echo "  - Bulk Update: $ENDPOINT/bulk/update-excel"
    echo ""
    
    echo "[2/3] Building frontend..."
    cd ..
    npm run build
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ Frontend built successfully!"
        echo ""
        
        echo "[3/3] Deploying frontend..."
        cd deploy
        ./deploy-frontend.sh
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "=========================================="
            echo "  ✓ DEPLOYMENT COMPLETE!"
            echo "=========================================="
            echo ""
            echo "Test bulk operations at:"
            echo "  https://d1hmzuewg6k3ss.cloudfront.net"
            echo ""
        else
            echo "✗ Frontend deployment failed"
            exit 1
        fi
    else
        echo "✗ Frontend build failed"
        exit 1
    fi
else
    echo "✗ Backend deployment failed"
    exit 1
fi
