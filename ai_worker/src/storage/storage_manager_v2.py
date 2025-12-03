"""
Storage Manager V2
통합 저장소 관리자 - 법적 증거 추적 지원

핵심 기능:
- 새로운 스키마 (src/schemas) 사용
- V2 파서 통합 (line_number, page_number 추적)
- SourceLocation 기반 법적 인용 지원
- 검색 결과에 정확한 위치 정보 포함
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from .vector_store import VectorStore
from .metadata_store import MetadataStore

# 새로운 스키마 사용
from src.schemas import (
    SourceLocation,
    FileType,
    EvidenceChunk,
    EvidenceFile,
    FileMetadata,
    ParsingStatus,
    SearchResult,
    SearchResultItem,
)

# V2 파서들
from src.parsers.kakaotalk_v2 import KakaoTalkParserV2
from src.parsers.pdf_parser_v2 import PDFParserV2
from src.parsers.image_parser_v2 import ImageParserV2
from src.parsers.audio_parser_v2 import AudioParserV2

# 분석 모듈
from src.analysis.legal_analyzer import LegalAnalyzer

logger = logging.getLogger(__name__)


def get_embedding(text: str) -> List[float]:
    """
    텍스트 임베딩 생성 (OpenAI API)

    Args:
        text: 임베딩할 텍스트

    Returns:
        List[float]: 임베딩 벡터
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

        return response.data[0].embedding

    except Exception as e:
        raise Exception(f"Embedding generation failed: {e}")


class StorageManagerV2:
    """
    통합 저장소 관리자 V2

    새로운 스키마와 V2 파서를 사용하여
    법적 증거 추적이 가능한 저장소를 제공합니다.

    핵심 기능:
    - 모든 증거에 정확한 원본 위치 정보 저장
    - 검색 결과에 법적 인용 형식 포함
    - 파일 해시로 무결성 증명
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        metadata_store: Optional[MetadataStore] = None,
        auto_analyze: bool = True
    ):
        """
        StorageManagerV2 초기화

        Args:
            vector_store: VectorStore 인스턴스 (None이면 환경변수로 생성)
            metadata_store: MetadataStore 인스턴스 (None이면 환경변수로 생성)
            auto_analyze: 청크 저장 시 자동 분석 여부 (기본: True)
        """
        self.vector_store = vector_store or VectorStore()
        self.metadata_store = metadata_store or MetadataStore()
        self.auto_analyze = auto_analyze

        # V2 파서 초기화
        self.parsers = {
            FileType.KAKAOTALK: KakaoTalkParserV2(),
            FileType.PDF: PDFParserV2(),
            FileType.IMAGE: ImageParserV2(),
            FileType.AUDIO: AudioParserV2(),
        }

        # 법적 분석기 초기화
        self.legal_analyzer = LegalAnalyzer(use_ai=False)

    def process_file(
        self,
        filepath: str,
        case_id: str,
        file_type: Optional[FileType] = None
    ) -> Dict[str, Any]:
        """
        파일 처리 및 저장

        Args:
            filepath: 처리할 파일 경로
            case_id: 케이스 ID
            file_type: 파일 타입 (None이면 자동 감지)

        Returns:
            Dict: 처리 결과
                - file_id: 파일 ID
                - total_chunks: 총 청크 수
                - chunks_stored: 저장된 청크 수
                - file_hash: 파일 해시
                - parsing_errors: 파싱 오류 (있는 경우)
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # 파일 타입 감지
        if file_type is None:
            file_type = self._detect_file_type(filepath)

        parser = self.parsers.get(file_type)
        if not parser:
            raise ValueError(f"Unsupported file type: {file_type}")

        # 파일 메타데이터 생성
        file_meta = self._create_file_metadata(filepath, file_type, case_id)

        try:
            # 파싱 및 청크 생성
            chunks, parsing_result = self._parse_file(
                filepath, parser, file_type, case_id, file_meta.file_id
            )

            if not chunks:
                raise ValueError("No chunks extracted from file")

            # 청크 저장
            chunks_stored = self._store_chunks(chunks, case_id)

            # 파일 메타데이터 업데이트 및 저장
            file_meta.parsing_status = ParsingStatus.SUCCESS
            file_meta.total_chunks = len(chunks)
            self._save_file_metadata(file_meta)

            result = {
                "file_id": file_meta.file_id,
                "total_chunks": len(chunks),
                "chunks_stored": chunks_stored,
                "file_hash": file_meta.metadata.file_hash_sha256 if file_meta.metadata else None,
            }

            # 파싱 오류 정보 추가
            if hasattr(parsing_result, 'error_pages') and parsing_result.error_pages:
                result["parsing_errors"] = {
                    "type": "pages",
                    "errors": parsing_result.error_pages
                }
            elif hasattr(parsing_result, 'error_lines') and parsing_result.error_lines:
                result["parsing_errors"] = {
                    "type": "lines",
                    "errors": parsing_result.error_lines
                }

            return result

        except Exception as e:
            # 에러 발생 시 롤백
            file_meta.parsing_status = ParsingStatus.FAILED
            file_meta.parsing_errors = [str(e)]
            self._save_file_metadata(file_meta)
            raise e

    def search(
        self,
        query: str,
        case_id: str,
        top_k: int = 10,
        file_types: Optional[List[FileType]] = None,
        min_confidence: int = 1
    ) -> SearchResult:
        """
        증거 검색 (법적 인용 정보 포함)

        Args:
            query: 검색 쿼리
            case_id: 케이스 ID
            top_k: 반환할 결과 개수
            file_types: 필터링할 파일 타입들
            min_confidence: 최소 신뢰도 레벨 (1-5)

        Returns:
            SearchResult: 검색 결과 (법적 인용 정보 포함)
        """
        import time
        start_time = time.time()

        # 쿼리 임베딩 생성
        query_embedding = get_embedding(query)

        # 벡터 검색
        raw_results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=top_k * 2,  # 필터링 위해 더 많이 가져옴
            where={"case_id": case_id}
        )

        # 결과를 SearchResultItem으로 변환
        items: List[SearchResultItem] = []
        for result in raw_results:
            item = self._convert_to_search_result_item(result, case_id)

            # 필터링
            if file_types and item.source_location.file_type not in file_types:
                continue
            if item.confidence_level < min_confidence:
                continue

            items.append(item)

            if len(items) >= top_k:
                break

        search_time_ms = (time.time() - start_time) * 1000

        # 필터 정보 구성
        filters_applied = {"case_id": case_id}
        if file_types:
            filters_applied["file_types"] = [ft.value for ft in file_types]
        if min_confidence > 1:
            filters_applied["min_confidence"] = min_confidence

        return SearchResult(
            query=query,
            query_type="semantic",
            items=items,
            total_count=len(items),
            filters_applied=filters_applied,
            search_time_ms=search_time_ms
        )

    def get_chunk_by_citation(
        self,
        case_id: str,
        file_name: str,
        line_number: Optional[int] = None,
        page_number: Optional[int] = None
    ) -> Optional[EvidenceChunk]:
        """
        인용 정보로 청크 조회

        예: "카톡_배우자.txt 247번째 줄"로 검색

        Args:
            case_id: 케이스 ID
            file_name: 파일명
            line_number: 라인 번호 (카카오톡용)
            page_number: 페이지 번호 (PDF용)

        Returns:
            EvidenceChunk 또는 None
        """
        # scroll을 사용하여 모든 관련 청크 가져오기
        chunks = self.vector_store.get_chunks_by_case(case_id)

        for chunk_data in chunks:
            if chunk_data.get("file_name") != file_name:
                continue

            # 라인 번호 매칭
            if line_number is not None:
                chunk_line = chunk_data.get("line_number")
                chunk_line_end = chunk_data.get("line_number_end")

                if chunk_line == line_number:
                    return self._chunk_data_to_evidence_chunk(chunk_data)
                if chunk_line_end and chunk_line <= line_number <= chunk_line_end:
                    return self._chunk_data_to_evidence_chunk(chunk_data)

            # 페이지 번호 매칭
            if page_number is not None:
                if chunk_data.get("page_number") == page_number:
                    return self._chunk_data_to_evidence_chunk(chunk_data)

        return None

    def get_context_around(
        self,
        chunk_id: str,
        case_id: str,
        context_size: int = 3
    ) -> Tuple[List[str], List[str]]:
        """
        청크 주변 컨텍스트 조회

        Args:
            chunk_id: 청크 ID
            case_id: 케이스 ID
            context_size: 앞뒤로 가져올 청크 수

        Returns:
            Tuple[List[str], List[str]]: (이전 컨텍스트, 이후 컨텍스트)
        """
        # 같은 파일의 모든 청크 가져오기
        all_chunks = self.vector_store.get_chunks_by_case(case_id)

        # chunk_id로 현재 청크 찾기
        current_chunk = None
        file_id = None
        for chunk in all_chunks:
            if chunk.get("chunk_id") == chunk_id:
                current_chunk = chunk
                file_id = chunk.get("file_id")
                break

        if not current_chunk or not file_id:
            return [], []

        # 같은 파일의 청크만 필터링하고 시간순 정렬
        file_chunks = [c for c in all_chunks if c.get("file_id") == file_id]
        file_chunks.sort(key=lambda x: x.get("timestamp", ""))

        # 현재 청크 인덱스 찾기
        current_idx = None
        for i, chunk in enumerate(file_chunks):
            if chunk.get("chunk_id") == chunk_id:
                current_idx = i
                break

        if current_idx is None:
            return [], []

        # 이전/이후 컨텍스트 추출
        context_before = []
        context_after = []

        for i in range(max(0, current_idx - context_size), current_idx):
            context_before.append(file_chunks[i].get("document", ""))

        for i in range(current_idx + 1, min(len(file_chunks), current_idx + context_size + 1)):
            context_after.append(file_chunks[i].get("document", ""))

        return context_before, context_after

    # ========== Private Methods ==========

    def _detect_file_type(self, filepath: str) -> FileType:
        """파일 타입 자동 감지"""
        path = Path(filepath)
        name_lower = path.name.lower()
        ext = path.suffix.lower()

        # 파일명으로 카카오톡 판단
        if "kakao" in name_lower or "카카오" in name_lower or "카톡" in name_lower:
            return FileType.KAKAOTALK

        # 확장자로 판단
        ext_map = {
            ".pdf": FileType.PDF,
            ".jpg": FileType.IMAGE,
            ".jpeg": FileType.IMAGE,
            ".png": FileType.IMAGE,
            ".heic": FileType.IMAGE,
            ".mp3": FileType.AUDIO,
            ".m4a": FileType.AUDIO,
            ".wav": FileType.AUDIO,
            ".txt": FileType.TEXT,
        }

        return ext_map.get(ext, FileType.TEXT)

    def _create_file_metadata(
        self,
        filepath: str,
        file_type: FileType,
        case_id: str
    ) -> EvidenceFile:
        """파일 메타데이터 생성"""
        import hashlib
        path = Path(filepath)

        # 파일 메타데이터 추출 (해시, 크기 등)
        metadata = None
        parser = self.parsers.get(file_type)
        if parser and hasattr(parser, 'get_file_metadata'):
            try:
                metadata = parser.get_file_metadata(filepath)
            except Exception:
                pass

        # 메타데이터가 없으면 기본값 생성
        if metadata is None:
            # 파일 해시 계산
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            file_hash = sha256_hash.hexdigest()
            file_size = path.stat().st_size

            metadata = FileMetadata(
                file_hash_sha256=file_hash,
                file_size_bytes=file_size
            )

        return EvidenceFile(
            filename=path.name,
            file_type=file_type,
            case_id=case_id,
            metadata=metadata,
            parsing_status=ParsingStatus.PROCESSING
        )

    def _parse_file(
        self,
        filepath: str,
        parser,
        file_type: FileType,
        case_id: str,
        file_id: str
    ) -> Tuple[List[EvidenceChunk], Any]:
        """파일 파싱 및 청크 생성"""
        if file_type == FileType.KAKAOTALK:
            return parser.parse_to_chunks(filepath, case_id, file_id)
        elif file_type == FileType.PDF:
            return parser.parse_to_chunks(filepath, case_id, file_id)
        elif file_type == FileType.IMAGE:
            return parser.parse_to_chunks(filepath, case_id, file_id)
        elif file_type == FileType.AUDIO:
            return parser.parse_to_chunks(filepath, case_id, file_id)
        else:
            raise ValueError(f"Unsupported file type for parsing: {file_type}")

    def _store_chunks(
        self,
        chunks: List[EvidenceChunk],
        case_id: str
    ) -> int:
        """청크들을 벡터 저장소에 저장 (자동 분석 포함)"""
        stored_count = 0

        # 자동 분석 실행
        if self.auto_analyze:
            chunks = self.legal_analyzer.analyze_batch(chunks)

        for chunk in chunks:
            try:
                # 임베딩 생성
                embedding = get_embedding(chunk.content)

                # Qdrant payload 구성 (SourceLocation 정보 포함)
                payload = chunk.to_search_payload()

                # 추가 위치 정보
                if chunk.source_location.line_number_end:
                    payload["line_number_end"] = chunk.source_location.line_number_end
                if chunk.source_location.segment_start_sec is not None:
                    payload["segment_start_sec"] = chunk.source_location.segment_start_sec
                if chunk.source_location.segment_end_sec is not None:
                    payload["segment_end_sec"] = chunk.source_location.segment_end_sec
                if chunk.source_location.image_index:
                    payload["image_index"] = chunk.source_location.image_index

                # 인용 형식 저장
                payload["citation"] = chunk.source_location.to_citation()

                # 분석 결과 저장
                if chunk.legal_analysis:
                    payload["reasoning"] = chunk.legal_analysis.reasoning
                    payload["matched_keywords"] = chunk.legal_analysis.matched_keywords
                    payload["requires_human_review"] = chunk.legal_analysis.requires_human_review

                # 벡터 저장
                vector_id = self.vector_store.add_evidence(
                    text=chunk.content,
                    embedding=embedding,
                    metadata=payload
                )

                chunk.vector_id = vector_id
                stored_count += 1

            except Exception as e:
                logger.error(f"Failed to store chunk {chunk.chunk_id}: {e}")
                continue

        return stored_count

    def _save_file_metadata(self, file_meta: EvidenceFile) -> None:
        """파일 메타데이터를 DynamoDB에 저장"""
        # 기존 스키마 형식으로 변환
        from .schemas import EvidenceFile as OldEvidenceFile

        old_format = OldEvidenceFile(
            file_id=file_meta.file_id,
            filename=file_meta.filename,
            file_type=file_meta.file_type.value if isinstance(file_meta.file_type, FileType) else file_meta.file_type,
            total_messages=file_meta.total_chunks,
            case_id=file_meta.case_id,
            filepath=file_meta.s3_key  # S3 경로 사용
        )

        self.metadata_store.save_file(old_format)

    def _convert_to_search_result_item(
        self,
        result: Dict[str, Any],
        case_id: str
    ) -> SearchResultItem:
        """벡터 검색 결과를 SearchResultItem으로 변환"""
        metadata = result.get("metadata", {})
        document = result.get("document", "")

        # SourceLocation 복원
        file_type_str = metadata.get("file_type", "text")
        file_type = FileType(file_type_str) if file_type_str in [ft.value for ft in FileType] else FileType.TEXT

        source_location = SourceLocation(
            file_name=metadata.get("file_name", "unknown"),
            file_type=file_type,
            line_number=metadata.get("line_number"),
            line_number_end=metadata.get("line_number_end"),
            page_number=metadata.get("page_number"),
            segment_start_sec=metadata.get("segment_start_sec"),
            segment_end_sec=metadata.get("segment_end_sec"),
            image_index=metadata.get("image_index")
        )

        # 타임스탬프 파싱
        timestamp = None
        ts_str = metadata.get("timestamp")
        if ts_str:
            try:
                timestamp = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                pass

        # 법적 카테고리
        legal_categories = metadata.get("legal_categories", [])
        confidence_level = metadata.get("confidence_level", 1)

        # 인용 형식 (저장된 값 사용 또는 생성)
        citation = metadata.get("citation") or source_location.to_citation()

        return SearchResultItem(
            chunk_id=metadata.get("chunk_id", result.get("id", "")),
            file_id=metadata.get("file_id", ""),
            case_id=case_id,
            source_location=source_location,
            citation=citation,
            content=document,
            sender=metadata.get("sender"),
            timestamp=timestamp,
            legal_categories=legal_categories,
            confidence_level=confidence_level,
            relevance_score=1.0 - result.get("distance", 0),
            match_reason="semantic_similarity"
        )

    def _chunk_data_to_evidence_chunk(self, chunk_data: Dict[str, Any]) -> EvidenceChunk:
        """Qdrant 데이터를 EvidenceChunk로 변환"""
        file_type_str = chunk_data.get("file_type", "text")
        file_type = FileType(file_type_str) if file_type_str in [ft.value for ft in FileType] else FileType.TEXT

        source_location = SourceLocation(
            file_name=chunk_data.get("file_name", "unknown"),
            file_type=file_type,
            line_number=chunk_data.get("line_number"),
            line_number_end=chunk_data.get("line_number_end"),
            page_number=chunk_data.get("page_number"),
            segment_start_sec=chunk_data.get("segment_start_sec"),
            segment_end_sec=chunk_data.get("segment_end_sec"),
            image_index=chunk_data.get("image_index")
        )

        timestamp = None
        ts_str = chunk_data.get("timestamp")
        if ts_str:
            try:
                timestamp = datetime.fromisoformat(ts_str)
            except (ValueError, TypeError):
                pass

        return EvidenceChunk(
            chunk_id=chunk_data.get("chunk_id", chunk_data.get("id", "")),
            file_id=chunk_data.get("file_id", ""),
            case_id=chunk_data.get("case_id", ""),
            source_location=source_location,
            content=chunk_data.get("document", ""),
            content_hash=chunk_data.get("content_hash", ""),
            sender=chunk_data.get("sender"),
            timestamp=timestamp,
            vector_id=chunk_data.get("id")
        )
