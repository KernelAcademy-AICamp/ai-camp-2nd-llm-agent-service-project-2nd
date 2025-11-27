"""
Test suite for QdrantVectorStore

TDD RED Phase: Tests for Qdrant integration
"""

import pytest
from typing import List, Dict, Any


class TestQdrantVectorStoreInitialization:
    def test_qdrant_store_creation_memory_mode(self):
        from src.storage.qdrant_store import QdrantVectorStore
        store = QdrantVectorStore(mode="memory")
        assert store is not None
        assert store.mode == "memory"

    def test_qdrant_store_collection_created(self):
        from src.storage.qdrant_store import QdrantVectorStore
        store = QdrantVectorStore(mode="memory", collection_name="test_evidence")
        assert store.collection_name == "test_evidence"


class TestQdrantVectorStoreAddEvidence:
    @pytest.fixture
    def qdrant_store(self):
        from src.storage.qdrant_store import QdrantVectorStore
        return QdrantVectorStore(mode="memory", collection_name="test_leh")

    def test_add_single_evidence(self, qdrant_store):
        text = "배우자의 외도 증거"
        metadata = {"chunk_id": "chunk001", "file_id": "file001", "case_id": "case001"}
        embedding = [0.1] * 1536
        vector_id = qdrant_store.add_evidence(text=text, embedding=embedding, metadata=metadata)
        assert vector_id is not None
        assert isinstance(vector_id, str)

    def test_add_multiple_evidences(self, qdrant_store):
        texts = ["증거1", "증거2", "증거3"]
        embeddings = [[0.1] * 1536 for _ in range(3)]
        metadatas = [{"chunk_id": f"chunk{i}", "file_id": "file001", "case_id": "case001"} for i in range(3)]
        vector_ids = qdrant_store.add_evidences(texts=texts, embeddings=embeddings, metadatas=metadatas)
        assert len(vector_ids) == 3

    def test_count_after_add(self, qdrant_store):
        qdrant_store.add_evidence("테스트", [0.1] * 1536, {"chunk_id": "c1", "case_id": "case001"})
        assert qdrant_store.count() == 1


class TestQdrantVectorStoreSearch:
    @pytest.fixture
    def populated_qdrant(self):
        from src.storage.qdrant_store import QdrantVectorStore
        store = QdrantVectorStore(mode="memory", collection_name="test_search")
        store.add_evidences(
            ["외도 증거", "경제 증거", "폭력 증거"],
            [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536],
            [{"chunk_id": "c1", "case_id": "case001", "type": "외도"},
             {"chunk_id": "c2", "case_id": "case001", "type": "경제"},
             {"chunk_id": "c3", "case_id": "case001", "type": "폭력"}]
        )
        return store

    def test_search_by_embedding(self, populated_qdrant):
        results = populated_qdrant.search(query_embedding=[0.1] * 1536, n_results=2)
        assert len(results) <= 2
        assert all("score" in r for r in results)

    def test_search_with_metadata_filter(self, populated_qdrant):
        results = populated_qdrant.search(query_embedding=[0.1] * 1536, n_results=5, where={"type": "외도"})
        assert len(results) >= 1
        assert results[0]["metadata"]["type"] == "외도"


class TestQdrantVectorStoreUtility:
    @pytest.fixture
    def qdrant_store(self):
        from src.storage.qdrant_store import QdrantVectorStore
        return QdrantVectorStore(mode="memory", collection_name="test_util")

    def test_get_by_id(self, qdrant_store):
        vid = qdrant_store.add_evidence("테스트", [0.1] * 1536, {"chunk_id": "c1", "case_id": "case001"})
        result = qdrant_store.get_by_id(vid)
        assert result["document"] == "테스트"

    def test_delete_by_id(self, qdrant_store):
        vid = qdrant_store.add_evidence("삭제", [0.1] * 1536, {"chunk_id": "c1", "case_id": "case001"})
        assert qdrant_store.count() == 1
        qdrant_store.delete_by_id(vid)
        assert qdrant_store.count() == 0

    def test_delete_by_case(self, qdrant_store):
        for i in range(3):
            qdrant_store.add_evidence(f"c1_{i}", [0.1]*1536, {"chunk_id": f"c{i}", "case_id": "case001"})
        qdrant_store.add_evidence("c2", [0.2]*1536, {"chunk_id": "cx", "case_id": "case002"})
        assert qdrant_store.count() == 4
        deleted = qdrant_store.delete_by_case("case001")
        assert deleted == 3
        assert qdrant_store.count() == 1

    def test_clear_collection(self, qdrant_store):
        for i in range(5):
            qdrant_store.add_evidence(f"e{i}", [0.1]*1536, {"chunk_id": f"c{i}", "case_id": "case001"})
        assert qdrant_store.count() == 5
        qdrant_store.clear()
        assert qdrant_store.count() == 0


class TestQdrantCaseIsolation:
    @pytest.fixture
    def qdrant_store(self):
        from src.storage.qdrant_store import QdrantVectorStore
        return QdrantVectorStore(mode="memory", collection_name="test_isolation")

    def test_count_by_case(self, qdrant_store):
        for i in range(3):
            qdrant_store.add_evidence(f"e{i}", [0.1]*1536, {"chunk_id": f"c{i}", "case_id": "case001"})
        for i in range(2):
            qdrant_store.add_evidence(f"e{i}", [0.2]*1536, {"chunk_id": f"c{i}", "case_id": "case002"})
        assert qdrant_store.count_by_case("case001") == 3
        assert qdrant_store.count_by_case("case002") == 2

    def test_verify_case_isolation(self, qdrant_store):
        qdrant_store.add_evidence("c1", [0.1]*1536, {"chunk_id": "c1", "case_id": "case001"})
        qdrant_store.add_evidence("c2", [0.2]*1536, {"chunk_id": "c2", "case_id": "case002"})
        assert qdrant_store.verify_case_isolation("case001") is True