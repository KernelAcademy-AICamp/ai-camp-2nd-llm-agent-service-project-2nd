"""
Hash Utilities for Idempotency and Duplicate Prevention

Provides SHA-256 hashing for:
- Local files (after S3 download)
- S3 objects directly (streaming hash)
- Content strings
"""

import hashlib
import logging
from typing import Optional, Tuple

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Buffer size for streaming hash (8KB)
HASH_BUFFER_SIZE = 8192


def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a local file.

    Args:
        file_path: Path to the local file

    Returns:
        SHA-256 hash as hexadecimal string (64 characters)

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(HASH_BUFFER_SIZE), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def calculate_s3_object_hash(
    bucket_name: str,
    object_key: str,
    s3_client=None
) -> Optional[str]:
    """
    Calculate SHA-256 hash of an S3 object by streaming.

    This method streams the S3 object and calculates hash without
    downloading the entire file to disk first.

    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        s3_client: Optional boto3 S3 client (created if not provided)

    Returns:
        SHA-256 hash as hexadecimal string, or None if error
    """
    if s3_client is None:
        s3_client = boto3.client('s3')

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        sha256_hash = hashlib.sha256()

        # Stream body and hash in chunks
        body = response['Body']
        for chunk in body.iter_chunks(chunk_size=HASH_BUFFER_SIZE):
            sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    except ClientError as e:
        logger.error(f"Failed to hash S3 object s3://{bucket_name}/{object_key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error hashing S3 object: {e}")
        return None


def calculate_content_hash(content: str, encoding: str = "utf-8") -> str:
    """
    Calculate SHA-256 hash of string content.

    Args:
        content: String content to hash
        encoding: Character encoding (default: utf-8)

    Returns:
        SHA-256 hash as hexadecimal string
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content.encode(encoding))
    return sha256_hash.hexdigest()


def get_s3_etag(
    bucket_name: str,
    object_key: str,
    s3_client=None
) -> Tuple[Optional[str], Optional[int]]:
    """
    Get S3 object's ETag and size without downloading.

    ETag can be used as a quick check before full hash calculation.
    Note: ETag is MD5 for single-part uploads, but different for multipart.

    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key
        s3_client: Optional boto3 S3 client

    Returns:
        Tuple of (etag, content_length) or (None, None) if error
    """
    if s3_client is None:
        s3_client = boto3.client('s3')

    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        etag = response.get('ETag', '').strip('"')
        content_length = response.get('ContentLength', 0)
        return etag, content_length

    except ClientError as e:
        logger.error(f"Failed to get S3 object metadata: {e}")
        return None, None


def is_duplicate_by_hash(
    file_hash: str,
    existing_hashes: set
) -> bool:
    """
    Check if file hash exists in the set of existing hashes.

    Args:
        file_hash: SHA-256 hash to check
        existing_hashes: Set of existing hashes

    Returns:
        True if duplicate, False otherwise
    """
    return file_hash in existing_hashes
