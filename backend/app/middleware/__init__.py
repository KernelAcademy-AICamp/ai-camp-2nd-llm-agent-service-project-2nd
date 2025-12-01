"""
Legal Evidence Hub (LEH) - Middleware Package
"""

from .error_handler import (
    LEHException,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    ConflictError,
    ValidationError,
    register_exception_handlers
)
from .security import SecurityHeadersMiddleware, HTTPSRedirectMiddleware
from .audit_log import AuditLogMiddleware

__all__ = [
    "LEHException",
    "AuthenticationError",
    "PermissionError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "register_exception_handlers",
    "SecurityHeadersMiddleware",
    "HTTPSRedirectMiddleware",
    "AuditLogMiddleware"
]
