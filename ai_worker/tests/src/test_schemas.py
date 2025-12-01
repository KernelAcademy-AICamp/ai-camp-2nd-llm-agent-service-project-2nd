"""
Test suite for data schemas
"""

from datetime import datetime
from src.storage.schemas import EvidenceFile, EvidenceChunk, generate_file_id, generate_chunk_id


class TestEvidenceFile:
    """Test EvidenceFile schema"""

    def test_evidence_file_creation(self):
        """EvidenceFile 생성 테스트"""
        file = EvidenceFile(
            filename="chat.txt",
            file_type="kakaotalk",
            total_messages=10,
            case_id="case001"
        )

        assert file.filename == "chat.txt"
        assert file.file_type == "kakaotalk"
        assert file.total_messages == 10
        assert file.case_id == "case001"
        assert file.file_id is not None  # UUID 자동 생성
        assert file.parsed_at is not None  # 현재 시간 자동 설정

    def test_evidence_file_with_custom_id(self):
        """커스텀 file_id 설정 테스트"""
        custom_id = "custom-file-001"

        file = EvidenceFile(
            file_id=custom_id,
            filename="document.pdf",
            file_type="pdf",
            total_messages=1,
            case_id="case002"
        )

        assert file.file_id == custom_id

    def test_evidence_file_optional_filepath(self):
        """선택적 filepath 테스트"""
        file = EvidenceFile(
            filename="chat.txt",
            file_type="text",
            total_messages=5,
            case_id="case003",
            filepath="/path/to/chat.txt"
        )

        assert file.filepath == "/path/to/chat.txt"

    def test_evidence_file_serialization(self):
        """JSON 직렬화 테스트"""
        file = EvidenceFile(
            filename="test.txt",
            file_type="text",
            total_messages=3,
            case_id="case004"
        )

        json_data = file.model_dump()

        assert "file_id" in json_data
        assert "filename" in json_data
        assert "parsed_at" in json_data


class TestEvidenceChunk:
    """Test EvidenceChunk schema"""

    def test_evidence_chunk_creation(self):
        """EvidenceChunk 생성 테스트"""
        chunk = EvidenceChunk(
            file_id="file001",
            content="테스트 메시지",
            timestamp=datetime(2024, 1, 15, 10, 30),
            sender="홍길동",
            case_id="case001"
        )

        assert chunk.file_id == "file001"
        assert chunk.content == "테스트 메시지"
        assert chunk.timestamp.year == 2024
        assert chunk.sender == "홍길동"
        assert chunk.case_id == "case001"
        assert chunk.chunk_id is not None  # UUID 자동 생성

    def test_evidence_chunk_optional_score(self):
        """선택적 score 테스트"""
        chunk = EvidenceChunk(
            file_id="file001",
            content="메시지",
            timestamp=datetime.now(),
            sender="김철수",
            case_id="case001",
            score=8.5
        )

        assert chunk.score == 8.5

    def test_evidence_chunk_optional_vector_id(self):
        """선택적 vector_id 테스트"""
        chunk = EvidenceChunk(
            file_id="file001",
            content="메시지",
            timestamp=datetime.now(),
            sender="이영희",
            case_id="case001"
        )

        assert chunk.vector_id is None

        # vector_id 업데이트
        chunk.vector_id = "vector123"
        assert chunk.vector_id == "vector123"

    def test_evidence_chunk_serialization(self):
        """JSON 직렬화 테스트"""
        chunk = EvidenceChunk(
            file_id="file001",
            content="테스트",
            timestamp=datetime.now(),
            sender="박민수",
            case_id="case001"
        )

        json_data = chunk.model_dump()

        assert "chunk_id" in json_data
        assert "file_id" in json_data
        assert "content" in json_data
        assert "timestamp" in json_data


class TestHelperFunctions:
    """Test helper functions"""

    def test_generate_file_id(self):
        """파일 ID 생성 테스트"""
        id1 = generate_file_id()
        id2 = generate_file_id()

        assert id1 != id2  # 고유한 ID 생성
        assert len(id1) > 0
        assert "-" in id1  # UUID 형식

    def test_generate_chunk_id(self):
        """청크 ID 생성 테스트"""
        id1 = generate_chunk_id()
        id2 = generate_chunk_id()

        assert id1 != id2  # 고유한 ID 생성
        assert len(id1) > 0
        assert "-" in id1  # UUID 형식

    def test_id_generation_uniqueness(self):
        """ID 고유성 대량 테스트"""
        file_ids = {generate_file_id() for _ in range(100)}
        chunk_ids = {generate_chunk_id() for _ in range(100)}

        assert len(file_ids) == 100  # 모두 고유
        assert len(chunk_ids) == 100  # 모두 고유
