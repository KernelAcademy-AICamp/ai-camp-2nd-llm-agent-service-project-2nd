"""
Test suite for MetadataStore (DynamoDB)
Uses mocking to avoid actual AWS calls
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.storage.metadata_store import MetadataStore
from src.storage.schemas import EvidenceFile, EvidenceChunk


@pytest.fixture
def mock_dynamodb_client():
    """Mock DynamoDB client"""
    with patch('boto3.client') as mock_client:
        mock_ddb = MagicMock()
        mock_client.return_value = mock_ddb
        yield mock_ddb


@pytest.fixture
def metadata_store(mock_dynamodb_client):
    """MetadataStore with mocked DynamoDB"""
    with patch.dict('os.environ', {
        'DYNAMODB_TABLE': 'test_table',
        'AWS_REGION': 'ap-northeast-2'
    }):
        store = MetadataStore(table_name='test_table', region='ap-northeast-2')
        store._client = mock_dynamodb_client
        return store


class TestMetadataStoreInitialization:
    """Test MetadataStore initialization"""

    def test_metadata_store_creation(self):
        """MetadataStore 생성 테스트"""
        with patch.dict('os.environ', {
            'DYNAMODB_TABLE': 'test_table',
            'AWS_REGION': 'ap-northeast-2'
        }):
            with patch('boto3.client'):
                store = MetadataStore()
                assert store is not None
                assert store.table_name == 'test_table'
                assert store.region == 'ap-northeast-2'

    def test_metadata_store_with_custom_params(self):
        """커스텀 파라미터로 생성 테스트"""
        with patch('boto3.client'):
            store = MetadataStore(
                table_name='custom_table',
                region='us-west-2'
            )
            assert store.table_name == 'custom_table'
            assert store.region == 'us-west-2'


class TestEvidenceFileOperations:
    """Test evidence file CRUD operations"""

    def test_save_evidence_file(self, metadata_store, mock_dynamodb_client):
        """증거 파일 저장 테스트"""
        file = EvidenceFile(
            filename="chat.txt",
            file_type="kakaotalk",
            total_messages=10,
            case_id="case001"
        )

        metadata_store.save_file(file)

        # DynamoDB put_item이 호출되었는지 확인
        mock_dynamodb_client.put_item.assert_called_once()
        call_args = mock_dynamodb_client.put_item.call_args
        assert call_args.kwargs['TableName'] == 'test_table'
        assert 'Item' in call_args.kwargs

    def test_get_evidence_file(self, metadata_store, mock_dynamodb_client):
        """증거 파일 조회 테스트"""
        # Mock 응답 설정
        mock_dynamodb_client.get_item.return_value = {
            'Item': {
                'evidence_id': {'S': 'file001'},
                'file_id': {'S': 'file001'},
                'filename': {'S': 'chat.txt'},
                'file_type': {'S': 'kakaotalk'},
                'parsed_at': {'S': '2024-01-15T10:30:00'},
                'total_messages': {'N': '10'},
                'case_id': {'S': 'case001'},
                'filepath': {'NULL': True}
            }
        }

        result = metadata_store.get_file('file001')

        assert result is not None
        assert result.filename == 'chat.txt'
        assert result.total_messages == 10
        assert result.case_id == 'case001'

    def test_get_nonexistent_file(self, metadata_store, mock_dynamodb_client):
        """존재하지 않는 파일 조회 테스트"""
        mock_dynamodb_client.get_item.return_value = {}

        result = metadata_store.get_file("nonexistent-id")
        assert result is None

    def test_get_files_by_case_id(self, metadata_store, mock_dynamodb_client):
        """케이스 ID로 파일 조회 테스트"""
        # Mock 응답 설정
        mock_dynamodb_client.query.return_value = {
            'Items': [
                {
                    'evidence_id': {'S': f'file{i}'},
                    'file_id': {'S': f'file{i}'},
                    'filename': {'S': f'file{i}.txt'},
                    'file_type': {'S': 'text'},
                    'parsed_at': {'S': '2024-01-15T10:30:00'},
                    'total_messages': {'N': '5'},
                    'case_id': {'S': 'case001'},
                    'filepath': {'NULL': True},
                    'record_type': {'S': 'file'}
                }
                for i in range(3)
            ]
        }

        files = metadata_store.get_files_by_case("case001")

        assert len(files) == 3
        assert all(f.case_id == "case001" for f in files)

    def test_delete_evidence_file(self, metadata_store, mock_dynamodb_client):
        """증거 파일 삭제 테스트"""
        metadata_store.delete_file("file001")

        mock_dynamodb_client.delete_item.assert_called_once()
        call_args = mock_dynamodb_client.delete_item.call_args
        assert call_args.kwargs['Key']['evidence_id']['S'] == 'file001'


class TestEvidenceChunkOperations:
    """Test evidence chunk CRUD operations"""

    def test_save_evidence_chunk(self, metadata_store, mock_dynamodb_client):
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

        mock_dynamodb_client.put_item.assert_called_once()
        call_args = mock_dynamodb_client.put_item.call_args
        item = call_args.kwargs['Item']
        assert item['content']['S'] == "테스트 메시지"
        assert item['sender']['S'] == "홍길동"

    def test_save_multiple_chunks(self, metadata_store, mock_dynamodb_client):
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

        # put_item 호출 확인 (개별 저장으로 변경됨)
        assert mock_dynamodb_client.put_item.call_count == 5

    def test_get_chunk(self, metadata_store, mock_dynamodb_client):
        """청크 조회 테스트"""
        mock_dynamodb_client.get_item.return_value = {
            'Item': {
                'evidence_id': {'S': 'chunk_chunk001'},
                'chunk_id': {'S': 'chunk001'},
                'file_id': {'S': 'file001'},
                'content': {'S': '테스트 메시지'},
                'score': {'NULL': True},
                'timestamp': {'S': '2024-01-15T10:30:00'},
                'sender': {'S': '홍길동'},
                'vector_id': {'S': 'vector123'},
                'case_id': {'S': 'case001'}
            }
        }

        result = metadata_store.get_chunk('chunk001')

        assert result is not None
        assert result.content == '테스트 메시지'
        assert result.sender == '홍길동'

    def test_get_chunks_by_case_id(self, metadata_store, mock_dynamodb_client):
        """케이스 ID로 청크 조회 테스트"""
        mock_dynamodb_client.query.return_value = {
            'Items': [
                {
                    'evidence_id': {'S': f'chunk_chunk{i}'},
                    'chunk_id': {'S': f'chunk{i}'},
                    'file_id': {'S': f'file{i}'},
                    'content': {'S': f'메시지{i}'},
                    'score': {'NULL': True},
                    'timestamp': {'S': '2024-01-15T10:30:00'},
                    'sender': {'S': '홍길동'},
                    'vector_id': {'NULL': True},
                    'case_id': {'S': 'case001'},
                    'record_type': {'S': 'chunk'}
                }
                for i in range(3)
            ]
        }

        chunks = metadata_store.get_chunks_by_case("case001")

        assert len(chunks) == 3
        assert all(c.case_id == "case001" for c in chunks)

    def test_update_chunk_score(self, metadata_store, mock_dynamodb_client):
        """청크 점수 업데이트 테스트"""
        metadata_store.update_chunk_score("chunk001", 8.5)

        mock_dynamodb_client.update_item.assert_called_once()
        call_args = mock_dynamodb_client.update_item.call_args
        assert call_args.kwargs['ExpressionAttributeValues'][':score']['N'] == '8.5'

    def test_delete_evidence_chunk(self, metadata_store, mock_dynamodb_client):
        """증거 청크 삭제 테스트"""
        metadata_store.delete_chunk("chunk001")

        mock_dynamodb_client.delete_item.assert_called_once()


class TestStatistics:
    """Test statistics and aggregation methods"""

    def test_count_files_by_case(self, metadata_store, mock_dynamodb_client):
        """케이스별 파일 개수 테스트"""
        mock_dynamodb_client.query.return_value = {'Count': 3}

        count = metadata_store.count_files_by_case("case001")
        assert count == 3

    def test_count_chunks_by_case(self, metadata_store, mock_dynamodb_client):
        """케이스별 청크 개수 테스트"""
        mock_dynamodb_client.query.return_value = {'Count': 5}

        count = metadata_store.count_chunks_by_case("case001")
        assert count == 5

    def test_get_case_summary(self, metadata_store, mock_dynamodb_client):
        """케이스 요약 정보 테스트"""
        # 파일 카운트와 청크 카운트에 대한 별도 응답
        mock_dynamodb_client.query.side_effect = [
            {'Count': 2},  # file count
            {'Count': 10}  # chunk count
        ]

        summary = metadata_store.get_case_summary("case001")

        assert summary["file_count"] == 2
        assert summary["chunk_count"] == 10
        assert summary["case_id"] == "case001"


class TestCaseManagement:
    """Test case management operations"""

    def test_list_cases(self, metadata_store, mock_dynamodb_client):
        """케이스 목록 조회 테스트"""
        mock_dynamodb_client.scan.return_value = {
            'Items': [
                {'case_id': {'S': 'case001'}},
                {'case_id': {'S': 'case002'}},
                {'case_id': {'S': 'case003'}}
            ]
        }

        cases = metadata_store.list_cases()

        assert len(cases) == 3
        assert 'case001' in cases

    def test_delete_case(self, metadata_store, mock_dynamodb_client):
        """케이스 삭제 테스트"""
        # Query 결과 설정
        mock_dynamodb_client.query.return_value = {
            'Items': [
                {'evidence_id': {'S': 'file001'}},
                {'evidence_id': {'S': 'chunk_chunk001'}}
            ]
        }

        metadata_store.delete_case("case001")

        # delete_item이 2번 호출되었는지 확인
        assert mock_dynamodb_client.delete_item.call_count == 2
