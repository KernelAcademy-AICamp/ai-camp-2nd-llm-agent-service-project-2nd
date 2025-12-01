"""
Hybrid Search Engine Module
증거 검색 + 법률 지식 검색 통합
"""

from typing import List
from src.storage.search_engine import SearchEngine
from src.service_rag.legal_search import LegalSearchEngine
from src.user_rag.schemas import HybridSearchResult


class HybridSearchEngine:
    """
    하이브리드 검색 엔진

    Given: 검색 쿼리 + case_id
    When: search() 호출
    Then: 증거 + 법률 지식 통합 검색 결과 반환

    기능:
    - 케이스 증거 검색 (SearchEngine)
    - 법률 지식 검색 (LegalSearchEngine)
    - 두 결과를 통합하여 반환
    - 거리 기준 정렬
    """

    def __init__(
        self,
        storage_manager=None,
        evidence_collection: str = "leh_evidence",
        legal_collection: str = "legal_knowledge"
    ):
        """
        초기화

        Args:
            storage_manager: StorageManager 인스턴스 (증거 검색용)
            evidence_collection: 증거 벡터 컬렉션명
            legal_collection: 법률 지식 컬렉션명
        """
        # 증거 검색 엔진
        if storage_manager:
            self.evidence_search = SearchEngine(storage_manager)
        else:
            # Mock or test mode
            self.evidence_search = SearchEngine(Mock())

        # 법률 지식 검색 엔진
        self.legal_search = LegalSearchEngine(
            collection_name=legal_collection
        )

    def search(
        self,
        query: str,
        case_id: str,
        top_k: int = 10,
        search_evidence: bool = True,
        search_legal: bool = True
    ) -> List[HybridSearchResult]:
        """
        하이브리드 검색

        Given: 쿼리 + case_id + 검색 옵션
        When: 증거 및/또는 법률 지식 검색 실행
        Then: 통합 검색 결과 반환

        Args:
            query: 검색 쿼리
            case_id: 케이스 ID
            top_k: 최대 결과 개수
            search_evidence: 증거 검색 여부
            search_legal: 법률 지식 검색 여부

        Returns:
            List[HybridSearchResult]: 통합 검색 결과

        Raises:
            ValueError: 빈 쿼리인 경우
        """
        if not query or query.strip() == "":
            raise ValueError("Empty query")

        all_results = []

        # 1. 증거 검색
        if search_evidence:
            evidence_results = self.evidence_search.search(
                query=query,
                case_id=case_id,
                top_k=top_k
            )

            for result in evidence_results:
                hybrid_result = HybridSearchResult(
                    source="evidence",
                    result_type="message",
                    content=result.content,
                    distance=result.distance,
                    relevance_score=1.0 - result.distance,  # 거리 -> 점수 변환
                    metadata={
                        "chunk_id": result.chunk_id,
                        "sender": result.sender,
                        "timestamp": result.timestamp.isoformat() if result.timestamp else None,
                        "case_id": result.case_id
                    }
                )
                all_results.append(hybrid_result)

        # 2. 법률 지식 검색
        if search_legal:
            legal_results = self.legal_search.search(
                query=query,
                top_k=top_k
            )

            for result in legal_results:
                hybrid_result = HybridSearchResult(
                    source="legal",
                    result_type=result.doc_type,  # "statute" or "case_law"
                    content=result.content,
                    distance=result.distance,
                    relevance_score=1.0 - result.distance,
                    metadata=result.metadata
                )
                all_results.append(hybrid_result)

        # 3. 거리 기준 정렬 (낮은 거리 = 높은 유사도)
        all_results.sort(key=lambda x: x.distance)

        # 4. top_k 제한
        return all_results[:top_k]

    def search_with_weights(
        self,
        query: str,
        case_id: str,
        top_k: int = 10,
        evidence_weight: float = 0.6,
        legal_weight: float = 0.4
    ) -> List[HybridSearchResult]:
        """
        가중치 기반 하이브리드 검색

        Args:
            query: 검색 쿼리
            case_id: 케이스 ID
            top_k: 최대 결과 개수
            evidence_weight: 증거 가중치
            legal_weight: 법률 지식 가중치

        Returns:
            List[HybridSearchResult]: 가중치 적용된 검색 결과
        """
        # 기본 하이브리드 검색 수행
        results = self.search(query, case_id, top_k=top_k * 2)

        # 가중치 적용
        for result in results:
            if result.source == "evidence":
                result.relevance_score *= evidence_weight
            else:
                result.relevance_score *= legal_weight

        # relevance_score 기준 재정렬
        results.sort(key=lambda x: x.relevance_score, reverse=True)

        return results[:top_k]


# Mock for testing when storage_manager is None
class Mock:
    """Mock object for testing"""
    pass
