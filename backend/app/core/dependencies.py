"""
FastAPI dependencies for authentication and authorization

Supports both:
1. Authorization header (Bearer token) - for API clients
2. HTTP-only cookies (access_token) - for browser clients
"""

from fastapi import Depends, Header, Cookie, Request
from typing import Optional
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.db.session import get_db
from app.middleware import AuthenticationError, PermissionError
from app.db.models import User, UserRole
from app.repositories.user_repository import UserRepository


def get_current_user_id(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
) -> str:
    """
    Extract and validate user ID from JWT token

    Supports both Authorization header and HTTP-only cookie.
    Priority: Authorization header > Cookie

    Args:
        authorization: Authorization header (Bearer token)
        access_token: HTTP-only cookie with access token

    Returns:
        User ID from token

    Raises:
        AuthenticationError: Invalid or missing token
    """
    token = None

    # Try Authorization header first (for API clients)
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        else:
            raise AuthenticationError("잘못된 인증 형식입니다.")

    # Fall back to cookie (for browser clients)
    if not token and access_token:
        token = access_token

    if not token:
        raise AuthenticationError("인증이 필요합니다.")

    # Decode and validate token
    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationError("유효하지 않은 토큰입니다.")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("토큰에 사용자 정보가 없습니다.")

    return user_id


def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from database

    Args:
        user_id: User ID from JWT token
        db: Database session

    Returns:
        User object

    Raises:
        AuthenticationError: User not found
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        raise AuthenticationError("사용자를 찾을 수 없습니다.")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role for access

    Args:
        current_user: Current authenticated user

    Returns:
        User object if user is admin

    Raises:
        PermissionError: User is not admin
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionError("Admin 권한이 필요합니다.")

    return current_user


def require_lawyer_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require lawyer or admin role for access

    Args:
        current_user: Current authenticated user

    Returns:
        User object if user is lawyer or admin

    Raises:
        PermissionError: User is staff (insufficient permissions)
    """
    if current_user.role not in [UserRole.LAWYER, UserRole.ADMIN]:
        raise PermissionError("Lawyer 또는 Admin 권한이 필요합니다.")

    return current_user
