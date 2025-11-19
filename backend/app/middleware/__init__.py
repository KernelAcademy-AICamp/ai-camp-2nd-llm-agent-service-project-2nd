"""
Legal Evidence Hub (LEH) - Middleware Package
"""

from .error_handler import (
    LEHException,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    ConflictError,
    register_exception_handlers
)
from .security import SecurityHeadersMiddleware, HTTPSRedirectMiddleware

__all__ = [
    "LEHException",
    "AuthenticationError",
    "PermissionError",
    "NotFoundError",
    "ConflictError",
    "register_exception_handlers",
    "SecurityHeadersMiddleware",
    "HTTPSRedirectMiddleware"
]
