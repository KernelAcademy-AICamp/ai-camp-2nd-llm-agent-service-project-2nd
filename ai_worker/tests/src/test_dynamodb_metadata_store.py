"""
DynamoDB Metadata Store Tests
Tests for DynamoDBMetadataStore class with mocked boto3

TDD Phase: RED -> GREEN -> REFACTOR
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
from decimal import Decimal

# Import will be done with mock to avoid AWS credentials requirement


class TestDynamoDBMetadataStoreInit:
    """DynamoDBMetadataStore 초기화 테스트"""

    @patch("boto3.resource")
    def test_init_with_default_values(self, mock_boto3_resource):
        """기본값으로 초기화 테스트"""
        # Given: 환경변수 미설정 상태
        mock_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # When: DynamoDBMetadataStore 초기화
        with patch.dict(
            "os.environ",
            {"DYNAMODB_TABLE_EVIDENCE_METADATA": "", "AWS_REGION": ""},
            clear=False,
        ):
            from src.storage.dynamodb_metadata_store import DynamoDBMetadataStore

            store = DynamoDBMetadataStore()

        # Then: 기본값 사용
        assert store.table_name == "leh-evidence-metadata"
        assert store.region_name == "ap-northeast-2"
        mock_boto3_resource.assert_called_once_with(
            "dynamodb", region_name="ap-northeast-2"
        )

    @patch("boto3.resource")
    def test_init_with_custom_values(self, mock_boto3_resource):
        """커스텀 값으로 초기화 테스트"""
        # Given: 커스텀 설정
        mock_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb

        # When: 커스텀 값으로 초기화
        from src.storage.dynamodb_metadata_store import DynamoDBMetadataStore

        store = DynamoDBMetadataStore(
            table_name="custom-table", region_name="us-west-2"
        )

        # Then: 커스텀 값 사용
        assert store.table_name == "custom-table"
        assert store.region_name == "us-west-2"


class TestDynamoDBMetadataStoreFileOperations:
    """파일 작업 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 DynamoDBMetadataStore 인스턴스"""
        with patch("boto3.resource") as mock_boto3:
            mock_table = MagicMock()
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_boto3.return_value = mock_dynamodb

            from src.storage.dynamodb_metadata_store import DynamoDBMetadataStore

            store = DynamoDBMetadataStore(
                table_name="test-table", region_name="ap-northeast-2"
            )
            store._mock_table = mock_table
            yield store

    @pytest.fixture
    def sample_evidence_file(self):
        """샘플 EvidenceFile 객체"""
        from src.storage.schemas import EvidenceFile

        return EvidenceFile(
            file_id="file-123",
            filename="kakaotalk_20240101.txt",
            file_type="kakaotalk",
            parsed_at=datetime(2024, 1, 1, 12, 0, 0),
            total_messages=100,
            case_id="case-456",
            filepath="/tmp/kakaotalk_20240101.txt",
        )

    def test_save_file_success(self, mock_store, sample_evidence_file):
        """파일 저장 성공 테스트"""
        # Given: 샘플 파일과 모킹된 테이블
        mock_store._mock_table.put_item = MagicMock()

        # When: 파일 저장
        mock_store.save_file(sample_evidence_file)

        # Then: put_item이 올바른 인자로 호출됨
        mock_store._mock_table.put_item.assert_called_once()
        call_args = mock_store._mock_table.put_item.call_args
        item = call_args[1]["Item"]

        assert item["PK"] == "FILE#file-123"
        assert item["SK"] == "META#case-456"
        assert item["filename"] == "kakaotalk_20240101.txt"
        assert item["entity_type"] == "FILE"

    def test_get_file_found(self, mock_store):
        """파일 조회 성공 테스트"""
        # Given: 존재하는 파일
        mock_store._mock_table.query.return_value = {
            "Items": [
                {
                    "file_id": "file-123",
                    "filename": "test.txt",
                    "file_type": "text",
                    "parsed_at": "2024-01-01T12:00:00",
                    "total_messages": 50,
                    "case_id": "case-456",
                    "filepath": "/tmp/test.txt",
                }
            ]
        }

        # When: 파일 조회
        result = mock_store.get_file("file-123")

        # Then: EvidenceFile 반환
        assert result is not None
        assert result.file_id == "file-123"
        assert result.filename == "test.txt"
        assert result.case_id == "case-456"

    def test_get_file_not_found(self, mock_store):
        """파일 조회 실패 테스트 (존재하지 않음)"""
        # Given: 존재하지 않는 파일
        mock_store._mock_table.query.return_value = {"Items": []}

        # When: 파일 조회
        result = mock_store.get_file("non-existent")

        # Then: None 반환
        assert result is None

    def test_get_files_by_case(self, mock_store):
        """케이스별 파일 목록 조회 테스트"""
        # Given: 케이스에 속한 파일들
        mock_store._mock_table.query.return_value = {
            "Items": [
                {
                    "file_id": "file-1",
                    "filename": "test1.txt",
                    "file_type": "text",
                    "parsed_at": "2024-01-01T12:00:00",
                    "total_messages": 10,
                    "case_id": "case-456",
                    "filepath": "",
                    "entity_type": "FILE",
                },
                {
                    "file_id": "file-2",
                    "filename": "test2.txt",
                    "file_type": "text",
                    "parsed_at": "2024-01-02T12:00:00",
                    "total_messages": 20,
                    "case_id": "case-456",
                    "filepath": "",
                    "entity_type": "FILE",
                },
            ]
        }

        # When: 케이스별 파일 조회
        results = mock_store.get_files_by_case("case-456")

        # Then: 파일 목록 반환
        assert len(results) == 2
        assert results[0].file_id == "file-1"
        assert results[1].file_id == "file-2"

    def test_delete_file(self, mock_store):
        """파일 삭제 테스트"""
        # Given: 존재하는 파일
        mock_store._mock_table.query.return_value = {
            "Items": [
                {
                    "file_id": "file-123",
                    "filename": "test.txt",
                    "file_type": "text",
                    "parsed_at": "2024-01-01T12:00:00",
                    "total_messages": 10,
                    "case_id": "case-456",
                    "filepath": "",
                }
            ]
        }
        mock_store._mock_table.delete_item = MagicMock()

        # When: 파일 삭제
        mock_store.delete_file("file-123")

        # Then: delete_item 호출됨
        mock_store._mock_table.delete_item.assert_called_once()
        call_args = mock_store._mock_table.delete_item.call_args
        key = call_args[1]["Key"]
        assert key["PK"] == "FILE#file-123"
        assert key["SK"] == "META#case-456"


class TestDynamoDBMetadataStoreChunkOperations:
    """청크 작업 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 DynamoDBMetadataStore 인스턴스"""
        with patch("boto3.resource") as mock_boto3:
            mock_table = MagicMock()
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_boto3.return_value = mock_dynamodb

            from src.storage.dynamodb_metadata_store import DynamoDBMetadataStore

            store = DynamoDBMetadataStore(
                table_name="test-table", region_name="ap-northeast-2"
            )
            store._mock_table = mock_table
            yield store

    @pytest.fixture
    def sample_evidence_chunk(self):
        """샘플 EvidenceChunk 객체"""
        from src.storage.schemas import EvidenceChunk

        return EvidenceChunk(
            chunk_id="chunk-123",
            file_id="file-456",
            content="테스트 메시지 내용입니다.",
            score=8.5,
            timestamp=datetime(2024, 1, 1, 12, 30, 0),
            sender="홍길동",
            vector_id="vec-789",
            case_id="case-001",
        )

    def test_save_chunk_success(self, mock_store, sample_evidence_chunk):
        """청크 저장 성공 테스트"""
        # Given: 샘플 청크
        mock_store._mock_table.put_item = MagicMock()

        # When: 청크 저장
        mock_store.save_chunk(sample_evidence_chunk)

        # Then: put_item 호출됨
        mock_store._mock_table.put_item.assert_called_once()
        call_args = mock_store._mock_table.put_item.call_args
        item = call_args[1]["Item"]

        assert item["PK"] == "CHUNK#chunk-123"
        assert item["SK"] == "FILE#file-456"
        assert item["content"] == "테스트 메시지 내용입니다."
        assert item["score"] == Decimal("8.5")
        assert item["entity_type"] == "CHUNK"

    def test_save_chunks_batch(self, mock_store):
        """여러 청크 일괄 저장 테스트"""
        from src.storage.schemas import EvidenceChunk

        # Given: 여러 청크
        chunks = [
            EvidenceChunk(
                chunk_id=f"chunk-{i}",
                file_id="file-456",
                content=f"메시지 {i}",
                timestamp=datetime(2024, 1, 1, 12, i),
                sender="홍길동",
                case_id="case-001",
            )
            for i in range(3)
        ]

        mock_batch_writer = MagicMock()
        mock_batch_writer.__enter__ = MagicMock(return_value=mock_batch_writer)
        mock_batch_writer.__exit__ = MagicMock(return_value=False)
        mock_store._mock_table.batch_writer.return_value = mock_batch_writer

        # When: 일괄 저장
        mock_store.save_chunks(chunks)

        # Then: batch_writer의 put_item이 3번 호출됨
        assert mock_batch_writer.put_item.call_count == 3

    def test_get_chunk_found(self, mock_store):
        """청크 조회 성공 테스트"""
        # Given: 존재하는 청크
        mock_store._mock_table.query.return_value = {
            "Items": [
                {
                    "chunk_id": "chunk-123",
                    "file_id": "file-456",
                    "content": "테스트 내용",
                    "score": Decimal("7.5"),
                    "timestamp": "2024-01-01T12:30:00",
                    "sender": "홍길동",
                    "vector_id": "vec-789",
                    "case_id": "case-001",
                }
            ]
        }

        # When: 청크 조회
        result = mock_store.get_chunk("chunk-123")

        # Then: EvidenceChunk 반환
        assert result is not None
        assert result.chunk_id == "chunk-123"
        assert result.content == "테스트 내용"
        assert result.score == 7.5  # Decimal -> float 변환

    def test_get_chunk_not_found(self, mock_store):
        """청크 조회 실패 테스트"""
        # Given: 존재하지 않는 청크
        mock_store._mock_table.query.return_value = {"Items": []}

        # When: 청크 조회
        result = mock_store.get_chunk("non-existent")

        # Then: None 반환
        assert result is None

    def test_get_chunks_by_file(self, mock_store):
        """파일별 청크 목록 조회 테스트"""
        # Given: 파일에 속한 청크들
        mock_store._mock_table.query.return_value = {
            "Items": [
                {
                    "chunk_id": "chunk-1",
                    "file_id": "file-456",
                    "content": "메시지 1",
                    "timestamp": "2024-01-01T12:00:00",
                    "sender": "홍길동",
                    "case_id": "case-001",
                    "entity_type": "CHUNK",
                },
                {
                    "chunk_id": "chunk-2",
                    "file_id": "file-456",
                    "content": "메시지 2",
                    "timestamp": "2024-01-01T12:01:00",
                    "sender": "김철수",
                    "case_id": "case-001",
                    "entity_type": "CHUNK",
                },
            ]
        }

        # When: 파일별 청크 조회
        results = mock_store.get_chunks_by_file("file-456")

        # Then: 청크 목록 반환
        assert len(results) == 2
        assert results[0].chunk_id == "chunk-1"
        assert results[1].chunk_id == "chunk-2"

    def test_get_chunks_by_case(self, mock_store):
        """케이스별 청크 목록 조회 테스트"""
        # Given: 케이스에 속한 청크들
        mock_store._mock_table.query.return_value = {
            "Items": [
                {
                    "chunk_id": "chunk-1",
                    "file_id": "file-456",
                    "content": "증거 1",
                    "timestamp": "2024-01-01T12:00:00",
                    "sender": "홍길동",
                    "case_id": "case-001",
                    "entity_type": "CHUNK",
                }
            ]
        }

        # When: 케이스별 청크 조회
        results = mock_store.get_chunks_by_case("case-001")

        # Then: 청크 목록 반환
        assert len(results) == 1
        assert results[0].case_id == "case-001"

    def test_update_chunk_score(self, mock_store):
        """청크 점수 업데이트 테스트"""
        # Given: 존재하는 청크
        mock_store._mock_table.query.return_value = {
            "Items": [
                {
                    "chunk_id": "chunk-123",
                    "file_id": "file-456",
                    "content": "테스트",
                    "timestamp": "2024-01-01T12:00:00",
                    "sender": "홍길동",
                    "case_id": "case-001",
                }
            ]
        }
        mock_store._mock_table.update_item = MagicMock()

        # When: 점수 업데이트
        mock_store.update_chunk_score("chunk-123", 9.0)

        # Then: update_item 호출됨
        mock_store._mock_table.update_item.assert_called_once()
        call_args = mock_store._mock_table.update_item.call_args
        assert call_args[1]["ExpressionAttributeValues"][":score"] == Decimal("9.0")

    def test_delete_chunk(self, mock_store):
        """청크 삭제 테스트"""
        # Given: 존재하는 청크
        mock_store._mock_table.query.return_value = {
            "Items": [
                {
                    "chunk_id": "chunk-123",
                    "file_id": "file-456",
                    "content": "테스트",
                    "timestamp": "2024-01-01T12:00:00",
                    "sender": "홍길동",
                    "case_id": "case-001",
                }
            ]
        }
        mock_store._mock_table.delete_item = MagicMock()

        # When: 청크 삭제
        mock_store.delete_chunk("chunk-123")

        # Then: delete_item 호출됨
        mock_store._mock_table.delete_item.assert_called_once()


class TestDynamoDBMetadataStoreStatistics:
    """통계 및 집계 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 DynamoDBMetadataStore 인스턴스"""
        with patch("boto3.resource") as mock_boto3:
            mock_table = MagicMock()
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_boto3.return_value = mock_dynamodb

            from src.storage.dynamodb_metadata_store import DynamoDBMetadataStore

            store = DynamoDBMetadataStore(
                table_name="test-table", region_name="ap-northeast-2"
            )
            store._mock_table = mock_table
            yield store

    def test_count_files_by_case(self, mock_store):
        """케이스별 파일 개수 테스트"""
        # Given: 파일 개수 응답
        mock_store._mock_table.query.return_value = {"Count": 5}

        # When: 파일 개수 조회
        count = mock_store.count_files_by_case("case-001")

        # Then: 개수 반환
        assert count == 5

    def test_count_chunks_by_case(self, mock_store):
        """케이스별 청크 개수 테스트"""
        # Given: 청크 개수 응답
        mock_store._mock_table.query.return_value = {"Count": 150}

        # When: 청크 개수 조회
        count = mock_store.count_chunks_by_case("case-001")

        # Then: 개수 반환
        assert count == 150

    def test_get_case_summary(self, mock_store):
        """케이스 요약 정보 테스트"""
        # Given: 파일/청크 개수 응답
        mock_store._mock_table.query.side_effect = [
            {"Count": 3},  # count_files_by_case
            {"Count": 50},  # count_chunks_by_case
        ]

        # When: 케이스 요약 조회
        summary = mock_store.get_case_summary("case-001")

        # Then: 요약 정보 반환
        assert summary["case_id"] == "case-001"
        assert summary["file_count"] == 3
        assert summary["chunk_count"] == 50

    def test_get_case_stats_alias(self, mock_store):
        """get_case_stats 별칭 테스트"""
        # Given: 파일/청크 개수 응답
        mock_store._mock_table.query.side_effect = [
            {"Count": 2},
            {"Count": 30},
        ]

        # When: get_case_stats 호출
        stats = mock_store.get_case_stats("case-001")

        # Then: get_case_summary와 동일한 결과
        assert stats["case_id"] == "case-001"
        assert stats["file_count"] == 2


class TestDynamoDBMetadataStoreCaseManagement:
    """케이스 관리 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 DynamoDBMetadataStore 인스턴스"""
        with patch("boto3.resource") as mock_boto3:
            mock_table = MagicMock()
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_boto3.return_value = mock_dynamodb

            from src.storage.dynamodb_metadata_store import DynamoDBMetadataStore

            store = DynamoDBMetadataStore(
                table_name="test-table", region_name="ap-northeast-2"
            )
            store._mock_table = mock_table
            yield store

    def test_list_cases(self, mock_store):
        """케이스 목록 조회 테스트"""
        # Given: 케이스 ID가 포함된 아이템들
        mock_store._mock_table.scan.return_value = {
            "Items": [
                {"case_id": "case-001"},
                {"case_id": "case-002"},
                {"case_id": "case-001"},  # 중복
            ]
        }

        # When: 케이스 목록 조회
        cases = mock_store.list_cases()

        # Then: 중복 제거된 정렬된 목록 반환
        assert cases == ["case-001", "case-002"]

    def test_delete_case(self, mock_store):
        """케이스 삭제 테스트"""
        # Given: 케이스에 속한 청크와 파일
        mock_store._mock_table.query.side_effect = [
            # get_chunks_by_case
            {
                "Items": [
                    {
                        "chunk_id": "chunk-1",
                        "file_id": "file-1",
                        "content": "test",
                        "timestamp": "2024-01-01T12:00:00",
                        "sender": "홍길동",
                        "case_id": "case-001",
                        "entity_type": "CHUNK",
                    }
                ]
            },
            # get_chunk (for delete_chunk)
            {
                "Items": [
                    {
                        "chunk_id": "chunk-1",
                        "file_id": "file-1",
                        "content": "test",
                        "timestamp": "2024-01-01T12:00:00",
                        "sender": "홍길동",
                        "case_id": "case-001",
                    }
                ]
            },
            # get_files_by_case
            {
                "Items": [
                    {
                        "file_id": "file-1",
                        "filename": "test.txt",
                        "file_type": "text",
                        "parsed_at": "2024-01-01T12:00:00",
                        "total_messages": 10,
                        "case_id": "case-001",
                        "filepath": "",
                        "entity_type": "FILE",
                    }
                ]
            },
            # get_file (for delete_file)
            {
                "Items": [
                    {
                        "file_id": "file-1",
                        "filename": "test.txt",
                        "file_type": "text",
                        "parsed_at": "2024-01-01T12:00:00",
                        "total_messages": 10,
                        "case_id": "case-001",
                        "filepath": "",
                    }
                ]
            },
        ]
        mock_store._mock_table.delete_item = MagicMock()

        # When: 케이스 삭제
        mock_store.delete_case("case-001")

        # Then: delete_item이 2번 호출됨 (청크 1개 + 파일 1개)
        assert mock_store._mock_table.delete_item.call_count == 2


class TestDynamoDBMetadataStoreHelperMethods:
    """헬퍼 메서드 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 DynamoDBMetadataStore 인스턴스"""
        with patch("boto3.resource") as mock_boto3:
            mock_table = MagicMock()
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            mock_boto3.return_value = mock_dynamodb

            from src.storage.dynamodb_metadata_store import DynamoDBMetadataStore

            store = DynamoDBMetadataStore(
                table_name="test-table", region_name="ap-northeast-2"
            )
            yield store

    def test_item_to_evidence_file(self, mock_store):
        """DynamoDB 아이템을 EvidenceFile로 변환 테스트"""
        # Given: DynamoDB 아이템
        item = {
            "file_id": "file-123",
            "filename": "test.txt",
            "file_type": "text",
            "parsed_at": "2024-01-01T12:00:00",
            "total_messages": 50,
            "case_id": "case-001",
            "filepath": "/tmp/test.txt",
        }

        # When: 변환
        result = mock_store._item_to_evidence_file(item)

        # Then: EvidenceFile 객체
        assert result.file_id == "file-123"
        assert result.filename == "test.txt"
        assert result.total_messages == 50
        assert result.parsed_at == datetime(2024, 1, 1, 12, 0, 0)

    def test_item_to_evidence_chunk_with_decimal_score(self, mock_store):
        """DynamoDB 아이템을 EvidenceChunk로 변환 테스트 (Decimal 점수)"""
        # Given: DynamoDB 아이템 (Decimal 점수 포함)
        item = {
            "chunk_id": "chunk-123",
            "file_id": "file-456",
            "content": "테스트 내용",
            "score": Decimal("8.5"),
            "timestamp": "2024-01-01T12:30:00",
            "sender": "홍길동",
            "vector_id": "vec-789",
            "case_id": "case-001",
        }

        # When: 변환
        result = mock_store._item_to_evidence_chunk(item)

        # Then: EvidenceChunk 객체 (score는 float)
        assert result.chunk_id == "chunk-123"
        assert result.score == 8.5
        assert isinstance(result.score, float)

    def test_item_to_evidence_chunk_without_score(self, mock_store):
        """DynamoDB 아이템을 EvidenceChunk로 변환 테스트 (점수 없음)"""
        # Given: DynamoDB 아이템 (점수 없음)
        item = {
            "chunk_id": "chunk-123",
            "file_id": "file-456",
            "content": "테스트 내용",
            "timestamp": "2024-01-01T12:30:00",
            "sender": "홍길동",
            "case_id": "case-001",
        }

        # When: 변환
        result = mock_store._item_to_evidence_chunk(item)

        # Then: score는 None
        assert result.score is None
