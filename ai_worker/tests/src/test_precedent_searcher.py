"""
PrecedentSearcher 테스트

유사 판례 검색 모듈의 단위 테스트
"""

import pytest
from unittest.mock import patch, MagicMock

from src.analysis.precedent_searcher import (
    PrecedentSearcher,
    PrecedentCase,
    search_similar_cases,
    FAULT_TYPE_QUERIES,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_qdrant_client():
    """Qdrant 클라이언트 Mock"""
    client = MagicMock()

    # get_collections mock
    collection_mock = MagicMock()
    collection_mock.name = "leh_legal_knowledge"
    client.get_collections.return_value.collections = [collection_mock]

    # get_collection mock (for is_available)
    client.get_collection.return_value.points_count = 10

    return client


@pytest.fixture
def mock_embedding():
    """OpenAI 임베딩 Mock"""
    return [0.1] * 1536  # text-embedding-3-small 차원


def make_mock_search_hit(
    point_id: str = "point-001",
    score: float = 0.85,
    content: str = "외도로 인한 이혼 재산분할 60:40 판결",
    case_number: str = "2023드합1234",
    court: str = "서울가정법원",
    doc_type: str = "case_law",
):
    """Mock 검색 결과 생성"""
    hit = MagicMock()
    hit.id = point_id
    hit.score = score
    hit.payload = {
        "document": content,
        "content": content,
        "case_number": case_number,
        "court": court,
        "doc_type": doc_type,
        "decision_date": "2023-06-15",
        "summary": content[:100],
    }
    return hit


# =============================================================================
# PrecedentCase 테스트
# =============================================================================

class TestPrecedentCase:
    """PrecedentCase 데이터클래스 테스트"""

    def test_basic_creation(self):
        """기본 생성"""
        case = PrecedentCase(
            case_ref="서울가정법원 2023드합1234",
            similarity_score=0.85,
            division_ratio="60:40",
            key_factors=["외도", "폭력"],
        )
        assert case.case_ref == "서울가정법원 2023드합1234"
        assert case.similarity_score == 0.85

    def test_to_dict(self):
        """딕셔너리 변환"""
        case = PrecedentCase(
            case_ref="서울가정법원 2023드합1234",
            similarity_score=0.8567,
            division_ratio="60:40",
            key_factors=["외도"],
            summary="판결 요지",
        )
        d = case.to_dict()

        assert d["case_ref"] == "서울가정법원 2023드합1234"
        assert d["similarity_score"] == 0.86  # 반올림
        assert d["division_ratio"] == "60:40"
        assert d["key_factors"] == ["외도"]


# =============================================================================
# FAULT_TYPE_QUERIES 테스트
# =============================================================================

class TestFaultTypeQueries:
    """유책사유 쿼리 매핑 테스트"""

    def test_all_fault_types_have_queries(self):
        """모든 유책사유에 쿼리가 정의되어 있는지"""
        expected_types = [
            "adultery", "violence", "verbal_abuse", "economic_abuse",
            "desertion", "financial_misconduct", "child_abuse", "substance_abuse"
        ]
        for fault_type in expected_types:
            assert fault_type in FAULT_TYPE_QUERIES
            assert len(FAULT_TYPE_QUERIES[fault_type]) > 0

    def test_adultery_query_contains_keywords(self):
        """부정행위 쿼리 키워드 확인"""
        query = FAULT_TYPE_QUERIES["adultery"]
        assert "외도" in query or "부정행위" in query


# =============================================================================
# PrecedentSearcher 초기화 테스트
# =============================================================================

class TestPrecedentSearcherInit:
    """PrecedentSearcher 초기화 테스트"""

    def test_default_init(self):
        """기본 초기화 (환경변수 사용)"""
        with patch.dict("os.environ", {"QDRANT_URL": "http://test:6333"}):
            searcher = PrecedentSearcher()
            assert searcher.collection_name == "leh_legal_knowledge"

    def test_custom_collection(self):
        """커스텀 컬렉션명"""
        searcher = PrecedentSearcher(
            url="http://test:6333",
            collection_name="custom_collection"
        )
        assert searcher.collection_name == "custom_collection"


# =============================================================================
# 쿼리 빌드 테스트
# =============================================================================

class TestBuildQuery:
    """쿼리 생성 테스트"""

    def test_single_fault_type(self):
        """단일 유책사유 쿼리"""
        searcher = PrecedentSearcher(url="http://test:6333")
        query = searcher._build_query_from_fault_types(["adultery"])
        assert "외도" in query or "부정행위" in query

    def test_multiple_fault_types(self):
        """여러 유책사유 쿼리"""
        searcher = PrecedentSearcher(url="http://test:6333")
        query = searcher._build_query_from_fault_types(["adultery", "violence"])
        assert "재산분할" in query

    def test_empty_fault_types(self):
        """빈 유책사유 목록"""
        searcher = PrecedentSearcher(url="http://test:6333")
        query = searcher._build_query_from_fault_types([])
        assert "이혼 재산분할" in query

    def test_unknown_fault_type(self):
        """알 수 없는 유책사유"""
        searcher = PrecedentSearcher(url="http://test:6333")
        query = searcher._build_query_from_fault_types(["unknown_type"])
        assert "이혼 재산분할" in query


# =============================================================================
# 분할 비율 추출 테스트
# =============================================================================

class TestExtractDivisionRatio:
    """분할 비율 추출 테스트"""

    def test_colon_format(self):
        """콜론 형식 (60:40)"""
        searcher = PrecedentSearcher(url="http://test:6333")
        text = "재산분할 비율 60:40으로 판결"
        ratio = searcher._extract_division_ratio(text)
        assert ratio == "60:40"

    def test_korean_format(self):
        """한글 형식 (60대40)"""
        searcher = PrecedentSearcher(url="http://test:6333")
        text = "원고 60대40 비율로 분할"
        ratio = searcher._extract_division_ratio(text)
        assert ratio == "60:40"

    def test_no_ratio_returns_default(self):
        """비율 없으면 기본값"""
        searcher = PrecedentSearcher(url="http://test:6333")
        text = "재산분할 판결"
        ratio = searcher._extract_division_ratio(text)
        assert ratio == "50:50"


# =============================================================================
# 주요 요인 추출 테스트
# =============================================================================

class TestExtractKeyFactors:
    """주요 요인 추출 테스트"""

    def test_extract_adultery(self):
        """외도 키워드 추출"""
        searcher = PrecedentSearcher(url="http://test:6333")
        text = "피고의 외도로 인한 이혼"
        factors = searcher._extract_key_factors(text, ["adultery"])
        assert "외도" in factors

    def test_extract_violence(self):
        """폭력 키워드 추출"""
        searcher = PrecedentSearcher(url="http://test:6333")
        text = "가정폭력 피해자"
        factors = searcher._extract_key_factors(text, ["violence"])
        assert "폭력" in factors or "폭행" in factors

    def test_no_matching_returns_default(self):
        """매칭 없으면 기본값"""
        searcher = PrecedentSearcher(url="http://test:6333")
        text = "일반 이혼 판결"
        factors = searcher._extract_key_factors(text, [])
        assert factors == ["일반"]


# =============================================================================
# 검색 결과 파싱 테스트
# =============================================================================

class TestParseSearchResult:
    """검색 결과 파싱 테스트"""

    def test_parse_full_result(self):
        """전체 정보가 있는 결과 파싱"""
        searcher = PrecedentSearcher(url="http://test:6333")
        hit = make_mock_search_hit(
            score=0.85,
            content="외도로 인한 이혼 60:40 판결",
            case_number="2023드합1234",
            court="서울가정법원",
        )
        result = searcher._parse_search_result(hit, ["adultery"])

        assert "서울가정법원" in result.case_ref
        assert result.similarity_score == 0.85
        assert result.division_ratio == "60:40"
        assert "외도" in result.key_factors

    def test_parse_minimal_result(self):
        """최소 정보만 있는 결과 파싱"""
        searcher = PrecedentSearcher(url="http://test:6333")
        hit = MagicMock()
        hit.id = "point-001"
        hit.score = 0.70
        hit.payload = {"document": "이혼 판결"}

        result = searcher._parse_search_result(hit, [])

        assert result.case_ref is not None
        assert result.similarity_score == 0.70


# =============================================================================
# is_available 테스트
# =============================================================================

class TestIsAvailable:
    """서비스 가용성 테스트"""

    def test_available_when_collection_exists(self, mock_qdrant_client):
        """컬렉션 존재 시 True"""
        with patch.object(PrecedentSearcher, "client", mock_qdrant_client):
            searcher = PrecedentSearcher(url="http://test:6333")
            assert searcher.is_available() is True

    def test_not_available_when_no_url(self):
        """URL 없으면 False"""
        with patch.dict("os.environ", {"QDRANT_URL": ""}, clear=False):
            searcher = PrecedentSearcher(url=None)
            searcher.url = None  # 명시적으로 None 설정
            assert searcher.is_available() is False

    def test_not_available_when_collection_missing(self):
        """컬렉션 없으면 False"""
        client = MagicMock()
        client.get_collections.return_value.collections = []

        with patch.object(PrecedentSearcher, "client", client):
            searcher = PrecedentSearcher(url="http://test:6333")
            assert searcher.is_available() is False


# =============================================================================
# 검색 기능 테스트 (Mocked)
# =============================================================================

class TestSearchByFaultTypes:
    """유책사유 기반 검색 테스트"""

    def test_empty_fault_types_returns_empty(self):
        """빈 유책사유 목록은 빈 결과"""
        searcher = PrecedentSearcher(url="http://test:6333")
        results = searcher.search_by_fault_types([])
        assert results == []

    @patch("src.analysis.precedent_searcher.PrecedentSearcher._get_embedding")
    def test_search_with_results(self, mock_embedding, mock_qdrant_client):
        """검색 결과 반환"""
        mock_embedding.return_value = [0.1] * 1536

        mock_qdrant_client.search.return_value = [
            make_mock_search_hit(score=0.85),
            make_mock_search_hit(point_id="point-002", score=0.75),
        ]

        with patch.object(PrecedentSearcher, "client", mock_qdrant_client):
            searcher = PrecedentSearcher(url="http://test:6333")
            results = searcher.search_by_fault_types(["adultery"])

            assert len(results) == 2
            assert results[0].similarity_score == 0.85

    @patch("src.analysis.precedent_searcher.PrecedentSearcher._get_embedding")
    def test_search_no_results(self, mock_embedding, mock_qdrant_client):
        """검색 결과 없음"""
        mock_embedding.return_value = [0.1] * 1536
        mock_qdrant_client.search.return_value = []

        with patch.object(PrecedentSearcher, "client", mock_qdrant_client):
            searcher = PrecedentSearcher(url="http://test:6333")
            results = searcher.search_by_fault_types(["adultery"])

            assert results == []


# =============================================================================
# 간편 함수 테스트
# =============================================================================

class TestSearchSimilarCasesFunction:
    """search_similar_cases 간편 함수 테스트"""

    def test_function_returns_list(self):
        """함수가 리스트 반환"""
        # URL 없으면 빈 리스트 반환
        with patch.dict("os.environ", {"QDRANT_URL": ""}):
            results = search_similar_cases(["adultery"])
            assert isinstance(results, list)
