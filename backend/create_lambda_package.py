#!/usr/bin/env python3
import os
import zipfile
from pathlib import Path

def create_lambda_package():
    """Create Lambda deployment package"""
    backend_dir = Path(__file__).parent
    
    # Source: base package from .serverless
    base_package = backend_dir / '.serverless' / 'debtor-portal-api.zip'
    
    if not base_package.exists():
        print(f"Base package not found: {base_package}")
        return
    
    # Temp extraction dir
    temp_dir = backend_dir / 'temp_package'
    temp_dir.mkdir(exist_ok=True)
    
    print(f"Extracting base package: {base_package}")
    with zipfile.ZipFile(base_package, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    print("Copying updated files...")
    # Copy updated api files
    import shutil
    shutil.copy2(backend_dir / 'api' / 'views.py', temp_dir / 'api' / 'views.py')
    shutil.copy2(backend_dir / 'api' / 'urls.py', temp_dir / 'api' / 'urls.py')
    
    # Create new package
    output_package = backend_dir / 'lambda-fixed.zip'
    print(f"Creating Lambda package: {output_package}")
    
    with zipfile.ZipFile(output_package, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)
    
    # Get size
    size_mb = output_package.stat().st_size / (1024 * 1024)
    print(f"Package created: {output_package} ({size_mb:.2f} MB)")
    
    # Cleanup
    print("Cleaning up temp directory...")
    shutil.rmtree(temp_dir)
    
    return output_package

if __name__ == '__main__':
    create_lambda_package()
