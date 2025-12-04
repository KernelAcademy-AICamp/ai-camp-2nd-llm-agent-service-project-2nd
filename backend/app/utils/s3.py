"""
S3 utilities for presigned URL generation and file operations
Real AWS boto3 implementation
"""

from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
from app.core.config import settings
import boto3
import logging
import uuid

logger = logging.getLogger(__name__)

# Export bucket and paths
EXPORTS_BUCKET = getattr(settings, 'S3_EXPORTS_BUCKET', settings.S3_EVIDENCE_BUCKET)
EXPORTS_PREFIX = "exports"


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


def upload_export_file(
    file_bytes: bytes,
    case_id: str,
    export_job_id: str,
    file_format: str,
    content_type: str,
    expires_hours: int = 24
) -> Dict[str, any]:
    """
    Upload generated export file to S3 with expiration metadata.

    Args:
        file_bytes: File content as bytes
        case_id: Case ID for path organization
        export_job_id: Export job ID for unique filename
        file_format: File format extension (docx, pdf)
        content_type: MIME content type
        expires_hours: Hours until file expires (default 24)

    Returns:
        Dict with:
            - s3_key: S3 object key
            - file_size: Size in bytes
            - expires_at: Expiration datetime (ISO format)

    Security:
        - Files are stored with expiration metadata
        - Max expiration is 24 hours for temporary exports
    """
    # Build S3 key: exports/{case_id}/{export_job_id}.{format}
    s3_key = f"{EXPORTS_PREFIX}/{case_id}/{export_job_id}.{file_format}"

    # Calculate expiration
    expires_at = datetime.now(timezone.utc) + timedelta(hours=min(expires_hours, 24))

    try:
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

        # Upload file with metadata
        s3_client.put_object(
            Bucket=EXPORTS_BUCKET,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
            Metadata={
                'export_job_id': export_job_id,
                'case_id': case_id,
                'expires_at': expires_at.isoformat()
            }
        )

        file_size = len(file_bytes)
        logger.info(
            f"Uploaded export file: bucket={EXPORTS_BUCKET}, key={s3_key}, "
            f"size={file_size}, expires={expires_at.isoformat()}"
        )

        return {
            "s3_key": s3_key,
            "file_size": file_size,
            "expires_at": expires_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to upload export file: {e}")
        raise


def generate_export_download_url(
    s3_key: str,
    filename: Optional[str] = None,
    expires_in: int = 3600
) -> str:
    """
    Generate presigned download URL for export file.

    Args:
        s3_key: S3 object key
        filename: Optional filename for Content-Disposition header
        expires_in: URL expiration in seconds (default 1 hour, max 1 hour)

    Returns:
        Presigned download URL string

    Security:
        - Max expiration is 3600 seconds (1 hour) for export downloads
        - Uses Content-Disposition for proper filename
    """
    # Security: Enforce max expiration for exports
    if expires_in > 3600:
        expires_in = 3600

    try:
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

        params = {
            'Bucket': EXPORTS_BUCKET,
            'Key': s3_key
        }

        # Add Content-Disposition for filename if provided
        if filename:
            params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'

        url = s3_client.generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=expires_in
        )

        logger.info(f"Generated export download URL for key={s3_key}")
        return url

    except Exception as e:
        logger.error(f"Failed to generate export download URL: {e}")
        raise


def delete_export_file(s3_key: str) -> bool:
    """
    Delete export file from S3.

    Args:
        s3_key: S3 object key

    Returns:
        True if deletion successful
    """
    try:
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

        s3_client.delete_object(
            Bucket=EXPORTS_BUCKET,
            Key=s3_key
        )

        logger.info(f"Deleted export file: key={s3_key}")
        return True

    except Exception as e:
        logger.error(f"Failed to delete export file: {e}")
        raise
