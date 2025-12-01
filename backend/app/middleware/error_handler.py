"""
Legal Evidence Hub (LEH) - Error Handler Middleware
Global exception handling for consistent error responses
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import uuid
from datetime import datetime, timezone
import logging
from app.core.logging_filter import SensitiveDataFilter

logger = logging.getLogger(__name__)
logger.addFilter(SensitiveDataFilter())


class LEHException(Exception):
    """
    Base exception class for LEH-specific errors
    """
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(LEHException):
    """Authentication failed (401)"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            code="AUTHENTICATION_FAILED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class PermissionError(LEHException):
    """Permission denied (403)"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(LEHException):
    """Resource not found (404)"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictError(LEHException):
    """Resource conflict (409)"""
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT
        )


class ValidationError(LEHException):
    """Validation error (400)"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


async def leh_exception_handler(request: Request, exc: LEHException) -> JSONResponse:
    """
    Handler for LEH-specific exceptions
    """
    error_id = str(uuid.uuid4())

    logger.error(
        f"LEH Exception [{error_id}]: {exc.code} - {exc.message}",
        extra={
            "error_id": error_id,
            "code": exc.code,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "error_id": error_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handler for standard HTTP exceptions
    """
    error_id = str(uuid.uuid4())

    logger.warning(
        f"HTTP Exception [{error_id}]: {exc.status_code} - {exc.detail}",
        extra={
            "error_id": error_id,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "error_id": error_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for request validation errors (422)
    """
    error_id = str(uuid.uuid4())

    logger.warning(
        f"Validation Error [{error_id}]: {exc.errors()}",
        extra={
            "error_id": error_id,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "error_id": error_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": exc.errors()
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unexpected exceptions (500)

    SECURITY NOTE: Do not expose internal error details in production
    """
    error_id = str(uuid.uuid4())

    logger.error(
        f"Unexpected Exception [{error_id}]: {str(exc)}",
        extra={
            "error_id": error_id,
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )

    # In production, hide internal details
    from app.core.config import settings

    if settings.APP_ENV == "prod":
        message = "An internal error occurred. Please contact support."
    else:
        message = f"{type(exc).__name__}: {str(exc)}"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": message,
                "error_id": error_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )


def register_exception_handlers(app):
    """
    Register all exception handlers to the FastAPI app
    """
    app.add_exception_handler(LEHException, leh_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
