#!/usr/bin/env python3
import os
import zipfile
from pathlib import Path

def zip_directory(source_dir, output_file):
    """Zip a directory with all contents"""
    print(f"Creating zip from: {source_dir}")
    print(f"Output file: {output_file}")
    
    file_count = 0
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
                file_count += 1
                if file_count % 100 == 0:
                    print(f"Added {file_count} files...")
    
    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\nCompleted! Added {file_count} files")
    print(f"Package size: {size_mb:.2f} MB")

if __name__ == '__main__':
    backend_dir = Path(__file__).parent
    source = backend_dir / 'temp_working'
    output = backend_dir / 'lambda-corrected.zip'
    
    zip_directory(source, output)
