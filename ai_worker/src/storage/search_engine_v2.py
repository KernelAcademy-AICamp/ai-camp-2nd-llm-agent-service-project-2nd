"""
Search Engine V2
고급 검색 엔진 - 법적 인용 형식 지원

핵심 기능:
- 새로운 스키마 (src/schemas) 사용
- 법적 인용 형식 (파일명 N번째 줄) 출력
- 카테고리/신뢰도 필터링
- 컨텍스트 확장 (주변 증거 포함)
- 자연어 질의 지원
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.schemas import (
    SourceLocation,
    FileType,
    LegalCategory,
    ConfidenceLevel,
    SearchResult,
    SearchResultItem,
)

logger = logging.getLogger(__name__)


def get_embedding(text: str) -> List[float]:
    """텍스트 임베딩 생성"""
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


class SearchEngineV2:
    """
    고급 검색 엔진 V2

    법적 증거 검색에 특화된 검색 엔진입니다.
    검색 결과에 정확한 위치 정보와 법적 분류를 포함합니다.

    Usage:
        engine = SearchEngineV2(vector_store)

        # 기본 검색
        result = engine.search("외도 증거", case_id="case_001")

        # 응답 출력
        print(result.to_answer())
        # **'외도 증거'** 검색 결과: 3건
        # 1. 카톡_배우자.txt 247번째 줄 (2023-05-10 09:23) [김영희]
        #    "어제 그 사람 또 만났어..."
        #    신뢰도: Level 4, 카테고리: adultery
    """

    def __init__(self, vector_store):
        """
        Args:
            vector_store: VectorStore 인스턴스
        """
        self.vector_store = vector_store

    def search(
        self,
        query: str,
        case_id: str,
        top_k: int = 10,
        file_types: Optional[List[FileType]] = None,
        categories: Optional[List[LegalCategory]] = None,
        min_confidence: int = 1,
        sender: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        expand_context: bool = False,
        context_window: int = 2
    ) -> SearchResult:
        """
        증거 검색 (법적 인용 형식 포함)

        Args:
            query: 검색 쿼리 (자연어)
            case_id: 케이스 ID
            top_k: 반환할 결과 개수
            file_types: 파일 타입 필터 (예: [FileType.KAKAOTALK])
            categories: 법적 카테고리 필터 (예: [LegalCategory.ADULTERY])
            min_confidence: 최소 신뢰도 레벨 (1-5)
            sender: 발신자 필터
            start_date: 시작 날짜 필터
            end_date: 종료 날짜 필터
            expand_context: 컨텍스트 확장 여부
            context_window: 앞뒤로 가져올 청크 수

        Returns:
            SearchResult: 검색 결과 (법적 인용 형식 포함)
        """
        start_time = time.time()

        # 쿼리 임베딩 생성
        try:
            query_embedding = get_embedding(query)
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return SearchResult(
                query=query,
                query_type="error",
                items=[],
                total_count=0,
                summary=f"임베딩 생성 실패: {e}"
            )

        # 하이브리드 검색 사용 (네이티브 필터링)
        category_values = [c.value for c in categories] if categories else None
        file_type_values = [ft.value for ft in file_types] if file_types else None

        # hybrid_search가 있으면 사용, 없으면 기존 search 사용
        if hasattr(self.vector_store, 'hybrid_search'):
            raw_results = self.vector_store.hybrid_search(
                query_embedding=query_embedding,
                n_results=top_k * 2,  # 날짜 필터용 여유분
                case_id=case_id,
                categories=category_values,
                min_confidence=min_confidence,
                sender=sender,
                file_types=file_type_values
            )
        else:
            # 폴백: 기존 search
            raw_results = self.vector_store.search(
                query_embedding=query_embedding,
                n_results=top_k * 3,
                where={"case_id": case_id}
            )

        # SearchResultItem으로 변환
        items: List[SearchResultItem] = []
        for result in raw_results:
            item = self._convert_to_search_item(result, case_id, query)

            # 날짜 필터만 후처리 (벡터 DB에서 지원 어려움)
            if start_date and item.timestamp and item.timestamp < start_date:
                continue
            if end_date and item.timestamp and item.timestamp > end_date:
                continue

            # hybrid_search 미사용 시 추가 필터
            if not hasattr(self.vector_store, 'hybrid_search'):
                if not self._passes_filters(
                    item,
                    file_types=file_types,
                    categories=categories,
                    min_confidence=min_confidence,
                    sender=sender,
                    start_date=start_date,
                    end_date=end_date
                ):
                    continue

            items.append(item)

            if len(items) >= top_k:
                break

        # 컨텍스트 확장
        if expand_context and items:
            items = self._expand_context(items, case_id, context_window)

        # 필터 정보 구성
        filters_applied = {"case_id": case_id}
        if file_types:
            filters_applied["file_types"] = [ft.value for ft in file_types]
        if categories:
            filters_applied["categories"] = [c.value for c in categories]
        if min_confidence > 1:
            filters_applied["min_confidence"] = min_confidence
        if sender:
            filters_applied["sender"] = sender
        if start_date:
            filters_applied["start_date"] = start_date.isoformat()
        if end_date:
            filters_applied["end_date"] = end_date.isoformat()

        # 검색 시간
        search_time_ms = (time.time() - start_time) * 1000

        # 요약 생성
        summary = self._generate_summary(items, query)

        return SearchResult(
            query=query,
            query_type=self._detect_query_type(query),
            items=items,
            total_count=len(items),
            filters_applied=filters_applied,
            summary=summary,
            search_time_ms=search_time_ms
        )

    def search_by_category(
        self,
        category: LegalCategory,
        case_id: str,
        top_k: int = 20,
        min_confidence: int = 1
    ) -> SearchResult:
        """
        카테고리 기반 검색

        예: "외도 증거 전체 조회"

        Args:
            category: 검색할 카테고리
            case_id: 케이스 ID
            top_k: 반환할 결과 개수
            min_confidence: 최소 신뢰도

        Returns:
            SearchResult: 해당 카테고리의 모든 증거
        """
        # 카테고리 관련 쿼리 생성
        category_queries = {
            LegalCategory.ADULTERY: "외도 불륜 부정행위",
            LegalCategory.DESERTION: "유기 가출 연락두절",
            LegalCategory.DOMESTIC_VIOLENCE: "폭력 폭행 학대",
            LegalCategory.MISTREATMENT_BY_INLAWS: "시댁 시어머니 시아버지",
            LegalCategory.FINANCIAL_MISCONDUCT: "재산 은닉 낭비",
        }

        query = category_queries.get(category, category.value)

        return self.search(
            query=query,
            case_id=case_id,
            top_k=top_k,
            categories=[category],
            min_confidence=min_confidence
        )

    def search_by_person(
        self,
        person_name: str,
        case_id: str,
        top_k: int = 20
    ) -> SearchResult:
        """
        인물 기반 검색

        예: "김영희가 보낸 메시지"

        Args:
            person_name: 인물 이름
            case_id: 케이스 ID
            top_k: 반환할 결과 개수

        Returns:
            SearchResult: 해당 인물의 메시지
        """
        return self.search(
            query=person_name,
            case_id=case_id,
            top_k=top_k,
            sender=person_name
        )

    def get_evidence_by_citation(
        self,
        file_name: str,
        case_id: str,
        line_number: Optional[int] = None,
        page_number: Optional[int] = None
    ) -> Optional[SearchResultItem]:
        """
        인용 정보로 직접 조회

        예: "카톡_배우자.txt 247번째 줄"

        Args:
            file_name: 파일명
            case_id: 케이스 ID
            line_number: 라인 번호 (카카오톡용)
            page_number: 페이지 번호 (PDF용)

        Returns:
            SearchResultItem 또는 None
        """
        # Qdrant에서 해당 케이스의 모든 청크 조회
        chunks = self.vector_store.get_chunks_by_case(case_id)

        for chunk_data in chunks:
            if chunk_data.get("file_name") != file_name:
                continue

            # 라인 번호 매칭
            if line_number is not None:
                chunk_line = chunk_data.get("line_number")
                chunk_line_end = chunk_data.get("line_number_end")

                if chunk_line == line_number:
                    return self._chunk_data_to_search_item(chunk_data, case_id)
                if chunk_line_end and chunk_line <= line_number <= chunk_line_end:
                    return self._chunk_data_to_search_item(chunk_data, case_id)

            # 페이지 번호 매칭
            if page_number is not None:
                if chunk_data.get("page_number") == page_number:
                    return self._chunk_data_to_search_item(chunk_data, case_id)

        return None

    def get_high_value_evidence(
        self,
        case_id: str,
        min_confidence: int = 4,
        top_k: int = 20
    ) -> SearchResult:
        """
        고가치 증거 조회 (Level 4-5)

        Args:
            case_id: 케이스 ID
            min_confidence: 최소 신뢰도 (기본: 4)
            top_k: 반환할 결과 개수

        Returns:
            SearchResult: 고가치 증거 목록
        """
        return self.search(
            query="증거",  # 범용 쿼리
            case_id=case_id,
            top_k=top_k,
            min_confidence=min_confidence
        )

    # ========== Private Methods ==========

    def _convert_to_search_item(
        self,
        result: Dict[str, Any],
        case_id: str,
        query: str
    ) -> SearchResultItem:
        """벡터 검색 결과를 SearchResultItem으로 변환"""
        metadata = result.get("metadata", {})
        document = result.get("document", "")

        # SourceLocation 복원
        file_type_str = metadata.get("file_type", "text")
        try:
            file_type = FileType(file_type_str)
        except ValueError:
            file_type = FileType.TEXT

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
        legal_categories = []
        cats = metadata.get("legal_categories", [])
        for cat in cats:
            try:
                legal_categories.append(LegalCategory(cat))
            except ValueError:
                pass

        # 신뢰도
        conf_level = metadata.get("confidence_level", 1)
        try:
            confidence_level = ConfidenceLevel(conf_level)
        except ValueError:
            confidence_level = ConfidenceLevel.UNCERTAIN

        # 인용 형식
        citation = metadata.get("citation") or source_location.to_citation()

        # 하이라이트 생성
        content_highlight = self._highlight_query(document, query)

        # 관련성 점수 (distance를 score로 변환)
        relevance_score = 1.0 - result.get("distance", 0)

        return SearchResultItem(
            chunk_id=metadata.get("chunk_id", result.get("id", "")),
            file_id=metadata.get("file_id", ""),
            case_id=case_id,
            source_location=source_location,
            citation=citation,
            content=document,
            content_highlight=content_highlight,
            sender=metadata.get("sender"),
            timestamp=timestamp,
            legal_categories=legal_categories,
            confidence_level=confidence_level,
            relevance_score=round(relevance_score, 3),
            match_reason=metadata.get("reasoning", "semantic_similarity")
        )

    def _chunk_data_to_search_item(
        self,
        chunk_data: Dict[str, Any],
        case_id: str
    ) -> SearchResultItem:
        """Qdrant 청크 데이터를 SearchResultItem으로 변환"""
        file_type_str = chunk_data.get("file_type", "text")
        try:
            file_type = FileType(file_type_str)
        except ValueError:
            file_type = FileType.TEXT

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

        legal_categories = []
        for cat in chunk_data.get("legal_categories", []):
            try:
                legal_categories.append(LegalCategory(cat))
            except ValueError:
                pass

        conf_level = chunk_data.get("confidence_level", 1)
        try:
            confidence_level = ConfidenceLevel(conf_level)
        except ValueError:
            confidence_level = ConfidenceLevel.UNCERTAIN

        citation = chunk_data.get("citation") or source_location.to_citation()

        return SearchResultItem(
            chunk_id=chunk_data.get("chunk_id", chunk_data.get("id", "")),
            file_id=chunk_data.get("file_id", ""),
            case_id=case_id,
            source_location=source_location,
            citation=citation,
            content=chunk_data.get("document", ""),
            sender=chunk_data.get("sender"),
            timestamp=timestamp,
            legal_categories=legal_categories,
            confidence_level=confidence_level,
            relevance_score=1.0,
            match_reason="direct_lookup"
        )

    def _passes_filters(
        self,
        item: SearchResultItem,
        file_types: Optional[List[FileType]] = None,
        categories: Optional[List[LegalCategory]] = None,
        min_confidence: int = 1,
        sender: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bool:
        """필터 조건 통과 여부 확인"""
        # 파일 타입 필터
        if file_types and item.source_location.file_type not in file_types:
            return False

        # 카테고리 필터
        if categories:
            if not any(cat in item.legal_categories for cat in categories):
                return False

        # 신뢰도 필터
        item_confidence = (
            item.confidence_level.value
            if hasattr(item.confidence_level, 'value')
            else item.confidence_level
        )
        if item_confidence < min_confidence:
            return False

        # 발신자 필터
        if sender and item.sender != sender:
            return False

        # 날짜 필터
        if item.timestamp:
            if start_date and item.timestamp < start_date:
                return False
            if end_date and item.timestamp > end_date:
                return False

        return True

    def _expand_context(
        self,
        items: List[SearchResultItem],
        case_id: str,
        context_window: int
    ) -> List[SearchResultItem]:
        """컨텍스트 확장 - 주변 청크 포함"""
        # 케이스의 모든 청크 가져오기
        all_chunks = self.vector_store.get_chunks_by_case(case_id)

        for item in items:
            # 같은 파일의 청크만 필터링
            file_chunks = [
                c for c in all_chunks
                if c.get("file_id") == item.file_id
            ]

            if not file_chunks:
                continue

            # 타임스탬프로 정렬
            file_chunks.sort(key=lambda x: x.get("timestamp", ""))

            # 현재 청크 인덱스 찾기
            current_idx = None
            for i, chunk in enumerate(file_chunks):
                if chunk.get("chunk_id") == item.chunk_id:
                    current_idx = i
                    break

            if current_idx is None:
                continue

            # 이전/이후 컨텍스트 추출
            context_before = []
            context_after = []

            for i in range(max(0, current_idx - context_window), current_idx):
                context_before.append(file_chunks[i].get("document", ""))

            for i in range(current_idx + 1, min(len(file_chunks), current_idx + context_window + 1)):
                context_after.append(file_chunks[i].get("document", ""))

            item.context_before = context_before
            item.context_after = context_after

        return items

    def _highlight_query(self, content: str, query: str) -> str:
        """쿼리 키워드 하이라이트"""
        if not query or not content:
            return content

        highlighted = content
        # 간단한 키워드 하이라이트 (** 사용)
        for word in query.split():
            if len(word) >= 2 and word in highlighted:
                highlighted = highlighted.replace(word, f"**{word}**")

        return highlighted

    def _detect_query_type(self, query: str) -> str:
        """쿼리 유형 감지"""
        query_lower = query.lower()

        # 카테고리 관련
        category_keywords = ["외도", "불륜", "폭력", "폭행", "유기", "시댁"]
        if any(kw in query_lower for kw in category_keywords):
            return "category"

        # 시간 관련
        time_keywords = ["언제", "날짜", "월", "일", "년"]
        if any(kw in query_lower for kw in time_keywords):
            return "time"

        # 인물 관련
        if "누가" in query_lower or "보낸" in query_lower:
            return "person"

        return "general"

    def _generate_summary(self, items: List[SearchResultItem], query: str) -> str:
        """검색 결과 요약 생성"""
        if not items:
            return f"'{query}'에 대한 검색 결과가 없습니다."

        # 카테고리별 카운트
        category_counts = {}
        high_value_count = 0

        for item in items:
            for cat in item.legal_categories:
                cat_name = cat.value if hasattr(cat, 'value') else cat
                category_counts[cat_name] = category_counts.get(cat_name, 0) + 1

            conf_value = (
                item.confidence_level.value
                if hasattr(item.confidence_level, 'value')
                else item.confidence_level
            )
            if conf_value >= 4:
                high_value_count += 1

        summary_parts = [f"총 {len(items)}건의 증거 발견"]

        if category_counts:
            cats_str = ", ".join([f"{k}: {v}건" for k, v in category_counts.items()])
            summary_parts.append(f"카테고리별: {cats_str}")

        if high_value_count > 0:
            summary_parts.append(f"고가치 증거(Level 4-5): {high_value_count}건")

        return ". ".join(summary_parts)
