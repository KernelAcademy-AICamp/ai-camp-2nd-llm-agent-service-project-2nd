"""
Service layer for business logic
Per BACKEND_SERVICE_REPOSITORY_GUIDE.md pattern
"""

from app.services.auth_service import AuthService

__all__ = ["AuthService"]
