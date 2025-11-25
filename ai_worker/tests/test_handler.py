"""
Test suite for handler.py - S3 Event Processing
Following TDD approach: RED-GREEN-REFACTOR

Phase 1: 2.1 Event 파싱 테스트
- S3 Event JSON bucket.name, object.key 추출
- 지원하지 않는 파일 확장자 DLQ 전송
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from handler import handle, route_and_process, route_parser


class TestS3EventParsing:
    """S3 이벤트 파싱 테스트 (2.1)"""

    def test_extract_bucket_and_key_from_valid_s3_event(self):
        """
        Given: 유효한 S3 ObjectCreated 이벤트
        When: handle() 함수로 이벤트 처리
        Then: bucket name과 object key가 정확히 추출됨
        """
        # Given
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "leh-evidence-bucket"},
                        "object": {"key": "cases/case123/evidence/document.pdf"}
                    }
                }
            ]
        }
        context = {}

        # When
        with patch('handler.route_and_process') as mock_process:
            mock_process.return_value = {"status": "processed"}
            result = handle(event, context)

        # Then
        mock_process.assert_called_once_with(
            "leh-evidence-bucket",
            "cases/case123/evidence/document.pdf"
        )
        assert result["statusCode"] == 200

    def test_handle_url_encoded_object_key_with_plus(self):
        """
        Given: + 기호로 인코딩된 공백이 있는 객체 키
        When: S3 이벤트 처리
        Then: 공백으로 올바르게 디코딩됨
        """
        # Given: 공백이 +로 인코딩된 경우
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "leh-bucket"},
                        "object": {"key": "folder/file+with+spaces.txt"}
                    }
                }
            ]
        }
        context = {}

        # When
        with patch('handler.route_and_process') as mock_process:
            mock_process.return_value = {"status": "processed"}
            handle(event, context)

        # Then: URL 디코딩된 키로 호출되어야 함 (+ → 공백)
        called_key = mock_process.call_args[0][1]
        assert called_key == "folder/file with spaces.txt"

    def test_handle_url_encoded_object_key_with_percent(self):
        """
        Given: %20으로 인코딩된 공백이 있는 객체 키
        When: S3 이벤트 처리
        Then: 공백으로 올바르게 디코딩됨
        """
        # Given: 공백이 %20으로 인코딩된 경우
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "leh-bucket"},
                        "object": {"key": "folder/file%20with%20spaces.txt"}
                    }
                }
            ]
        }
        context = {}

        # When
        with patch('handler.route_and_process') as mock_process:
            mock_process.return_value = {"status": "processed"}
            handle(event, context)

        # Then: URL 디코딩된 키로 호출되어야 함 (%20 → 공백)
        called_key = mock_process.call_args[0][1]
        assert called_key == "folder/file with spaces.txt"

    def test_ignore_non_s3_events(self):
        """
        Given: S3 Records가 없는 이벤트
        When: handle() 함수 호출
        Then: 무시되고 적절한 상태 반환
        """
        # Given
        event = {"test": "data"}  # No Records field
        context = {}

        # When
        result = handle(event, context)

        # Then
        assert result["status"] == "ignored"
        assert result["reason"] == "No S3 Records found"

    def test_process_multiple_s3_records(self):
        """
        Given: 여러 개의 S3 레코드를 가진 이벤트
        When: handle() 함수 호출
        Then: 모든 레코드가 처리됨
        """
        # Given
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "bucket1"},
                        "object": {"key": "file1.pdf"}
                    }
                },
                {
                    "s3": {
                        "bucket": {"name": "bucket2"},
                        "object": {"key": "file2.jpg"}
                    }
                }
            ]
        }
        context = {}

        # When
        with patch('handler.route_and_process') as mock_process:
            mock_process.return_value = {"status": "processed"}
            result = handle(event, context)

        # Then
        assert mock_process.call_count == 2
        result_body = json.loads(result["body"])
        assert len(result_body["results"]) == 2


class TestUnsupportedFileTypes:
    """지원하지 않는 파일 타입 처리 테스트 (2.1)"""

    def test_skip_unsupported_file_extension(self):
        """
        Given: 지원하지 않는 확장자 (.xyz)
        When: route_and_process() 호출
        Then: status='skipped' 반환
        """
        # Given
        bucket = "test-bucket"
        key = "folder/unsupported.xyz"

        # When
        result = route_and_process(bucket, key)

        # Then
        assert result["status"] == "skipped"
        assert "unsupported" in result["reason"].lower()
        assert result["file"] == key

    def test_supported_file_extensions(self):
        """
        Given: 지원되는 확장자들
        When: route_parser() 호출
        Then: 적절한 파서 반환
        """
        # PDF
        assert route_parser('.pdf') is not None
        assert route_parser('.PDF') is not None  # 대소문자 무시

        # Images
        assert route_parser('.jpg') is not None
        assert route_parser('.png') is not None

        # Audio
        assert route_parser('.mp3') is not None
        assert route_parser('.wav') is not None

        # Video
        assert route_parser('.mp4') is not None

        # Text
        assert route_parser('.txt') is not None

    def test_unsupported_extensions_return_none(self):
        """
        Given: 지원하지 않는 확장자들
        When: route_parser() 호출
        Then: None 반환
        """
        # Unsupported extensions
        assert route_parser('.xyz') is None
        assert route_parser('.docx') is None
        assert route_parser('.exe') is None


class TestFileProcessing:
    """파일 타입별 처리 테스트 (2.2)"""

    @patch('handler.boto3')
    def test_download_file_from_s3(self, mock_boto3):
        """
        Given: S3에 PDF 파일이 존재
        When: route_and_process() 호출
        Then: S3에서 파일을 /tmp로 다운로드
        """
        # Given
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client
        bucket = "test-bucket"
        key = "test-file.pdf"

        # When
        with patch('handler.route_parser') as mock_parser:
            mock_parser_instance = Mock()
            mock_parser_instance.parse.return_value = {
                "content": "test content",
                "metadata": {}
            }
            mock_parser.return_value = mock_parser_instance

            route_and_process(bucket, key)

        # Then: S3 client가 파일을 다운로드했는지 확인
        mock_boto3.client.assert_called_once_with('s3')
        mock_s3_client.download_file.assert_called_once()
        # 다운로드 위치가 /tmp인지 확인
        call_args = mock_s3_client.download_file.call_args[0]
        assert call_args[0] == bucket
        assert call_args[1] == key
        assert '/tmp' in call_args[2] or 'tmp' in call_args[2].lower()

    @pytest.mark.skip(reason="Storage integration tested in test_real_integration.py with actual files")
    def test_execute_parser_on_downloaded_file(self):
        """
        This test is skipped because the full storage integration is now tested
        in test_real_integration.py using actual files and real storage backends.
        """
        pass


class TestErrorHandling:
    """에러 처리 테스트"""

    def test_handle_malformed_s3_record(self):
        """
        Given: 잘못된 형식의 S3 레코드
        When: handle() 호출
        Then: 에러 상태 반환하고 계속 진행
        """
        # Given
        event = {
            "Records": [
                {
                    "s3": {
                        # Missing bucket or object
                        "bucket": {}
                    }
                }
            ]
        }
        context = {}

        # When
        result = handle(event, context)

        # Then
        result_body = json.loads(result["body"])
        # 에러가 발생하더라도 statusCode는 200이어야 함 (Lambda 재시도 방지)
        assert result["statusCode"] == 200

    def test_error_in_processing_returns_error_status(self):
        """
        Given: 파일 처리 중 예외 발생
        When: route_and_process() 호출
        Then: error status 반환
        """
        # Given
        bucket = "test-bucket"
        key = "test-file.pdf"

        # When
        with patch('handler.route_parser', side_effect=Exception("Test error")):
            result = route_and_process(bucket, key)

        # Then
        assert result["status"] == "error"
        assert "error" in result
        assert result["file"] == key


@pytest.mark.skip(reason="Storage integration fully tested in test_real_integration.py")
class TestStorageAndAnalysisIntegration:
    """
    Phase 6: 스토리지 및 분석 통합 테스트 (2.6)

    NOTE: These tests are skipped because the full storage integration pipeline
    is now tested in test_real_integration.py using:
    - Real fixture files (kakaotalk_sample.txt)
    - Real ChromaDB and SQLite storage
    - Real OpenAI API (mocked at API level only)
    - Real parsing and indexing pipeline

    See test_real_integration.py for comprehensive coverage of:
    - MetadataStore.save_file() operations
    - VectorStore.add_evidence() operations
    - Article840Tagger.tag() operations
    - Complete processing result verification
    """

    def test_save_metadata_to_store(self):
        """Covered by test_real_integration.py::test_metadata_file_saved"""
        pass

    def test_index_all_chunks_to_vector_store(self):
        """Covered by test_real_integration.py::test_vector_store_indexed"""
        pass

    def test_tag_all_messages_with_article_840(self):
        """Covered by test_real_integration.py::test_article_840_tagging"""
        pass

    def test_return_complete_processing_result(self):
        """Covered by test_real_integration.py::test_full_pipeline_integration"""
        pass
