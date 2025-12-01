"""
User RAG Schemas
케이스별 검색 결과 데이터 모델
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class HybridSearchResult(BaseModel):
    """
    하이브리드 검색 결과

    Attributes:
        source: 검색 소스 ("evidence" or "legal")
        result_type: 결과 타입 ("message", "statute", "case_law")
        content: 내용
        distance: 유사도 거리
        relevance_score: 관련성 점수 (0-1)
        metadata: 메타데이터
    """
    source: str  # "evidence" or "legal"
    result_type: str  # "message", "statute", "case_law"
    content: str
    distance: float
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextualSearchRequest(BaseModel):
    """
    컨텍스트 기반 검색 요청

    Attributes:
        query: 검색 쿼리
        case_id: 케이스 ID
        search_history: 이전 검색 기록 (선택)
        user_context: 사용자 컨텍스트 (선택)
    """
    query: str
    case_id: str
    search_history: List[str] = Field(default_factory=list)
    user_context: Optional[Dict[str, Any]] = None


class RankedSearchResult(BaseModel):
    """
    순위 조정된 검색 결과

    Attributes:
        result: 원본 검색 결과
        final_score: 최종 점수
        ranking_factors: 순위 결정 요인
    """
    result: HybridSearchResult
    final_score: float
    ranking_factors: Dict[str, float] = Field(default_factory=dict)
