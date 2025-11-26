"""
Test suite for LegalSearchEngine
Basic tests for legal knowledge search
"""

import pytest
from unittest.mock import Mock, patch
from src.service_rag.legal_search import LegalSearchEngine
from src.service_rag.schemas import LegalSearchResult


class TestLegalSearchEngine:
    """Test LegalSearchEngine"""

    @patch('src.service_rag.legal_search.get_vector_store')
    def test_search_engine_creation(self, mock_get_vector_store):
        """LegalSearchEngine 생성 테스트"""
        engine = LegalSearchEngine()

        assert engine is not None
        assert hasattr(engine, 'vector_store')

    @patch('src.service_rag.legal_search.get_vector_store')
    @patch('src.service_rag.legal_search.get_embedding')
    def test_search(self, mock_embedding, mock_get_vector_store):
        """기본 검색 테스트"""
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store_instance = Mock()
        mock_get_vector_store.return_value = mock_vector_store_instance

        # Mock search results
        mock_vector_store_instance.search.return_value = [
            {
                "id": "chunk_1",
                "distance": 0.1,
                "metadata": {
                    "doc_type": "statute",
                    "doc_id": "s001",
                    "content": "민법 제840조 내용",
                    "statute_name": "민법",
                    "article_number": "제840조"
                }
            }
        ]

        engine = LegalSearchEngine()
        results = engine.search("이혼 원인", top_k=5)

        assert len(results) > 0
        assert isinstance(results[0], LegalSearchResult)
        assert results[0].doc_type == "statute"

    @patch('src.service_rag.legal_search.get_vector_store')
    @patch('src.service_rag.legal_search.get_embedding')
    def test_search_statutes_only(self, mock_embedding, mock_get_vector_store):
        """법령 전용 검색 테스트"""
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store_instance = Mock()
        mock_get_vector_store.return_value = mock_vector_store_instance

        mock_vector_store_instance.search.return_value = [
            {
                "id": "chunk_1",
                "distance": 0.1,
                "metadata": {
                    "doc_type": "statute",
                    "doc_id": "s001",
                    "content": "법령 내용",
                    "category": "가족관계법"
                }
            }
        ]

        engine = LegalSearchEngine()
        results = engine.search_statutes("이혼", top_k=5, category="가족관계법")

        assert len(results) > 0
        assert all(r.doc_type == "statute" for r in results)

    @patch('src.service_rag.legal_search.get_vector_store')
    @patch('src.service_rag.legal_search.get_embedding')
    def test_search_cases_only(self, mock_embedding, mock_get_vector_store):
        """판례 전용 검색 테스트"""
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store_instance = Mock()
        mock_get_vector_store.return_value = mock_vector_store_instance

        mock_vector_store_instance.search.return_value = [
            {
                "id": "chunk_1",
                "distance": 0.1,
                "metadata": {
                    "doc_type": "case_law",
                    "doc_id": "c001",
                    "content": "판례 요지",
                    "court": "대법원",
                    "category": "가사"
                }
            }
        ]

        engine = LegalSearchEngine()
        results = engine.search_cases("이혼", top_k=5, court="대법원")

        assert len(results) > 0
        assert all(r.doc_type == "case_law" for r in results)


class TestFactoryIntegration:
    """Test factory integration for environment-based backend selection"""

    @patch('src.service_rag.legal_search.get_vector_store')
    @patch('src.service_rag.legal_search.get_embedding')
    def test_search_engine_uses_factory(self, mock_embedding, mock_get_vector_store):
        """
        LegalSearchEngine이 팩토리를 통해 VectorStore를 가져오는지 테스트 (RED)

        Given: 환경 변수에 따라 VectorStore가 결정됨
        When: LegalSearchEngine 생성
        Then: get_vector_store() 팩토리 함수가 호출됨
        """
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store = Mock()
        mock_get_vector_store.return_value = mock_vector_store

        engine = LegalSearchEngine()

        # 팩토리 함수가 호출되었는지 확인
        mock_get_vector_store.assert_called_once()

    @patch.dict('os.environ', {'ENVIRONMENT': 'prod', 'OPENSEARCH_ENDPOINT': 'https://test.opensearch.amazonaws.com'})
    @patch('src.service_rag.legal_search.get_vector_store')
    @patch('src.service_rag.legal_search.get_embedding')
    def test_search_engine_production_environment(self, mock_embedding, mock_get_vector_store):
        """
        프로덕션 환경에서 OpenSearch 사용 테스트 (RED)

        Given: ENVIRONMENT=prod, OPENSEARCH_ENDPOINT 설정
        When: LegalSearchEngine 생성
        Then: get_vector_store()가 호출되어 OpenSearch 반환
        """
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store = Mock()
        mock_get_vector_store.return_value = mock_vector_store

        engine = LegalSearchEngine()

        mock_get_vector_store.assert_called_once()

    @patch.dict('os.environ', {'ENVIRONMENT': 'local'}, clear=False)
    @patch('src.service_rag.legal_search.get_vector_store')
    @patch('src.service_rag.legal_search.get_embedding')
    def test_search_engine_local_environment(self, mock_embedding, mock_get_vector_store):
        """
        로컬 환경에서 ChromaDB 사용 테스트 (RED)

        Given: ENVIRONMENT=local
        When: LegalSearchEngine 생성
        Then: get_vector_store()가 호출되어 ChromaDB 반환
        """
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store = Mock()
        mock_get_vector_store.return_value = mock_vector_store

        engine = LegalSearchEngine()

        mock_get_vector_store.assert_called_once()
