"""
Test suite for handler.py - S3 Event Processing
Following TDD approach: RED-GREEN-REFACTOR

Phase 1: 2.1 Event 파싱 테스트
- S3 Event JSON bucket.name, object.key 추출
- 지원하지 않는 파일 확장자 DLQ 전송
"""

import json
from unittest.mock import Mock, patch
from handler import (
    handle,
    route_and_process,
    route_parser,
    _extract_case_id,
    _extract_evidence_id_from_s3_key
)


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

    @patch('handler.boto3')
    @patch('handler.MetadataStore')
    @patch('handler.VectorStore')
    @patch('handler.Article840Tagger')
    def test_execute_parser_on_downloaded_file(
        self,
        mock_tagger_class,
        mock_vector_class,
        mock_metadata_class,
        mock_boto3
    ):
        """
        Given: S3에서 파일을 다운로드
        When: route_and_process() 호출
        Then: 적절한 파서로 파일을 파싱
        """
        # Given
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client
        bucket = "test-bucket"
        key = "document.txt"

        # MetadataStore mock
        mock_metadata_instance = Mock()
        mock_metadata_instance.save_file.return_value = {
            'file_id': 'test-id',
            'case_id': bucket,
            'file_path': key,
            'file_type': '.txt',
            'created_at': '2024-01-01T00:00:00'
        }
        mock_metadata_class.return_value = mock_metadata_instance

        # VectorStore mock
        mock_vector_instance = Mock()
        mock_vector_instance.add_chunk_with_metadata.return_value = 'chunk-id'
        mock_vector_class.return_value = mock_vector_instance

        # Article840Tagger mock
        mock_tagger_instance = Mock()
        mock_tagging_result = Mock()
        mock_tagging_result.categories = []
        mock_tagging_result.confidence = 0.0
        mock_tagging_result.matched_keywords = []
        mock_tagger_instance.tag.return_value = mock_tagging_result
        mock_tagger_class.return_value = mock_tagger_instance

        # When
        with patch('handler.route_parser') as mock_parser:
            mock_parser_instance = Mock()
            mock_message = Mock()
            mock_message.content = "parsed text content"
            mock_message.sender = "System"
            mock_message.timestamp = None
            mock_message.metadata = {"source_type": "text"}
            mock_parser_instance.parse.return_value = [mock_message]
            mock_parser.return_value = mock_parser_instance

            result = route_and_process(bucket, key)

        # Then: 파서가 실행되었는지 확인
        mock_parser_instance.parse.assert_called_once()
        # 파싱 결과가 반환에 포함되는지 확인
        assert result["status"] == "processed"


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


class TestStorageAndAnalysisIntegration:
    """Phase 6: 스토리지 및 분석 통합 테스트 (2.6)"""

    @patch('handler.boto3')
    @patch('handler.MetadataStore')
    @patch('handler.VectorStore')
    @patch('handler.Article840Tagger')
    def test_save_metadata_to_store(
        self,
        mock_tagger_class,
        mock_vector_class,
        mock_metadata_class,
        mock_boto3
    ):
        """
        Given: PDF 파일 파싱 완료
        When: route_and_process() 호출
        Then: MetadataStore.save_file() 호출됨
        """
        # Given
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # MetadataStore mock
        mock_metadata_instance = Mock()
        mock_metadata_instance.save_file.return_value = {
            'file_id': 'test-file-id-123',
            'case_id': 'test-bucket',
            'file_path': 'test.pdf',
            'file_type': '.pdf',
            'created_at': '2024-01-01T00:00:00'
        }
        mock_metadata_class.return_value = mock_metadata_instance

        # VectorStore mock
        mock_vector_instance = Mock()
        mock_vector_instance.add_chunk_with_metadata.return_value = 'chunk-id-1'
        mock_vector_class.return_value = mock_vector_instance

        # Article840Tagger mock
        mock_tagger_instance = Mock()
        mock_tagging_result = Mock()
        mock_tagging_result.categories = []
        mock_tagging_result.confidence = 0.0
        mock_tagging_result.matched_keywords = []
        mock_tagger_instance.tag.return_value = mock_tagging_result
        mock_tagger_class.return_value = mock_tagger_instance

        # Parser mock
        with patch('handler.route_parser') as mock_parser:
            mock_parser_instance = Mock()
            mock_message = Mock()
            mock_message.content = "test content"
            mock_message.sender = "System"
            mock_message.timestamp = None
            mock_message.metadata = {"source_type": "text"}
            mock_parser_instance.parse.return_value = [mock_message]
            mock_parser.return_value = mock_parser_instance

            # When
            result = route_and_process("test-bucket", "test.pdf")

        # Then: save_file가 EvidenceFile 객체로 호출됨
        mock_metadata_instance.save_file.assert_called_once()
        # file_id는 동적으로 생성되므로 패턴만 확인
        assert result["file_id"].startswith("file_")
        assert result["status"] == "processed"

    @patch('handler.boto3')
    @patch('handler.MetadataStore')
    @patch('handler.VectorStore')
    @patch('handler.Article840Tagger')
    def test_index_all_chunks_to_vector_store(
        self,
        mock_tagger_class,
        mock_vector_class,
        mock_metadata_class,
        mock_boto3
    ):
        """
        Given: 여러 청크로 파싱된 파일
        When: route_and_process() 호출
        Then: 모든 청크가 VectorStore.add_chunk_with_metadata()로 인덱싱됨
        """
        # Given
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # MetadataStore mock
        mock_metadata_instance = Mock()
        mock_metadata_instance.save_file.return_value = {
            'file_id': 'file-123',
            'case_id': 'bucket',
            'file_path': 'chat.txt',
            'file_type': '.txt',
            'created_at': '2024-01-01T00:00:00'
        }
        mock_metadata_class.return_value = mock_metadata_instance

        # VectorStore mock
        mock_vector_instance = Mock()
        mock_vector_instance.add_chunk_with_metadata.side_effect = ['chunk-1', 'chunk-2', 'chunk-3']
        mock_vector_class.return_value = mock_vector_instance

        # Article840Tagger mock
        mock_tagger_instance = Mock()
        mock_tagging_result = Mock()
        mock_tagging_result.categories = []
        mock_tagging_result.confidence = 0.0
        mock_tagging_result.matched_keywords = []
        mock_tagger_instance.tag.return_value = mock_tagging_result
        mock_tagger_class.return_value = mock_tagger_instance

        # Parser mock - 3개의 메시지 반환
        with patch('handler.route_parser') as mock_parser:
            mock_parser_instance = Mock()
            messages = []
            for i in range(3):
                msg = Mock()
                msg.content = f"message {i}"
                msg.sender = f"user{i}"
                msg.timestamp = None
                msg.metadata = {"source_type": "kakaotalk"}
                messages.append(msg)
            mock_parser_instance.parse.return_value = messages
            mock_parser.return_value = mock_parser_instance

            # When
            result = route_and_process("bucket", "chat.txt")

        # Then
        assert mock_vector_instance.add_chunk_with_metadata.call_count == 3
        assert result["chunks_indexed"] == 3
        assert result["file_id"].startswith("file_")

    @patch('handler.boto3')
    @patch('handler.MetadataStore')
    @patch('handler.VectorStore')
    @patch('handler.Article840Tagger')
    def test_tag_all_messages_with_article_840(
        self,
        mock_tagger_class,
        mock_vector_class,
        mock_metadata_class,
        mock_boto3
    ):
        """
        Given: 파싱된 메시지들
        When: route_and_process() 호출
        Then: 각 메시지에 대해 Article840Tagger.tag() 호출됨
        """
        # Given
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # MetadataStore mock
        mock_metadata_instance = Mock()
        mock_metadata_instance.save_file.return_value = {
            'file_id': 'file-123',
            'case_id': 'bucket',
            'file_path': 'evidence.txt',
            'file_type': '.txt',
            'created_at': '2024-01-01T00:00:00'
        }
        mock_metadata_class.return_value = mock_metadata_instance

        # VectorStore mock
        mock_vector_instance = Mock()
        mock_vector_instance.add_chunk_with_metadata.return_value = 'chunk-id'
        mock_vector_class.return_value = mock_vector_instance

        # Article840Tagger mock
        from src.analysis.article_840_tagger import Article840Category
        mock_tagger_instance = Mock()
        mock_tagging_result = Mock()
        mock_tagging_result.categories = [Article840Category.ADULTERY]
        mock_tagging_result.confidence = 0.85
        mock_tagging_result.matched_keywords = ["외도", "불륜"]
        mock_tagger_instance.tag.return_value = mock_tagging_result
        mock_tagger_class.return_value = mock_tagger_instance

        # Parser mock - 2개의 메시지
        with patch('handler.route_parser') as mock_parser:
            mock_parser_instance = Mock()
            msg1 = Mock()
            msg1.content = "외도 증거"
            msg1.sender = "user1"
            msg1.timestamp = None
            msg1.metadata = {"source_type": "text"}
            msg2 = Mock()
            msg2.content = "불륜 관련"
            msg2.sender = "user2"
            msg2.timestamp = None
            msg2.metadata = {"source_type": "text"}
            mock_parser_instance.parse.return_value = [msg1, msg2]
            mock_parser.return_value = mock_parser_instance

            # When
            result = route_and_process("bucket", "evidence.txt")

        # Then
        assert mock_tagger_instance.tag.call_count == 2
        assert "tags" in result
        assert len(result["tags"]) == 2
        # 첫 번째 태그 검증
        first_tag = result["tags"][0]
        assert "adultery" in first_tag["categories"]
        assert first_tag["confidence"] == 0.85
        assert "외도" in first_tag["matched_keywords"]

    @patch('handler.boto3')
    @patch('handler.MetadataStore')
    @patch('handler.VectorStore')
    @patch('handler.Article840Tagger')
    def test_return_complete_processing_result(
        self,
        mock_tagger_class,
        mock_vector_class,
        mock_metadata_class,
        mock_boto3
    ):
        """
        Given: 파일 처리 완료
        When: route_and_process() 호출
        Then: file_id, chunks_indexed, tags를 포함한 결과 반환
        """
        # Given
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # MetadataStore mock
        mock_metadata_instance = Mock()
        mock_metadata_instance.save_file.return_value = {
            'file_id': 'complete-file-id',
            'case_id': 'complete-bucket',
            'file_path': 'complete.pdf',
            'file_type': '.pdf',
            'created_at': '2024-01-01T00:00:00'
        }
        mock_metadata_class.return_value = mock_metadata_instance

        # VectorStore mock
        mock_vector_instance = Mock()
        mock_vector_instance.add_chunk_with_metadata.side_effect = ['c1', 'c2']
        mock_vector_class.return_value = mock_vector_instance

        # Article840Tagger mock
        mock_tagger_instance = Mock()
        mock_tagging_result = Mock()
        mock_tagging_result.categories = []
        mock_tagging_result.confidence = 0.5
        mock_tagging_result.matched_keywords = []
        mock_tagger_instance.tag.return_value = mock_tagging_result
        mock_tagger_class.return_value = mock_tagger_instance

        # Parser mock
        with patch('handler.route_parser') as mock_parser:
            mock_parser_instance = Mock()
            msg1 = Mock()
            msg1.content = "content1"
            msg1.sender = "System"
            msg1.timestamp = None
            msg1.metadata = {"source_type": "pdf"}
            msg2 = Mock()
            msg2.content = "content2"
            msg2.sender = "System"
            msg2.timestamp = None
            msg2.metadata = {"source_type": "pdf"}
            mock_parser_instance.parse.return_value = [msg1, msg2]
            mock_parser.return_value = mock_parser_instance

            # When
            result = route_and_process("complete-bucket", "complete.pdf")

        # Then
        assert result["status"] == "processed"
        assert result["file"] == "complete.pdf"
        assert result["file_id"].startswith("file_")
        assert result["chunks_indexed"] == 2
        assert result["tags"] == [
            {"categories": [], "confidence": 0.5, "matched_keywords": []},
            {"categories": [], "confidence": 0.5, "matched_keywords": []}
        ]
        assert result["parser_type"] is not None
        assert result["bucket"] == "complete-bucket"


class TestE2EIntegration:
    """E2E 통합 테스트 (2.8) - Backend ↔ AI Worker"""

    def test_extract_case_id_from_backend_format(self):
        """
        Given: Backend 형식 S3 키 (cases/{case_id}/raw/{ev_id}_{filename})
        When: _extract_case_id() 호출
        Then: case_id가 정확히 추출됨
        """
        # Given
        object_key = "cases/case_001/raw/ev_abc123_photo.jpg"

        # When
        case_id = _extract_case_id(object_key, "fallback-bucket")

        # Then
        assert case_id == "case_001"

    def test_extract_case_id_from_legacy_format(self):
        """
        Given: 레거시 형식 S3 키 (evidence/{case_id}/filename)
        When: _extract_case_id() 호출
        Then: case_id가 정확히 추출됨
        """
        # Given
        object_key = "evidence/case_002/document.pdf"

        # When
        case_id = _extract_case_id(object_key, "fallback-bucket")

        # Then
        assert case_id == "case_002"

    def test_extract_case_id_fallback(self):
        """
        Given: 형식이 맞지 않는 S3 키
        When: _extract_case_id() 호출
        Then: fallback 값 반환
        """
        # Given
        object_key = "document.pdf"

        # When
        case_id = _extract_case_id(object_key, "fallback-bucket")

        # Then
        assert case_id == "fallback-bucket"

    def test_extract_evidence_id_from_backend_format(self):
        """
        Given: Backend 형식 S3 키 (cases/{case_id}/raw/{ev_id}_{filename})
        When: _extract_evidence_id_from_s3_key() 호출
        Then: evidence_id가 정확히 추출됨 (ev_xxx)
        """
        # Given
        object_key = "cases/case_001/raw/ev_abc123_photo.jpg"

        # When
        evidence_id = _extract_evidence_id_from_s3_key(object_key)

        # Then
        assert evidence_id == "ev_abc123"

    def test_extract_evidence_id_with_underscore_in_filename(self):
        """
        Given: 파일명에 언더스코어가 포함된 S3 키
        When: _extract_evidence_id_from_s3_key() 호출
        Then: evidence_id만 정확히 추출됨
        """
        # Given
        object_key = "cases/case_001/raw/ev_xyz789_my_document_file.pdf"

        # When
        evidence_id = _extract_evidence_id_from_s3_key(object_key)

        # Then
        assert evidence_id == "ev_xyz789"

    def test_extract_evidence_id_returns_none_for_legacy_format(self):
        """
        Given: 레거시 형식 S3 키 (evidence_id 없음)
        When: _extract_evidence_id_from_s3_key() 호출
        Then: None 반환
        """
        # Given
        object_key = "evidence/case_002/document.pdf"

        # When
        evidence_id = _extract_evidence_id_from_s3_key(object_key)

        # Then
        assert evidence_id is None

    def test_extract_evidence_id_returns_none_for_non_ev_prefix(self):
        """
        Given: ev_ 접두어가 없는 S3 키
        When: _extract_evidence_id_from_s3_key() 호출
        Then: None 반환
        """
        # Given
        object_key = "cases/case_001/raw/file_123_photo.jpg"

        # When
        evidence_id = _extract_evidence_id_from_s3_key(object_key)

        # Then
        assert evidence_id is None
