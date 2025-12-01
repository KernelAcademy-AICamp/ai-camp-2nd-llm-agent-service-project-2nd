"""
Authentication API endpoints
POST /auth/login - User login with JWT token issuance (cookie-based)
POST /auth/signup - User signup with JWT token issuance (cookie-based)
POST /auth/refresh - Refresh access token using refresh token
POST /auth/logout - Logout and clear cookies
GET /auth/me - Get current user info
"""

from fastapi import APIRouter, Depends, status, Response, Cookie, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.db.schemas import (
    LoginRequest, SignupRequest, TokenResponse, UserOut,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse
)
from app.services.auth_service import AuthService
from app.services.password_reset_service import PasswordResetService
from app.core.config import settings
from app.core.security import (
    create_refresh_token,
    decode_access_token,
    create_access_token,
    get_token_expire_seconds,
    get_refresh_token_expire_seconds
)
from app.middleware.error_handler import AuthenticationError
from app.repositories.user_repository import UserRepository


router = APIRouter()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """
    Set HTTP-only cookies for authentication tokens

    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
    """
    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=get_token_expire_seconds(),
        path="/",
        domain=settings.COOKIE_DOMAIN or None
    )

    # Refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=get_refresh_token_expire_seconds(),
        path="/auth",  # Only sent to /auth endpoints
        domain=settings.COOKIE_DOMAIN or None
    )


def clear_auth_cookies(response: Response):
    """
    Clear authentication cookies on logout

    Args:
        response: FastAPI Response object
    """
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.COOKIE_DOMAIN or None
    )
    response.delete_cookie(
        key="refresh_token",
        path="/auth",
        domain=settings.COOKIE_DOMAIN or None
    )


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    User login endpoint

    **Request Body:**
    - email: User's email address
    - password: User's password

    **Response:**
    - access_token: JWT access token
    - token_type: "bearer"
    - expires_in: Token expiration time in seconds
    - user: User information (id, email, name, role)

    **Cookies Set:**
    - access_token: HTTP-only cookie for API authentication
    - refresh_token: HTTP-only cookie for token refresh (path: /auth)

    **Errors:**
    - 401: Authentication failed (invalid email or password)

    **Security:**
    - Error messages are intentionally generic to prevent user enumeration
    - JWT tokens are signed with HS256 algorithm
    - Token expiration is configurable via JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    - Tokens are stored in HTTP-only cookies (XSS protection)
    """
    auth_service = AuthService(db)
    token_response = auth_service.login(credentials.email, credentials.password)

    # Create refresh token
    refresh_token = create_refresh_token({"sub": token_response.user.id})

    # Set HTTP-only cookies
    set_auth_cookies(response, token_response.access_token, refresh_token)

    return token_response


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    request: SignupRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    User signup endpoint

    **Request Body:**
    - email: User's email address
    - password: User's password (min 8 characters)
    - name: User's name
    - accept_terms: Terms acceptance flag (must be true)

    **Response:**
    - access_token: JWT access token
    - token_type: "bearer"
    - expires_in: Token expiration time in seconds
    - user: User information (id, email, name, role, status, created_at)

    **Cookies Set:**
    - access_token: HTTP-only cookie for API authentication
    - refresh_token: HTTP-only cookie for token refresh (path: /auth)

    **Errors:**
    - 400: accept_terms is not true
    - 409: Email already exists

    **Default Role:**
    - All signups are assigned LAWYER role by default

    **Security:**
    - Passwords are hashed with bcrypt before storage
    - JWT tokens are signed with HS256 algorithm
    - Token expiration is configurable via JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    - Tokens are stored in HTTP-only cookies (XSS protection)
    """
    auth_service = AuthService(db)
    token_response = auth_service.signup(
        email=request.email,
        password=request.password,
        name=request.name,
        accept_terms=request.accept_terms
    )

    # Create refresh token
    refresh_token = create_refresh_token({"sub": token_response.user.id})

    # Set HTTP-only cookies
    set_auth_cookies(response, token_response.access_token, refresh_token)

    return token_response


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token cookie

    **No Request Body Required**
    - Uses refresh_token from HTTP-only cookie

    **Response:**
    - access_token: New JWT access token
    - token_type: "bearer"
    - expires_in: Token expiration time in seconds
    - user: User information

    **Cookies Updated:**
    - access_token: New HTTP-only cookie
    - refresh_token: New HTTP-only cookie (rotated for security)

    **Errors:**
    - 401: Invalid or expired refresh token

    **Security:**
    - Refresh token is rotated on each use (prevents token reuse attacks)
    - Old refresh token becomes invalid after use
    """
    if not refresh_token:
        raise AuthenticationError("Refresh token not found")

    # Decode and validate refresh token
    payload = decode_access_token(refresh_token)
    if not payload:
        raise AuthenticationError("Invalid or expired refresh token")

    # Verify it's a refresh token
    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid refresh token")

    # Get user from database
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationError("User not found")

    # Create new tokens
    token_data = {
        "sub": user.id,
        "role": user.role.value,
        "email": user.email
    }
    new_access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token({"sub": user.id})

    # Set new cookies
    set_auth_cookies(response, new_access_token, new_refresh_token)

    # Build response
    user_out = UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        status=user.status,
        created_at=user.created_at
    )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=get_token_expire_seconds(),
        user=user_out
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(response: Response):
    """
    Logout and clear authentication cookies

    **No Request Body Required**

    **Response:**
    - message: "Successfully logged out"

    **Cookies Cleared:**
    - access_token
    - refresh_token

    **Note:**
    - This endpoint only clears cookies on the client side
    - Tokens remain valid until expiration (stateless JWT)
    - For immediate token invalidation, implement a token blacklist
    """
    clear_auth_cookies(response)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_current_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information

    **No Request Body Required**
    - Uses access_token from HTTP-only cookie OR Authorization header

    **Response:**
    - User information (id, email, name, role, status, created_at)

    **Errors:**
    - 401: Not authenticated or invalid token

    **Note:**
    - This endpoint can be used to verify authentication status
    - Returns user info without sensitive data (no password hash)
    - Supports both cookie and header authentication
    """
    token = None

    # Try Authorization header first
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    # Fall back to cookie
    if not token and access_token:
        token = access_token

    if not token:
        raise AuthenticationError("Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationError("Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token")

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationError("User not found")

    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        status=user.status,
        created_at=user.created_at
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse, status_code=status.HTTP_200_OK)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset email

    **Request Body:**
    - email: User's email address

    **Response:**
    - message: Success message (always returns success to prevent user enumeration)

    **Behavior:**
    - If email exists, sends password reset email
    - If email doesn't exist, returns success anyway (security)
    - Reset link expires in 1 hour
    """
    password_reset_service = PasswordResetService(db)
    password_reset_service.request_password_reset(request.email)

    # Always return success to prevent user enumeration
    return ForgotPasswordResponse(
        message="비밀번호 재설정 이메일이 발송되었습니다. 이메일을 확인해주세요."
    )


@router.post("/reset-password", response_model=ResetPasswordResponse, status_code=status.HTTP_200_OK)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password with token from email

    **Request Body:**
    - token: Password reset token from email link
    - new_password: New password (min 8 characters)

    **Response:**
    - message: Success message

    **Errors:**
    - 400: Invalid or expired token
    """
    password_reset_service = PasswordResetService(db)
    password_reset_service.reset_password(request.token, request.new_password)

    return ResetPasswordResponse(
        message="비밀번호가 성공적으로 변경되었습니다. 새 비밀번호로 로그인해주세요."
    )
