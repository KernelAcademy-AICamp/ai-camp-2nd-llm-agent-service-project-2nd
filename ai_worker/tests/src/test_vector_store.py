"""
Test suite for VectorStore (ChromaDB)
"""

import pytest
import shutil
from pathlib import Path
from datetime import datetime
from src.storage.vector_store import VectorStore


@pytest.fixture
def temp_vector_db(tmp_path):
    """임시 ChromaDB 디렉토리"""
    db_path = tmp_path / "chromadb_test"
    yield str(db_path)
    # 테스트 후 정리 (Windows 파일 잠금 문제 무시)
    if db_path.exists():
        shutil.rmtree(db_path, ignore_errors=True)


@pytest.fixture
def vector_store(temp_vector_db):
    """VectorStore 인스턴스"""
    return VectorStore(persist_directory=temp_vector_db)


class TestVectorStoreInitialization:
    """Test VectorStore initialization"""

    def test_vector_store_creation(self, temp_vector_db):
        """VectorStore 생성 테스트"""
        store = VectorStore(persist_directory=temp_vector_db)

        assert store is not None
        assert store.persist_directory == temp_vector_db

    def test_collection_created_on_init(self, vector_store):
        """초기화 시 컬렉션 생성 확인"""
        assert vector_store.collection is not None
        assert vector_store.collection.name == "leh_evidence"

    def test_persist_directory_created(self, temp_vector_db):
        """persist 디렉토리 생성 확인"""
        VectorStore(persist_directory=temp_vector_db)

        assert Path(temp_vector_db).exists()


class TestVectorStoreAddEvidence:
    """Test adding evidence to vector store"""

    def test_add_single_evidence(self, vector_store):
        """단일 증거 추가 테스트"""
        text = "배우자의 외도 증거"
        metadata = {
            "chunk_id": "chunk001",
            "file_id": "file001",
            "sender": "홍길동",
            "case_id": "case001"
        }

        # 임베딩은 모의(mock) - 실제로는 OpenAI API 호출
        embedding = [0.1] * 768  # 768차원 벡터

        vector_id = vector_store.add_evidence(
            text=text,
            embedding=embedding,
            metadata=metadata
        )

        assert vector_id is not None
        assert isinstance(vector_id, str)

    def test_add_multiple_evidences(self, vector_store):
        """여러 증거 추가 테스트"""
        texts = ["증거1", "증거2", "증거3"]
        embeddings = [[0.1] * 768 for _ in range(3)]
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
        assert all(isinstance(vid, str) for vid in vector_ids)

    def test_collection_count_after_add(self, vector_store):
        """증거 추가 후 개수 확인"""
        text = "테스트 증거"
        embedding = [0.1] * 768
        metadata = {"chunk_id": "chunk001", "case_id": "case001"}

        vector_store.add_evidence(text, embedding, metadata)

        count = vector_store.count()
        assert count == 1


class TestVectorStoreSearch:
    """Test vector similarity search"""

    @pytest.fixture
    def populated_store(self, vector_store):
        """데이터가 있는 VectorStore"""
        # 샘플 데이터 추가
        texts = [
            "배우자의 외도 증거 관련 대화",
            "생활비 지급 관련 은행 거래 내역",
            "폭언 및 협박 관련 카카오톡 대화"
        ]
        embeddings = [
            [0.1] * 768,  # 외도
            [0.2] * 768,  # 생활비
            [0.3] * 768   # 폭언
        ]
        metadatas = [
            {"chunk_id": "chunk001", "file_id": "file001", "case_id": "case001", "type": "외도"},
            {"chunk_id": "chunk002", "file_id": "file001", "case_id": "case001", "type": "경제"},
            {"chunk_id": "chunk003", "file_id": "file002", "case_id": "case001", "type": "폭력"}
        ]

        vector_store.add_evidences(texts, embeddings, metadatas)
        return vector_store

    def test_search_by_embedding(self, populated_store):
        """임베딩 유사도 검색 테스트"""
        query_embedding = [0.1] * 768  # 외도와 유사

        results = populated_store.search(
            query_embedding=query_embedding,
            n_results=2
        )

        assert len(results) <= 2
        assert all("distance" in r for r in results)
        assert all("metadata" in r for r in results)
        assert all("document" in r for r in results)

    def test_search_with_metadata_filter(self, populated_store):
        """메타데이터 필터링 검색 테스트"""
        query_embedding = [0.1] * 768

        results = populated_store.search(
            query_embedding=query_embedding,
            n_results=5,
            where={"type": "외도"}
        )

        assert len(results) >= 1
        assert results[0]["metadata"]["type"] == "외도"

    def test_search_by_case_id(self, populated_store):
        """케이스 ID로 필터링 검색 테스트"""
        query_embedding = [0.1] * 768

        results = populated_store.search(
            query_embedding=query_embedding,
            n_results=10,
            where={"case_id": "case001"}
        )

        assert all(r["metadata"]["case_id"] == "case001" for r in results)


class TestVectorStoreUtility:
    """Test utility methods"""

    def test_get_by_id(self, vector_store):
        """ID로 벡터 조회 테스트"""
        text = "테스트 증거"
        embedding = [0.1] * 768
        metadata = {"chunk_id": "chunk001", "case_id": "case001"}

        vector_id = vector_store.add_evidence(text, embedding, metadata)

        result = vector_store.get_by_id(vector_id)

        assert result is not None
        assert result["document"] == text
        assert result["metadata"]["chunk_id"] == "chunk001"

    def test_delete_by_id(self, vector_store):
        """ID로 벡터 삭제 테스트"""
        text = "삭제될 증거"
        embedding = [0.1] * 768
        metadata = {"chunk_id": "chunk001", "case_id": "case001"}

        vector_id = vector_store.add_evidence(text, embedding, metadata)

        # 삭제 전 확인
        assert vector_store.count() == 1

        # 삭제
        vector_store.delete_by_id(vector_id)

        # 삭제 후 확인
        assert vector_store.count() == 0

    def test_clear_collection(self, vector_store):
        """컬렉션 전체 삭제 테스트"""
        # 데이터 추가
        for i in range(5):
            vector_store.add_evidence(
                text=f"증거{i}",
                embedding=[0.1] * 768,
                metadata={"chunk_id": f"chunk{i}", "case_id": "case001"}
            )

        assert vector_store.count() == 5

        # 전체 삭제
        vector_store.clear()

        assert vector_store.count() == 0
