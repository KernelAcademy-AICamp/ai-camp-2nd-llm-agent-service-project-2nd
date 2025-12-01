"""
SearchEngine Module
Advanced search functionality with filtering and context expansion
"""

from typing import List, Dict, Any, Optional
from .schemas import SearchResult


class SearchEngine:
    """
    고급 검색 엔진

    기능:
    - 벡터 유사도 검색
    - 메타데이터 필터링 (발신자, 날짜)
    - 컨텍스트 확장 (주변 청크 포함)
    """

    def __init__(self, storage_manager):
        """
        SearchEngine 초기화

        Args:
            storage_manager: StorageManager 인스턴스
        """
        self.storage = storage_manager

    def search(
        self,
        query: str,
        case_id: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        expand_context: bool = False,
        context_window: int = 2
    ) -> List[SearchResult]:
        """
        고급 검색

        Given: 검색 쿼리, 케이스 ID, 옵션
        When: 벡터 검색 → 필터링 → 컨텍스트 확장
        Then: SearchResult 리스트 반환

        Args:
            query: 검색 쿼리
            case_id: 케이스 ID
            top_k: 반환할 최대 결과 개수
            filters: 필터 옵션
                - sender: 발신자 필터
                - start_date: 시작 날짜
                - end_date: 종료 날짜
            expand_context: 컨텍스트 확장 여부
            context_window: 앞뒤로 가져올 청크 개수

        Returns:
            List[SearchResult]: 검색 결과 리스트 (거리 오름차순)
        """
        # 1. 기본 벡터 검색
        raw_results = self.storage.search(
            query=query,
            case_id=case_id,
            top_k=top_k * 2  # 필터링 후 결과가 줄어들 수 있으므로 여유분 확보
        )

        if not raw_results:
            return []

        # 2. SearchResult 객체로 변환
        search_results = []
        for result in raw_results:
            # 메타데이터에서 chunk_id 찾기
            chunk_id = result["metadata"].get("chunk_id")
            if not chunk_id:
                # chunk_id가 없으면 vector_id로 metadata에서 청크 찾기
                # 일단 건너뛰기 (vector_id로 역조회는 복잡)
                continue

            # MetadataStore에서 청크 정보 가져오기
            chunk = self.storage.metadata_store.get_chunk(chunk_id)
            if not chunk:
                continue

            search_result = SearchResult(
                chunk_id=chunk.chunk_id,
                file_id=chunk.file_id,
                content=chunk.content,
                distance=result["distance"],
                timestamp=chunk.timestamp,
                sender=chunk.sender,
                case_id=chunk.case_id,
                metadata=result["metadata"]
            )

            search_results.append(search_result)

        # 3. 필터링 적용
        if filters:
            search_results = self._apply_filters(search_results, filters)

        # 4. top_k 제한
        search_results = search_results[:top_k]

        # 5. 컨텍스트 확장
        if expand_context:
            search_results = self._expand_context(
                search_results,
                context_window=context_window
            )

        return search_results

    def _apply_filters(
        self,
        results: List[SearchResult],
        filters: Dict[str, Any]
    ) -> List[SearchResult]:
        """
        필터링 적용

        Args:
            results: 검색 결과 리스트
            filters: 필터 조건

        Returns:
            필터링된 결과
        """
        filtered = results

        # 발신자 필터
        if "sender" in filters:
            sender = filters["sender"]
            filtered = [r for r in filtered if r.sender == sender]

        # 날짜 범위 필터
        if "start_date" in filters:
            start_date = filters["start_date"]
            filtered = [r for r in filtered if r.timestamp >= start_date]

        if "end_date" in filters:
            end_date = filters["end_date"]
            filtered = [r for r in filtered if r.timestamp <= end_date]

        return filtered

    def _expand_context(
        self,
        results: List[SearchResult],
        context_window: int = 2
    ) -> List[SearchResult]:
        """
        컨텍스트 확장 - 주변 청크 포함

        Args:
            results: 검색 결과 리스트
            context_window: 앞뒤로 가져올 청크 개수

        Returns:
            컨텍스트가 추가된 결과 리스트
        """
        expanded_results = []

        for result in results:
            # 같은 파일의 모든 청크 가져오기
            file_chunks = self.storage.metadata_store.get_chunks_by_file(
                result.file_id
            )

            if not file_chunks:
                expanded_results.append(result)
                continue

            # timestamp 순으로 정렬
            file_chunks.sort(key=lambda c: c.timestamp)

            # 현재 청크의 인덱스 찾기
            current_idx = None
            for i, chunk in enumerate(file_chunks):
                if chunk.chunk_id == result.chunk_id:
                    current_idx = i
                    break

            if current_idx is None:
                expanded_results.append(result)
                continue

            # 이전 컨텍스트
            context_before = []
            for i in range(max(0, current_idx - context_window), current_idx):
                context_before.append(file_chunks[i].content)

            # 이후 컨텍스트
            context_after = []
            for i in range(current_idx + 1, min(len(file_chunks), current_idx + context_window + 1)):
                context_after.append(file_chunks[i].content)

            # SearchResult 업데이트
            result.context_before = context_before if context_before else None
            result.context_after = context_after if context_after else None

            expanded_results.append(result)

        return expanded_results
