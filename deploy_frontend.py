import boto3
import os
from pathlib import Path
import mimetypes

def deploy_frontend():
    try:
        # Create S3 client
        s3_client = boto3.client('s3', region_name='ap-southeast-1')
        bucket_name = 'power-amc-debtor-portal-frontend-dev'
        dist_folder = 'dist'
        
        print(f"Deploying frontend to S3 bucket: {bucket_name}")
        
        # Upload all files from dist folder
        uploaded_count = 0
        for file_path in Path(dist_folder).rglob('*'):
            if file_path.is_file():
                # Get relative path
                relative_path = file_path.relative_to(dist_folder)
                s3_key = str(relative_path).replace('\\', '/')
                
                # Determine content type
                content_type, _ = mimetypes.guess_type(str(file_path))
                if not content_type:
                    content_type = 'application/octet-stream'
                
                # Upload file
                extra_args = {'ContentType': content_type}
                
                # Set cache control for assets
                if '.js' in s3_key or '.css' in s3_key:
                    extra_args['CacheControl'] = 'public, max-age=31536000'
                elif s3_key == 'index.html':
                    extra_args['CacheControl'] = 'no-cache'
                
                print(f"  Uploading: {s3_key}")
                s3_client.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key,
                    ExtraArgs=extra_args
                )
                uploaded_count += 1
        
        print(f"\n✓ Frontend deployed successfully!")
        print(f"  Files uploaded: {uploaded_count}")
        print(f"  CloudFront URL: https://d1hmzuewg6k3ss.cloudfront.net")
        
        return True
        
    except Exception as e:
        print(f"✗ Error deploying frontend: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    success = deploy_frontend()
    sys.exit(0 if success else 1)
