#!/usr/bin/env python3
import os
import zipfile
from pathlib import Path

backend_dir = Path(__file__).parent
source = backend_dir / 'temp_safe_update'
output = backend_dir / 'lambda-safe-deploy.zip'

print(f"Creating safe deployment package: {output}")
file_count = 0

with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
    for root, dirs, files in os.walk(source):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, source)
            zipf.write(file_path, arcname)
            file_count += 1
            if file_count % 1000 == 0:
                print(f"  {file_count} files...")

size_mb = os.path.getsize(output) / (1024 * 1024)
print(f"✓ Complete: {file_count} files, {size_mb:.2f} MB")
