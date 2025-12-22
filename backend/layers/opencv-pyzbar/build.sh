#!/bin/bash
# Build OpenCV + pyzbar Lambda layer using local pip

rm -rf python opencv-pyzbar-layer.zip
mkdir -p python

# Install packages locally (compatible with Lambda)
pip3 install -r requirements.txt -t python/ --no-cache-dir

# Clean up unnecessary files
find python -name '*.pyc' -delete
find python -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find python -name 'test*' -type d -exec rm -rf {} + 2>/dev/null || true
find python -name '*.dist-info' -type d -exec rm -rf {} + 2>/dev/null || true

# Check if packages were installed
if [ -d "python" ]; then
    echo "Packages installed:"
    ls -la python/ | head -10
    echo "Layer size before compression:"
    du -sh python/
else
    echo "ERROR: No packages installed"
    exit 1
fi

# Create layer zip
zip -r opencv-pyzbar-layer.zip python/

echo "Layer created: opencv-pyzbar-layer.zip ($(du -h opencv-pyzbar-layer.zip | cut -f1))"