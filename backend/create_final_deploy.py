#!/usr/bin/env python3
import os
import zipfile
from pathlib import Path
import shutil

backend_dir = Path(__file__).parent

# Step 1: Extract lambda-corrected.zip
print("Step 1: Extracting lambda-corrected.zip...")
corrected_zip = backend_dir / 'lambda-corrected.zip'
temp_dir = backend_dir / 'temp_final_deploy'

if temp_dir.exists():
    shutil.rmtree(temp_dir)

with zipfile.ZipFile(corrected_zip, 'r') as zip_ref:
    zip_ref.extractall(temp_dir)
print("  ✓ Extracted")

# Step 2: Update lambda_handler.py
print("Step 2: Updating lambda_handler.py...")
shutil.copy2(backend_dir / 'lambda_handler.py', temp_dir / 'lambda_handler.py')
print("  ✓ Updated lambda_handler.py")

# Step 3: Create final package
print("Step 3: Creating final deployment package...")
output_zip = backend_dir / 'lambda-final-deploy.zip'
file_count = 0

with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, temp_dir)
            zipf.write(file_path, arcname)
            file_count += 1
            if file_count % 1000 == 0:
                print(f"  Added {file_count} files...")

size_mb = os.path.getsize(output_zip) / (1024 * 1024)
print(f"\n✓ Package created: {output_zip}")
print(f"  Files: {file_count}")
print(f"  Size: {size_mb:.2f} MB")

# Cleanup
shutil.rmtree(temp_dir)
print("  ✓ Cleaned up temp directory")
