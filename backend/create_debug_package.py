#!/usr/bin/env python3
import os
import zipfile
from pathlib import Path

backend_dir = Path(__file__).parent
source = backend_dir / 'temp_deploy'
output = backend_dir / 'lambda-debug.zip'

print(f"Creating Lambda package: {output}")
file_count = 0

with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
    for root, dirs, files in os.walk(source):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, source)
            zipf.write(file_path, arcname)
            file_count += 1
            if file_count % 500 == 0:
                print(f"  Added {file_count} files...")

size_mb = os.path.getsize(output) / (1024 * 1024)
print(f"✓ Package created: {file_count} files, {size_mb:.2f} MB")
