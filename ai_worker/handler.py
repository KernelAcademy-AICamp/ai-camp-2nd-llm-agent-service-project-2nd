"""
AWS Lambda Handler for LEH AI Worker.
Triggered by S3 ObjectCreated events.

Storage Architecture (Lambda Compatible):
- MetadataStore → DynamoDB (leh_evidence table)
- VectorStore → Qdrant Cloud
"""

import json
import logging
import os
import urllib.parse
import uuid
from datetime import datetime, timezone

import boto3
from pathlib import Path
from typing import Dict, Any, Optional

# Import AI Pipeline modules
from src.parsers import (
    ImageVisionParser,
    PDFParser,
    AudioParser,
    VideoParser
)
from src.parsers.text import TextParser
from src.storage.metadata_store import MetadataStore
from src.storage.vector_store import VectorStore
from src.storage.schemas import EvidenceFile
from src.analysis.article_840_tagger import Article840Tagger
from src.utils.logging_filter import SensitiveDataFilter
from src.utils.embeddings import get_embedding_with_fallback  # Embedding utility with fallback

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addFilter(SensitiveDataFilter())


def route_parser(file_extension: str) -> Optional[Any]:
    """
    파일 확장자에 따라 적절한 파서를 반환

    Args:
        file_extension: 파일 확장자 (예: '.pdf', '.jpg', '.mp4')

    Returns:
        적절한 파서 인스턴스 또는 None
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
        logger.warning(f"Unsupported file type: {ext}")
        return None


def route_and_process(bucket_name: str, object_key: str) -> Dict[str, Any]:
    """
    S3 파일을 파싱하고 분석하는 메인 처리 함수

    Args:
        bucket_name: S3 버킷 이름
        object_key: S3 객체 키 (파일 경로)

    Returns:
        처리 결과 딕셔너리

    Storage Flow:
        1. Parse file → Get messages/chunks
        2. Save file metadata → DynamoDB (MetadataStore)
        3. Generate embeddings → OpenAI
        4. Store vectors + metadata → Qdrant (VectorStore)
        5. Run analysis → Article 840 Tagger
    """
    try:
        # 파일 확장자 추출
        file_path = Path(object_key)
        file_extension = file_path.suffix

        logger.info(f"Processing file: {object_key} (extension: {file_extension})")

        # 적절한 파서 선택
        parser = route_parser(file_extension)
        if not parser:
            return {
                "status": "skipped",
                "reason": f"Unsupported file type: {file_extension}",
                "file": object_key
            }

        # S3에서 파일 다운로드
        s3_client = boto3.client('s3')
        local_path = f"/tmp/{file_path.name}"

        # 임시 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        s3_client.download_file(bucket_name, object_key, local_path)
        logger.info(f"Downloaded {object_key} to {local_path}")

        # 파서 실행
        parsed_result = parser.parse(local_path)
        logger.info(f"Parsed {object_key} with {parser.__class__.__name__}")

        # case_id 추출 (object_key에서 첫 번째 디렉토리 또는 bucket_name)
        # 예: cases/{case_id}/raw/ev_xxx_file.txt → case_id 추출
        case_id = _extract_case_id(object_key, bucket_name)

        # evidence_id 추출 (Backend 레코드 업데이트용)
        # 예: cases/{case_id}/raw/ev_abc123_file.txt → ev_abc123
        backend_evidence_id = _extract_evidence_id_from_s3_key(object_key)

        # 파일 메타데이터 생성
        file_id = backend_evidence_id or f"file_{uuid.uuid4().hex[:12]}"
        source_type = parsed_result[0].metadata.get("source_type", "unknown") if parsed_result else "unknown"

        # 메타데이터 저장 (DynamoDB)
        metadata_store = MetadataStore()

        # 벡터 임베딩 및 저장 (Qdrant)
        vector_store = VectorStore()
        chunk_ids = []

        for idx, message in enumerate(parsed_result):
            chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"
            content = message.content
            timestamp = message.timestamp.isoformat() if message.timestamp else datetime.now(timezone.utc).isoformat()

            # Embedding 생성 (with fallback - never fails)
            embedding, is_real_embedding = get_embedding_with_fallback(content)
            if not is_real_embedding:
                logger.info(f"Using fallback embedding for chunk {idx}")

            # Qdrant에 벡터 + 메타데이터 저장
            vector_store.add_chunk_with_metadata(
                chunk_id=chunk_id,
                file_id=file_id,
                case_id=case_id,
                content=content,
                embedding=embedding,
                timestamp=timestamp,
                sender=message.sender,
                score=None
            )
            chunk_ids.append(chunk_id)

        logger.info(f"Indexed {len(chunk_ids)} chunks to Qdrant")

        # 분석 엔진 실행 (Article 840 Tagger)
        tagger = Article840Tagger()

        tags_list = []
        all_categories = set()
        for message in parsed_result:
            tagging_result = tagger.tag(message)
            tags_list.append({
                "categories": [cat.value for cat in tagging_result.categories],
                "confidence": tagging_result.confidence,
                "matched_keywords": tagging_result.matched_keywords
            })
            all_categories.update(cat.value for cat in tagging_result.categories)

        # AI 요약 생성 (간단한 통계 기반)
        ai_summary = f"총 {len(parsed_result)}개 메시지 분석 완료. 감지된 태그: {', '.join(all_categories) if all_categories else '없음'}"

        # Article 840 태그 집계
        article_840_tags = {
            "categories": list(all_categories),
            "total_messages": len(parsed_result),
            "chunks_indexed": len(chunk_ids)
        }

        # 메타데이터 저장/업데이트 (DynamoDB)
        if backend_evidence_id:
            # Backend가 생성한 레코드 업데이트
            metadata_store.update_evidence_status(
                evidence_id=backend_evidence_id,
                status="processed",
                ai_summary=ai_summary,
                article_840_tags=article_840_tags,
                qdrant_id=chunk_ids[0] if chunk_ids else None
            )
            logger.info(f"Updated Backend evidence: {backend_evidence_id} → processed")
        else:
            # Fallback: 새 레코드 생성 (기존 방식)
            evidence_file = EvidenceFile(
                file_id=file_id,
                filename=file_path.name,
                file_type=source_type,
                parsed_at=datetime.now(timezone.utc),
                total_messages=len(parsed_result),
                case_id=case_id,
                filepath=object_key
            )
            metadata_store.save_file(evidence_file)
            logger.info(f"Created new evidence record: {file_id}")

        return {
            "status": "processed",
            "file": object_key,
            "parser_type": parser.__class__.__name__,
            "bucket": bucket_name,
            "case_id": case_id,
            "file_id": file_id,
            "evidence_id": backend_evidence_id,
            "chunks_indexed": len(chunk_ids),
            "tags": tags_list,
            "ai_summary": ai_summary
        }

    except Exception as e:
        logger.error(f"Error processing {object_key}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "file": object_key,
            "error": str(e)
        }


def _extract_case_id(object_key: str, fallback: str) -> str:
    """
    S3 object key에서 case_id 추출

    Expected formats:
    - cases/{case_id}/raw/{evidence_id}_{filename} → case_id (Backend format)
    - evidence/{case_id}/filename.ext → case_id
    - {case_id}/filename.ext → case_id
    - filename.ext → fallback (bucket name)

    Args:
        object_key: S3 object key
        fallback: Fallback value (bucket name)

    Returns:
        Extracted case_id
    """
    parts = object_key.split('/')

    # cases/{case_id}/raw/{evidence_id}_{filename} 패턴 (Backend format)
    if len(parts) >= 4 and parts[0] == 'cases' and parts[2] == 'raw':
        return parts[1]

    # evidence/{case_id}/file.ext 패턴
    if len(parts) >= 3 and parts[0] == 'evidence':
        return parts[1]

    # {case_id}/file.ext 패턴
    if len(parts) >= 2:
        return parts[0]

    # 파일만 있는 경우 fallback
    return fallback


def _extract_evidence_id_from_s3_key(object_key: str) -> Optional[str]:
    """
    S3 object key에서 evidence_id 추출 (Backend 레코드 업데이트용)

    Expected format:
    - cases/{case_id}/raw/{evidence_id}_{filename}
    - 예: cases/case_001/raw/ev_abc123_photo.jpg → ev_abc123

    Args:
        object_key: S3 object key

    Returns:
        evidence_id if found, None otherwise
    """
    parts = object_key.split('/')

    # cases/{case_id}/raw/{evidence_id}_{filename} 패턴
    if len(parts) >= 4 and parts[0] == 'cases' and parts[2] == 'raw':
        filename = parts[3]
        # ev_xxx_filename.ext → ev_xxx 추출
        if filename.startswith('ev_') and '_' in filename[3:]:
            # ev_abc123_photo.jpg → ['ev', 'abc123', 'photo.jpg']
            ev_parts = filename.split('_', 2)
            if len(ev_parts) >= 2:
                return f"ev_{ev_parts[1]}"

    return None


def handle(event, context):
    """
    AWS Lambda Entrypoint.
    S3 이벤트를 수신하여 파일 정보를 파싱하고 AI 파이프라인을 시작합니다.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # S3 이벤트가 아닌 경우(테스트 등) 방어 로직
    if "Records" not in event:
        return {"status": "ignored", "reason": "No S3 Records found"}

    results = []

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

        except Exception as e:
            logger.error(f"Error processing record: {e}", exc_info=True)
            # 실제 운영 시에는 여기서 DLQ로 보내거나 에러를 다시 raise 해야 함
            results.append({"error": str(e), "status": "failed"})

    return {
        "statusCode": 200,
        "body": json.dumps({"results": results})
    }
