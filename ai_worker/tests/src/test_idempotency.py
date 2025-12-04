"""
Test suite for Idempotency & Duplicate Prevention (Issue #85)

Tests:
- SHA-256 hash calculation
- Duplicate detection via hash
- Conditional DynamoDB writes
- Concurrent processing protection
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from botocore.exceptions import ClientError

from src.utils.hash import (
    calculate_file_hash,
    calculate_content_hash,
    is_duplicate_by_hash
)
from src.storage.metadata_store import MetadataStore, DuplicateError
from src.storage.schemas import EvidenceFile


class TestHashUtilities:
    """Test SHA-256 hash calculation utilities"""

    def test_calculate_file_hash(self):
        """Test file hash calculation"""
        # Create temp file with known content
        content = b"Test content for hashing"
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            file_hash = calculate_file_hash(temp_path)

            # SHA-256 produces 64-character hex string
            assert len(file_hash) == 64
            assert file_hash.isalnum()

            # Same content should produce same hash
            hash2 = calculate_file_hash(temp_path)
            assert file_hash == hash2
        finally:
            os.unlink(temp_path)

    def test_calculate_file_hash_different_content(self):
        """Test that different content produces different hashes"""
        content1 = b"First content"
        content2 = b"Second content"

        with tempfile.NamedTemporaryFile(delete=False) as f1:
            f1.write(content1)
            path1 = f1.name

        with tempfile.NamedTemporaryFile(delete=False) as f2:
            f2.write(content2)
            path2 = f2.name

        try:
            hash1 = calculate_file_hash(path1)
            hash2 = calculate_file_hash(path2)

            assert hash1 != hash2
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_calculate_content_hash(self):
        """Test content string hash calculation"""
        content = "Test string content"
        hash1 = calculate_content_hash(content)

        assert len(hash1) == 64
        assert hash1.isalnum()

        # Same content = same hash
        hash2 = calculate_content_hash(content)
        assert hash1 == hash2

        # Different content = different hash
        hash3 = calculate_content_hash("Different content")
        assert hash1 != hash3

    def test_is_duplicate_by_hash(self):
        """Test duplicate detection by hash"""
        existing_hashes = {"abc123", "def456", "ghi789"}

        assert is_duplicate_by_hash("abc123", existing_hashes) is True
        assert is_duplicate_by_hash("xyz999", existing_hashes) is False


class TestIdempotencyMetadataStore:
    """Test MetadataStore idempotency methods"""

    @pytest.fixture
    def mock_dynamodb_client(self):
        """Mock DynamoDB client"""
        with patch('boto3.client') as mock_client:
            mock_ddb = MagicMock()
            mock_client.return_value = mock_ddb
            yield mock_ddb

    @pytest.fixture
    def metadata_store(self, mock_dynamodb_client):
        """MetadataStore with mocked DynamoDB"""
        with patch.dict('os.environ', {
            'DDB_EVIDENCE_TABLE': 'test_table',
            'AWS_REGION': 'ap-northeast-2'
        }, clear=True):
            store = MetadataStore(table_name='test_table', region='ap-northeast-2')
            store._client = mock_dynamodb_client
            return store

    def test_check_hash_exists_found(self, metadata_store, mock_dynamodb_client):
        """Test hash existence check - hash found"""
        mock_dynamodb_client.query.return_value = {
            'Items': [{
                'evidence_id': {'S': 'ev_existing'},
                'file_hash': {'S': 'abc123def456'},
                'status': {'S': 'processed'}
            }]
        }

        result = metadata_store.check_hash_exists('abc123def456')

        assert result is not None
        assert result['evidence_id'] == 'ev_existing'

    def test_check_hash_exists_not_found(self, metadata_store, mock_dynamodb_client):
        """Test hash existence check - hash not found"""
        mock_dynamodb_client.query.return_value = {'Items': []}

        result = metadata_store.check_hash_exists('nonexistent_hash')

        assert result is None

    def test_check_hash_exists_gsi_fallback(self, metadata_store, mock_dynamodb_client):
        """Test hash check falls back to scan when GSI doesn't exist"""
        # First call (GSI) raises ValidationException
        mock_dynamodb_client.query.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'GSI not found'}},
            'Query'
        )
        # Scan returns result
        mock_dynamodb_client.scan.return_value = {
            'Items': [{
                'evidence_id': {'S': 'ev_found'},
                'file_hash': {'S': 'abc123'}
            }]
        }

        result = metadata_store.check_hash_exists('abc123')

        assert result is not None
        mock_dynamodb_client.scan.assert_called_once()

    def test_check_evidence_processed_true(self, metadata_store, mock_dynamodb_client):
        """Test check if evidence is already processed - true"""
        mock_dynamodb_client.get_item.return_value = {
            'Item': {
                'evidence_id': {'S': 'ev_123'},
                'status': {'S': 'processed'}
            }
        }

        result = metadata_store.check_evidence_processed('ev_123')

        assert result is True

    def test_check_evidence_processed_false(self, metadata_store, mock_dynamodb_client):
        """Test check if evidence is processed - false (pending)"""
        mock_dynamodb_client.get_item.return_value = {
            'Item': {
                'evidence_id': {'S': 'ev_123'},
                'status': {'S': 'pending'}
            }
        }

        result = metadata_store.check_evidence_processed('ev_123')

        assert result is False

    def test_check_evidence_processed_not_exists(self, metadata_store, mock_dynamodb_client):
        """Test check if evidence is processed - not exists"""
        mock_dynamodb_client.get_item.return_value = {}

        result = metadata_store.check_evidence_processed('ev_nonexistent')

        assert result is False

    def test_save_file_if_not_exists_success(self, metadata_store, mock_dynamodb_client):
        """Test conditional save - success when not exists"""
        file = EvidenceFile(
            file_id="new_file",
            filename="test.txt",
            file_type="text",
            parsed_at=datetime.now(timezone.utc),
            total_messages=10,
            case_id="case001"
        )

        result = metadata_store.save_file_if_not_exists(file, "hash123")

        assert result is True
        mock_dynamodb_client.put_item.assert_called_once()
        call_args = mock_dynamodb_client.put_item.call_args
        assert 'ConditionExpression' in call_args.kwargs
        assert call_args.kwargs['ConditionExpression'] == 'attribute_not_exists(evidence_id)'

    def test_save_file_if_not_exists_duplicate(self, metadata_store, mock_dynamodb_client):
        """Test conditional save - fails when already exists"""
        mock_dynamodb_client.put_item.side_effect = ClientError(
            {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Already exists'}},
            'PutItem'
        )

        file = EvidenceFile(
            file_id="existing_file",
            filename="test.txt",
            file_type="text",
            parsed_at=datetime.now(timezone.utc),
            total_messages=10,
            case_id="case001"
        )

        with pytest.raises(DuplicateError):
            metadata_store.save_file_if_not_exists(file, "hash123")

    def test_update_evidence_with_hash_success(self, metadata_store, mock_dynamodb_client):
        """Test conditional update - success"""
        result = metadata_store.update_evidence_with_hash(
            evidence_id="ev_123",
            file_hash="hash456",
            status="processed",
            ai_summary="Test summary",
            skip_if_processed=True
        )

        assert result is True
        mock_dynamodb_client.update_item.assert_called_once()
        call_args = mock_dynamodb_client.update_item.call_args
        assert 'ConditionExpression' in call_args.kwargs

    def test_update_evidence_with_hash_already_processed(self, metadata_store, mock_dynamodb_client):
        """Test conditional update - skipped because already processed"""
        mock_dynamodb_client.update_item.side_effect = ClientError(
            {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Already processed'}},
            'UpdateItem'
        )

        result = metadata_store.update_evidence_with_hash(
            evidence_id="ev_123",
            file_hash="hash456",
            status="processed",
            skip_if_processed=True
        )

        assert result is False

    def test_update_evidence_with_hash_no_condition(self, metadata_store, mock_dynamodb_client):
        """Test update without condition check"""
        result = metadata_store.update_evidence_with_hash(
            evidence_id="ev_123",
            file_hash="hash456",
            status="processed",
            skip_if_processed=False  # Force update
        )

        assert result is True
        call_args = mock_dynamodb_client.update_item.call_args
        # No ConditionExpression when skip_if_processed=False
        assert 'ConditionExpression' not in call_args.kwargs

    def test_check_s3_key_exists_found(self, metadata_store, mock_dynamodb_client):
        """Test S3 key existence check - found"""
        mock_dynamodb_client.query.return_value = {
            'Items': [{
                'evidence_id': {'S': 'ev_123'},
                's3_key': {'S': 'cases/case001/raw/ev_123_file.txt'},
                'status': {'S': 'processed'}
            }]
        }

        result = metadata_store.check_s3_key_exists('cases/case001/raw/ev_123_file.txt')

        assert result is not None
        assert result['evidence_id'] == 'ev_123'

    def test_check_s3_key_exists_not_found(self, metadata_store, mock_dynamodb_client):
        """Test S3 key existence check - not found"""
        mock_dynamodb_client.query.return_value = {'Items': []}

        result = metadata_store.check_s3_key_exists('nonexistent_key')

        assert result is None


class TestHandlerIdempotency:
    """Test handler-level idempotency checks"""

    @pytest.fixture
    def mock_all_dependencies(self):
        """Mock all external dependencies for handler"""
        with patch('boto3.client') as mock_boto, \
             patch('handler.MetadataStore') as mock_store_class, \
             patch('handler.VectorStore') as mock_vector_class, \
             patch('handler.calculate_file_hash') as mock_hash:

            mock_s3 = MagicMock()
            mock_boto.return_value = mock_s3

            mock_store = MagicMock()
            mock_store_class.return_value = mock_store

            mock_vector = MagicMock()
            mock_vector_class.return_value = mock_vector

            mock_hash.return_value = "test_hash_123456"

            yield {
                's3': mock_s3,
                'metadata_store': mock_store,
                'vector_store': mock_vector,
                'hash': mock_hash
            }

    def test_handler_skips_already_processed(self, mock_all_dependencies):
        """Test handler skips already processed evidence"""
        from handler import route_and_process

        # Setup: evidence already processed
        mock_all_dependencies['metadata_store'].check_evidence_processed.return_value = True

        # Mock file download
        with patch('os.makedirs'), \
             patch('builtins.open', MagicMock()):

            result = route_and_process(
                bucket_name="test-bucket",
                object_key="cases/case001/raw/ev_abc123_file.txt"
            )

        assert result['status'] == 'skipped'
        assert result['reason'] == 'already_processed'

    def test_handler_skips_duplicate_hash(self, mock_all_dependencies):
        """Test handler skips file with duplicate hash"""
        from handler import route_and_process

        # Setup: not processed yet, but hash exists
        mock_all_dependencies['metadata_store'].check_evidence_processed.return_value = False
        mock_all_dependencies['metadata_store'].check_hash_exists.return_value = {
            'evidence_id': 'ev_existing',
            'status': 'processed'
        }

        with patch('os.makedirs'), \
             patch('builtins.open', MagicMock()):

            result = route_and_process(
                bucket_name="test-bucket",
                object_key="cases/case001/raw/ev_new_file.txt"
            )

        assert result['status'] == 'skipped'
        assert result['reason'] == 'duplicate_hash'
