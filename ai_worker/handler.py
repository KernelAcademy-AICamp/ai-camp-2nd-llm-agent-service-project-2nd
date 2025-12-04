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
from src.parsers.text import TextParser

# Optional parsers - may not be available if dependencies are missing
try:
    from src.parsers import ImageVisionParser
except ImportError:
    ImageVisionParser = None  # type: ignore

try:
    from src.parsers import PDFParser
except ImportError:
    PDFParser = None  # type: ignore

try:
    from src.parsers import AudioParser
except ImportError:
    AudioParser = None  # type: ignore

try:
    from src.parsers import VideoParser
except ImportError:
    VideoParser = None  # type: ignore
from src.storage.metadata_store import MetadataStore, DuplicateError
from src.storage.vector_store import VectorStore
from src.storage.schemas import EvidenceFile
from src.analysis.article_840_tagger import Article840Tagger
from src.analysis.summarizer import EvidenceSummarizer
from src.utils.logging_filter import SensitiveDataFilter
from src.utils.embeddings import get_embedding_with_fallback  # Embedding utility with fallback
from src.utils.hash import calculate_file_hash  # Hash utility for idempotency

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addFilter(SensitiveDataFilter())


def route_parser(file_extension: str) -> Optional[Any]:
    """
    파일 확장자에 따라 적절한 파서를 반환

    NOTE: Keep in sync with backend/app/services/evidence_service.py type_mapping

    Args:
        file_extension: 파일 확장자 (예: '.pdf', '.jpg', '.mp4')

    Returns:
        적절한 파서 인스턴스 또는 None
    """
    ext = file_extension.lower()

    # 이미지 파일 (image)
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        if ImageVisionParser is None:
            logger.warning("ImageVisionParser not available (missing dependencies)")
            return None
        return ImageVisionParser()

    # PDF 파일 (pdf)
    elif ext == '.pdf':
        if PDFParser is None:
            logger.warning("PDFParser not available (missing dependencies)")
            return None
        return PDFParser()

    # 오디오 파일 (audio)
    elif ext in ['.mp3', '.wav', '.m4a', '.aac']:
        if AudioParser is None:
            logger.warning("AudioParser not available (missing dependencies)")
            return None
        return AudioParser()

    # 비디오 파일 (video)
    elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
        if VideoParser is None:
            logger.warning("VideoParser not available (missing dependencies)")
            return None
        return VideoParser()

    # 텍스트 파일 (text) - 카톡 포함
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

        # ============================================
        # Idempotency Check - Calculate hash and check duplicates
        # ============================================
        file_hash = calculate_file_hash(local_path)
        logger.info(f"Calculated file hash: {file_hash[:16]}...")

        # Initialize metadata store for idempotency checks
        metadata_store = MetadataStore()

        # Check 1: Has this evidence_id already been processed?
        backend_evidence_id = _extract_evidence_id_from_s3_key(object_key)
        if backend_evidence_id and metadata_store.check_evidence_processed(backend_evidence_id):
            logger.info(f"Evidence {backend_evidence_id} already processed, skipping")
            return {
                "status": "skipped",
                "reason": "already_processed",
                "evidence_id": backend_evidence_id,
                "file": object_key
            }

        # Check 2: Has a file with this hash already been processed?
        existing_by_hash = metadata_store.check_hash_exists(file_hash)
        if existing_by_hash:
            logger.info(f"Duplicate file detected (hash match: {existing_by_hash.get('evidence_id')}), skipping")
            return {
                "status": "skipped",
                "reason": "duplicate_hash",
                "existing_evidence_id": existing_by_hash.get('evidence_id'),
                "file_hash": file_hash[:16],
                "file": object_key
            }

        # Check 3: Has this S3 key already been processed?
        existing_by_s3_key = metadata_store.check_s3_key_exists(object_key)
        if existing_by_s3_key and existing_by_s3_key.get('status') == 'processed':
            logger.info(f"S3 key already processed ({existing_by_s3_key.get('evidence_id')}), skipping")
            return {
                "status": "skipped",
                "reason": "already_processed_s3_key",
                "existing_evidence_id": existing_by_s3_key.get('evidence_id'),
                "file": object_key
            }

        # ============================================
        # Parsing - File is new, proceed with processing
        # ============================================

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

        # 메타데이터 저장 (DynamoDB) - metadata_store already initialized above

        # 분석 엔진 초기화
        tagger = Article840Tagger()
        summarizer = EvidenceSummarizer()
        vector_store = VectorStore()

        # 벡터 임베딩, 분석, 저장을 통합 처리
        chunk_ids = []
        tags_list = []
        all_categories = set()

        for idx, message in enumerate(parsed_result):
            chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"
            content = message.content
            timestamp = message.timestamp.isoformat() if message.timestamp else datetime.now(timezone.utc).isoformat()

            # 1. Article 840 태깅 (먼저 실행하여 메타데이터 확보)
            tagging_result = tagger.tag(message)
            categories = [cat.value for cat in tagging_result.categories]
            confidence = tagging_result.confidence
            tags_list.append({
                "categories": categories,
                "confidence": confidence,
                "matched_keywords": tagging_result.matched_keywords
            })
            all_categories.update(categories)

            # 2. Embedding 생성 (with fallback - never fails)
            embedding, is_real_embedding = get_embedding_with_fallback(content)
            if not is_real_embedding:
                logger.info(f"Using fallback embedding for chunk {idx}")

            # 3. 메타데이터 추출 (파서에서 제공하는 정보 활용)
            metadata = message.metadata if hasattr(message, 'metadata') else {}
            line_number = metadata.get("line_number")
            page_number = metadata.get("page_number")
            segment_start = metadata.get("segment_start_sec")
            segment_end = metadata.get("segment_end_sec")

            # 4. Qdrant에 벡터 + 풍부한 메타데이터 저장
            # Collection name: case_rag_{case_id} (Backend와 동일한 형식)
            collection_name = f"case_rag_{case_id}"
            vector_store.add_chunk_with_metadata(
                chunk_id=chunk_id,
                file_id=file_id,
                case_id=case_id,
                content=content,
                embedding=embedding,
                timestamp=timestamp,
                sender=message.sender,
                score=None,
                collection_name=collection_name,
                # Extended metadata
                file_name=file_path.name,
                file_type=source_type,
                legal_categories=categories if categories else None,
                confidence_level=confidence if confidence else None,
                line_number=line_number,
                page_number=page_number,
                segment_start_sec=segment_start,
                segment_end_sec=segment_end,
                is_fallback_embedding=not is_real_embedding
            )
            chunk_ids.append(chunk_id)

        logger.info(f"Indexed {len(chunk_ids)} chunks to Qdrant with full metadata")

        # AI 요약 생성 (GPT-4 기반)
        try:
            summary_result = summarizer.summarize_evidence(parsed_result, max_words=100)
            ai_summary = summary_result.summary
            logger.info(f"AI Summary generated: {ai_summary[:100]}...")
        except Exception as e:
            # 요약 실패 시 fallback
            logger.warning(f"AI summarization failed, using fallback: {e}")
            ai_summary = f"총 {len(parsed_result)}개 메시지 분석 완료. 감지된 태그: {', '.join(all_categories) if all_categories else '없음'}"

        # Article 840 태그 집계
        article_840_tags = {
            "categories": list(all_categories),
            "total_messages": len(parsed_result),
            "chunks_indexed": len(chunk_ids)
        }

        # 원문 텍스트 합치기 (STT/OCR 결과)
        # 메시지가 많으면 앞부분만 저장 (DynamoDB 400KB 제한)
        full_content = "\n".join([msg.content for msg in parsed_result])
        if len(full_content) > 50000:  # ~50KB 제한
            full_content = full_content[:50000] + "\n\n... (이하 생략, 전체 {} 메시지)".format(len(parsed_result))

        # 메타데이터 저장/업데이트 (DynamoDB)
        # 파일명에서 원본 파일명 추출 (ev_xxx_filename.ext → filename.ext)
        original_filename = file_path.name
        if original_filename.startswith('ev_') and '_' in original_filename[3:]:
            # ev_abc123_photo.jpg → photo.jpg
            parts = original_filename.split('_', 2)
            if len(parts) >= 3:
                original_filename = parts[2]

        if backend_evidence_id:
            # Backend가 생성한 레코드 업데이트 (또는 먼저 실행된 경우 생성)
            # case_id, filename 등 필수 필드도 함께 저장하여 조회 가능하게 함
            # Use update_evidence_with_hash for idempotency (conditional write)
            updated = metadata_store.update_evidence_with_hash(
                evidence_id=backend_evidence_id,
                file_hash=file_hash,
                status="processed",
                ai_summary=ai_summary,
                article_840_tags=article_840_tags,
                qdrant_id=chunk_ids[0] if chunk_ids else None,
                case_id=case_id,
                filename=original_filename,
                s3_key=object_key,
                file_type=source_type,
                content=full_content,
                skip_if_processed=True  # Idempotency: skip if already processed
            )
            if updated:
                logger.info(f"Updated Backend evidence: {backend_evidence_id} → processed (case_id={case_id})")
            else:
                logger.info(f"Evidence {backend_evidence_id} was already processed (concurrent execution)")
                return {
                    "status": "skipped",
                    "reason": "concurrent_processed",
                    "evidence_id": backend_evidence_id,
                    "file": object_key
                }
        else:
            # Fallback: 새 레코드 생성 (기존 방식)
            # Use save_file_if_not_exists for idempotency (conditional write)
            evidence_file = EvidenceFile(
                file_id=file_id,
                filename=file_path.name,
                file_type=source_type,
                parsed_at=datetime.now(timezone.utc),
                total_messages=len(parsed_result),
                case_id=case_id,
                filepath=object_key
            )
            try:
                metadata_store.save_file_if_not_exists(evidence_file, file_hash)
                logger.info(f"Created new evidence record: {file_id}")
            except DuplicateError:
                logger.info(f"Evidence {file_id} already exists (concurrent execution)")
                return {
                    "status": "skipped",
                    "reason": "concurrent_created",
                    "evidence_id": file_id,
                    "file": object_key
                }

        return {
            "status": "processed",
            "file": object_key,
            "parser_type": parser.__class__.__name__,
            "bucket": bucket_name,
            "case_id": case_id,
            "file_id": file_id,
            "evidence_id": backend_evidence_id,
            "file_hash": file_hash,  # Include hash for idempotency tracking
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
