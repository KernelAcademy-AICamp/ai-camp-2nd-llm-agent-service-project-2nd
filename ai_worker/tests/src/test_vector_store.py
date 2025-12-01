"""
Test suite for VectorStore (Qdrant)
Uses mocking for unit tests, real connection for integration tests
"""

import pytest
from unittest.mock import MagicMock, patch
from src.storage.vector_store import VectorStore


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    mock_client = MagicMock()
    # Mock get_collections response
    mock_client.get_collections.return_value = MagicMock(collections=[])
    return mock_client


@pytest.fixture
def vector_store(mock_qdrant_client):
    """VectorStore with mocked Qdrant client"""
    with patch.dict('os.environ', {
        'QDRANT_URL': 'http://localhost:6333',
        'QDRANT_API_KEY': 'test_key',
        'VECTOR_SIZE': '1536'
    }):
        with patch('qdrant_client.QdrantClient') as MockQdrantClient:
            MockQdrantClient.return_value = mock_qdrant_client
            store = VectorStore(
                url='http://localhost:6333',
                api_key='test_key',
                vector_size=1536
            )
            store._client = mock_qdrant_client
            store._initialized_collections.add('leh_evidence')
            return store


class TestVectorStoreInitialization:
    """Test VectorStore initialization"""

    def test_vector_store_creation(self):
        """VectorStore 생성 테스트"""
        with patch.dict('os.environ', {
            'QDRANT_URL': 'http://localhost:6333',
            'QDRANT_API_KEY': 'test_key'
        }):
            with patch('qdrant_client.QdrantClient'):
                store = VectorStore()
                assert store is not None
                assert store.url == 'http://localhost:6333'
                assert store.collection_name == 'leh_evidence'

    def test_vector_store_with_custom_params(self):
        """커스텀 파라미터로 생성 테스트"""
        with patch('qdrant_client.QdrantClient'):
            store = VectorStore(
                url='http://custom:6333',
                api_key='custom_key',
                collection_name='custom_collection',
                vector_size=768
            )
            assert store.url == 'http://custom:6333'
            assert store.collection_name == 'custom_collection'
            assert store.vector_size == 768

    def test_requires_url(self):
        """URL 필수 확인"""
        with patch.dict('os.environ', {'QDRANT_URL': ''}, clear=True):
            with pytest.raises(ValueError, match="QDRANT_URL is required"):
                VectorStore(url=None)


class TestVectorStoreAddEvidence:
    """Test adding evidence to vector store"""

    def test_add_single_evidence(self, vector_store, mock_qdrant_client):
        """단일 증거 추가 테스트"""
        text = "배우자의 외도 증거"
        embedding = [0.1] * 1536
        metadata = {
            "chunk_id": "chunk001",
            "file_id": "file001",
            "sender": "홍길동",
            "case_id": "case001"
        }

        vector_id = vector_store.add_evidence(
            text=text,
            embedding=embedding,
            metadata=metadata
        )

        assert vector_id is not None
        mock_qdrant_client.upsert.assert_called_once()

    def test_add_multiple_evidences(self, vector_store, mock_qdrant_client):
        """여러 증거 추가 테스트"""
        texts = ["증거1", "증거2", "증거3"]
        embeddings = [[0.1] * 1536 for _ in range(3)]
        metadatas = [
            {"chunk_id": f"chunk{i}", "file_id": "file001", "case_id": "case001"}
            for i in range(3)
        ]

        vector_ids = vector_store.add_evidences(
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        assert len(vector_ids) == 3
        mock_qdrant_client.upsert.assert_called_once()

    def test_add_chunk_with_metadata(self, vector_store, mock_qdrant_client):
        """청크 메타데이터와 함께 벡터 저장 테스트"""
        vector_id = vector_store.add_chunk_with_metadata(
            chunk_id="chunk001",
            file_id="file001",
            case_id="case001",
            content="테스트 내용",
            embedding=[0.1] * 1536,
            timestamp="2024-01-15T10:30:00",
            sender="홍길동",
            score=8.5
        )

        assert vector_id == "chunk001"
        mock_qdrant_client.upsert.assert_called_once()


class TestVectorStoreSearch:
    """Test vector similarity search"""

    def test_search_by_embedding(self, vector_store, mock_qdrant_client):
        """임베딩 유사도 검색 테스트"""
        # Mock search response
        mock_hit = MagicMock()
        mock_hit.id = "vec001"
        mock_hit.score = 0.95
        mock_hit.payload = {
            "document": "검색된 증거",
            "case_id": "case001",
            "chunk_id": "chunk001"
        }
        mock_qdrant_client.search.return_value = [mock_hit]

        query_embedding = [0.1] * 1536
        results = vector_store.search(
            query_embedding=query_embedding,
            n_results=5
        )

        assert len(results) == 1
        assert results[0]["document"] == "검색된 증거"
        assert "distance" in results[0]

    def test_search_with_case_filter(self, vector_store, mock_qdrant_client):
        """케이스 ID 필터링 검색 테스트"""
        mock_hit = MagicMock()
        mock_hit.id = "vec001"
        mock_hit.score = 0.9
        mock_hit.payload = {
            "document": "필터링된 증거",
            "case_id": "case001"
        }
        mock_qdrant_client.search.return_value = [mock_hit]

        results = vector_store.search(
            query_embedding=[0.1] * 1536,
            n_results=5,
            where={"case_id": "case001"}
        )

        assert len(results) == 1
        # Verify filter was passed
        mock_qdrant_client.search.assert_called_once()


class TestVectorStoreUtility:
    """Test utility methods"""

    def test_get_by_id(self, vector_store, mock_qdrant_client):
        """ID로 벡터 조회 테스트"""
        mock_point = MagicMock()
        mock_point.id = "vec001"
        mock_point.payload = {
            "document": "조회된 증거",
            "case_id": "case001"
        }
        mock_qdrant_client.retrieve.return_value = [mock_point]

        result = vector_store.get_by_id("vec001")

        assert result is not None
        assert result["document"] == "조회된 증거"

    def test_get_by_id_not_found(self, vector_store, mock_qdrant_client):
        """존재하지 않는 ID 조회 테스트"""
        mock_qdrant_client.retrieve.return_value = []

        result = vector_store.get_by_id("nonexistent")
        assert result is None

    def test_delete_by_id(self, vector_store, mock_qdrant_client):
        """ID로 벡터 삭제 테스트"""
        vector_store.delete_by_id("vec001")

        mock_qdrant_client.delete.assert_called_once()

    def test_count(self, vector_store, mock_qdrant_client):
        """컬렉션 개수 확인 테스트"""
        mock_info = MagicMock()
        mock_info.points_count = 100
        mock_qdrant_client.get_collection.return_value = mock_info

        count = vector_store.count()

        assert count == 100


class TestCaseIsolation:
    """Test case isolation methods"""

    def test_count_by_case(self, vector_store, mock_qdrant_client):
        """케이스별 벡터 개수 테스트"""
        mock_result = MagicMock()
        mock_result.count = 25
        mock_qdrant_client.count.return_value = mock_result

        count = vector_store.count_by_case("case001")

        assert count == 25

    def test_delete_by_case(self, vector_store, mock_qdrant_client):
        """케이스별 벡터 삭제 테스트"""
        # Mock count response
        mock_count = MagicMock()
        mock_count.count = 5
        mock_qdrant_client.count.return_value = mock_count

        deleted = vector_store.delete_by_case("case001")

        assert deleted == 5
        mock_qdrant_client.delete.assert_called_once()

    def test_get_chunks_by_case(self, vector_store, mock_qdrant_client):
        """케이스의 모든 청크 조회 테스트"""
        mock_point = MagicMock()
        mock_point.id = "chunk001"
        mock_point.payload = {
            "document": "청크 내용",
            "case_id": "case001",
            "file_id": "file001"
        }
        mock_qdrant_client.scroll.return_value = ([mock_point], None)

        chunks = vector_store.get_chunks_by_case("case001")

        assert len(chunks) == 1
        assert chunks[0]["case_id"] == "case001"


# =============================================================================
# Integration Tests (require actual Qdrant connection)
# Run with: pytest -m integration
# =============================================================================

@pytest.mark.integration
class TestVectorStoreIntegration:
    """Integration tests with real Qdrant connection"""

    @pytest.fixture
    def real_vector_store(self):
        """실제 Qdrant 연결"""
        import os
        from dotenv import load_dotenv
        load_dotenv()

        if not os.getenv('QDRANT_URL'):
            pytest.skip("QDRANT_URL not configured")

        return VectorStore()

    def test_real_add_and_search(self, real_vector_store):
        """실제 벡터 추가 및 검색 테스트"""
        import uuid

        test_case_id = f"test_{uuid.uuid4().hex[:8]}"
        embedding = [0.1] * 1536

        # Add
        vector_id = real_vector_store.add_evidence(
            text="통합 테스트 증거",
            embedding=embedding,
            metadata={"case_id": test_case_id}
        )
        assert vector_id is not None

        # Search
        results = real_vector_store.search(
            query_embedding=embedding,
            n_results=5,
            where={"case_id": test_case_id}
        )
        assert len(results) >= 1

        # Cleanup
        real_vector_store.delete_by_case(test_case_id)
