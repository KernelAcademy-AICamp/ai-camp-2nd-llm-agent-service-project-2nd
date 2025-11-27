"""
Dead Letter Queue (DLQ) Module for LEH AI Worker
Handles sending failed records to SQS DLQ for later processing/debugging
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DLQManager:
    """
    DLQ 매니저 클래스

    실패한 레코드를 SQS Dead Letter Queue로 전송합니다.
    """

    def __init__(self, queue_url: Optional[str] = None):
        """
        DLQManager 초기화

        Args:
            queue_url: SQS DLQ URL (기본: 환경변수 DLQ_URL)
        """
        self.queue_url = queue_url or os.getenv("DLQ_URL")
        self.sqs = boto3.client("sqs")

    def send_to_dlq(
        self,
        record: Dict[str, Any],
        error: Exception,
        context: Any = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        실패한 레코드를 DLQ로 전송

        Args:
            record: 원본 S3 이벤트 레코드
            error: 발생한 예외
            context: Lambda context 객체 (선택)
            additional_metadata: 추가 메타데이터 (선택)

        Returns:
            bool: 전송 성공 여부
        """
        if not self.queue_url:
            logger.warning("DLQ_URL not configured, skipping DLQ send")
            return False

        try:
            # DLQ 메시지 구성
            dlq_message = {
                "original_record": record,
                "error_type": error.__class__.__name__,
                "error_message": str(error),
                "is_retryable": getattr(error, "is_retryable", False),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "lambda_request_id": getattr(context, "aws_request_id", None) if context else None,
                "lambda_function_name": getattr(context, "function_name", None) if context else None,
            }

            # 추가 메타데이터 병합
            if additional_metadata:
                dlq_message["metadata"] = additional_metadata

            # S3 정보 추출 (디버깅용)
            s3_info = record.get("s3", {})
            dlq_message["s3_bucket"] = s3_info.get("bucket", {}).get("name")
            dlq_message["s3_key"] = s3_info.get("object", {}).get("key")

            # SQS로 전송
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(dlq_message, ensure_ascii=False, default=str),
                MessageAttributes={
                    "ErrorType": {
                        "StringValue": error.__class__.__name__,
                        "DataType": "String"
                    },
                    "IsRetryable": {
                        "StringValue": str(getattr(error, "is_retryable", False)),
                        "DataType": "String"
                    }
                }
            )

            message_id = response.get("MessageId")
            logger.info(f"Sent record to DLQ: MessageId={message_id}, Error={error.__class__.__name__}")

            return True

        except ClientError as e:
            logger.error(f"Failed to send record to DLQ: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending to DLQ: {e}")
            return False


# 모듈 레벨 편의 함수
_dlq_manager: Optional[DLQManager] = None


def get_dlq_manager() -> DLQManager:
    """
    싱글턴 DLQ 매니저 반환
    """
    global _dlq_manager
    if _dlq_manager is None:
        _dlq_manager = DLQManager()
    return _dlq_manager


def send_to_dlq(
    record: Dict[str, Any],
    error: Exception,
    context: Any = None,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    실패한 레코드를 DLQ로 전송 (편의 함수)

    Args:
        record: 원본 S3 이벤트 레코드
        error: 발생한 예외
        context: Lambda context 객체 (선택)
        additional_metadata: 추가 메타데이터 (선택)

    Returns:
        bool: 전송 성공 여부
    """
    return get_dlq_manager().send_to_dlq(record, error, context, additional_metadata)
