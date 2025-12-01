"""
Sensitive Data Logging Tests for AI Worker.
Ensures that sensitive information is not exposed in logs.

Focus: 실제로 로그에 노출될 수 있는 경로 테스트
1. S3 이벤트 로깅 (handler.py:182)
2. 에러 메시지 로깅 (handler.py:169)
"""

import logging
from unittest.mock import patch, MagicMock
from handler import handle


class TestSensitiveDataLogging:
    """Test that sensitive data is not logged"""

    def test_error_message_with_sensitive_content_sanitized(self, caplog):
        """
        에러 메시지에 포함된 민감한 증거 내용이 마스킹되어야 함

        파서 에러 시 Exception 메시지에 증거 내용이 포함될 수 있음
        """
        caplog.set_level(logging.INFO)

        sensitive_content = "남편이 바람을 피웠다는 증거입니다"

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "sensitive_evidence.txt"}
                    }
                }
            ]
        }

        # Mock TextParser to raise error with sensitive content
        with patch('handler.boto3'), \
             patch('handler.TextParser') as mock_parser_class:

            mock_parser = MagicMock()
            # 파서가 민감한 내용을 포함한 에러를 발생시킴
            mock_parser.parse.side_effect = Exception(
                f"Failed to parse: {sensitive_content}"
            )
            mock_parser_class.return_value = mock_parser

            # When: Lambda handler 호출
            handle(event, {})

            # Then: 로그에 민감한 내용이 그대로 노출되지 않아야 함
            log_output = caplog.text
            assert sensitive_content not in log_output, \
                "민감한 증거 내용이 에러 로그에 노출되었습니다!"

    def test_error_message_with_api_key_sanitized(self, caplog):
        """
        에러 메시지에 포함된 API 키가 마스킹되어야 함

        OpenAI API 호출 에러 시 API 키가 에러 메시지에 포함될 수 있음
        """
        caplog.set_level(logging.INFO)

        fake_api_key = "sk-proj-abc123xyz456def789ghi012jkl345mno678pqr901stu234"

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "test.pdf"}
                    }
                }
            ]
        }

        with patch('handler.boto3'), \
             patch('handler.PDFParser') as mock_parser_class:

            mock_parser = MagicMock()
            # API 키를 포함한 에러 발생
            mock_parser.parse.side_effect = Exception(
                f"OpenAI API error with key {fake_api_key}: Invalid request"
            )
            mock_parser_class.return_value = mock_parser

            # When: Lambda handler 호출
            handle(event, {})

            # Then: 로그에 API 키가 그대로 노출되지 않아야 함
            log_output = caplog.text
            assert fake_api_key not in log_output, \
                "OpenAI API 키가 에러 로그에 노출되었습니다!"

    def test_aws_credentials_not_logged(self, caplog):
        """
        AWS 자격증명이 로그에 노출되지 않아야 함

        AWS Access Key, Secret Key 노출 시 인프라 침해 위험
        """
        caplog.set_level(logging.INFO)

        # Given: 에러 발생 시나리오 (AWS 자격증명 포함)
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "test.pdf"}
                    }
                }
            ]
        }

        # Mock boto3 to raise error with credentials in message
        with patch('handler.boto3') as mock_boto3:
            mock_s3 = MagicMock()
            mock_boto3.client.return_value = mock_s3

            # 에러 메시지에 자격증명 패턴 포함
            mock_s3.download_file.side_effect = Exception(
                "Error: AKIAIOSFODNN7EXAMPLE credentials invalid"
            )

            # When: Lambda handler 호출
            handle(event, {})

            # Then: 로그에 AWS Access Key 패턴이 없어야 함
            log_output = caplog.text
            assert "AKIAIOSFODNN7EXAMPLE" not in log_output or \
                   "AKIA***" in log_output, \
                "AWS Access Key가 로그에 노출되었습니다!"

    def test_parser_error_with_sensitive_message_sanitized(self, caplog):
        """
        파서 에러 메시지에 포함된 민감한 내용이 마스킹되어야 함

        카톡 파싱 실패 시 에러 메시지에 대화 내용 조각이 포함될 수 있음
        """
        caplog.set_level(logging.INFO)

        sensitive_message = "배우자가 외도 중이라는 제보를 받았습니다"

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "kakaotalk.txt"}
                    }
                }
            ]
        }

        with patch('handler.boto3'), \
             patch('handler.TextParser') as mock_parser_class:

            mock_parser = MagicMock()
            # 파싱 에러에 민감한 내용 포함
            mock_parser.parse.side_effect = Exception(
                f"Parse error at line 42: {sensitive_message}"
            )
            mock_parser_class.return_value = mock_parser

            # When: Lambda handler 호출
            handle(event, {})

            # Then: 로그에 민감한 메시지가 그대로 노출되지 않아야 함
            log_output = caplog.text
            assert sensitive_message not in log_output, \
                "민감한 메시지가 에러 로그에 노출되었습니다!"

    def test_s3_event_with_user_ip_sanitized(self, caplog):
        """
        S3 이벤트에 포함된 사용자 IP 주소가 마스킹되어야 함

        handler.py:182에서 S3 이벤트 전체를 로깅하므로 민감 메타데이터 노출 위험
        """
        caplog.set_level(logging.INFO)

        # Given: 사용자 IP를 포함한 S3 이벤트
        user_ip = "203.0.113.42"
        event = {
            "Records": [
                {
                    "requestParameters": {
                        "sourceIPAddress": user_ip
                    },
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "test.pdf"}
                    }
                }
            ]
        }

        with patch('handler.boto3'), \
             patch('handler.PDFParser') as mock_parser_class, \
             patch('handler.MetadataStore') as mock_metadata_class, \
             patch('handler.VectorStore') as mock_vector_class, \
             patch('handler.Article840Tagger'):

            # Configure mocks to return JSON-serializable data
            mock_parser = MagicMock()
            mock_parser.parse.return_value = {
                "content": "test content",
                "metadata": {}
            }
            mock_parser_class.return_value = mock_parser

            mock_metadata = MagicMock()
            mock_metadata.save_evidence_file.return_value = {"file_id": "test-id"}
            mock_metadata_class.return_value = mock_metadata

            mock_vector = MagicMock()
            mock_vector.index_chunks.return_value = None
            mock_vector_class.return_value = mock_vector

            # When: Lambda handler 호출
            handle(event, {})

            # Then: 사용자 IP가 로그에 그대로 노출되지 않아야 함
            log_output = caplog.text
            assert user_ip not in log_output, \
                "사용자 IP 주소가 S3 이벤트 로그에 노출되었습니다!"
