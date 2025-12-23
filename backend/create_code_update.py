#!/usr/bin/env python3
import zipfile
from pathlib import Path

def create_code_only_package():
    """Create package with just updated Python files"""
    backend_dir = Path(__file__).parent
    output_package = backend_dir / 'lambda-code-update.zip'
    
    print(f"Creating code-only package: {output_package}")
    
    with zipfile.ZipFile(output_package, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add api directory files
        api_dir = backend_dir / 'api'
        for py_file in api_dir.glob('*.py'):
            arcname = f'api/{py_file.name}'
            print(f"Adding: {arcname}")
            zipf.write(py_file, arcname)
    
    size_kb = output_package.stat().st_size / 1024
    print(f"Package created: {output_package} ({size_kb:.2f} KB)")
    return output_package

if __name__ == '__main__':
    create_code_only_package()
