"""
S3 utilities for presigned URL generation
Mock implementation for development/testing

In production, replace with real boto3 calls:
    import boto3
    s3_client = boto3.client('s3')
    return s3_client.generate_presigned_post(...)
"""

from typing import Dict
from app.core.config import settings
import uuid


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
    """
    # Security: Enforce max expiration
    if expires_in > 300:
        expires_in = 300

    # Mock implementation
    # TODO: Replace with boto3 when AWS is configured
    # s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
    # return s3_client.generate_presigned_post(
    #     Bucket=bucket,
    #     Key=key,
    #     Fields={"Content-Type": content_type},
    #     Conditions=[
    #         {"Content-Type": content_type},
    #         ["content-length-range", 0, 104857600]  # 100MB max
    #     ],
    #     ExpiresIn=expires_in
    # )

    # Mock response matching AWS S3 presigned POST structure
    return {
        "upload_url": f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/",
        "fields": {
            "key": key,
            "Content-Type": content_type,
            "policy": "mock-policy-base64",
            "x-amz-algorithm": "AWS4-HMAC-SHA256",
            "x-amz-credential": f"mock-credential/{settings.AWS_REGION}/s3/aws4_request",
            "x-amz-date": "20250120T000000Z",
            "x-amz-signature": "mock-signature"
        },
        "expires_in": expires_in  # Add for testing purposes
    }


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

    # Mock implementation
    # TODO: Replace with boto3 when AWS is configured
    # s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
    # return s3_client.generate_presigned_url(
    #     'get_object',
    #     Params={'Bucket': bucket, 'Key': key},
    #     ExpiresIn=expires_in
    # )

    # Mock response
    return f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}?mock-signature=true&expires={expires_in}"
