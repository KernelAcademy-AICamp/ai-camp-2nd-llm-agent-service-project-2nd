"""
Integration tests for Qdrant vector database
Requires: docker run -d -p 6333:6333 qdrant/qdrant
"""

import pytest
from app.utils.qdrant import (
    create_case_collection,
    delete_case_collection,
    index_evidence_document,
    search_evidence_by_semantic,
    get_all_documents_in_case
)


@pytest.fixture
def test_case_id():
    """Test case ID for integration tests"""
    return "test_case_integration_001"


@pytest.fixture(autouse=True)
def cleanup_collection(test_case_id):
    """Cleanup collection before and after each test"""
    # Cleanup before
    delete_case_collection(test_case_id)
    yield
    # Cleanup after
    delete_case_collection(test_case_id)


class TestQdrantIntegration:
    """Integration tests for Qdrant operations"""

    @pytest.mark.integration
    def test_create_collection_success(self, test_case_id):
        """Test creating a new collection"""
        result = create_case_collection(test_case_id)
        assert result is True

    @pytest.mark.integration
    def test_create_collection_idempotent(self, test_case_id):
        """Test creating same collection twice is idempotent"""
        result1 = create_case_collection(test_case_id)
        result2 = create_case_collection(test_case_id)
        assert result1 is True
        assert result2 is True

    @pytest.mark.integration
    def test_index_document_success(self, test_case_id):
        """Test indexing a document with content"""
        # Create collection first
        create_case_collection(test_case_id)

        document = {
            "id": "ev_test_001",
            "case_id": test_case_id,
            "content": "배우자가 폭언을 하며 욕설을 했습니다. 이혼 사유에 해당합니다.",
            "labels": ["폭언", "욕설"],
            "type": "audio",
            "filename": "recording.mp3"
        }

        result = index_evidence_document(test_case_id, document)
        assert result == "ev_test_001"

    @pytest.mark.integration
    def test_search_semantic_success(self, test_case_id):
        """Test semantic search finds relevant documents"""
        # Create and populate collection
        create_case_collection(test_case_id)

        documents = [
            {
                "id": "ev_001",
                "case_id": test_case_id,
                "content": "배우자의 부정행위 증거입니다. 외도 현장 사진.",
                "labels": ["부정행위", "외도"],
                "type": "image"
            },
            {
                "id": "ev_002",
                "case_id": test_case_id,
                "content": "배우자가 폭언과 욕설을 했습니다. 녹음 파일입니다.",
                "labels": ["폭언"],
                "type": "audio"
            },
            {
                "id": "ev_003",
                "case_id": test_case_id,
                "content": "가계부 내역입니다. 생활비 지출 기록.",
                "labels": ["재산"],
                "type": "document"
            }
        ]

        for doc in documents:
            index_evidence_document(test_case_id, doc)

        # Search for infidelity-related evidence
        results = search_evidence_by_semantic(
            case_id=test_case_id,
            query="외도 부정행위",
            top_k=2
        )

        assert len(results) > 0
        # First result should be the infidelity document
        assert results[0].get("id") == "ev_001" or "부정행위" in results[0].get("content", "")

    @pytest.mark.integration
    def test_search_with_filter(self, test_case_id):
        """Test semantic search with label filter"""
        create_case_collection(test_case_id)

        documents = [
            {
                "id": "ev_001",
                "content": "폭언 녹음 파일",
                "labels": ["폭언"],
                "type": "audio"
            },
            {
                "id": "ev_002",
                "content": "부정행위 사진",
                "labels": ["부정행위"],
                "type": "image"
            }
        ]

        for doc in documents:
            index_evidence_document(test_case_id, doc)

        # Search with label filter
        results = search_evidence_by_semantic(
            case_id=test_case_id,
            query="증거",
            top_k=5,
            filters={"labels": ["폭언"]}
        )

        # Should only return documents with "폭언" label
        assert all("폭언" in r.get("labels", []) for r in results)

    @pytest.mark.integration
    def test_get_all_documents(self, test_case_id):
        """Test retrieving all documents in a case"""
        create_case_collection(test_case_id)

        documents = [
            {"id": "ev_001", "content": "문서 1", "labels": []},
            {"id": "ev_002", "content": "문서 2", "labels": []},
            {"id": "ev_003", "content": "문서 3", "labels": []}
        ]

        for doc in documents:
            index_evidence_document(test_case_id, doc)

        all_docs = get_all_documents_in_case(test_case_id)
        assert len(all_docs) == 3

    @pytest.mark.integration
    def test_delete_collection_success(self, test_case_id):
        """Test deleting a collection"""
        create_case_collection(test_case_id)
        index_evidence_document(test_case_id, {
            "id": "ev_001",
            "content": "테스트"
        })

        result = delete_case_collection(test_case_id)
        assert result is True

        # Verify collection is gone
        all_docs = get_all_documents_in_case(test_case_id)
        assert len(all_docs) == 0

    @pytest.mark.integration
    def test_delete_nonexistent_collection(self, test_case_id):
        """Test deleting non-existent collection returns False"""
        result = delete_case_collection("nonexistent_case_xyz")
        assert result is False

    @pytest.mark.integration
    def test_search_empty_collection(self, test_case_id):
        """Test searching empty/nonexistent collection returns empty"""
        results = search_evidence_by_semantic(
            case_id="nonexistent_case",
            query="테스트",
            top_k=5
        )
        assert results == []
