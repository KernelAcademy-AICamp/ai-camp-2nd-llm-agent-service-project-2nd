"""
Test suite for MetadataStore (SQLite)
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from src.storage.metadata_store import MetadataStore
from src.storage.schemas import EvidenceFile, EvidenceChunk


@pytest.fixture
def temp_db(tmp_path):
    """임시 SQLite 데이터베이스"""
    db_path = tmp_path / "test_metadata.db"
    yield str(db_path)
    # 테스트 후 정리
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def metadata_store(temp_db):
    """MetadataStore 인스턴스"""
    return MetadataStore(db_path=temp_db)


class TestMetadataStoreInitialization:
    """Test MetadataStore initialization"""

    def test_metadata_store_creation(self, temp_db):
        """MetadataStore 생성 테스트"""
        store = MetadataStore(db_path=temp_db)

        assert store is not None
        assert store.db_path == temp_db

    def test_database_file_created(self, temp_db):
        """데이터베이스 파일 생성 확인"""
        MetadataStore(db_path=temp_db)

        assert Path(temp_db).exists()

    def test_tables_created_on_init(self, metadata_store):
        """초기화 시 테이블 생성 확인"""
        conn = sqlite3.connect(metadata_store.db_path)
        cursor = conn.cursor()

        # evidence_files 테이블 존재 확인
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='evidence_files'
        """)
        assert cursor.fetchone() is not None

        # evidence_chunks 테이블 존재 확인
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='evidence_chunks'
        """)
        assert cursor.fetchone() is not None

        conn.close()


class TestEvidenceFileOperations:
    """Test evidence file CRUD operations"""

    def test_save_evidence_file(self, metadata_store):
        """증거 파일 저장 테스트"""
        file = EvidenceFile(
            filename="chat.txt",
            file_type="kakaotalk",
            total_messages=10,
            case_id="case001"
        )

        metadata_store.save_file(file)

        # 저장 확인
        retrieved = metadata_store.get_file(file.file_id)
        assert retrieved is not None
        assert retrieved.filename == "chat.txt"
        assert retrieved.total_messages == 10

    def test_get_nonexistent_file(self, metadata_store):
        """존재하지 않는 파일 조회 테스트"""
        result = metadata_store.get_file("nonexistent-id")

        assert result is None

    def test_get_files_by_case_id(self, metadata_store):
        """케이스 ID로 파일 조회 테스트"""
        # 여러 파일 저장
        for i in range(3):
            file = EvidenceFile(
                filename=f"file{i}.txt",
                file_type="text",
                total_messages=5,
                case_id="case001"
            )
            metadata_store.save_file(file)

        # case001의 파일들 조회
        files = metadata_store.get_files_by_case("case001")

        assert len(files) == 3
        assert all(f.case_id == "case001" for f in files)

    def test_delete_evidence_file(self, metadata_store):
        """증거 파일 삭제 테스트"""
        file = EvidenceFile(
            filename="delete_me.txt",
            file_type="text",
            total_messages=1,
            case_id="case001"
        )

        metadata_store.save_file(file)
        assert metadata_store.get_file(file.file_id) is not None

        # 삭제
        metadata_store.delete_file(file.file_id)
        assert metadata_store.get_file(file.file_id) is None


class TestEvidenceChunkOperations:
    """Test evidence chunk CRUD operations"""

    def test_save_evidence_chunk(self, metadata_store):
        """증거 청크 저장 테스트"""
        chunk = EvidenceChunk(
            file_id="file001",
            content="테스트 메시지",
            timestamp=datetime(2024, 1, 15, 10, 30),
            sender="홍길동",
            case_id="case001",
            vector_id="vector123"
        )

        metadata_store.save_chunk(chunk)

        # 저장 확인
        retrieved = metadata_store.get_chunk(chunk.chunk_id)
        assert retrieved is not None
        assert retrieved.content == "테스트 메시지"
        assert retrieved.sender == "홍길동"
        assert retrieved.vector_id == "vector123"

    def test_save_multiple_chunks(self, metadata_store):
        """여러 청크 일괄 저장 테스트"""
        chunks = [
            EvidenceChunk(
                file_id="file001",
                content=f"메시지{i}",
                timestamp=datetime.now(),
                sender="홍길동",
                case_id="case001"
            )
            for i in range(5)
        ]

        metadata_store.save_chunks(chunks)

        # 저장 확인
        for chunk in chunks:
            retrieved = metadata_store.get_chunk(chunk.chunk_id)
            assert retrieved is not None

    def test_get_chunks_by_file_id(self, metadata_store):
        """파일 ID로 청크 조회 테스트"""
        # 여러 청크 저장
        for i in range(3):
            chunk = EvidenceChunk(
                file_id="file001",
                content=f"메시지{i}",
                timestamp=datetime.now(),
                sender="홍길동",
                case_id="case001"
            )
            metadata_store.save_chunk(chunk)

        # file001의 청크들 조회
        chunks = metadata_store.get_chunks_by_file("file001")

        assert len(chunks) == 3
        assert all(c.file_id == "file001" for c in chunks)

    def test_get_chunks_by_case_id(self, metadata_store):
        """케이스 ID로 청크 조회 테스트"""
        # case001의 청크들 저장
        for i in range(3):
            chunk = EvidenceChunk(
                file_id=f"file{i}",
                content=f"메시지{i}",
                timestamp=datetime.now(),
                sender="홍길동",
                case_id="case001"
            )
            metadata_store.save_chunk(chunk)

        # case001의 모든 청크 조회
        chunks = metadata_store.get_chunks_by_case("case001")

        assert len(chunks) == 3
        assert all(c.case_id == "case001" for c in chunks)

    def test_update_chunk_score(self, metadata_store):
        """청크 점수 업데이트 테스트"""
        chunk = EvidenceChunk(
            file_id="file001",
            content="점수 테스트",
            timestamp=datetime.now(),
            sender="홍길동",
            case_id="case001",
            score=None  # 초기 점수 없음
        )

        metadata_store.save_chunk(chunk)

        # 점수 업데이트
        metadata_store.update_chunk_score(chunk.chunk_id, 8.5)

        # 확인
        updated = metadata_store.get_chunk(chunk.chunk_id)
        assert updated.score == 8.5

    def test_delete_evidence_chunk(self, metadata_store):
        """증거 청크 삭제 테스트"""
        chunk = EvidenceChunk(
            file_id="file001",
            content="삭제될 메시지",
            timestamp=datetime.now(),
            sender="홍길동",
            case_id="case001"
        )

        metadata_store.save_chunk(chunk)
        assert metadata_store.get_chunk(chunk.chunk_id) is not None

        # 삭제
        metadata_store.delete_chunk(chunk.chunk_id)
        assert metadata_store.get_chunk(chunk.chunk_id) is None


class TestStatistics:
    """Test statistics and aggregation methods"""

    def test_count_files_by_case(self, metadata_store):
        """케이스별 파일 개수 테스트"""
        # case001에 3개 파일
        for i in range(3):
            file = EvidenceFile(
                filename=f"file{i}.txt",
                file_type="text",
                total_messages=1,
                case_id="case001"
            )
            metadata_store.save_file(file)

        count = metadata_store.count_files_by_case("case001")
        assert count == 3

    def test_count_chunks_by_case(self, metadata_store):
        """케이스별 청크 개수 테스트"""
        # case001에 5개 청크
        for i in range(5):
            chunk = EvidenceChunk(
                file_id="file001",
                content=f"메시지{i}",
                timestamp=datetime.now(),
                sender="홍길동",
                case_id="case001"
            )
            metadata_store.save_chunk(chunk)

        count = metadata_store.count_chunks_by_case("case001")
        assert count == 5

    def test_get_case_summary(self, metadata_store):
        """케이스 요약 정보 테스트"""
        # 파일 저장
        file = EvidenceFile(
            filename="chat.txt",
            file_type="kakaotalk",
            total_messages=3,
            case_id="case001"
        )
        metadata_store.save_file(file)

        # 청크 저장
        for i in range(3):
            chunk = EvidenceChunk(
                file_id=file.file_id,
                content=f"메시지{i}",
                timestamp=datetime.now(),
                sender="홍길동",
                case_id="case001"
            )
            metadata_store.save_chunk(chunk)

        summary = metadata_store.get_case_summary("case001")

        assert summary["file_count"] == 1
        assert summary["chunk_count"] == 3
        assert summary["case_id"] == "case001"
