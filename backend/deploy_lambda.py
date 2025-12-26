import boto3
import sys

def deploy_lambda():
    try:
        # Create Lambda client
        lambda_client = boto3.client('lambda', region_name='ap-southeast-1')
        
        # Update function code
        print("Updating Lambda function...")
        response = lambda_client.update_function_code(
            FunctionName='debtor-portal-api-dev-api',
            S3Bucket='debtor-portal-api-dev-serverlessdeploymentbucket-rhgfzohvfm57',
            S3Key='lambda-final.zip'
        )
        
        print(f"✓ Lambda function updated successfully!")
        print(f"  Function: {response['FunctionName']}")
        print(f"  Size: {response['CodeSize'] / 1024 / 1024:.2f} MB")
        print(f"  State: {response['State']}")
        print(f"  Last Modified: {response['LastModified']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error deploying Lambda: {str(e)}")
        return False

if __name__ == "__main__":
    success = deploy_lambda()
    sys.exit(0 if success else 1)
