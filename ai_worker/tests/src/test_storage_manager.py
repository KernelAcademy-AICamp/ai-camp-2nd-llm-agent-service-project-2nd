"""
Test suite for StorageManager
Following TDD approach: RED-GREEN-REFACTOR
"""

import pytest
from unittest.mock import patch
from src.storage.storage_manager import StorageManager


@pytest.fixture
def temp_storage(tmp_path):
    """임시 저장소 디렉토리"""
    vector_db = tmp_path / "chromadb"
    metadata_db = tmp_path / "metadata.db"

    yield {
        "vector_db": str(vector_db),
        "metadata_db": str(metadata_db)
    }


@pytest.fixture
def storage_manager(temp_storage):
    """StorageManager 인스턴스"""
    return StorageManager(
        vector_db_path=temp_storage["vector_db"],
        metadata_db_path=temp_storage["metadata_db"]
    )


@pytest.fixture
def sample_kakaotalk_file():
    """샘플 카카오톡 파일 경로"""
    return "tests/fixtures/kakaotalk_sample.txt"


@pytest.fixture
def sample_text_file():
    """샘플 텍스트 파일 경로"""
    return "tests/fixtures/text_sample.txt"


class TestStorageManagerInitialization:
    """Test StorageManager initialization"""

    def test_storage_manager_creation(self, temp_storage):
        """StorageManager 생성 테스트"""
        manager = StorageManager(
            vector_db_path=temp_storage["vector_db"],
            metadata_db_path=temp_storage["metadata_db"]
        )

        assert manager is not None
        assert manager.vector_store is not None
        assert manager.metadata_store is not None

    def test_storage_paths_configured(self, storage_manager, temp_storage):
        """저장소 경로 설정 확인"""
        assert storage_manager.vector_store.persist_directory == temp_storage["vector_db"]
        assert storage_manager.metadata_store.db_path == temp_storage["metadata_db"]


class TestProcessFile:
    """Test file processing and storage"""

    @patch('src.storage.storage_manager.get_embedding')
    def test_process_kakaotalk_file(self, mock_embedding, storage_manager, sample_kakaotalk_file):
        """카카오톡 파일 처리 테스트"""
        # Mock 임베딩 함수 (실제 OpenAI API 호출 대신)
        mock_embedding.return_value = [0.1] * 768

        result = storage_manager.process_file(
            filepath=sample_kakaotalk_file,
            case_id="case001"
        )

        # 결과 검증
        assert result is not None
        assert result["file_id"] is not None
        assert result["total_messages"] > 0
        assert result["chunks_stored"] > 0

    @patch('src.storage.storage_manager.get_embedding')
    def test_process_text_file(self, mock_embedding, storage_manager, sample_text_file):
        """텍스트 파일 처리 테스트"""
        mock_embedding.return_value = [0.1] * 768

        result = storage_manager.process_file(
            filepath=sample_text_file,
            case_id="case002"
        )

        assert result is not None
        assert result["file_id"] is not None
        assert result["total_messages"] == 1  # 텍스트는 1개 메시지

    @patch('src.storage.storage_manager.get_embedding')
    def test_metadata_stored_after_processing(self, mock_embedding, storage_manager, sample_kakaotalk_file):
        """처리 후 메타데이터 저장 확인"""
        mock_embedding.return_value = [0.1] * 768

        result = storage_manager.process_file(
            filepath=sample_kakaotalk_file,
            case_id="case001"
        )

        file_id = result["file_id"]

        # 메타데이터 저장 확인
        file_meta = storage_manager.metadata_store.get_file(file_id)
        assert file_meta is not None
        assert file_meta.case_id == "case001"

    @patch('src.storage.storage_manager.get_embedding')
    def test_vectors_stored_after_processing(self, mock_embedding, storage_manager, sample_kakaotalk_file):
        """처리 후 벡터 저장 확인"""
        mock_embedding.return_value = [0.1] * 768

        result = storage_manager.process_file(
            filepath=sample_kakaotalk_file,
            case_id="case001"
        )

        # 벡터 개수 확인
        vector_count = storage_manager.vector_store.count()
        assert vector_count == result["chunks_stored"]

    @patch('src.storage.storage_manager.get_embedding')
    def test_chunks_have_vector_ids(self, mock_embedding, storage_manager, sample_kakaotalk_file):
        """청크에 vector_id 설정 확인"""
        mock_embedding.return_value = [0.1] * 768

        result = storage_manager.process_file(
            filepath=sample_kakaotalk_file,
            case_id="case001"
        )

        file_id = result["file_id"]

        # 청크 조회
        chunks = storage_manager.metadata_store.get_chunks_by_file(file_id)

        # 모든 청크에 vector_id가 있는지 확인
        assert all(chunk.vector_id is not None for chunk in chunks)


class TestSearchEvidence:
    """Test evidence search functionality"""

    @pytest.fixture
    def populated_storage(self, storage_manager, sample_kakaotalk_file):
        """데이터가 있는 StorageManager"""
        with patch('src.storage.storage_manager.get_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 768

            storage_manager.process_file(
                filepath=sample_kakaotalk_file,
                case_id="case001"
            )

        return storage_manager

    @patch('src.storage.storage_manager.get_embedding')
    def test_search_by_query(self, mock_embedding, populated_storage):
        """쿼리로 증거 검색 테스트"""
        mock_embedding.return_value = [0.1] * 768

        results = populated_storage.search(
            query="이혼 소송",
            case_id="case001",
            top_k=5
        )

        assert len(results) > 0
        assert all("content" in r for r in results)
        assert all("metadata" in r for r in results)

    @patch('src.storage.storage_manager.get_embedding')
    def test_search_filtered_by_case_id(self, mock_embedding, populated_storage):
        """케이스 ID로 필터링된 검색 테스트"""
        mock_embedding.return_value = [0.1] * 768

        results = populated_storage.search(
            query="증거",
            case_id="case001",
            top_k=10
        )

        # 모든 결과가 case001에 속하는지 확인
        assert all(r["metadata"]["case_id"] == "case001" for r in results)


class TestGetCaseData:
    """Test case data retrieval"""

    @pytest.fixture
    def populated_storage(self, storage_manager, sample_kakaotalk_file):
        """데이터가 있는 StorageManager"""
        with patch('src.storage.storage_manager.get_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 768

            storage_manager.process_file(
                filepath=sample_kakaotalk_file,
                case_id="case001"
            )

        return storage_manager

    def test_get_case_summary(self, populated_storage):
        """케이스 요약 정보 조회 테스트"""
        summary = populated_storage.get_case_summary("case001")

        assert summary["case_id"] == "case001"
        assert summary["file_count"] > 0
        assert summary["chunk_count"] > 0

    def test_get_case_files(self, populated_storage):
        """케이스 파일 목록 조회 테스트"""
        files = populated_storage.get_case_files("case001")

        assert len(files) > 0
        assert all(f.case_id == "case001" for f in files)

    def test_get_case_chunks(self, populated_storage):
        """케이스 청크 목록 조회 테스트"""
        chunks = populated_storage.get_case_chunks("case001")

        assert len(chunks) > 0
        assert all(c.case_id == "case001" for c in chunks)


class TestErrorHandling:
    """Test error handling"""

    def test_process_nonexistent_file_raises_error(self, storage_manager):
        """존재하지 않는 파일 처리 시 에러"""
        with pytest.raises(FileNotFoundError):
            storage_manager.process_file(
                filepath="nonexistent_file.txt",
                case_id="case001"
            )

    @patch('src.storage.storage_manager.get_embedding')
    def test_embedding_failure_rollback(self, mock_embedding, storage_manager, sample_text_file):
        """임베딩 실패 시 롤백 테스트"""
        # 임베딩 함수가 에러를 발생시키도록 설정
        mock_embedding.side_effect = Exception("OpenAI API Error")

        with pytest.raises(Exception):
            storage_manager.process_file(
                filepath=sample_text_file,
                case_id="case001"
            )

        # 메타데이터가 저장되지 않았는지 확인
        files = storage_manager.metadata_store.get_files_by_case("case001")
        assert len(files) == 0

        # 벡터가 저장되지 않았는지 확인
        assert storage_manager.vector_store.count() == 0
