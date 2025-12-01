"""
Audit Log Middleware - Automatic logging of sensitive API requests
Logs user actions (LOGIN, VIEW, CREATE, UPDATE, DELETE) to audit_logs table
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.repositories.audit_log_repository import AuditLogRepository
from app.db.schemas import AuditAction
from typing import Optional
import re


# Sensitive endpoints to log (HTTP method + path pattern)
AUDITABLE_ENDPOINTS = {
    # Authentication
    ("POST", r"^/auth/login$"): AuditAction.LOGIN,
    ("POST", r"^/auth/signup$"): AuditAction.SIGNUP,

    # Cases
    ("POST", r"^/cases$"): AuditAction.CREATE_CASE,
    ("GET", r"^/cases/[^/]+$"): AuditAction.VIEW_CASE,
    ("DELETE", r"^/cases/[^/]+$"): AuditAction.DELETE_CASE,

    # Evidence
    ("POST", r"^/evidence/presigned-url$"): AuditAction.UPLOAD_EVIDENCE,
    ("GET", r"^/evidence/[^/]+$"): AuditAction.VIEW_EVIDENCE,

    # Admin
    ("POST", r"^/admin/users/invite$"): AuditAction.INVITE_USER,
    ("DELETE", r"^/admin/users/[^/]+$"): AuditAction.DELETE_USER,

    # Draft
    ("POST", r"^/cases/[^/]+/draft-preview$"): AuditAction.GENERATE_DRAFT,
}


def extract_object_id(path: str, pattern: str) -> Optional[str]:
    """
    Extract object ID from URL path if pattern contains ID placeholder

    Args:
        path: Request path (e.g., "/cases/case_123abc")
        pattern: Regex pattern (e.g., r"^/cases/[^/]+$")

    Returns:
        Extracted ID or None
    """
    # Extract ID from path if pattern contains [^/]+ (ID placeholder)
    if "[^/]+" in pattern:
        # Match the pattern and extract ID
        match = re.match(pattern.replace("[^/]+", r"([^/]+)"), path)
        if match:
            return match.group(1)  # First captured group is the ID
    return None


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log sensitive API requests to audit_logs table
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and log if it matches auditable endpoints

        Args:
            request: FastAPI Request object
            call_next: Next middleware/route handler

        Returns:
            Response from next handler
        """
        # Call next handler first (to get user_id from auth)
        response: Response = await call_next(request)

        # Only log successful requests (2xx status codes)
        if 200 <= response.status_code < 300:
            await self._log_if_auditable(request, response)

        return response

    async def _log_if_auditable(self, request: Request, response: Response):
        """
        Check if request should be logged and create audit log entry

        Args:
            request: FastAPI Request object
            response: Response object
        """
        method = request.method
        path = request.url.path

        # Find matching auditable endpoint
        action = None
        object_id = None

        for (endpoint_method, pattern), audit_action in AUDITABLE_ENDPOINTS.items():
            if endpoint_method == method and re.match(pattern, path):
                action = audit_action
                object_id = extract_object_id(path, pattern)
                break

        # If not auditable, skip
        if not action:
            return

        # Get user_id from request state (set by JWT dependency)
        user_id = getattr(request.state, "user_id", None)

        # Skip logging if user_id is not available (e.g., signup endpoint)
        # Signup will be logged with the newly created user_id by AuthService
        if not user_id:
            return

        # Create audit log entry
        db: Session = SessionLocal()
        try:
            audit_repo = AuditLogRepository(db)
            audit_repo.create(
                user_id=user_id,
                action=action.value,
                object_id=object_id
            )
            db.commit()
        except Exception as e:
            # Don't fail the request if audit logging fails
            # Just log the error (in production, use proper logging)
            print(f"[AuditLogMiddleware] Failed to create audit log: {e}")
            db.rollback()
        finally:
            db.close()
