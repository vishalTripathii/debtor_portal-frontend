"""
Storage Utilities for Debtor Portal

This module provides storage path helpers and migration utilities
for transitioning from filesystem to S3 storage.

The module uses the aws_storage module which automatically switches
between local filesystem (development) and S3 (production).
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, BinaryIO
from django.conf import settings

# Import the storage module
from api.aws_storage import storage, get_storage

# Storage key prefixes (equivalent to directories in S3)
UPLOADS_PREFIX = 'uploads'
IMAGES_PREFIX = 'debtor_images'
RECEIPTS_PREFIX = 'payment_receipts'
PDF_STAGING_PREFIX = 'pdf_staging'


def get_upload_key(filename: str, upload_id: Optional[str] = None) -> str:
    """
    Generate storage key for uploaded Excel/CSV files.

    Args:
        filename: Original filename
        upload_id: Optional upload ID for organization

    Returns:
        Storage key like 'uploads/UPL-20240101-001/data.xlsx'
    """
    if upload_id:
        return f"{UPLOADS_PREFIX}/{upload_id}/{filename}"
    return f"{UPLOADS_PREFIX}/{filename}"


def get_image_key(account_number: str, extension: str = 'png') -> str:
    """
    Generate storage key for debtor/account images.

    Args:
        account_number: Account number
        extension: File extension (default: png)

    Returns:
        Storage key like 'debtor_images/123456789.png'
    """
    return f"{IMAGES_PREFIX}/{account_number}.{extension}"


def get_receipt_key(filename: str) -> str:
    """
    Generate storage key for payment receipts.

    Args:
        filename: Receipt filename

    Returns:
        Storage key like 'payment_receipts/1234567890_receipt.jpg'
    """
    return f"{RECEIPTS_PREFIX}/{filename}"


def get_pdf_staging_key(job_id: str, filename: str) -> str:
    """
    Generate storage key for PDF staging files.

    Args:
        job_id: Processing job ID
        filename: PDF filename

    Returns:
        Storage key like 'pdf_staging/job-abc123/file.pdf'
    """
    return f"{PDF_STAGING_PREFIX}/{job_id}/{filename}"


def generate_receipt_filename(original_filename: str) -> str:
    """
    Generate a unique filename for a payment receipt.

    Args:
        original_filename: Original uploaded filename

    Returns:
        Unique filename with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    ext = os.path.splitext(original_filename)[1] if original_filename else '.jpg'
    return f"receipt_{timestamp}{ext}"


def generate_upload_id() -> str:
    """
    Generate a unique upload ID.

    Returns:
        Upload ID like 'UPL-20240101-001'
    """
    from api.database import get_upload_history_collection

    today = datetime.now().strftime('%Y%m%d')
    prefix = f"UPL-{today}-"

    # Find the highest number for today
    upload_history = get_upload_history_collection()
    today_uploads = list(upload_history.find(
        {'upload_id': {'$regex': f'^{prefix}'}},
        {'upload_id': 1}
    ).sort('upload_id', -1).limit(1))

    if today_uploads:
        last_num = int(today_uploads[0]['upload_id'].split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    return f"{prefix}{new_num:03d}"


# ============================================
# FILE UPLOAD HELPERS
# ============================================

def save_uploaded_file(
    file_obj: Union[BinaryIO, bytes],
    key: str,
    content_type: Optional[str] = None
) -> dict:
    """
    Save an uploaded file to storage.

    Args:
        file_obj: File object or bytes
        key: Storage key
        content_type: MIME type

    Returns:
        Dict with 'key', 'url', 'size'
    """
    return storage.upload_file(file_obj, key, content_type)


def save_receipt(file_obj, original_filename: str) -> dict:
    """
    Save a payment receipt.

    Args:
        file_obj: Uploaded file
        original_filename: Original filename

    Returns:
        Dict with 'key', 'url', 'filename'
    """
    filename = generate_receipt_filename(original_filename)
    key = get_receipt_key(filename)
    result = storage.upload_file(file_obj, key)
    result['filename'] = filename
    return result


def save_debtor_image(account_number: str, image_data: bytes, extension: str = 'png') -> dict:
    """
    Save a debtor image (QR code, etc).

    Args:
        account_number: Account number
        image_data: Image data as bytes
        extension: File extension

    Returns:
        Dict with 'key', 'url'
    """
    key = get_image_key(account_number, extension)
    return storage.upload_file(image_data, key, f'image/{extension}')


def save_pdf_to_staging(job_id: str, filename: str, file_obj) -> dict:
    """
    Save a PDF to staging for processing.

    Args:
        job_id: Processing job ID
        filename: PDF filename
        file_obj: File object

    Returns:
        Dict with 'key', 'url'
    """
    key = get_pdf_staging_key(job_id, filename)
    return storage.upload_file(file_obj, key, 'application/pdf')


# ============================================
# FILE RETRIEVAL HELPERS
# ============================================

def get_file(key: str) -> bytes:
    """
    Get file content by key.

    Args:
        key: Storage key

    Returns:
        File content as bytes
    """
    return storage.download_file(key)


def get_receipt(filename: str) -> bytes:
    """
    Get a payment receipt.

    Args:
        filename: Receipt filename

    Returns:
        Receipt content as bytes
    """
    key = get_receipt_key(filename)
    return storage.download_file(key)


def get_debtor_image(account_number: str, extension: str = 'png') -> bytes:
    """
    Get a debtor image.

    Args:
        account_number: Account number
        extension: File extension (ignored if debtor_images record exists)

    Returns:
        Image content as bytes
    """
    # First check debtor_images collection for the correct storage key
    try:
        from api.database import get_debtor_images_collection
        debtor_images = get_debtor_images_collection()
        image_record = debtor_images.find_one({'account_number': account_number})
        
        if image_record and image_record.get('storage_key'):
            # Use the exact storage key from the database
            return storage.download_file(image_record['storage_key'])
    except Exception as e:
        # If database lookup fails, fall back to filename pattern
        pass
    
    # Fallback: try the old filename pattern approach
    key = get_image_key(account_number, extension)
    return storage.download_file(key)


def get_presigned_receipt_url(filename: str, expiration: int = 3600) -> str:
    """
    Get a presigned URL for a receipt.

    Args:
        filename: Receipt filename
        expiration: URL expiration in seconds

    Returns:
        Presigned URL
    """
    key = get_receipt_key(filename)
    return storage.get_presigned_url(key, expiration)


def get_presigned_image_url(account_number: str, expiration: int = 3600) -> str:
    """
    Get a presigned URL for a debtor image.

    Args:
        account_number: Account number
        expiration: URL expiration in seconds

    Returns:
        Presigned URL
    """
    key = get_image_key(account_number)
    return storage.get_presigned_url(key, expiration)


# ============================================
# FILE EXISTENCE & DELETION
# ============================================

def file_exists(key: str) -> bool:
    """Check if a file exists."""
    return storage.file_exists(key)


def receipt_exists(filename: str) -> bool:
    """Check if a receipt exists."""
    key = get_receipt_key(filename)
    return storage.file_exists(key)


def debtor_image_exists(account_number: str, extension: str = 'png') -> bool:
    """Check if a debtor image exists."""
    key = get_image_key(account_number, extension)
    return storage.file_exists(key)


def delete_file(key: str) -> bool:
    """Delete a file by key."""
    return storage.delete_file(key)


def delete_receipt(filename: str) -> bool:
    """Delete a receipt."""
    key = get_receipt_key(filename)
    return storage.delete_file(key)


def delete_debtor_image(account_number: str, extension: str = 'png') -> bool:
    """Delete a debtor image."""
    key = get_image_key(account_number, extension)
    return storage.delete_file(key)


def delete_staging_folder(job_id: str) -> dict:
    """Delete all files in a staging folder."""
    prefix = f"{PDF_STAGING_PREFIX}/{job_id}/"
    return storage.delete_folder(prefix)


# ============================================
# LISTING FILES
# ============================================

def list_staging_files(job_id: str) -> list:
    """
    List all files in a staging folder.

    Args:
        job_id: Processing job ID

    Returns:
        List of file info dicts
    """
    prefix = f"{PDF_STAGING_PREFIX}/{job_id}/"
    return storage.list_files(prefix)


def list_receipts(max_keys: int = 1000) -> list:
    """List all receipts."""
    return storage.list_files(RECEIPTS_PREFIX, max_keys)


def list_debtor_images(max_keys: int = 1000) -> list:
    """List all debtor images."""
    return storage.list_files(IMAGES_PREFIX, max_keys)


# ============================================
# BACKWARD COMPATIBILITY
# ============================================

# For backward compatibility during migration, these paths can still be used
# but operations should go through the storage module
MEDIA_DIR = Path(settings.BASE_DIR).parent / 'media'
IMAGES_DIR = MEDIA_DIR / 'debtor_images'
UPLOADS_DIR = MEDIA_DIR / 'uploads'
RECEIPTS_DIR = MEDIA_DIR / 'payment_receipts'
PDF_STAGING_DIR = MEDIA_DIR / 'pdf_staging'


def ensure_local_dirs():
    """Create local directories for development mode."""
    if os.environ.get('USE_S3_STORAGE', 'False').lower() != 'true':
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
        PDF_STAGING_DIR.mkdir(parents=True, exist_ok=True)


# Ensure directories exist in local mode
ensure_local_dirs()
