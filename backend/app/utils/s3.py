"""
S3 utilities for presigned URL generation
Real AWS boto3 implementation
"""

from typing import Dict
from app.core.config import settings
import boto3
import logging

logger = logging.getLogger(__name__)


def generate_presigned_upload_url(
    bucket: str,
    key: str,
    content_type: str,
    expires_in: int = 300
) -> Dict[str, any]:
    """
    Generate S3 presigned PUT URL for file upload

    Args:
        bucket: S3 bucket name
        key: S3 object key (path)
        content_type: File content type (e.g., 'application/pdf')
        expires_in: URL expiration in seconds (max 300 = 5 minutes)

    Returns:
        Dict with 'upload_url' for direct PUT upload

    Security:
        - Max expiration is 300 seconds (5 minutes) per SECURITY_COMPLIANCE.md
        - Validates expires_in parameter
    """
    # Security: Enforce max expiration
    if expires_in > 300:
        expires_in = 300

    try:
        # Real AWS S3 client
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

        # Generate presigned PUT URL for direct upload
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket,
                'Key': key,
                'ContentType': content_type
            },
            ExpiresIn=expires_in
        )

        logger.info(f"Generated presigned PUT URL for bucket={bucket}, key={key}")

        return {
            "upload_url": url,
            "fields": {}  # No fields needed for PUT upload
        }

    except Exception as e:
        logger.error(f"Failed to generate presigned PUT URL: {e}")
        raise


def generate_presigned_download_url(
    bucket: str,
    key: str,
    expires_in: int = 300
) -> str:
    """
    Generate S3 presigned GET URL for file download

    Args:
        bucket: S3 bucket name
        key: S3 object key (path)
        expires_in: URL expiration in seconds (max 300 = 5 minutes)

    Returns:
        Presigned download URL string

    Security:
        - Max expiration is 300 seconds (5 minutes)
    """
    # Security: Enforce max expiration
    if expires_in > 300:
        expires_in = 300

    try:
        # Real AWS S3 client
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expires_in
        )

        logger.info(f"Generated presigned GET URL for bucket={bucket}, key={key}")
        return url

    except Exception as e:
        logger.error(f"Failed to generate presigned GET URL: {e}")
        raise
