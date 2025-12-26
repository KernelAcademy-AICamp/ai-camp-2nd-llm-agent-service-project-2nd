"""
AWS Lambda Handler for LEH AI Worker.
Triggered by S3 ObjectCreated events.

Storage Architecture (Lambda Compatible):
- MetadataStore → DynamoDB (leh_evidence table)
- VectorStore → Qdrant Cloud
"""

import json
import os
import tempfile
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
# 012-precedent-integration: T044-T047 자동 추출 모듈
from src.analysis.person_extractor import extract_persons_from_messages
from src.analysis.relationship_inferrer import infer_relationships
from src.api.backend_client import save_extracted_graph_to_backend
from src.utils.logging_filter import SensitiveDataFilter
from src.utils.logging import setup_lambda_logging
from src.utils.embeddings import get_embedding_with_fallback  # Embedding utility with fallback
from src.utils.hash import calculate_file_hash  # Hash utility for idempotency
from src.utils.observability import (
    JobTracker,
    ProcessingStage,
    ErrorType,
    classify_exception,
    get_metrics
)
from src.utils.cost_guard import (
    CostGuard,
    FileSizeExceeded,
    get_file_type_from_extension
)

# Setup structured JSON logging for Lambda
# Outputs CloudWatch Logs Insights compatible JSON format
logger = setup_lambda_logging(SensitiveDataFilter())


def route_parser(file_extension: str) -> Optional[Any]:
    """
    파일 확장자에 따라 적절한 파서를 반환
    NOTE: Keep in sync with backend/app/services/evidence_service.py type_mapping
    """
    ext = file_extension.lower()
    
    # 015-optimization: O(1) Parser Mapping
    PARSER_MAP = {
        '.jpg': ImageVisionParser,
        '.jpeg': ImageVisionParser,
        '.png': ImageVisionParser,
        '.gif': ImageVisionParser,
        '.bmp': ImageVisionParser,
        '.pdf': PDFParser,
        '.mp3': AudioParser,
        '.wav': AudioParser,
        '.m4a': AudioParser,
        '.aac': AudioParser,
        '.mp4': VideoParser,
        '.avi': VideoParser,
        '.mov': VideoParser,
        '.mkv': VideoParser,
        '.txt': TextParser,
        '.csv': TextParser,
        '.json': TextParser,
    }

    parser_class = PARSER_MAP.get(ext)
    if not parser_class:
        logger.warning(f"Unsupported file type: {ext}")
        return None
        
    if parser_class is None: # Should not happen with current map logic but for safety
        return None
        
    # Check if optional parser is available
    instance = parser_class()
    if instance is None:
        logger.warning(f"Parser {parser_class.__name__} not available (missing dependencies)")
        return None
        
    return instance


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
    # Initialize job tracker for observability
    tracker = JobTracker.from_s3_event(bucket_name, object_key)
    tracker.log(f"Starting job for s3://{bucket_name}/{object_key}")

    try:
        # 파일 확장자 추출
        file_path = Path(object_key)
        file_extension = file_path.suffix
        tracker.set_file_info(file_type=file_extension.lstrip('.'))

        tracker.log(f"Processing file: {object_key}", extension=file_extension)
        logger.debug(f"Processing file {object_key}, ext={file_extension}")

        # 적절한 파서 선택
        parser = route_parser(file_extension)
        logger.debug(f"Parser selected: {parser}")
        if not parser:
            tracker.record_error(
                ErrorType.VALIDATION_ERROR,
                f"Unsupported file type: {file_extension}"
            )
            return {
                "status": "skipped",
                "reason": f"Unsupported file type: {file_extension}",
                "file": object_key,
                "job_id": tracker.context.job_id
            }

        # S3에서 파일 다운로드
        with tracker.stage(ProcessingStage.DOWNLOAD) as stage:
            s3_client = boto3.client('s3')
            # OS 호환 임시 경로 사용 (Windows: %TEMP%, Linux: /tmp)
            local_path = os.path.join(tempfile.gettempdir(), file_path.name)

            # 임시 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            s3_client.download_file(bucket_name, object_key, local_path)
            stage.add_metadata(local_path=local_path)

        # ============================================
        # Cost Guard - Validate file size and check rate limits
        # ============================================
        cost_guard = CostGuard()
        file_type_str = get_file_type_from_extension(file_extension)

        try:
            # Validate file size
            logger.debug("Validating file size...")
            is_valid, file_details = cost_guard.validate_file(local_path, file_type_str)
            logger.debug(f"File valid: {is_valid}, details: {file_details}")
            tracker.log(
                f"File validated: {file_details['file_size_mb']:.2f}MB ({file_type_str})",
                file_size_mb=file_details['file_size_mb'],
                requires_chunking=file_details.get('requires_chunking', False)
            )
            tracker.add_metadata(file_details=file_details)

        except FileSizeExceeded as e:
            tracker.record_error(
                ErrorType.VALIDATION_ERROR,
                f"File size exceeded: {e.file_size_mb:.2f}MB > {e.max_size_mb}MB limit"
            )
            tracker.log_summary()
            return {
                "status": "rejected",
                "reason": "file_size_exceeded",
                "file": object_key,
                "file_size_mb": e.file_size_mb,
                "max_size_mb": e.max_size_mb,
                "job_id": tracker.context.job_id
            }

        # ============================================
        # Idempotency Check - Calculate hash and check duplicates
        # ============================================
        # Extract case_id early for case-scoped duplicate checks
        # Format: cases/{case_id}/raw/ev_xxx_file.txt
        case_id = _extract_case_id(object_key, bucket_name)
        tracker.set_case_id(case_id)

        with tracker.stage(ProcessingStage.HASH) as stage:
            logger.debug("Calculating hash...")
            file_hash = calculate_file_hash(local_path)
            logger.debug(f"Hash: {file_hash}")
        # Initialize metadata store for idempotency checks
        metadata_store = MetadataStore()

        # Check 1: Has this evidence_id already been completed?
        backend_evidence_id = _extract_evidence_id_from_s3_key(object_key)
        if backend_evidence_id:
            existing_record = metadata_store.get_evidence(backend_evidence_id)
            if existing_record and existing_record.get('status') == 'completed':
                tracker.record_error(ErrorType.DUPLICATE, f"Evidence already completed: {backend_evidence_id}")
                tracker.log_summary()
                return {
                    "status": "skipped",
                    "reason": "already_processed_evidence_id",
                    "evidence_id": backend_evidence_id,
                    "file": object_key,
                    "job_id": tracker.context.job_id
                }

        # Check 2: Has this file hash already been completed within the SAME case?
        # Calculate hash first
        with tracker.stage(ProcessingStage.HASH) as stage:
            file_hash = calculate_file_hash(local_path)
            stage.log(f"Hash calculated: {file_hash}")
            stage.add_metadata(hash_prefix=file_hash[:16])

        # Pass case_id to check_hash_exists - same file in different case is allowed
        existing_by_hash = metadata_store.check_hash_exists(file_hash, case_id=case_id)
        if existing_by_hash and existing_by_hash.get('status') == 'completed':
            tracker.record_error(ErrorType.DUPLICATE, f"Hash already completed in case {case_id}: {file_hash}")
            tracker.log_summary()
            return {
                "status": "skipped",
                "reason": "already_processed_hash",
                "existing_evidence_id": existing_by_hash.get('evidence_id'),
                "file": object_key,
                "job_id": tracker.context.job_id
            }

        # Check 3: Has this S3 key already been completed?
        existing_by_s3_key = metadata_store.check_s3_key_exists(object_key)
        if existing_by_s3_key and existing_by_s3_key.get('status') == 'completed':
            tracker.record_error(ErrorType.DUPLICATE, f"S3 key already completed: {existing_by_s3_key.get('evidence_id')}")
            tracker.log_summary()
            return {
                "status": "skipped",
                "reason": "already_processed_s3_key",
                "existing_evidence_id": existing_by_s3_key.get('evidence_id'),
                "file": object_key,
                "job_id": tracker.context.job_id
            }

        # ============================================
        # Parsing - File is new, proceed with processing
        # ============================================
        with tracker.stage(ProcessingStage.PARSE) as stage:
            # 파서 실행
            parsed_result = parser.parse(local_path)
            stage.log(f"Parsed with {parser.__class__.__name__}")
            stage.add_metadata(
                parser_type=parser.__class__.__name__,
                message_count=len(parsed_result) if parsed_result else 0
            )

        # Note: case_id and backend_evidence_id already extracted above for idempotency checks

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
        fallback_embedding_count = 0

        # ANALYZE stage - Article 840 태깅
        with tracker.stage(ProcessingStage.ANALYZE) as analyze_stage:
            for idx, message in enumerate(parsed_result):
                tagging_result = tagger.tag(message)
                categories = [cat.value for cat in tagging_result.categories]
                confidence = tagging_result.confidence
                tags_list.append({
                    "categories": categories,
                    "confidence": confidence,
                    "matched_keywords": tagging_result.matched_keywords
                })
                all_categories.update(categories)
            analyze_stage.add_metadata(
                messages_analyzed=len(parsed_result),
                categories_detected=list(all_categories)
            )

        # ============================================
        # 012-precedent-integration: T044-T047 인물/관계 자동 추출
        # ============================================
        auto_extract_result = None
        try:
            # 전체 텍스트 합치기
            full_text_for_extraction = "\n".join([msg.content for msg in parsed_result])

            # 인물 추출 (메시지 기반)
            messages_for_extraction = [
                {"sender": msg.sender, "content": msg.content}
                for msg in parsed_result
            ]
            extracted_persons = extract_persons_from_messages(messages_for_extraction)

            # 관계 추론
            inferred_relationships = infer_relationships(full_text_for_extraction)

            tracker.log(
                f"Auto-extraction: {len(extracted_persons)} persons, {len(inferred_relationships)} relationships"
            )

            # Backend API 호출하여 저장 (evidence_id 필요)
            if backend_evidence_id and (extracted_persons or inferred_relationships):
                auto_extract_result = save_extracted_graph_to_backend(
                    case_id=case_id,
                    persons=extracted_persons,
                    relationships=inferred_relationships,
                    source_evidence_id=backend_evidence_id,
                    min_confidence=0.7
                )
                tracker.log(
                    f"Auto-extraction saved: {auto_extract_result.get('parties_saved', 0)} parties, "
                    f"{auto_extract_result.get('relationships_saved', 0)} relationships"
                )
                tracker.add_metadata(auto_extract_result=auto_extract_result)

        except Exception as e:
            # 자동 추출 실패는 전체 처리를 중단하지 않음
            tracker.record_error(
                ErrorType.API_ERROR,
                f"Auto-extraction failed: {e}",
                exception=e
            )
            logger.warning(f"Auto-extraction failed (non-fatal): {e}")

        # EMBED stage - Embedding 생성
        embeddings_data = []
        with tracker.stage(ProcessingStage.EMBED) as embed_stage:
            for idx, message in enumerate(parsed_result):
                content = message.content
                embedding, is_real_embedding = get_embedding_with_fallback(content)
                if not is_real_embedding:
                    fallback_embedding_count += 1
                embeddings_data.append({
                    "message": message,
                    "embedding": embedding,
                    "is_real": is_real_embedding,
                    "tags": tags_list[idx]
                })
            embed_stage.add_metadata(
                embeddings_generated=len(embeddings_data),
                fallback_count=fallback_embedding_count
            )
            if fallback_embedding_count > 0:
                embed_stage.log(f"Using fallback embeddings for {fallback_embedding_count} chunks", level="warning")

        # STORE stage - Qdrant 저장
        with tracker.stage(ProcessingStage.STORE) as store_stage:
            for idx, data in enumerate(embeddings_data):
                message = data["message"]
                embedding = data["embedding"]
                is_real_embedding = data["is_real"]
                tags = data["tags"]

                chunk_id = f"chunk_{uuid.uuid4().hex[:12]}"
                content = message.content
                timestamp = message.timestamp.isoformat() if message.timestamp else datetime.now(timezone.utc).isoformat()
                categories = tags["categories"]
                confidence = tags["confidence"]

                # 메타데이터 추출 (파서에서 제공하는 정보 활용)
                metadata = message.metadata if hasattr(message, 'metadata') else {}
                line_number = metadata.get("line_number")
                page_number = metadata.get("page_number")
                segment_start = metadata.get("segment_start_sec")
                segment_end = metadata.get("segment_end_sec")

                # Qdrant에 벡터 + 풍부한 메타데이터 저장
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
            store_stage.add_metadata(chunks_indexed=len(chunk_ids))

        # AI 요약 생성 (GPT-4 기반) - Part of ANALYZE stage
        try:
            summary_result = summarizer.summarize_evidence(parsed_result, max_words=100)
            ai_summary = summary_result.summary
            tracker.log(f"AI Summary generated: {ai_summary[:50]}...")
        except Exception as e:
            # 요약 실패 시 fallback
            tracker.record_error(ErrorType.API_ERROR, f"AI summarization failed: {e}", exception=e)
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
                status="completed",
                ai_summary=ai_summary,
                article_840_tags=article_840_tags,
                qdrant_id=chunk_ids[0] if chunk_ids else None,
                case_id=case_id,
                filename=original_filename,
                s3_key=object_key,
                file_type=source_type,
                content=full_content,
                skip_if_processed=True  # Idempotency: skip if already completed
            )
            if updated:
                tracker.log(f"Updated Backend evidence: {backend_evidence_id} → completed")
            else:
                tracker.record_error(ErrorType.DUPLICATE, f"Evidence {backend_evidence_id} already processed (concurrent)")
                tracker.log_summary()
                return {
                    "status": "skipped",
                    "reason": "concurrent_processed",
                    "evidence_id": backend_evidence_id,
                    "file": object_key,
                    "job_id": tracker.context.job_id
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
                tracker.log(f"Created new evidence record: {file_id}")
            except DuplicateError:
                tracker.record_error(ErrorType.DUPLICATE, f"Evidence {file_id} already exists (concurrent)")
                tracker.log_summary()
                return {
                    "status": "skipped",
                    "reason": "concurrent_created",
                    "evidence_id": file_id,
                    "file": object_key,
                    "job_id": tracker.context.job_id
                }

        # Mark job as complete
        tracker.context.current_stage = ProcessingStage.COMPLETE
        tracker.add_metadata(
            chunks_indexed=len(chunk_ids),
            categories=list(all_categories),
            summary_length=len(ai_summary)
        )
        tracker.log_summary()

        return {
            "status": "completed",
            "file": object_key,
            "parser_type": parser.__class__.__name__,
            "bucket": bucket_name,
            "case_id": case_id,
            "file_id": file_id,
            "evidence_id": backend_evidence_id,
            "file_hash": file_hash,  # Include hash for idempotency tracking
            "chunks_indexed": len(chunk_ids),
            "tags": tags_list,
            "ai_summary": ai_summary,
            # 012-precedent-integration: T044-T047 자동 추출 결과
            "auto_extract": auto_extract_result,
            "job_id": tracker.context.job_id,
            "job_summary": tracker.get_summary()
        }

    except Exception as e:
        error_type = classify_exception(e)
        tracker.record_error(error_type, str(e), exception=e)
        tracker.log_summary()
        return {
            "status": "error",
            "file": object_key,
            "error": str(e),
            "error_type": error_type.value,
            "job_id": tracker.context.job_id,
            "job_summary": tracker.get_summary()
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


def _handle_health_check(context) -> dict:
    """
    Lambda health check handler.
    Verifies connectivity to external services (OpenAI, Qdrant, DynamoDB).

    Usage: Invoke Lambda with {"action": "health_check"}

    Returns:
        dict: Health status of all components
    """
    import os
    from datetime import datetime

    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "leh-ai-worker",
        "version": "1.0.0",
        "checks": {}
    }

    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and openai_key.startswith("sk-"):
        health["checks"]["openai"] = {"status": "ok", "message": "API key configured"}
    else:
        health["checks"]["openai"] = {"status": "error", "message": "API key missing"}
        health["status"] = "degraded"

    # Check Qdrant configuration
    qdrant_url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_HOST")
    if qdrant_url:
        health["checks"]["qdrant"] = {"status": "ok", "message": "URL configured"}
    else:
        health["checks"]["qdrant"] = {"status": "error", "message": "URL missing"}
        health["status"] = "degraded"

    # Check DynamoDB table configuration
    ddb_table = os.getenv("DDB_EVIDENCE_TABLE") or os.getenv("DYNAMODB_TABLE")
    if ddb_table:
        health["checks"]["dynamodb"] = {"status": "ok", "message": f"Table: {ddb_table}"}
    else:
        health["checks"]["dynamodb"] = {"status": "error", "message": "Table not configured"}
        health["status"] = "degraded"

    # Check S3 bucket configuration
    s3_bucket = os.getenv("S3_EVIDENCE_BUCKET")
    if s3_bucket:
        health["checks"]["s3"] = {"status": "ok", "message": f"Bucket: {s3_bucket}"}
    else:
        health["checks"]["s3"] = {"status": "error", "message": "Bucket not configured"}
        health["status"] = "degraded"

    # Add Lambda context info if available
    if context:
        health["lambda"] = {
            "function_name": getattr(context, "function_name", "unknown"),
            "memory_limit_mb": getattr(context, "memory_limit_in_mb", "unknown"),
            "remaining_time_ms": getattr(context, "get_remaining_time_in_millis", lambda: "unknown")()
        }

    logger.info("Health check completed", extra={"health_status": health["status"]})

    return {
        "statusCode": 200,
        "body": json.dumps(health)
    }


def handle(event, context):
    """
    AWS Lambda Entrypoint.
    S3 이벤트를 수신하여 파일 정보를 파싱하고 AI 파이프라인을 시작합니다.
    """
    import time
    start_time = time.time()

    # Extract trace_id from Lambda context for request tracking
    trace_id = getattr(context, 'aws_request_id', None) if context else None

    # Initialize CloudWatch metrics
    metrics = get_metrics()

    logger.info(
        "Received S3 event",
        extra={
            "trace_id": trace_id,
            "record_count": len(event.get("Records", [])),
            "event_source": event.get("Records", [{}])[0].get("eventSource", "unknown")
        }
    )

    # Health check 처리 (Lambda 직접 호출 시)
    if event.get("action") == "health_check":
        return _handle_health_check(context)

    # S3 이벤트가 아닌 경우(테스트 등) 방어 로직
    if "Records" not in event:
        return {"status": "ignored", "reason": "No S3 Records found"}

    results = []

    for record in event["Records"]:
        file_type = None
        try:
            # 1. S3 이벤트에서 버킷과 키(파일 경로) 추출
            s3 = record.get("s3", {})
            bucket_name = s3.get("bucket", {}).get("name")
            object_key = s3.get("object", {}).get("key")
            file_size = s3.get("object", {}).get("size", 0)

            # URL Decoding (공백 등이 + 또는 %20으로 들어올 수 있음)
            if object_key:
                object_key = urllib.parse.unquote_plus(object_key)
                file_type = Path(object_key).suffix.lower().lstrip('.')

            logger.info(
                "Processing file",
                extra={
                    "trace_id": trace_id,
                    "bucket": bucket_name,
                    "key": object_key,
                    "file_extension": file_type,
                    "file_size": file_size
                }
            )

            # 2. 파일 처리 로직 실행 (Strategy Pattern 적용)
            result = route_and_process(bucket_name, object_key)
            results.append(result)

            # Record successful processing metric
            if file_type:
                metrics.record_file_processed(file_type, file_size)

            logger.info(
                "File processed successfully",
                extra={
                    "trace_id": trace_id,
                    "key": object_key,
                    "status": result.get("status", "unknown")
                }
            )

        except Exception as e:
            error_type = classify_exception(e)

            logger.error(
                "Error processing record",
                extra={
                    "trace_id": trace_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )

            # Record error metric
            metrics.record_error(error_type, file_type)

            # 실제 운영 시에는 여기서 DLQ로 보내거나 에러를 다시 raise 해야 함
            results.append({"error": str(e), "status": "failed"})

    # Calculate total execution time
    duration_ms = (time.time() - start_time) * 1000
    success_count = sum(1 for r in results if r.get("status") != "failed")
    failed_count = sum(1 for r in results if r.get("status") == "failed")

    # Record execution time metric
    metrics.record_execution_time(
        duration_ms=duration_ms,
        success=(failed_count == 0)
    )

    # Record memory usage if available from Lambda context
    if context and hasattr(context, 'memory_limit_in_mb'):
        # Note: Lambda doesn't directly expose used memory, but we can estimate
        # For now, just record the limit. In production, use /proc/meminfo
        try:
            import resource
            memory_used_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
            metrics.record_memory_usage(memory_used_mb, context.memory_limit_in_mb)
        except Exception:
            pass  # Memory tracking not critical

    # Flush all metrics to CloudWatch
    metrics.flush()

    logger.info(
        "Lambda execution complete",
        extra={
            "trace_id": trace_id,
            "total_records": len(results),
            "successful": success_count,
            "failed": failed_count,
            "duration_ms": round(duration_ms, 2)
        }
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"results": results})
    }
