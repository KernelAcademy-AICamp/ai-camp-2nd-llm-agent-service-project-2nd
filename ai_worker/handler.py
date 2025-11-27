"""
AWS Lambda Handler for LEH AI Worker.
Triggered by S3 ObjectCreated events.
"""

import json
import logging
import os
import re
import urllib.parse
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import AI Pipeline modules
from src.parsers import (
    ImageOCRParser,
    ImageVisionParser,
    PDFParser,
    AudioParser,
    VideoParser
)
from src.parsers.text import TextParser
from src.storage import get_metadata_store, get_vector_store, get_storage_info
from src.storage.schemas import EvidenceFile, EvidenceChunk
from src.storage.storage_manager import get_embedding
from src.analysis.summarizer import EvidenceSummarizer
from src.analysis.article_840_tagger import Article840Tagger
from src.utils.logging_filter import SensitiveDataFilter

# Import error handling modules
from .errors import (
    RetryableError,
    FatalError,
    ParseError,
    UnsupportedFileTypeError,
    S3DownloadError,
    EmbeddingError,
    StorageError,
    ValidationError
)
from .dlq import send_to_dlq

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addFilter(SensitiveDataFilter())


def extract_case_id(object_key: str) -> str:
    """
    S3 객체 키에서 case_id 추출

    Expected format: cases/{case_id}/raw/{filename}

    Args:
        object_key: S3 객체 키 (예: "cases/case-123/raw/evidence.pdf")

    Returns:
        str: 추출된 case_id

    Raises:
        ValueError: S3 키 형식이 잘못된 경우
    """
    match = re.match(r'cases/([^/]+)/', object_key)
    if match:
        return match.group(1)

    # fallback: 버킷명이나 기본값 대신 파일명 기반 ID 생성
    logger.warning(f"Could not extract case_id from key: {object_key}, using filename hash")
    return f"unknown-{hash(object_key) % 100000}"


def route_parser(file_extension: str) -> Any:
    """
    파일 확장자에 따라 적절한 파서를 반환

    Args:
        file_extension: 파일 확장자 (예: '.pdf', '.jpg', '.mp4')

    Returns:
        적절한 파서 인스턴스

    Raises:
        UnsupportedFileTypeError: 지원하지 않는 파일 형식
    """
    ext = file_extension.lower()

    # 이미지 파일
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        # Vision API 우선 사용 (감정/맥락 분석)
        return ImageVisionParser()

    # PDF 파일
    elif ext == '.pdf':
        return PDFParser()

    # 오디오 파일
    elif ext in ['.mp3', '.wav', '.m4a', '.aac']:
        return AudioParser()

    # 비디오 파일
    elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
        return VideoParser()

    # 텍스트 파일 (카톡 포함)
    elif ext in ['.txt', '.csv', '.json']:
        return TextParser()

    else:
        raise UnsupportedFileTypeError(f"Unsupported file type: {ext}")


def route_and_process(bucket_name: str, object_key: str) -> Dict[str, Any]:
    """
    S3 파일을 파싱하고 분석하는 메인 처리 함수

    Args:
        bucket_name: S3 버킷 이름
        object_key: S3 객체 키 (파일 경로)

    Returns:
        처리 결과 딕셔너리

    Raises:
        RetryableError: 재시도 가능한 에러 (네트워크, 임시 장애)
        FatalError: 재시도 불가능한 에러 (파일 손상, 지원 안 되는 형식)
    """
    local_path = None  # /tmp 파일 경로 추적용

    try:
        # case_id 추출 (S3 키에서 추출, 없으면 fallback)
        case_id = extract_case_id(object_key)
        logger.info(f"Extracted case_id: {case_id} from key: {object_key}")

        # 파일 확장자 추출
        file_path = Path(object_key)
        file_extension = file_path.suffix

        logger.info(f"Processing file: {object_key} (extension: {file_extension})")

        # 적절한 파서 선택 (UnsupportedFileTypeError 발생 가능)
        parser = route_parser(file_extension)

        # S3에서 파일 다운로드
        try:
            s3_client = boto3.client('s3')
            local_path = f"/tmp/{file_path.name}"  # finally에서 정리하기 위해 추적

            # 임시 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            s3_client.download_file(bucket_name, object_key, local_path)
            logger.info(f"Downloaded {object_key} to {local_path}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ["NoSuchKey", "NoSuchBucket", "AccessDenied"]:
                raise FatalError(f"S3 access error: {error_code}", e)
            else:
                raise S3DownloadError(f"S3 download failed: {e}", e)

        # 파서 실행
        try:
            parsed_result = parser.parse(local_path)
            logger.info(f"Parsed {object_key} with {parser.__class__.__name__}")
        except Exception as e:
            raise ParseError(f"Failed to parse file: {e}", e)

        if not parsed_result:
            raise ParseError(f"No content parsed from file: {object_key}")

        # 메타데이터 저장 (환경에 따라 SQLite 또는 DynamoDB 자동 선택)
        try:
            metadata_store = get_metadata_store(local_db_path="/tmp/metadata.db")

            # EvidenceFile 객체 생성 (올바른 방식)
            file_meta = EvidenceFile(
                filename=file_path.name,
                file_type=file_extension,
                total_messages=len(parsed_result),
                case_id=case_id,
                filepath=object_key
            )
            metadata_store.save_file(file_meta)
            logger.info(f"Saved metadata for {object_key}: file_id={file_meta.file_id}")
        except Exception as e:
            raise StorageError(f"Failed to save file metadata: {e}", e)

        # 벡터 임베딩 및 저장 (환경에 따라 ChromaDB 또는 OpenSearch 자동 선택)
        try:
            vector_store = get_vector_store(local_persist_dir="/tmp/chromadb")
        except Exception as e:
            raise StorageError(f"Failed to initialize vector store: {e}", e)

        chunk_ids = []

        for idx, message in enumerate(parsed_result):
            # 청크 메타데이터 생성
            chunk = EvidenceChunk(
                file_id=file_meta.file_id,
                content=message.content,
                timestamp=message.timestamp,
                sender=message.sender,
                case_id=case_id
            )

            # 임베딩 생성 (실제 OpenAI API 호출)
            try:
                embedding = get_embedding(message.content)
            except Exception as e:
                raise EmbeddingError(f"Failed to generate embedding: {e}", e)

            # 올바른 시그니처로 벡터 저장: add_evidence(text, embedding, metadata)
            try:
                vector_id = vector_store.add_evidence(
                    text=message.content,
                    embedding=embedding,
                    metadata={
                        "file_id": file_meta.file_id,
                        "chunk_id": chunk.chunk_id,
                        "case_id": case_id,
                        "sender": message.sender,
                        "timestamp": message.timestamp.isoformat() if message.timestamp else None,
                        "chunk_index": idx,
                        **message.metadata
                    }
                )

                # vector_id 설정 후 청크 저장
                chunk.vector_id = vector_id
                metadata_store.save_chunk(chunk)
                chunk_ids.append(vector_id)
            except Exception as e:
                raise StorageError(f"Failed to store chunk {idx}: {e}", e)

        logger.info(f"Indexed {len(chunk_ids)} chunks to vector store")

        # 분석 엔진 실행 (Summarizer + Article 840 Tagger)
        summarizer = EvidenceSummarizer()
        tagger = Article840Tagger()

        summaries = []
        tags_list = []
        for message in parsed_result:
            # 요약 생성 (필요시)
            # summary = summarizer.summarize(message)
            # summaries.append(summary)

            # Article 840 태깅
            tagging_result = tagger.tag(message)
            tags_list.append({
                "categories": [cat.value for cat in tagging_result.categories],
                "confidence": tagging_result.confidence,
                "matched_keywords": tagging_result.matched_keywords
            })

        return {
            "status": "processed",
            "file": object_key,
            "parser_type": parser.__class__.__name__,
            "bucket": bucket_name,
            "file_id": file_meta.file_id,
            "chunks_indexed": len(chunk_ids),
            "tags": tags_list
        }

    except (RetryableError, FatalError):
        # 에러 타입 분류된 에러는 그대로 상위로 전파
        raise

    except Exception as e:
        # 분류되지 않은 예상치 못한 에러 → FatalError로 래핑
        logger.error(f"Unexpected error processing {object_key}: {str(e)}", exc_info=True)
        raise FatalError(f"Unexpected error: {str(e)}", e)

    finally:
        # /tmp 파일 정리 (Lambda 512MB 제한 대응)
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
                logger.info(f"Cleaned up temporary file: {local_path}")
            except OSError as cleanup_error:
                logger.warning(f"Failed to clean up {local_path}: {cleanup_error}")


def handle(event, context):
    """
    AWS Lambda Entrypoint.
    S3 이벤트를 수신하여 파일 정보를 파싱하고 AI 파이프라인을 시작합니다.

    에러 처리 전략:
    - RetryableError: Lambda 자동 재시도 유도 (예외 re-raise)
    - FatalError: DLQ로 전송 후 계속 처리
    - 모든 레코드 실패 시: Lambda 실패로 처리 (전체 재시도)
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # S3 이벤트가 아닌 경우(테스트 등) 방어 로직
    if "Records" not in event:
        return {"status": "ignored", "reason": "No S3 Records found"}

    results: List[Dict[str, Any]] = []
    failed_records: List[Dict[str, Any]] = []
    retryable_errors: List[Exception] = []

    for record in event["Records"]:
        try:
            # 1. S3 이벤트에서 버킷과 키(파일 경로) 추출
            s3 = record.get("s3", {})
            bucket_name = s3.get("bucket", {}).get("name")
            object_key = s3.get("object", {}).get("key")

            # URL Decoding (공백 등이 + 또는 %20으로 들어올 수 있음)
            if object_key:
                object_key = urllib.parse.unquote_plus(object_key)

            logger.info(f"Processing file: s3://{bucket_name}/{object_key}")

            # 2. 파일 처리 로직 실행 (Strategy Pattern 적용)
            result = route_and_process(bucket_name, object_key)
            results.append(result)

        except RetryableError as e:
            # 재시도 가능한 에러: 로깅 후 나중에 전체 재시도
            logger.warning(f"Retryable error for record: {e}")
            retryable_errors.append(e)
            failed_records.append(record)
            results.append({
                "status": "failed",
                "error": str(e),
                "error_type": "retryable",
                "file": record.get("s3", {}).get("object", {}).get("key")
            })

        except FatalError as e:
            # 재시도 불가능한 에러: DLQ로 전송
            logger.error(f"Fatal error for record: {e}")
            sent = send_to_dlq(record, e, context)
            failed_records.append(record)
            results.append({
                "status": "failed",
                "error": str(e),
                "error_type": "fatal",
                "sent_to_dlq": sent,
                "file": record.get("s3", {}).get("object", {}).get("key")
            })

        except Exception as e:
            # 예상치 못한 에러: DLQ로 전송
            logger.exception(f"Unexpected error for record: {e}")
            sent = send_to_dlq(record, e, context)
            failed_records.append(record)
            results.append({
                "status": "failed",
                "error": str(e),
                "error_type": "unexpected",
                "sent_to_dlq": sent,
                "file": record.get("s3", {}).get("object", {}).get("key")
            })

    # 결과 요약
    total_records = len(event["Records"])
    success_count = total_records - len(failed_records)
    failed_count = len(failed_records)

    logger.info(f"Processing complete: {success_count}/{total_records} succeeded, {failed_count} failed")

    # 재시도 가능한 에러가 있으면 Lambda 재시도 유도
    if retryable_errors:
        # 모든 레코드가 retryable error로 실패한 경우에만 재시도
        if len(retryable_errors) == total_records:
            logger.error(f"All {total_records} records failed with retryable errors, triggering Lambda retry")
            raise retryable_errors[0]  # 첫 번째 에러로 Lambda 재시도 유도

    # 모든 레코드가 실패한 경우 (하나라도 retryable이면 위에서 처리됨)
    if failed_count == total_records and total_records > 0:
        logger.error(f"All {total_records} records failed")
        # 이미 DLQ로 전송됨, 200 반환하여 Lambda 재시도 방지

    return {
        "statusCode": 200,
        "body": json.dumps({
            "results": results,
            "summary": {
                "total": total_records,
                "success": success_count,
                "failed": failed_count
            }
        })
    }
