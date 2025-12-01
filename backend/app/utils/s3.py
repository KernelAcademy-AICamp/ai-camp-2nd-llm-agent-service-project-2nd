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
    Generate S3 presigned POST URL for file upload

    Args:
        bucket: S3 bucket name
        key: S3 object key (path)
        content_type: File content type (e.g., 'application/pdf')
        expires_in: URL expiration in seconds (max 300 = 5 minutes)

    Returns:
        Dict with 'upload_url' and 'fields' for multipart POST upload

    Security:
        - Max expiration is 300 seconds (5 minutes) per SECURITY_COMPLIANCE.md
        - Validates expires_in parameter
        - Max file size: 100MB
    """
    # Security: Enforce max expiration
    if expires_in > 300:
        expires_in = 300

    try:
        # Real AWS S3 client
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

        response = s3_client.generate_presigned_post(
            Bucket=bucket,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 0, 104857600]  # 100MB max
            ],
            ExpiresIn=expires_in
        )

        logger.info(f"Generated presigned POST URL for bucket={bucket}, key={key}")

        # boto3 returns 'url' and 'fields', but we need 'upload_url' and 'fields'
        return {
            "upload_url": response["url"],
            "fields": response["fields"]
        }

    except Exception as e:
        logger.error(f"Failed to generate presigned POST URL: {e}")
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
