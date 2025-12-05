"""
Precedent Searcher - 유사 판례 검색기

재산분할 관련 유사 판례를 Qdrant에서 검색합니다.

Usage:
    from src.analysis.precedent_searcher import PrecedentSearcher, search_similar_cases

    searcher = PrecedentSearcher()
    results = searcher.search_by_fault_types(
        fault_types=["adultery", "violence"],
        top_k=5
    )
"""

import os
import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 데이터 클래스
# =============================================================================

@dataclass
class PrecedentCase:
    """
    판례 정보

    Attributes:
        case_ref: 판례 번호 (예: "서울가정법원 2023드합1234")
        similarity_score: 유사도 (0.0~1.0)
        division_ratio: 분할 비율 (예: "60:40")
        key_factors: 주요 요인 (유책사유 등)
        summary: 판결 요지
        court: 법원
        decision_date: 선고일
    """
    case_ref: str
    similarity_score: float
    division_ratio: str
    key_factors: List[str]
    summary: str = ""
    court: str = ""
    decision_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "case_ref": self.case_ref,
            "similarity_score": round(self.similarity_score, 2),
            "division_ratio": self.division_ratio,
            "key_factors": self.key_factors,
            "summary": self.summary,
            "court": self.court,
            "decision_date": self.decision_date,
        }


# =============================================================================
# 유책사유 → 검색 쿼리 매핑
# =============================================================================

FAULT_TYPE_QUERIES = {
    "adultery": "외도 부정행위 불륜 바람 재산분할",
    "violence": "가정폭력 폭행 상해 재산분할",
    "verbal_abuse": "폭언 정서적학대 언어폭력 재산분할",
    "economic_abuse": "경제적학대 생활비 재산은닉 재산분할",
    "desertion": "유기 가출 별거 재산분할",
    "financial_misconduct": "도박 채무 재산탕진 재산분할",
    "child_abuse": "자녀학대 아동학대 양육 재산분할",
    "substance_abuse": "음주 알코올 약물 재산분할",
}

# 분할 비율 추출 패턴
RATIO_PATTERNS = [
    r"(\d+)\s*:\s*(\d+)",  # 60:40, 55 : 45
    r"(\d+)%?\s*대\s*(\d+)%?",  # 60대40, 60% 대 40%
    r"원고\s*(\d+)%?\s*[,·]\s*피고\s*(\d+)%?",  # 원고 60%, 피고 40%
]


# =============================================================================
# PrecedentSearcher 클래스
# =============================================================================

class PrecedentSearcher:
    """
    유사 판례 검색기

    Qdrant의 법률 지식 컬렉션에서 유사 판례를 검색합니다.

    Usage:
        searcher = PrecedentSearcher()

        # 유책사유 기반 검색
        results = searcher.search_by_fault_types(
            fault_types=["adultery", "violence"],
            top_k=5
        )

        # 쿼리 텍스트 기반 검색
        results = searcher.search_by_query(
            query="외도로 인한 이혼 재산분할 비율",
            top_k=5
        )
    """

    DEFAULT_COLLECTION = "leh_legal_knowledge"

    def __init__(
        self,
        url: str = None,
        api_key: str = None,
        collection_name: str = None,
    ):
        """
        PrecedentSearcher 초기화

        Args:
            url: Qdrant URL (기본값: 환경변수 QDRANT_URL)
            api_key: Qdrant API Key (기본값: 환경변수 QDRANT_API_KEY)
            collection_name: 컬렉션명 (기본값: leh_legal_knowledge)
        """
        self.url = url or os.environ.get("QDRANT_URL")
        self.api_key = api_key or os.environ.get("QDRANT_API_KEY")
        self.collection_name = collection_name or self.DEFAULT_COLLECTION

        self._client: Optional[QdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        """Lazy initialization of Qdrant client"""
        if self._client is None:
            if not self.url:
                raise ValueError("QDRANT_URL is required")

            self._client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=30
            )
        return self._client

    def _get_embedding(self, text: str) -> List[float]:
        """
        텍스트 임베딩 생성

        Args:
            text: 임베딩할 텍스트

        Returns:
            List[float]: 임베딩 벡터
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    def _build_query_from_fault_types(self, fault_types: List[str]) -> str:
        """
        유책사유 목록에서 검색 쿼리 생성

        Args:
            fault_types: 유책사유 목록

        Returns:
            str: 검색 쿼리
        """
        queries = []
        for fault_type in fault_types:
            query = FAULT_TYPE_QUERIES.get(fault_type, "")
            if query:
                queries.append(query)

        if not queries:
            # 기본 쿼리
            return "이혼 재산분할 판례"

        return " ".join(queries)

    def _extract_division_ratio(self, text: str) -> str:
        """
        텍스트에서 분할 비율 추출

        Args:
            text: 판례 텍스트

        Returns:
            str: 분할 비율 (예: "60:40") 또는 "50:50"
        """
        for pattern in RATIO_PATTERNS:
            match = re.search(pattern, text)
            if match:
                ratio1, ratio2 = match.groups()
                return f"{ratio1}:{ratio2}"

        # 기본값
        return "50:50"

    def _extract_key_factors(
        self,
        text: str,
        fault_types: List[str]
    ) -> List[str]:
        """
        텍스트에서 주요 요인 추출

        Args:
            text: 판례 텍스트
            fault_types: 검색에 사용된 유책사유

        Returns:
            List[str]: 주요 요인 목록
        """
        factors = []

        # 유책사유 한글명 매핑
        factor_keywords = {
            "adultery": ["외도", "부정행위", "불륜"],
            "violence": ["폭행", "폭력", "상해"],
            "verbal_abuse": ["폭언", "학대", "모욕"],
            "economic_abuse": ["생활비", "경제적"],
            "desertion": ["유기", "가출", "별거"],
            "financial_misconduct": ["도박", "채무", "낭비"],
            "child_abuse": ["자녀", "아동", "학대"],
            "substance_abuse": ["음주", "알코올", "약물"],
        }

        for fault_type in fault_types:
            keywords = factor_keywords.get(fault_type, [])
            for keyword in keywords:
                if keyword in text and keyword not in factors:
                    factors.append(keyword)
                    break

        return factors if factors else ["일반"]

    def _parse_search_result(
        self,
        hit: Any,
        fault_types: List[str]
    ) -> PrecedentCase:
        """
        Qdrant 검색 결과를 PrecedentCase로 변환

        Args:
            hit: Qdrant 검색 결과
            fault_types: 검색에 사용된 유책사유

        Returns:
            PrecedentCase: 판례 정보
        """
        payload = hit.payload or {}

        # 필드 추출
        content = payload.get("document", payload.get("content", ""))
        case_number = payload.get("case_number", payload.get("doc_id", ""))
        court = payload.get("court", "")
        decision_date = payload.get("decision_date", "")
        summary = payload.get("summary", content[:200] if content else "")

        # 판례 번호 포맷
        if court and case_number:
            case_ref = f"{court} {case_number}"
        elif case_number:
            case_ref = case_number
        else:
            case_ref = f"판례-{hit.id}"

        # 분할 비율 추출
        division_ratio = self._extract_division_ratio(content)

        # 주요 요인 추출
        key_factors = self._extract_key_factors(content, fault_types)

        return PrecedentCase(
            case_ref=case_ref,
            similarity_score=hit.score,
            division_ratio=division_ratio,
            key_factors=key_factors,
            summary=summary[:200] if len(summary) > 200 else summary,
            court=court,
            decision_date=decision_date,
        )

    def search_by_fault_types(
        self,
        fault_types: List[str],
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> List[PrecedentCase]:
        """
        유책사유 기반 유사 판례 검색

        Args:
            fault_types: 유책사유 목록
            top_k: 반환할 최대 결과 수
            min_score: 최소 유사도 점수

        Returns:
            List[PrecedentCase]: 유사 판례 목록
        """
        if not fault_types:
            return []

        try:
            # 검색 쿼리 생성
            query_text = self._build_query_from_fault_types(fault_types)

            # 임베딩 생성
            query_embedding = self._get_embedding(query_text)

            # 컬렉션 존재 확인
            try:
                collections = self.client.get_collections().collections
                if not any(c.name == self.collection_name for c in collections):
                    logger.warning(
                        f"Collection '{self.collection_name}' not found. "
                        "No precedent data available."
                    )
                    return []
            except Exception as e:
                logger.warning(f"Failed to check collections: {e}")
                return []

            # doc_type이 case_law인 문서만 검색
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_type",
                        match=MatchValue(value="case_law")
                    )
                ]
            )

            # Qdrant 검색
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
                score_threshold=min_score,
            )

            # 결과 변환
            precedents = []
            for hit in results:
                precedent = self._parse_search_result(hit, fault_types)
                precedents.append(precedent)

            return precedents

        except Exception as e:
            logger.error(f"Precedent search failed: {e}")
            return []

    def search_by_query(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3,
        doc_type: str = "case_law",
    ) -> List[PrecedentCase]:
        """
        쿼리 텍스트 기반 유사 판례 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            min_score: 최소 유사도 점수
            doc_type: 문서 유형 필터 (case_law, statute)

        Returns:
            List[PrecedentCase]: 유사 판례 목록
        """
        try:
            # 임베딩 생성
            query_embedding = self._get_embedding(query)

            # 필터 구성
            query_filter = None
            if doc_type:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="doc_type",
                            match=MatchValue(value=doc_type)
                        )
                    ]
                )

            # Qdrant 검색
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
                score_threshold=min_score,
            )

            # 결과 변환
            precedents = []
            for hit in results:
                precedent = self._parse_search_result(hit, [])
                precedents.append(precedent)

            return precedents

        except Exception as e:
            logger.error(f"Query search failed: {e}")
            return []

    def is_available(self) -> bool:
        """
        판례 검색 서비스 사용 가능 여부 확인

        Returns:
            bool: 서비스 사용 가능하면 True
        """
        try:
            if not self.url:
                return False

            collections = self.client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                return False

            # 컬렉션에 데이터가 있는지 확인
            info = self.client.get_collection(self.collection_name)
            return info.points_count > 0

        except Exception:
            return False


# =============================================================================
# 간편 함수
# =============================================================================

def search_similar_cases(
    fault_types: List[str],
    top_k: int = 5,
) -> List[PrecedentCase]:
    """
    유사 판례 검색 간편 함수

    Args:
        fault_types: 유책사유 목록
        top_k: 반환할 최대 결과 수

    Returns:
        List[PrecedentCase]: 유사 판례 목록
    """
    searcher = PrecedentSearcher()
    return searcher.search_by_fault_types(fault_types, top_k)


# =============================================================================
# 모듈 export
# =============================================================================

__all__ = [
    "PrecedentCase",
    "PrecedentSearcher",
    "search_similar_cases",
    "FAULT_TYPE_QUERIES",
]
