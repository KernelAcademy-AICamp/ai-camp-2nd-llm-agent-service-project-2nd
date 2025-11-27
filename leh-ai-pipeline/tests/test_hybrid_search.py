"""
Test suite for HybridSearchEngine
Following TDD approach: RED-GREEN-REFACTOR
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.user_rag.hybrid_search import HybridSearchEngine
from src.user_rag.schemas import HybridSearchResult


class TestHybridSearchEngineInitialization:
    """Test HybridSearchEngine initialization"""

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_engine_creation(self, mock_legal_search, mock_evidence_search):
        """HybridSearchEngine 생성 테스트"""
        engine = HybridSearchEngine()

        assert engine is not None

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_engine_has_components(self, mock_legal_search, mock_evidence_search):
        """내부 검색 엔진 확인"""
        engine = HybridSearchEngine()

        assert hasattr(engine, 'evidence_search')
        assert hasattr(engine, 'legal_search')


class TestBasicHybridSearch:
    """Test basic hybrid search"""

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_search_combines_evidence_and_legal(self, mock_legal_search, mock_evidence_search):
        """증거 + 법률 지식 통합 검색 테스트"""
        # Mock evidence search results
        mock_evidence_instance = MagicMock()
        mock_evidence_search.return_value = mock_evidence_instance
        mock_evidence_instance.search.return_value = [
            Mock(
                chunk_id="chunk_1",
                content="이혼 협의 중",
                distance=0.1,
                metadata={"sender": "A", "case_id": "case_001"}
            )
        ]

        # Mock legal search results
        mock_legal_instance = MagicMock()
        mock_legal_search.return_value = mock_legal_instance
        mock_legal_instance.search.return_value = [
            Mock(
                chunk_id="legal_1",
                doc_type="statute",
                content="민법 제840조",
                distance=0.2,
                metadata={"statute_name": "민법"}
            )
        ]

        engine = HybridSearchEngine()
        results = engine.search("이혼", case_id="case_001", top_k=10)

        assert len(results) > 0
        assert any(r.source == "evidence" for r in results)
        assert any(r.source == "legal" for r in results)

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_search_returns_hybrid_results(self, mock_legal_search, mock_evidence_search):
        """HybridSearchResult 타입 반환 확인"""
        mock_evidence_instance = MagicMock()
        mock_evidence_search.return_value = mock_evidence_instance
        mock_evidence_instance.search.return_value = []

        mock_legal_instance = MagicMock()
        mock_legal_search.return_value = mock_legal_instance
        mock_legal_instance.search.return_value = [
            Mock(
                chunk_id="legal_1",
                doc_type="statute",
                content="법령",
                distance=0.1,
                metadata={}
            )
        ]

        engine = HybridSearchEngine()
        results = engine.search("test", case_id="case_001")

        assert all(isinstance(r, HybridSearchResult) for r in results)


class TestSearchFiltering:
    """Test search filtering options"""

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_evidence_only_search(self, mock_legal_search, mock_evidence_search):
        """증거만 검색 테스트"""
        mock_evidence_instance = MagicMock()
        mock_evidence_search.return_value = mock_evidence_instance
        mock_evidence_instance.search.return_value = [
            Mock(chunk_id="e1", content="증거", distance=0.1, metadata={})
        ]

        mock_legal_instance = MagicMock()
        mock_legal_search.return_value = mock_legal_instance

        engine = HybridSearchEngine()
        results = engine.search("test", case_id="case_001", search_legal=False)

        assert all(r.source == "evidence" for r in results)
        mock_legal_instance.search.assert_not_called()

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_legal_only_search(self, mock_legal_search, mock_evidence_search):
        """법률 지식만 검색 테스트"""
        mock_evidence_instance = MagicMock()
        mock_evidence_search.return_value = mock_evidence_instance

        mock_legal_instance = MagicMock()
        mock_legal_search.return_value = mock_legal_instance
        mock_legal_instance.search.return_value = [
            Mock(chunk_id="l1", doc_type="statute", content="법령", distance=0.1, metadata={})
        ]

        engine = HybridSearchEngine()
        results = engine.search("test", case_id="case_001", search_evidence=False)

        assert all(r.source == "legal" for r in results)
        mock_evidence_instance.search.assert_not_called()


class TestResultMerging:
    """Test result merging and ranking"""

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_results_sorted_by_distance(self, mock_legal_search, mock_evidence_search):
        """결과가 거리순으로 정렬되는지 테스트"""
        mock_evidence_instance = MagicMock()
        mock_evidence_search.return_value = mock_evidence_instance
        mock_evidence_instance.search.return_value = [
            Mock(chunk_id="e1", content="증거1", distance=0.5, metadata={})
        ]

        mock_legal_instance = MagicMock()
        mock_legal_search.return_value = mock_legal_instance
        mock_legal_instance.search.return_value = [
            Mock(chunk_id="l1", doc_type="statute", content="법령", distance=0.2, metadata={})
        ]

        engine = HybridSearchEngine()
        results = engine.search("test", case_id="case_001", top_k=10)

        # 거리가 작은 것(더 유사한 것)이 먼저 와야 함
        assert results[0].distance < results[1].distance

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_top_k_limit(self, mock_legal_search, mock_evidence_search):
        """top_k 제한 테스트"""
        mock_evidence_instance = MagicMock()
        mock_evidence_search.return_value = mock_evidence_instance
        mock_evidence_instance.search.return_value = [
            Mock(chunk_id=f"e{i}", content=f"증거{i}", distance=i*0.1, metadata={})
            for i in range(10)
        ]

        mock_legal_instance = MagicMock()
        mock_legal_search.return_value = mock_legal_instance
        mock_legal_instance.search.return_value = [
            Mock(chunk_id=f"l{i}", doc_type="statute", content=f"법령{i}", distance=i*0.1, metadata={})
            for i in range(10)
        ]

        engine = HybridSearchEngine()
        results = engine.search("test", case_id="case_001", top_k=5)

        assert len(results) <= 5


class TestEdgeCases:
    """Test edge cases"""

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_no_results_from_either_source(self, mock_legal_search, mock_evidence_search):
        """양쪽 모두 결과 없을 때"""
        mock_evidence_instance = MagicMock()
        mock_evidence_search.return_value = mock_evidence_instance
        mock_evidence_instance.search.return_value = []

        mock_legal_instance = MagicMock()
        mock_legal_search.return_value = mock_legal_instance
        mock_legal_instance.search.return_value = []

        engine = HybridSearchEngine()
        results = engine.search("test", case_id="case_001")

        assert len(results) == 0

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_empty_query(self, mock_legal_search, mock_evidence_search):
        """빈 쿼리 처리"""
        engine = HybridSearchEngine()

        with pytest.raises(ValueError, match="Empty query"):
            engine.search("", case_id="case_001")


class TestSearchWithWeights:
    """Test weighted hybrid search"""

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_search_with_weights_applies_evidence_weight(self, mock_legal_search, mock_evidence_search):
        """증거 가중치 적용 테스트"""
        mock_evidence_instance = MagicMock()
        mock_evidence_search.return_value = mock_evidence_instance
        mock_evidence_instance.search.return_value = [
            Mock(
                chunk_id="e1",
                content="증거1",
                distance=0.1,
                sender="A",
                timestamp=None,
                case_id="case_001",
                metadata={}
            )
        ]

        mock_legal_instance = MagicMock()
        mock_legal_search.return_value = mock_legal_instance
        mock_legal_instance.search.return_value = []

        engine = HybridSearchEngine()
        results = engine.search_with_weights(
            "test",
            case_id="case_001",
            evidence_weight=0.8,
            legal_weight=0.2
        )

        assert len(results) > 0
        # 가중치가 적용되어야 함
        assert results[0].relevance_score is not None

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_search_with_weights_applies_legal_weight(self, mock_legal_search, mock_evidence_search):
        """법률 가중치 적용 테스트"""
        mock_evidence_instance = MagicMock()
        mock_evidence_search.return_value = mock_evidence_instance
        mock_evidence_instance.search.return_value = []

        mock_legal_instance = MagicMock()
        mock_legal_search.return_value = mock_legal_instance
        mock_legal_instance.search.return_value = [
            Mock(
                chunk_id="l1",
                doc_type="statute",
                content="법령1",
                distance=0.1,
                metadata={}
            )
        ]

        engine = HybridSearchEngine()
        results = engine.search_with_weights(
            "test",
            case_id="case_001",
            evidence_weight=0.6,
            legal_weight=0.4
        )

        assert len(results) > 0
        # 법률 결과에 legal_weight가 적용됨
        assert results[0].source == "legal"

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_search_with_weights_sorts_by_relevance(self, mock_legal_search, mock_evidence_search):
        """가중치 적용 후 relevance_score 정렬 테스트"""
        mock_evidence_instance = MagicMock()
        mock_evidence_search.return_value = mock_evidence_instance
        mock_evidence_instance.search.return_value = [
            Mock(
                chunk_id="e1",
                content="증거1",
                distance=0.3,  # 낮은 유사도
                sender="A",
                timestamp=None,
                case_id="case_001",
                metadata={}
            )
        ]

        mock_legal_instance = MagicMock()
        mock_legal_search.return_value = mock_legal_instance
        mock_legal_instance.search.return_value = [
            Mock(
                chunk_id="l1",
                doc_type="statute",
                content="법령1",
                distance=0.1,  # 높은 유사도
                metadata={}
            )
        ]

        engine = HybridSearchEngine()
        results = engine.search_with_weights(
            "test",
            case_id="case_001",
            evidence_weight=0.5,
            legal_weight=0.5
        )

        # relevance_score 기준 내림차순 정렬 확인
        if len(results) > 1:
            assert results[0].relevance_score >= results[1].relevance_score


class TestInitializationWithStorageManager:
    """Test initialization with storage_manager"""

    @patch('src.user_rag.hybrid_search.SearchEngine')
    @patch('src.user_rag.hybrid_search.LegalSearchEngine')
    def test_init_with_storage_manager(self, mock_legal_search, mock_evidence_search):
        """storage_manager로 초기화 테스트"""
        mock_storage_manager = MagicMock()

        engine = HybridSearchEngine(storage_manager=mock_storage_manager)

        # SearchEngine이 storage_manager와 함께 호출되어야 함
        mock_evidence_search.assert_called_once_with(mock_storage_manager)
        assert engine is not None
