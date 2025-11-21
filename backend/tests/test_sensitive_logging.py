"""
Sensitive Data Logging Tests for Backend API.

Ensures that sensitive information is not exposed in logs.

Focus: 실제로 로그에 노출될 수 있는 경로 테스트
1. Exception handler 로깅 (error_handler.py:92, 122, 151, 182)
2. 인증 실패 로깅 (비밀번호 노출 방지)
3. Validation error 로깅 (사용자 입력 노출 방지)
4. 증거 내용 로깅 (민감한 증거 내용 노출 방지)
"""

import pytest
import logging
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.middleware.error_handler import (
    LEHException,
    AuthenticationError,
    general_exception_handler
)


client = TestClient(app)


class TestSensitiveDataLogging:
    """Test that sensitive data is not logged in backend"""

    def test_authentication_error_password_not_logged(self, caplog):
        """
        인증 실패 시 비밀번호가 로그에 노출되지 않아야 함

        사용자가 잘못된 비밀번호로 로그인 시도할 때 에러 메시지에
        비밀번호가 포함되어서는 안 됨
        """
        caplog.set_level(logging.INFO)

        # Given: 민감한 비밀번호를 포함한 로그인 요청
        sensitive_password = "MySecretPassword123!"

        with patch('app.services.auth_service.AuthService.login') as mock_login:
            # 인증 실패 시 비밀번호를 포함한 에러 발생
            mock_login.side_effect = AuthenticationError(
                f"Invalid password: {sensitive_password}"
            )

            # When: 로그인 API 호출
            response = client.post(
                "/auth/login",
                json={"email": "test@example.com", "password": sensitive_password}
            )

            # Then: 응답은 401이지만 비밀번호는 로그에 노출되지 않아야 함
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

            log_output = caplog.text
            assert sensitive_password not in log_output, \
                "비밀번호가 인증 에러 로그에 노출되었습니다!"

    def test_validation_error_user_data_not_logged(self, caplog):
        """
        Validation 에러 시 사용자 입력 데이터가 로그에 노출되지 않아야 함

        Pydantic validation 에러 메시지에 민감한 사용자 입력이
        포함될 수 있음
        """
        caplog.set_level(logging.INFO)

        # Given: 민감한 데이터를 포함한 잘못된 요청
        sensitive_data = "배우자의 불륜 증거 사진입니다"

        # When: 잘못된 형식의 요청 (presigned-url에 필수 필드 누락)
        with patch('app.core.dependencies.get_current_user_id', return_value="user123"):
            response = client.post(
                "/evidence/presigned-url",
                json={
                    "case_id": "case123",
                    # filename 필드 누락 -> validation error
                    "content_type": sensitive_data  # 민감한 데이터가 잘못된 필드에
                }
            )

            # Then: Validation error이지만 민감한 데이터는 로그에 노출되지 않아야 함
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

            log_output = caplog.text
            # Note: Pydantic error details에 사용자 입력이 포함될 수 있음
            assert sensitive_data not in log_output, \
                "민감한 사용자 입력이 Validation 에러 로그에 노출되었습니다!"

    def test_general_exception_evidence_content_not_logged(self, caplog):
        """
        일반 예외 발생 시 증거 내용이 로그에 노출되지 않아야 함

        서비스 로직 에러 발생 시 Exception 메시지에 증거 내용이
        포함될 수 있음
        """
        caplog.set_level(logging.INFO)

        # Given: 민감한 증거 내용을 포함한 예외
        sensitive_evidence = "남편이 다른 여성과 함께 있는 사진"

        with patch('app.core.dependencies.get_current_user_id', return_value="user123"):
            with patch('app.services.evidence_service.EvidenceService.get_evidence_detail') as mock_get:
                # 증거 내용을 포함한 에러 발생
                mock_get.side_effect = Exception(
                    f"Failed to process evidence: {sensitive_evidence}"
                )

                # When: 증거 조회 API 호출
                response = client.get("/evidence/ev123")

                # Then: 500 에러이지만 증거 내용은 로그에 노출되지 않아야 함
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

                log_output = caplog.text
                assert sensitive_evidence not in log_output, \
                    "민감한 증거 내용이 Exception 로그에 노출되었습니다!"

    def test_exception_traceback_with_jwt_token_sanitized(self, caplog):
        """
        Exception traceback에 포함된 JWT 토큰이 마스킹되어야 함

        Traceback에 함수 인자나 변수가 포함될 수 있어서
        JWT 토큰이 노출될 위험이 있음
        """
        caplog.set_level(logging.INFO)

        # Given: JWT 토큰을 포함한 에러
        fake_jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

        with patch('app.core.dependencies.get_current_user_id') as mock_get_user:
            # JWT decode 실패 시 토큰을 포함한 에러
            mock_get_user.side_effect = Exception(
                f"JWT decode failed for token: {fake_jwt_token}"
            )

            # When: 인증이 필요한 API 호출
            response = client.post(
                "/evidence/presigned-url",
                json={
                    "case_id": "case123",
                    "filename": "test.pdf",
                    "content_type": "application/pdf"
                }
            )

            # Then: 500 에러이지만 JWT 토큰은 로그에 노출되지 않아야 함
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

            log_output = caplog.text
            assert fake_jwt_token not in log_output, \
                "JWT 토큰이 Exception 로그에 노출되었습니다!"

    def test_http_exception_detail_with_user_email_sanitized(self, caplog):
        """
        HTTP Exception detail에 포함된 사용자 이메일이 마스킹되어야 함

        FastAPI HTTPException의 detail 파라미터에 사용자 정보가
        포함될 수 있음
        """
        caplog.set_level(logging.INFO)

        # Given: 사용자 이메일을 포함한 HTTP 에러
        user_email = "victim@example.com"

        with patch('app.services.auth_service.AuthService.login') as mock_login:
            from fastapi import HTTPException

            # 이메일을 포함한 HTTP 에러
            mock_login.side_effect = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User {user_email} not found or inactive"
            )

            # When: 로그인 API 호출
            response = client.post(
                "/auth/login",
                json={"email": user_email, "password": "password123"}
            )

            # Then: 401 에러이지만 이메일은 로그에 노출되지 않아야 함
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

            log_output = caplog.text
            assert user_email not in log_output, \
                "사용자 이메일이 HTTP Exception 로그에 노출되었습니다!"

    def test_leh_exception_details_with_case_info_sanitized(self, caplog):
        """
        LEHException details에 포함된 사건 정보가 마스킹되어야 함

        LEHException.details에 민감한 사건 정보가 포함될 수 있음
        """
        caplog.set_level(logging.INFO)

        # Given: 사건 정보를 포함한 LEH 에러
        sensitive_case_info = "이혼 사건 - 배우자 불륜 증거"

        with patch('app.core.dependencies.get_current_user_id', return_value="user123"):
            with patch('app.services.evidence_service.EvidenceService.generate_upload_presigned_url') as mock_gen:
                from app.middleware.error_handler import PermissionError

                # 사건 정보를 포함한 권한 에러
                exc = PermissionError(
                    message=f"No access to case: {sensitive_case_info}"
                )
                mock_gen.side_effect = exc

                # When: Presigned URL 생성 API 호출
                response = client.post(
                    "/evidence/presigned-url",
                    json={
                        "case_id": "case123",
                        "filename": "evidence.pdf",
                        "content_type": "application/pdf"
                    }
                )

                # Then: 403 에러이지만 사건 정보는 로그에 노출되지 않아야 함
                assert response.status_code == status.HTTP_403_FORBIDDEN

                log_output = caplog.text
                assert sensitive_case_info not in log_output, \
                    "민감한 사건 정보가 LEH Exception 로그에 노출되었습니다!"
