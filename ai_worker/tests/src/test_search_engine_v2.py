"""
SearchEngineV2 테스트

Given: 검색 쿼리
When: SearchEngineV2.search() 호출
Then: SearchResult 반환 (법적 인용 형식 포함)
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.storage.search_engine_v2 import SearchEngineV2
from src.schemas import (
    SearchResult,
    SearchResultItem,
    SourceLocation,
    FileType,
    LegalCategory,
    ConfidenceLevel
)


class TestSearchEngineV2Initialization(unittest.TestCase):
    """SearchEngineV2 초기화 테스트"""

    def test_engine_creation(self):
        """Given: VectorStore 인스턴스
        When: SearchEngineV2() 생성
        Then: 검색 엔진 생성 성공"""
        mock_vector_store = Mock()
        engine = SearchEngineV2(mock_vector_store)

        self.assertIsNotNone(engine)
        self.assertEqual(engine.vector_store, mock_vector_store)


class TestSearchEngineV2PrivateMethods(unittest.TestCase):
    """Private 메소드 테스트"""

    def setUp(self):
        self.mock_vector_store = Mock()
        self.engine = SearchEngineV2(self.mock_vector_store)

    def test_detect_query_type_category(self):
        """Given: 카테고리 관련 쿼리
        When: _detect_query_type() 호출
        Then: 'category' 반환"""
        query_type = self.engine._detect_query_type("외도 증거 찾아줘")
        self.assertEqual(query_type, "category")

        query_type = self.engine._detect_query_type("폭력 관련 증거")
        self.assertEqual(query_type, "category")

    def test_detect_query_type_time(self):
        """Given: 시간 관련 쿼리
        When: _detect_query_type() 호출
        Then: 'time' 반환"""
        query_type = self.engine._detect_query_type("언제 만났어?")
        self.assertEqual(query_type, "time")

    def test_detect_query_type_person(self):
        """Given: 인물 관련 쿼리
        When: _detect_query_type() 호출
        Then: 'person' 반환"""
        query_type = self.engine._detect_query_type("누가 보낸 메시지야?")
        self.assertEqual(query_type, "person")

    def test_detect_query_type_general(self):
        """Given: 일반 쿼리
        When: _detect_query_type() 호출
        Then: 'general' 반환"""
        query_type = self.engine._detect_query_type("테스트 검색어")
        self.assertEqual(query_type, "general")

    def test_highlight_query(self):
        """Given: 내용과 쿼리
        When: _highlight_query() 호출
        Then: 키워드 하이라이트"""
        content = "외도 증거를 찾았습니다"
        query = "외도"

        highlighted = self.engine._highlight_query(content, query)
        self.assertIn("**외도**", highlighted)

    def test_generate_summary_empty(self):
        """Given: 빈 결과
        When: _generate_summary() 호출
        Then: 결과 없음 메시지"""
        summary = self.engine._generate_summary([], "테스트")
        self.assertIn("검색 결과가 없습니다", summary)

    def test_generate_summary_with_items(self):
        """Given: 검색 결과 있음
        When: _generate_summary() 호출
        Then: 통계 포함 요약"""
        # Mock SearchResultItem 생성
        mock_item = Mock()
        mock_item.legal_categories = [LegalCategory.ADULTERY]
        mock_item.confidence_level = ConfidenceLevel.STRONG

        summary = self.engine._generate_summary([mock_item], "외도")
        self.assertIn("1건", summary)


class TestSearchEngineV2Filters(unittest.TestCase):
    """필터링 테스트"""

    def setUp(self):
        self.mock_vector_store = Mock()
        self.engine = SearchEngineV2(self.mock_vector_store)

    def test_passes_filters_file_type(self):
        """Given: 파일 타입 필터
        When: _passes_filters() 호출
        Then: 일치하는 파일 타입만 통과"""
        mock_item = Mock()
        mock_item.source_location = Mock()
        mock_item.source_location.file_type = FileType.KAKAOTALK
        mock_item.legal_categories = []
        mock_item.confidence_level = Mock(value=1)
        mock_item.sender = None
        mock_item.timestamp = None

        # KAKAOTALK 타입만 허용
        result = self.engine._passes_filters(
            mock_item,
            file_types=[FileType.KAKAOTALK]
        )
        self.assertTrue(result)

        # PDF 타입만 허용 - 불통과
        result = self.engine._passes_filters(
            mock_item,
            file_types=[FileType.PDF]
        )
        self.assertFalse(result)

    def test_passes_filters_category(self):
        """Given: 카테고리 필터
        When: _passes_filters() 호출
        Then: 해당 카테고리만 통과"""
        mock_item = Mock()
        mock_item.source_location = Mock()
        mock_item.source_location.file_type = FileType.TEXT
        mock_item.legal_categories = [LegalCategory.ADULTERY]
        mock_item.confidence_level = Mock(value=1)
        mock_item.sender = None
        mock_item.timestamp = None

        # ADULTERY 카테고리만 허용
        result = self.engine._passes_filters(
            mock_item,
            categories=[LegalCategory.ADULTERY]
        )
        self.assertTrue(result)

        # DESERTION만 허용 - 불통과
        result = self.engine._passes_filters(
            mock_item,
            categories=[LegalCategory.DESERTION]
        )
        self.assertFalse(result)

    def test_passes_filters_min_confidence(self):
        """Given: 최소 신뢰도 필터
        When: _passes_filters() 호출
        Then: 신뢰도 이상만 통과"""
        mock_item = Mock()
        mock_item.source_location = Mock()
        mock_item.source_location.file_type = FileType.TEXT
        mock_item.legal_categories = []
        mock_item.confidence_level = Mock(value=3)
        mock_item.sender = None
        mock_item.timestamp = None

        # 최소 신뢰도 2 - 통과
        result = self.engine._passes_filters(mock_item, min_confidence=2)
        self.assertTrue(result)

        # 최소 신뢰도 4 - 불통과
        result = self.engine._passes_filters(mock_item, min_confidence=4)
        self.assertFalse(result)

    def test_passes_filters_sender(self):
        """Given: 발신자 필터
        When: _passes_filters() 호출
        Then: 해당 발신자만 통과"""
        mock_item = Mock()
        mock_item.source_location = Mock()
        mock_item.source_location.file_type = FileType.TEXT
        mock_item.legal_categories = []
        mock_item.confidence_level = Mock(value=1)
        mock_item.sender = "홍길동"
        mock_item.timestamp = None

        result = self.engine._passes_filters(mock_item, sender="홍길동")
        self.assertTrue(result)

        result = self.engine._passes_filters(mock_item, sender="김영희")
        self.assertFalse(result)


class TestSearchEngineV2ConvertToSearchItem(unittest.TestCase):
    """검색 결과 변환 테스트"""

    def setUp(self):
        self.mock_vector_store = Mock()
        self.engine = SearchEngineV2(self.mock_vector_store)

    def test_convert_to_search_item(self):
        """Given: 벡터 검색 결과
        When: _convert_to_search_item() 호출
        Then: SearchResultItem 반환"""
        raw_result = {
            "id": "chunk_001",
            "document": "테스트 메시지 내용",
            "distance": 0.1,
            "metadata": {
                "chunk_id": "chunk_001",
                "file_id": "file_001",
                "file_name": "test.txt",
                "file_type": "text",
                "line_number": 10,
                "sender": "홍길동",
                "timestamp": "2023-05-10T09:23:00",
                "legal_categories": ["adultery"],
                "confidence_level": 4,
                "citation": "test.txt 10번째 줄"
            }
        }

        item = self.engine._convert_to_search_item(raw_result, "case_001", "외도")

        self.assertIsInstance(item, SearchResultItem)
        self.assertEqual(item.chunk_id, "chunk_001")
        self.assertEqual(item.sender, "홍길동")
        self.assertIn(LegalCategory.ADULTERY, item.legal_categories)

    def test_convert_handles_missing_metadata(self):
        """Given: 메타데이터 일부 누락
        When: _convert_to_search_item() 호출
        Then: 기본값으로 처리"""
        raw_result = {
            "id": "chunk_001",
            "document": "테스트",
            "distance": 0.2,
            "metadata": {
                "file_name": "test.txt"
            }
        }

        item = self.engine._convert_to_search_item(raw_result, "case_001", "테스트")

        self.assertIsInstance(item, SearchResultItem)
        self.assertEqual(item.source_location.file_type, FileType.TEXT)


class TestSearchEngineV2SearchMethods(unittest.TestCase):
    """검색 메소드 테스트 (Mocked)"""

    def setUp(self):
        self.mock_vector_store = Mock()
        self.engine = SearchEngineV2(self.mock_vector_store)

    @patch('src.storage.search_engine_v2.get_embedding')
    def test_search_returns_search_result(self, mock_embedding):
        """Given: 검색 쿼리
        When: search() 호출
        Then: SearchResult 반환"""
        mock_embedding.return_value = [0.1] * 1536
        self.mock_vector_store.search.return_value = []

        result = self.engine.search(
            query="외도 증거",
            case_id="case_001",
            top_k=10
        )

        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.query, "외도 증거")

    @patch('src.storage.search_engine_v2.get_embedding')
    def test_search_with_filters(self, mock_embedding):
        """Given: 필터 옵션
        When: search() 호출
        Then: 필터가 filters_applied에 포함"""
        mock_embedding.return_value = [0.1] * 1536
        self.mock_vector_store.search.return_value = []

        result = self.engine.search(
            query="증거",
            case_id="case_001",
            categories=[LegalCategory.ADULTERY],
            min_confidence=3
        )

        self.assertIn("categories", result.filters_applied)
        self.assertIn("min_confidence", result.filters_applied)

    @patch('src.storage.search_engine_v2.get_embedding')
    def test_search_handles_embedding_error(self, mock_embedding):
        """Given: 임베딩 실패
        When: search() 호출
        Then: 에러 메시지 포함 SearchResult"""
        mock_embedding.side_effect = Exception("API Error")

        result = self.engine.search(
            query="테스트",
            case_id="case_001"
        )

        self.assertEqual(result.total_count, 0)
        self.assertIn("실패", result.summary)

    def test_search_by_category(self):
        """Given: 카테고리
        When: search_by_category() 호출
        Then: 해당 카테고리 검색"""
        with patch.object(self.engine, 'search') as mock_search:
            mock_search.return_value = SearchResult(
                query="외도",
                query_type="category",
                items=[],
                total_count=0
            )

            self.engine.search_by_category(
                category=LegalCategory.ADULTERY,
                case_id="case_001"
            )

            mock_search.assert_called_once()
            call_args = mock_search.call_args
            self.assertIn(LegalCategory.ADULTERY, call_args.kwargs.get('categories', []))

    def test_search_by_person(self):
        """Given: 인물 이름
        When: search_by_person() 호출
        Then: 해당 인물 검색"""
        with patch.object(self.engine, 'search') as mock_search:
            mock_search.return_value = SearchResult(
                query="홍길동",
                query_type="person",
                items=[],
                total_count=0
            )

            self.engine.search_by_person(
                person_name="홍길동",
                case_id="case_001"
            )

            mock_search.assert_called_once()
            call_args = mock_search.call_args
            self.assertEqual(call_args.kwargs.get('sender'), "홍길동")

    def test_get_high_value_evidence(self):
        """Given: 케이스 ID
        When: get_high_value_evidence() 호출
        Then: min_confidence=4 이상 검색"""
        with patch.object(self.engine, 'search') as mock_search:
            mock_search.return_value = SearchResult(
                query="증거",
                query_type="general",
                items=[],
                total_count=0
            )

            self.engine.get_high_value_evidence(case_id="case_001")

            mock_search.assert_called_once()
            call_args = mock_search.call_args
            self.assertGreaterEqual(call_args.kwargs.get('min_confidence', 1), 4)


class TestSearchResultFormat(unittest.TestCase):
    """SearchResult 출력 형식 테스트"""

    def test_search_result_to_answer_empty(self):
        """Given: 빈 검색 결과
        When: to_answer() 호출
        Then: 결과 없음 메시지"""
        result = SearchResult(
            query="테스트",
            query_type="general",
            items=[],
            total_count=0
        )

        answer = result.to_answer()
        self.assertIn("검색 결과가 없습니다", answer)

    def test_search_result_to_answer_with_items(self):
        """Given: 검색 결과 있음
        When: to_answer() 호출
        Then: 법적 인용 형식 포함"""
        item = SearchResultItem(
            chunk_id="chunk_001",
            file_id="file_001",
            case_id="case_001",
            source_location=SourceLocation(
                file_name="test.txt",
                file_type=FileType.TEXT,
                line_number=10
            ),
            citation="test.txt 10번째 줄",
            content="테스트 내용",
            legal_categories=[LegalCategory.ADULTERY],
            confidence_level=ConfidenceLevel.STRONG
        )

        result = SearchResult(
            query="외도",
            query_type="category",
            items=[item],
            total_count=1
        )

        answer = result.to_answer()
        self.assertIn("test.txt", answer)
        self.assertIn("10번째 줄", answer)


if __name__ == '__main__':
    unittest.main()
