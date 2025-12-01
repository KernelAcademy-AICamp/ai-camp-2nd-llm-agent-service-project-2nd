"""
Test suite for LegalSearchEngine
Basic tests for legal knowledge search
"""

from unittest.mock import Mock, patch
from src.service_rag.legal_search import LegalSearchEngine
from src.service_rag.schemas import LegalSearchResult


class TestLegalSearchEngine:
    """Test LegalSearchEngine"""

    @patch('src.service_rag.legal_search.VectorStore')
    def test_search_engine_creation(self, mock_vector_store):
        """LegalSearchEngine 생성 테스트"""
        engine = LegalSearchEngine()

        assert engine is not None
        assert hasattr(engine, 'vector_store')

    @patch('src.service_rag.legal_search.VectorStore')
    @patch('src.service_rag.legal_search.get_embedding')
    def test_search(self, mock_embedding, mock_vector_store):
        """기본 검색 테스트"""
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store_instance = Mock()
        mock_vector_store.return_value = mock_vector_store_instance

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

    @patch('src.service_rag.legal_search.VectorStore')
    @patch('src.service_rag.legal_search.get_embedding')
    def test_search_statutes_only(self, mock_embedding, mock_vector_store):
        """법령 전용 검색 테스트"""
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store_instance = Mock()
        mock_vector_store.return_value = mock_vector_store_instance

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

    @patch('src.service_rag.legal_search.VectorStore')
    @patch('src.service_rag.legal_search.get_embedding')
    def test_search_cases_only(self, mock_embedding, mock_vector_store):
        """판례 전용 검색 테스트"""
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store_instance = Mock()
        mock_vector_store.return_value = mock_vector_store_instance

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
