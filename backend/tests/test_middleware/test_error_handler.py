"""
Unit tests for app/middleware/error_handler.py

TDD approach: Test custom exceptions, error handlers, and response formats
"""

import pytest
from fastapi import status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from unittest.mock import Mock
import json

from app.middleware.error_handler import (
    LEHException,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    ConflictError,
    leh_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)


@pytest.mark.unit
class TestCustomExceptions:
    """Test custom exception classes"""

    def test_leh_exception_base_class(self):
        """Test LEHException base class initialization"""
        exc = LEHException(
            code="TEST_ERROR",
            message="Test error message",
            status_code=500,
            details={"extra": "info"}
        )

        assert exc.code == "TEST_ERROR"
        assert exc.message == "Test error message"
        assert exc.status_code == 500
        assert exc.details == {"extra": "info"}
        assert str(exc) == "Test error message"

    def test_leh_exception_default_details(self):
        """Test LEHException with no details provided"""
        exc = LEHException(code="TEST", message="Test")

        assert exc.details == {}

    def test_authentication_error(self):
        """Test AuthenticationError returns 401"""
        exc = AuthenticationError("Invalid token")

        assert exc.code == "AUTHENTICATION_FAILED"
        assert exc.message == "Invalid token"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authentication_error_default_message(self):
        """Test AuthenticationError with default message"""
        exc = AuthenticationError()

        assert exc.message == "Authentication failed"
        assert exc.status_code == 401

    def test_permission_error(self):
        """Test PermissionError returns 403"""
        exc = PermissionError("No access to this case")

        assert exc.code == "PERMISSION_DENIED"
        assert exc.message == "No access to this case"
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_permission_error_default_message(self):
        """Test PermissionError with default message"""
        exc = PermissionError()

        assert exc.message == "Permission denied"

    def test_not_found_error(self):
        """Test NotFoundError returns 404"""
        exc = NotFoundError("Case")

        assert exc.code == "NOT_FOUND"
        assert exc.message == "Case not found"
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_not_found_error_default_resource(self):
        """Test NotFoundError with default resource name"""
        exc = NotFoundError()

        assert exc.message == "Resource not found"

    def test_conflict_error(self):
        """Test ConflictError returns 409"""
        exc = ConflictError("Draft already generating")

        assert exc.code == "CONFLICT"
        assert exc.message == "Draft already generating"
        assert exc.status_code == status.HTTP_409_CONFLICT

    def test_conflict_error_default_message(self):
        """Test ConflictError with default message"""
        exc = ConflictError()

        assert exc.message == "Resource conflict"


@pytest.mark.unit
@pytest.mark.asyncio
class TestExceptionHandlers:
    """Test exception handler functions"""

    async def test_leh_exception_handler_response_format(self):
        """Test that LEHException handler returns correct JSON format"""
        request = Mock()
        request.url.path = "/test/path"
        request.method = "GET"

        exc = NotFoundError("Case")

        response = await leh_exception_handler(request, exc)

        assert response.status_code == 404

        body = json.loads(response.body.decode())
        assert "error" in body
        assert body["error"]["code"] == "NOT_FOUND"
        assert body["error"]["message"] == "Case not found"
        assert "error_id" in body["error"]
        assert "timestamp" in body["error"]

    async def test_leh_exception_handler_includes_error_id(self):
        """Test that error_id is UUID format"""
        request = Mock()
        request.url.path = "/test"
        request.method = "POST"

        exc = AuthenticationError()

        response = await leh_exception_handler(request, exc)
        body = json.loads(response.body.decode())

        error_id = body["error"]["error_id"]
        # UUID format validation (basic)
        assert len(error_id) == 36
        assert error_id.count("-") == 4

    async def test_http_exception_handler(self):
        """Test HTTPException handler"""
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"

        exc = StarletteHTTPException(status_code=400, detail="Bad request")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 400
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "HTTP_400"
        assert body["error"]["message"] == "Bad request"

    async def test_validation_exception_handler(self):
        """Test validation error handler returns 422"""
        request = Mock()
        request.url.path = "/test"
        request.method = "POST"

        # Mock RequestValidationError
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = [
            {
                "loc": ["body", "email"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]

        response = await validation_exception_handler(request, exc)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "details" in body["error"]

    async def test_general_exception_handler_dev_mode(self, monkeypatch):
        """Test general exception handler shows details in dev mode"""
        # Mock settings to return dev environment
        from app.core import config
        mock_settings = Mock()
        mock_settings.APP_ENV = "dev"
        monkeypatch.setattr(config, "settings", mock_settings)

        request = Mock()
        request.url.path = "/test"
        request.method = "GET"

        exc = ValueError("Something went wrong")

        response = await general_exception_handler(request, exc)

        assert response.status_code == 500
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        # In dev mode, should include exception details
        assert "ValueError" in body["error"]["message"]

    async def test_general_exception_handler_prod_mode(self, monkeypatch):
        """Test general exception handler hides details in prod mode"""
        # Mock settings to return prod environment
        from app.core import config
        mock_settings = Mock()
        mock_settings.APP_ENV = "prod"
        monkeypatch.setattr(config, "settings", mock_settings)

        request = Mock()
        request.url.path = "/test"
        request.method = "GET"

        exc = ValueError("Sensitive internal error")

        response = await general_exception_handler(request, exc)

        assert response.status_code == 500
        body = json.loads(response.body.decode())
        # In prod mode, should NOT include exception details
        assert "Sensitive" not in body["error"]["message"]
        assert "internal error occurred" in body["error"]["message"]

    async def test_error_response_includes_timestamp(self):
        """Test that all error responses include ISO8601 timestamp"""
        request = Mock()
        request.url.path = "/test"
        request.method = "GET"

        exc = NotFoundError("Evidence")

        response = await leh_exception_handler(request, exc)
        body = json.loads(response.body.decode())

        timestamp = body["error"]["timestamp"]
        # Basic ISO8601 format check
        assert "T" in timestamp
        assert "Z" in timestamp or "+" in timestamp


@pytest.mark.unit
class TestErrorHandlerRegistration:
    """Test exception handler registration"""

    def test_register_exception_handlers(self):
        """Test that register_exception_handlers adds all handlers to app"""
        from fastapi import FastAPI
        from app.middleware.error_handler import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)

        # Verify that exception handlers are registered
        assert len(app.exception_handlers) > 0

        # Check for our custom exception types
        assert LEHException in app.exception_handlers
        assert StarletteHTTPException in app.exception_handlers
        assert RequestValidationError in app.exception_handlers
        assert Exception in app.exception_handlers
