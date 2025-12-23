"""
AWS S3 Storage Utility Module

This module provides a unified interface for file storage that works
with both local filesystem (for development) and AWS S3 (for production).

Usage:
    from api.aws_storage import storage

    # Upload a file
    storage.upload_file(file_obj, 'uploads/myfile.xlsx')

    # Download a file
    content = storage.download_file('uploads/myfile.xlsx')

    # Get a presigned URL for direct download
    url = storage.get_presigned_url('uploads/myfile.xlsx')

    # Check if file exists
    exists = storage.file_exists('uploads/myfile.xlsx')

    # Delete a file
    storage.delete_file('uploads/myfile.xlsx')
"""

import os
import io
import logging
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, BinaryIO, List, Dict, Any

# Try to import boto3, fall back to local storage if not available
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    ClientError = Exception

logger = logging.getLogger(__name__)


class LocalStorage:
    """
    Local filesystem storage for development.
    Mimics S3 interface for seamless switching.
    """

    def __init__(self, base_path: str = None):
        if base_path is None:
            # Default to media directory relative to backend
            base_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'media'
            )
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorage initialized with base path: {self.base_path}")

    def _get_full_path(self, key: str) -> Path:
        """Get the full filesystem path for a key."""
        return self.base_path / key

    def upload_file(
        self,
        file_obj: Union[BinaryIO, bytes, str],
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to local storage.

        Args:
            file_obj: File object, bytes, or string path to upload
            key: Storage key (path within storage)
            content_type: MIME type (optional, auto-detected if not provided)
            metadata: Additional metadata (ignored in local storage)

        Returns:
            Dict with upload info including 'key' and 'url'
        """
        full_path = self._get_full_path(key)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(file_obj, str):
            # It's a file path, copy the file
            import shutil
            shutil.copy2(file_obj, full_path)
        elif isinstance(file_obj, bytes):
            # It's raw bytes
            with open(full_path, 'wb') as f:
                f.write(file_obj)
        else:
            # It's a file-like object
            with open(full_path, 'wb') as f:
                # Handle Django's UploadedFile
                if hasattr(file_obj, 'read'):
                    content = file_obj.read()
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    f.write(content)
                else:
                    f.write(file_obj)

        logger.debug(f"LocalStorage: Uploaded file to {key}")
        return {
            'key': key,
            'url': f'/media/{key}',
            'size': full_path.stat().st_size
        }

    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Alias for upload_file for boto3 compatibility."""
        return self.upload_file(file_obj, key, content_type, metadata)

    def download_file(self, key: str) -> bytes:
        """
        Download a file from local storage.

        Args:
            key: Storage key

        Returns:
            File contents as bytes
        """
        full_path = self._get_full_path(key)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        with open(full_path, 'rb') as f:
            return f.read()

    def download_fileobj(self, key: str, file_obj: BinaryIO) -> None:
        """
        Download a file to a file object.

        Args:
            key: Storage key
            file_obj: File object to write to
        """
        content = self.download_file(key)
        file_obj.write(content)

    def get_file_stream(self, key: str) -> BinaryIO:
        """
        Get a file stream for reading.

        Args:
            key: Storage key

        Returns:
            BytesIO object with file contents
        """
        content = self.download_file(key)
        return io.BytesIO(content)

    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists.

        Args:
            key: Storage key

        Returns:
            True if file exists, False otherwise
        """
        return self._get_full_path(key).exists()

    def delete_file(self, key: str) -> bool:
        """
        Delete a file from storage.

        Args:
            key: Storage key

        Returns:
            True if deleted, False if not found
        """
        full_path = self._get_full_path(key)
        if full_path.exists():
            full_path.unlink()
            logger.debug(f"LocalStorage: Deleted file {key}")
            return True
        return False

    def delete_files(self, keys: List[str]) -> Dict[str, Any]:
        """
        Delete multiple files.

        Args:
            keys: List of storage keys

        Returns:
            Dict with 'deleted' count and 'errors' list
        """
        deleted = 0
        errors = []
        for key in keys:
            try:
                if self.delete_file(key):
                    deleted += 1
            except Exception as e:
                errors.append({'key': key, 'error': str(e)})
        return {'deleted': deleted, 'errors': errors}

    def delete_folder(self, prefix: str) -> Dict[str, Any]:
        """
        Delete all files with a given prefix (folder).

        Args:
            prefix: Folder prefix

        Returns:
            Dict with 'deleted' count
        """
        import shutil
        full_path = self._get_full_path(prefix)
        if full_path.exists() and full_path.is_dir():
            shutil.rmtree(full_path)
            logger.debug(f"LocalStorage: Deleted folder {prefix}")
            return {'deleted': True}
        return {'deleted': False}

    def list_files(self, prefix: str = '', max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        List files with a given prefix.

        Args:
            prefix: Key prefix to filter by
            max_keys: Maximum number of keys to return

        Returns:
            List of dicts with 'key', 'size', 'last_modified'
        """
        base = self._get_full_path(prefix)
        files = []

        if not base.exists():
            return files

        if base.is_file():
            return [{
                'key': prefix,
                'size': base.stat().st_size,
                'last_modified': datetime.fromtimestamp(base.stat().st_mtime)
            }]

        for path in base.rglob('*'):
            if path.is_file() and len(files) < max_keys:
                rel_path = path.relative_to(self.base_path)
                files.append({
                    'key': str(rel_path).replace('\\', '/'),
                    'size': path.stat().st_size,
                    'last_modified': datetime.fromtimestamp(path.stat().st_mtime)
                })

        return files

    def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        response_content_type: Optional[str] = None
    ) -> str:
        """
        Get a URL for the file (local path in development).

        Args:
            key: Storage key
            expiration: URL expiration in seconds (ignored in local)
            response_content_type: Content type for response (ignored in local)

        Returns:
            URL string (local path)
        """
        return f'/media/{key}'

    def get_file_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata.

        Args:
            key: Storage key

        Returns:
            Dict with file info or None if not found
        """
        full_path = self._get_full_path(key)
        if not full_path.exists():
            return None

        stat = full_path.stat()
        content_type, _ = mimetypes.guess_type(str(full_path))

        return {
            'key': key,
            'size': stat.st_size,
            'last_modified': datetime.fromtimestamp(stat.st_mtime),
            'content_type': content_type or 'application/octet-stream'
        }


class S3Storage:
    """
    AWS S3 storage for production.
    """

    def __init__(
        self,
        bucket_name: str = None,
        region: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None
    ):
        self.bucket_name = bucket_name or os.environ.get('S3_BUCKET_NAME')
        self.region = region or os.environ.get('S3_REGION', 'ap-southeast-1')

        if not self.bucket_name:
            raise ValueError("S3 bucket name is required")

        # Create S3 client
        client_kwargs = {'region_name': self.region}

        if aws_access_key_id and aws_secret_access_key:
            client_kwargs['aws_access_key_id'] = aws_access_key_id
            client_kwargs['aws_secret_access_key'] = aws_secret_access_key

        self.s3 = boto3.client('s3', **client_kwargs)
        self.s3_resource = boto3.resource('s3', **client_kwargs)
        self.bucket = self.s3_resource.Bucket(self.bucket_name)

        logger.info(f"S3Storage initialized with bucket: {self.bucket_name}")

    def upload_file(
        self,
        file_obj: Union[BinaryIO, bytes, str],
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to S3.

        Args:
            file_obj: File object, bytes, or string path to upload
            key: S3 key (path within bucket)
            content_type: MIME type (auto-detected if not provided)
            metadata: Additional metadata

        Returns:
            Dict with upload info including 'key' and 'url'
        """
        extra_args = {}

        # Auto-detect content type
        if content_type is None:
            content_type, _ = mimetypes.guess_type(key)
            content_type = content_type or 'application/octet-stream'

        extra_args['ContentType'] = content_type

        if metadata:
            extra_args['Metadata'] = metadata

        if isinstance(file_obj, str):
            # It's a file path
            self.s3.upload_file(file_obj, self.bucket_name, key, ExtraArgs=extra_args)
        elif isinstance(file_obj, bytes):
            # It's raw bytes
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_obj,
                **extra_args
            )
        else:
            # It's a file-like object
            # Reset position if possible
            if hasattr(file_obj, 'seek'):
                try:
                    file_obj.seek(0)
                except:
                    pass

            # Read content if it's a Django UploadedFile
            if hasattr(file_obj, 'read'):
                content = file_obj.read()
                if isinstance(content, str):
                    content = content.encode('utf-8')
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=content,
                    **extra_args
                )
            else:
                self.s3.upload_fileobj(file_obj, self.bucket_name, key, ExtraArgs=extra_args)

        logger.debug(f"S3Storage: Uploaded file to {key}")

        # Get file size
        head = self.s3.head_object(Bucket=self.bucket_name, Key=key)

        return {
            'key': key,
            'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}",
            'size': head.get('ContentLength', 0)
        }

    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Alias for upload_file for boto3 compatibility."""
        return self.upload_file(file_obj, key, content_type, metadata)

    def download_file(self, key: str) -> bytes:
        """
        Download a file from S3.

        Args:
            key: S3 key

        Returns:
            File contents as bytes
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {key}")
            raise

    def download_fileobj(self, key: str, file_obj: BinaryIO) -> None:
        """
        Download a file to a file object.

        Args:
            key: S3 key
            file_obj: File object to write to
        """
        self.s3.download_fileobj(self.bucket_name, key, file_obj)

    def get_file_stream(self, key: str) -> BinaryIO:
        """
        Get a streaming body for reading.

        Args:
            key: S3 key

        Returns:
            Streaming body
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body']
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {key}")
            raise

    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in S3.

        Args:
            key: S3 key

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            key: S3 key

        Returns:
            True (S3 delete is idempotent)
        """
        self.s3.delete_object(Bucket=self.bucket_name, Key=key)
        logger.debug(f"S3Storage: Deleted file {key}")
        return True

    def delete_files(self, keys: List[str]) -> Dict[str, Any]:
        """
        Delete multiple files from S3.

        Args:
            keys: List of S3 keys

        Returns:
            Dict with 'deleted' count and 'errors' list
        """
        if not keys:
            return {'deleted': 0, 'errors': []}

        # S3 batch delete (max 1000 keys per request)
        objects = [{'Key': key} for key in keys[:1000]]
        response = self.s3.delete_objects(
            Bucket=self.bucket_name,
            Delete={'Objects': objects}
        )

        deleted = len(response.get('Deleted', []))
        errors = response.get('Errors', [])

        logger.debug(f"S3Storage: Batch deleted {deleted} files")
        return {'deleted': deleted, 'errors': errors}

    def delete_folder(self, prefix: str) -> Dict[str, Any]:
        """
        Delete all files with a given prefix.

        Args:
            prefix: Key prefix (folder)

        Returns:
            Dict with 'deleted' count
        """
        # List all objects with prefix
        objects_to_delete = []
        paginator = self.s3.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            for obj in page.get('Contents', []):
                objects_to_delete.append({'Key': obj['Key']})

        if not objects_to_delete:
            return {'deleted': 0}

        # Delete in batches of 1000
        total_deleted = 0
        for i in range(0, len(objects_to_delete), 1000):
            batch = objects_to_delete[i:i + 1000]
            response = self.s3.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': batch}
            )
            total_deleted += len(response.get('Deleted', []))

        logger.debug(f"S3Storage: Deleted folder {prefix} ({total_deleted} files)")
        return {'deleted': total_deleted}

    def list_files(self, prefix: str = '', max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        List files with a given prefix.

        Args:
            prefix: Key prefix to filter by
            max_keys: Maximum number of keys to return

        Returns:
            List of dicts with 'key', 'size', 'last_modified'
        """
        files = []
        paginator = self.s3.get_paginator('list_objects_v2')

        for page in paginator.paginate(
            Bucket=self.bucket_name,
            Prefix=prefix,
            PaginationConfig={'MaxItems': max_keys}
        ):
            for obj in page.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                })

        return files

    def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        response_content_type: Optional[str] = None
    ) -> str:
        """
        Generate a presigned URL for downloading.

        Args:
            key: S3 key
            expiration: URL expiration in seconds
            response_content_type: Content type for response

        Returns:
            Presigned URL string
        """
        params = {
            'Bucket': self.bucket_name,
            'Key': key
        }

        if response_content_type:
            params['ResponseContentType'] = response_content_type

        return self.s3.generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=expiration
        )

    def get_presigned_upload_url(
        self,
        key: str,
        expiration: int = 3600,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a presigned URL for uploading.

        Args:
            key: S3 key
            expiration: URL expiration in seconds
            content_type: Content type for upload

        Returns:
            Dict with 'url' and 'fields' for form upload
        """
        conditions = []
        fields = {}

        if content_type:
            conditions.append({'Content-Type': content_type})
            fields['Content-Type'] = content_type

        return self.s3.generate_presigned_post(
            self.bucket_name,
            key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expiration
        )

    def get_file_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata from S3.

        Args:
            key: S3 key

        Returns:
            Dict with file info or None if not found
        """
        try:
            response = self.s3.head_object(Bucket=self.bucket_name, Key=key)
            return {
                'key': key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError:
            return None


def get_storage():
    """
    Factory function to get the appropriate storage backend.

    Returns LocalStorage for development or S3Storage for production.
    """
    use_s3 = os.environ.get('USE_S3_STORAGE', 'False').lower() == 'true'

    if use_s3 and BOTO3_AVAILABLE:
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        if bucket_name:
            return S3Storage()
        else:
            logger.warning("S3_BUCKET_NAME not set, falling back to local storage")
            return LocalStorage()
    else:
        return LocalStorage()


# Global storage instance
storage = get_storage()


# Convenience functions for backward compatibility
def upload_file(file_obj, key, content_type=None, metadata=None):
    return storage.upload_file(file_obj, key, content_type, metadata)


def download_file(key):
    return storage.download_file(key)


def file_exists(key):
    return storage.file_exists(key)


def delete_file(key):
    return storage.delete_file(key)


def get_presigned_url(key, expiration=3600):
    return storage.get_presigned_url(key, expiration)
