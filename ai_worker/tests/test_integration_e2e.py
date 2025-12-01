"""
End-to-End Integration Tests for AI Worker Lambda Handler
전체 파이프라인 통합 테스트

Phase 7: E2E 통합 테스트
- S3 이벤트 → Lambda 핸들러 → 전체 파이프라인 검증
"""

import json
from unittest.mock import Mock, patch
from datetime import datetime


class TestPDFProcessingE2E:
    """PDF 파일 처리 E2E 테스트"""

    @patch('handler.boto3')
    @patch('handler.MetadataStore')
    @patch('handler.VectorStore')
    @patch('handler.Article840Tagger')
    @patch('handler.PDFParser')
    def test_pdf_upload_complete_pipeline(
        self,
        mock_pdf_parser_class,
        mock_tagger_class,
        mock_vector_class,
        mock_metadata_class,
        mock_boto3
    ):
        """
        Given: S3에 PDF 파일 업로드 이벤트
        When: Lambda handler 실행
        Then: 파싱 → 메타데이터 저장 → 벡터 저장 → 태깅 전체 플로우 성공
        """
        from handler import handle
        from src.parsers.base import Message

        # Given: S3 이벤트
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "evidence-bucket"},
                        "object": {"key": "cases/case123/document.pdf"}
                    }
                }
            ]
        }
        context = {}

        # S3 mock
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # PDFParser mock - 3개의 텍스트 청크 반환
        mock_pdf_parser = Mock()
        messages = []
        for i in range(3):
            msg = Message(
                content=f"PDF 내용 {i+1}. 이혼 사유에 대한 증거입니다.",
                sender="System",
                timestamp=datetime.now(),
                metadata={"source_type": "pdf", "page": i+1}
            )
            messages.append(msg)
        mock_pdf_parser.parse.return_value = messages
        mock_pdf_parser_class.return_value = mock_pdf_parser

        # MetadataStore mock
        mock_metadata = Mock()
        mock_metadata.save_evidence_file.return_value = {
            'file_id': 'pdf-file-001',
            'case_id': 'evidence-bucket',
            'file_path': 'cases/case123/document.pdf',
            'file_type': '.pdf',
            'created_at': '2024-01-01T00:00:00'
        }
        mock_metadata_class.return_value = mock_metadata

        # VectorStore mock
        mock_vector = Mock()
        mock_vector.add_evidence.side_effect = ['chunk-1', 'chunk-2', 'chunk-3']
        mock_vector_class.return_value = mock_vector

        # Article840Tagger mock
        from src.analysis.article_840_tagger import Article840Category
        mock_tagger = Mock()
        mock_tag_result = Mock()
        mock_tag_result.categories = [Article840Category.ADULTERY]
        mock_tag_result.confidence = 0.75
        mock_tag_result.matched_keywords = ["이혼", "증거"]
        mock_tagger.tag.return_value = mock_tag_result
        mock_tagger_class.return_value = mock_tagger

        # When: Lambda handler 실행
        result = handle(event, context)

        # Then: 전체 파이프라인 성공
        assert result["statusCode"] == 200
        result_body = json.loads(result["body"])
        assert len(result_body["results"]) == 1

        processing_result = result_body["results"][0]
        assert processing_result["status"] == "processed"
        assert processing_result["file"] == "cases/case123/document.pdf"
        assert "parser_type" in processing_result  # parser_type 존재 확인
        assert processing_result["file_id"] == "pdf-file-001"
        assert processing_result["chunks_indexed"] == 3
        assert len(processing_result["tags"]) == 3

        # 각 컴포넌트가 올바르게 호출되었는지 검증
        mock_s3_client.download_file.assert_called_once()
        mock_pdf_parser.parse.assert_called_once()
        mock_metadata.save_evidence_file.assert_called_once()
        assert mock_vector.add_evidence.call_count == 3
        assert mock_tagger.tag.call_count == 3


class TestKakaoTalkProcessingE2E:
    """카카오톡 파일 처리 E2E 테스트"""

    @patch('handler.boto3')
    @patch('handler.MetadataStore')
    @patch('handler.VectorStore')
    @patch('handler.Article840Tagger')
    @patch('handler.TextParser')
    def test_kakaotalk_upload_complete_pipeline(
        self,
        mock_text_parser_class,
        mock_tagger_class,
        mock_vector_class,
        mock_metadata_class,
        mock_boto3
    ):
        """
        Given: S3에 카카오톡 채팅 파일 업로드 이벤트
        When: Lambda handler 실행
        Then: KakaoTalk 감지 → 파싱 → 저장 → 태깅 전체 플로우 성공
        """
        from handler import handle
        from src.parsers.base import Message

        # Given: S3 이벤트
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "chat-bucket"},
                        "object": {"key": "cases/case456/chat.txt"}
                    }
                }
            ]
        }
        context = {}

        # S3 mock
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # TextParser mock - 5개의 카카오톡 메시지 반환
        mock_text_parser = Mock()
        messages = []
        senders = ["홍길동", "김철수", "홍길동", "김철수", "홍길동"]
        contents = [
            "계속된 폭력에 지쳤습니다",
            "증거가 있나요?",
            "사진이 있습니다",
            "법적으로 도움드리겠습니다",
            "감사합니다"
        ]
        for i in range(5):
            msg = Message(
                content=contents[i],
                sender=senders[i],
                timestamp=datetime(2024, 1, 1, 10, i),
                metadata={"source_type": "kakaotalk", "message_index": i}
            )
            messages.append(msg)
        mock_text_parser.parse.return_value = messages
        mock_text_parser_class.return_value = mock_text_parser

        # MetadataStore mock
        mock_metadata = Mock()
        mock_metadata.save_evidence_file.return_value = {
            'file_id': 'kakao-file-001',
            'case_id': 'chat-bucket',
            'file_path': 'cases/case456/chat.txt',
            'file_type': '.txt',
            'created_at': '2024-01-01T00:00:00'
        }
        mock_metadata_class.return_value = mock_metadata

        # VectorStore mock
        mock_vector = Mock()
        mock_vector.add_evidence.side_effect = [f'chunk-{i}' for i in range(5)]
        mock_vector_class.return_value = mock_vector

        # Article840Tagger mock
        from src.analysis.article_840_tagger import Article840Category
        mock_tagger = Mock()

        # 첫 번째 메시지: 악의의 유기 관련 높은 신뢰도
        mock_tag_result_1 = Mock()
        mock_tag_result_1.categories = [Article840Category.DESERTION]
        mock_tag_result_1.confidence = 0.92
        mock_tag_result_1.matched_keywords = ["유기"]

        # 나머지: 낮은 신뢰도
        mock_tag_result_other = Mock()
        mock_tag_result_other.categories = []
        mock_tag_result_other.confidence = 0.1
        mock_tag_result_other.matched_keywords = []

        mock_tagger.tag.side_effect = [
            mock_tag_result_1,
            mock_tag_result_other,
            mock_tag_result_other,
            mock_tag_result_other,
            mock_tag_result_other
        ]
        mock_tagger_class.return_value = mock_tagger

        # When: Lambda handler 실행
        result = handle(event, context)

        # Then: 전체 파이프라인 성공
        assert result["statusCode"] == 200
        result_body = json.loads(result["body"])
        assert len(result_body["results"]) == 1

        processing_result = result_body["results"][0]
        assert processing_result["status"] == "processed"
        assert processing_result["file"] == "cases/case456/chat.txt"
        assert "parser_type" in processing_result  # parser_type 존재 확인
        assert processing_result["file_id"] == "kakao-file-001"
        assert processing_result["chunks_indexed"] == 5
        assert len(processing_result["tags"]) == 5

        # 첫 번째 태그는 악의의 유기 관련
        first_tag = processing_result["tags"][0]
        assert "desertion" in first_tag["categories"]
        assert first_tag["confidence"] == 0.92

        # 각 컴포넌트가 올바르게 호출되었는지 검증
        mock_s3_client.download_file.assert_called_once()
        mock_text_parser.parse.assert_called_once()
        mock_metadata.save_evidence_file.assert_called_once()
        assert mock_vector.add_evidence.call_count == 5
        assert mock_tagger.tag.call_count == 5


class TestImageProcessingE2E:
    """이미지 파일 처리 E2E 테스트"""

    @patch('handler.boto3')
    @patch('handler.MetadataStore')
    @patch('handler.VectorStore')
    @patch('handler.Article840Tagger')
    @patch('handler.ImageVisionParser')
    def test_image_upload_complete_pipeline(
        self,
        mock_vision_parser_class,
        mock_tagger_class,
        mock_vector_class,
        mock_metadata_class,
        mock_boto3
    ):
        """
        Given: S3에 이미지 파일 업로드 이벤트
        When: Lambda handler 실행
        Then: Vision API → 감정/맥락 분석 → 저장 → 태깅 전체 플로우 성공
        """
        from handler import handle
        from src.parsers.base import Message

        # Given: S3 이벤트
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "image-bucket"},
                        "object": {"key": "cases/case789/evidence.jpg"}
                    }
                }
            ]
        }
        context = {}

        # S3 mock
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # ImageVisionParser mock - Vision API 분석 결과
        mock_vision_parser = Mock()
        msg = Message(
            content="이미지 분석: 폭력 흔적이 포착되었습니다. 신체 상해 증거로 보입니다.",
            sender="GPT-4o Vision",
            timestamp=datetime.now(),
            metadata={
                "source_type": "image",
                "emotions": ["슬픔", "분노"],
                "context": "가정폭력 증거 사진",
                "confidence": 0.88
            }
        )
        mock_vision_parser.parse.return_value = [msg]
        mock_vision_parser_class.return_value = mock_vision_parser

        # MetadataStore mock
        mock_metadata = Mock()
        mock_metadata.save_evidence_file.return_value = {
            'file_id': 'image-file-001',
            'case_id': 'image-bucket',
            'file_path': 'cases/case789/evidence.jpg',
            'file_type': '.jpg',
            'created_at': '2024-01-01T00:00:00'
        }
        mock_metadata_class.return_value = mock_metadata

        # VectorStore mock
        mock_vector = Mock()
        mock_vector.add_evidence.return_value = 'img-chunk-1'
        mock_vector_class.return_value = mock_vector

        # Article840Tagger mock
        from src.analysis.article_840_tagger import Article840Category
        mock_tagger = Mock()
        mock_tag_result = Mock()
        mock_tag_result.categories = [Article840Category.DESERTION]
        mock_tag_result.confidence = 0.95
        mock_tag_result.matched_keywords = ["유기", "방치"]
        mock_tagger.tag.return_value = mock_tag_result
        mock_tagger_class.return_value = mock_tagger

        # When: Lambda handler 실행
        result = handle(event, context)

        # Then: 전체 파이프라인 성공
        assert result["statusCode"] == 200
        result_body = json.loads(result["body"])
        assert len(result_body["results"]) == 1

        processing_result = result_body["results"][0]
        assert processing_result["status"] == "processed"
        assert processing_result["file"] == "cases/case789/evidence.jpg"
        assert "parser_type" in processing_result  # parser_type 존재 확인
        assert processing_result["file_id"] == "image-file-001"
        assert processing_result["chunks_indexed"] == 1
        assert len(processing_result["tags"]) == 1

        # 태그 검증 - 악의의 유기 관련 높은 신뢰도
        tag = processing_result["tags"][0]
        assert "desertion" in tag["categories"]
        assert tag["confidence"] == 0.95
        assert "유기" in tag["matched_keywords"]

        # 각 컴포넌트가 올바르게 호출되었는지 검증
        mock_s3_client.download_file.assert_called_once()
        mock_vision_parser.parse.assert_called_once()
        mock_metadata.save_evidence_file.assert_called_once()
        mock_vector.add_evidence.assert_called_once()
        mock_tagger.tag.assert_called_once()


class TestMultiFileProcessingE2E:
    """여러 파일 동시 처리 E2E 테스트"""

    @patch('handler.boto3')
    @patch('handler.MetadataStore')
    @patch('handler.VectorStore')
    @patch('handler.Article840Tagger')
    def test_multiple_files_batch_processing(
        self,
        mock_tagger_class,
        mock_vector_class,
        mock_metadata_class,
        mock_boto3
    ):
        """
        Given: S3에 여러 파일 동시 업로드 이벤트
        When: Lambda handler 실행
        Then: 모든 파일이 독립적으로 처리됨
        """
        from handler import handle
        from src.parsers.base import Message

        # Given: 3개의 파일 업로드 이벤트
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "multi-bucket"},
                        "object": {"key": "file1.pdf"}
                    }
                },
                {
                    "s3": {
                        "bucket": {"name": "multi-bucket"},
                        "object": {"key": "file2.txt"}
                    }
                },
                {
                    "s3": {
                        "bucket": {"name": "multi-bucket"},
                        "object": {"key": "file3.jpg"}
                    }
                }
            ]
        }
        context = {}

        # S3 mock
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # MetadataStore mock
        mock_metadata = Mock()
        mock_metadata.save_evidence_file.side_effect = [
            {'file_id': f'file-{i}', 'case_id': 'multi-bucket', 'file_path': f'file{i}', 'file_type': ext, 'created_at': '2024-01-01'}
            for i, ext in enumerate(['.pdf', '.txt', '.jpg'], 1)
        ]
        mock_metadata_class.return_value = mock_metadata

        # VectorStore mock
        mock_vector = Mock()
        mock_vector.add_evidence.return_value = 'chunk-id'
        mock_vector_class.return_value = mock_vector

        # Article840Tagger mock
        mock_tagger = Mock()
        mock_tag_result = Mock()
        mock_tag_result.categories = []
        mock_tag_result.confidence = 0.5
        mock_tag_result.matched_keywords = []
        mock_tagger.tag.return_value = mock_tag_result
        mock_tagger_class.return_value = mock_tagger

        # Parser mocks
        with patch('handler.route_parser') as mock_route_parser:
            mock_parser = Mock()
            msg = Message(
                content="test",
                sender="System",
                timestamp=datetime.now(),
                metadata={"source_type": "test"}
            )
            mock_parser.parse.return_value = [msg]
            mock_route_parser.return_value = mock_parser

            # When: Lambda handler 실행
            result = handle(event, context)

        # Then: 모든 파일이 처리됨
        assert result["statusCode"] == 200
        result_body = json.loads(result["body"])
        assert len(result_body["results"]) == 3

        # 각 파일이 독립적으로 처리되었는지 확인
        for i, res in enumerate(result_body["results"], 1):
            assert res["status"] == "processed"
            assert res["file_id"] == f"file-{i}"

        # 각 컴포넌트가 3번씩 호출되었는지 검증
        assert mock_s3_client.download_file.call_count == 3
        assert mock_metadata.save_evidence_file.call_count == 3


class TestErrorRecoveryE2E:
    """에러 복구 E2E 테스트"""

    @patch('handler.boto3')
    def test_partial_failure_recovery(self, mock_boto3):
        """
        Given: 여러 파일 중 일부만 실패
        When: Lambda handler 실행
        Then: 성공한 파일은 처리되고 실패한 파일은 error 상태 반환
        """
        from handler import handle

        # Given: 2개 파일, 1개는 지원하지 않는 확장자
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "valid.pdf"}
                    }
                },
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "invalid.xyz"}
                    }
                }
            ]
        }
        context = {}

        # S3 mock
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # When: Lambda handler 실행
        result = handle(event, context)

        # Then: statusCode는 200 (Lambda 재시도 방지)
        assert result["statusCode"] == 200
        result_body = json.loads(result["body"])
        assert len(result_body["results"]) == 2

        # 두 번째 파일은 skipped 상태
        assert result_body["results"][1]["status"] == "skipped"
        assert "unsupported" in result_body["results"][1]["reason"].lower()
