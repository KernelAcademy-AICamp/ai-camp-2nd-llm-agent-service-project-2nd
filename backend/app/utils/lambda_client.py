"""
Lambda utilities for AI Worker invocation
Asynchronous Lambda invocation to trigger AI processing pipeline
"""

import json
import logging
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


def invoke_ai_worker(
    bucket: str,
    s3_key: str,
    evidence_id: str,
    case_id: str
) -> Dict[str, Any]:
    """
    Invoke AI Worker Lambda function asynchronously to process uploaded evidence

    Args:
        bucket: S3 bucket name where evidence is stored
        s3_key: S3 object key (path) of the uploaded file
        evidence_id: Evidence ID created by Backend
        case_id: Case ID the evidence belongs to

    Returns:
        Dict with invocation status and request_id

    Note:
        Uses 'Event' invocation type for async processing.
        The Lambda will process the file and update DynamoDB status to 'processed'.
    """
    if not settings.LAMBDA_AI_WORKER_ENABLED:
        logger.info("AI Worker Lambda invocation is disabled")
        return {
            "status": "skipped",
            "reason": "AI Worker Lambda is disabled"
        }

    try:
        lambda_client = boto3.client('lambda', region_name=settings.AWS_REGION)

        # Create S3 event-like payload that AI Worker handler expects
        payload = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": bucket},
                        "object": {"key": s3_key}
                    },
                    # Additional context for Backend integration
                    "eventSource": "backend:upload_complete",
                    "metadata": {
                        "evidence_id": evidence_id,
                        "case_id": case_id
                    }
                }
            ]
        }

        response = lambda_client.invoke(
            FunctionName=settings.LAMBDA_AI_WORKER_FUNCTION,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )

        status_code = response.get('StatusCode', 0)
        request_id = response.get('ResponseMetadata', {}).get('RequestId', 'unknown')

        if status_code == 202:
            logger.info(
                f"AI Worker Lambda invoked successfully: "
                f"function={settings.LAMBDA_AI_WORKER_FUNCTION}, "
                f"evidence_id={evidence_id}, request_id={request_id}"
            )
            return {
                "status": "invoked",
                "request_id": request_id,
                "function_name": settings.LAMBDA_AI_WORKER_FUNCTION
            }
        else:
            logger.warning(
                f"Unexpected Lambda status code: {status_code} for evidence_id={evidence_id}"
            )
            return {
                "status": "unexpected",
                "status_code": status_code,
                "request_id": request_id
            }

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))

        logger.error(
            f"Failed to invoke AI Worker Lambda: "
            f"error_code={error_code}, message={error_message}, "
            f"evidence_id={evidence_id}"
        )

        return {
            "status": "error",
            "error_code": error_code,
            "error_message": error_message
        }

    except Exception as e:
        logger.error(
            f"Unexpected error invoking AI Worker Lambda: {e}, evidence_id={evidence_id}",
            exc_info=True
        )
        return {
            "status": "error",
            "error_message": str(e)
        }
