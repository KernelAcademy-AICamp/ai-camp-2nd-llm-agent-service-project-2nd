"""
Legal Search Engine Module
법률 지식 검색 엔진
"""

from typing import List, Dict, Any, Optional
from src.storage.vector_store import VectorStore
from src.storage.storage_manager import get_embedding
from src.service_rag.schemas import LegalSearchResult


class LegalSearchEngine:
    """
    법률 지식 검색 엔진

    Given: 검색 쿼리
    When: search() 호출
    Then: 관련 법령/판례 반환

    기능:
    - 벡터 유사도 기반 검색
    - 문서 타입 필터링 (statute, case_law)
    - 메타데이터 필터링 (법원, 카테고리 등)
    """

    def __init__(
        self,
        collection_name: str = "legal_knowledge",
        persist_directory: str = "./data/legal_vectors"
    ):
        """
        초기화

        Args:
            collection_name: 벡터 DB 컬렉션명
            persist_directory: 벡터 DB 저장 경로
        """
        self.vector_store = VectorStore(
            collection_name=collection_name,
            persist_directory=persist_directory
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        doc_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[LegalSearchResult]:
        """
        법률 지식 검색

        Given: 검색 쿼리 + 필터
        When: 벡터 유사도 검색 실행
        Then: 관련 법령/판례 반환

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 개수
            doc_type: 문서 타입 필터 ("statute" or "case_law")
            filters: 추가 메타데이터 필터

        Returns:
            List[LegalSearchResult]: 검색 결과 리스트
        """
        # 쿼리 임베딩 생성
        query_embedding = get_embedding(query)

        # VectorStore 검색
        raw_results = self.vector_store.search(query_embedding, top_k=top_k * 2)

        # LegalSearchResult로 변환
        search_results = []
        for result in raw_results:
            metadata = result.get("metadata", {})
            search_result = LegalSearchResult(
                chunk_id=result["id"],
                doc_type=metadata.get("doc_type", ""),
                doc_id=metadata.get("doc_id", ""),
                content=metadata.get("content", ""),
                distance=result["distance"],
                metadata=metadata
            )
            search_results.append(search_result)

        # doc_type 필터 적용
        if doc_type:
            search_results = [r for r in search_results if r.doc_type == doc_type]

        # 추가 필터 적용
        if filters:
            search_results = self._apply_filters(search_results, filters)

        # top_k 제한
        return search_results[:top_k]

    def search_statutes(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[LegalSearchResult]:
        """
        법령 전용 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 개수
            category: 법령 카테고리 필터

        Returns:
            List[LegalSearchResult]: 법령 검색 결과
        """
        filters = {"category": category} if category else None
        return self.search(query, top_k=top_k, doc_type="statute", filters=filters)

    def search_cases(
        self,
        query: str,
        top_k: int = 5,
        court: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[LegalSearchResult]:
        """
        판례 전용 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 개수
            court: 법원 필터
            category: 사건 카테고리 필터

        Returns:
            List[LegalSearchResult]: 판례 검색 결과
        """
        filters = {}
        if court:
            filters["court"] = court
        if category:
            filters["category"] = category

        return self.search(
            query,
            top_k=top_k,
            doc_type="case_law",
            filters=filters if filters else None
        )

    def _apply_filters(
        self,
        results: List[LegalSearchResult],
        filters: Dict[str, Any]
    ) -> List[LegalSearchResult]:
        """
        메타데이터 필터 적용

        Args:
            results: 검색 결과 리스트
            filters: 필터 딕셔너리

        Returns:
            List[LegalSearchResult]: 필터링된 결과
        """
        filtered = results

        for key, value in filters.items():
            filtered = [
                r for r in filtered
                if r.metadata.get(key) == value
            ]

        return filtered
