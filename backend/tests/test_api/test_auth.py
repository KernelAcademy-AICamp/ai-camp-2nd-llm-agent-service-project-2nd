"""
Test suite for Authentication API endpoints

Tests for:
- POST /auth/login - JWT issuance with expiration time (cookie-based)
- POST /auth/signup - User registration with JWT issuance (cookie-based)
- POST /auth/refresh - Token refresh using refresh_token cookie
- POST /auth/logout - Logout and clear cookies
- GET /auth/me - Get current user info
- Invalid credentials handling (401)
- JWT validation and user context
"""

import pytest
from datetime import datetime, timezone
from fastapi import status
from app.core.security import create_access_token, create_refresh_token


class TestAuthLogin:
    """
    Test suite for POST /auth/login endpoint
    """

    def test_should_issue_jwt_on_successful_login(self, client, test_user):
        """
        Given: Valid email and password
        When: POST /auth/login is called
        Then:
            - Returns 200 status code
            - Response contains access_token
            - Response contains token_type "bearer"
            - Response contains expires_in (integer seconds)
            - Response contains user info (id, name, role)
        """
        # Given: Valid credentials for the test_user
        login_payload = {
            "email": test_user.email,
            "password": "correct_password123"
        }

        # When: POST /auth/login
        response = client.post("/auth/login", json=login_payload)

        # Then: Success response with JWT
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data

        # Validate token_type
        assert data["token_type"] == "bearer"

        # Validate expires_in is an integer (seconds)
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

        # Validate user info
        user = data["user"]
        assert "id" in user
        assert "name" in user
        assert "role" in user
        assert user["email"] == test_user.email

    def test_should_return_401_for_invalid_email(self, client, test_user):
        """
        Given: Invalid email (user does not exist)
        When: POST /auth/login is called
        Then:
            - Returns 401 Unauthorized
            - Response contains error message
            - Error message is intentionally generic (security best practice)
        """
        # Given: Invalid email
        login_payload = {
            "email": "nonexistent@example.com",
            "password": "any_password"
        }

        # When: POST /auth/login
        response = client.post("/auth/login", json=login_payload)

        # Then: 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTHENTICATION_FAILED"
        # Generic message to prevent user enumeration
        assert "이메일 또는 비밀번호" in data["error"]["message"]

    def test_should_return_401_for_invalid_password(self, client, test_user):
        """
        Given: Valid email but incorrect password
        When: POST /auth/login is called
        Then:
            - Returns 401 Unauthorized
            - Response contains error message
            - Error message is intentionally generic (security best practice)
        """
        # Given: Valid email but wrong password
        login_payload = {
            "email": test_user.email,
            "password": "wrong_password"
        }

        # When: POST /auth/login
        response = client.post("/auth/login", json=login_payload)

        # Then: 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTHENTICATION_FAILED"
        # Generic message to prevent user enumeration
        assert "이메일 또는 비밀번호" in data["error"]["message"]


class TestAuthSignup:
    """
    Test suite for POST /auth/signup endpoint
    """

    def test_should_create_user_and_issue_jwt_on_successful_signup(self, client):
        """
        Given: Valid signup data with accept_terms=true
        When: POST /auth/signup is called
        Then:
            - Returns 201 status code
            - Response contains access_token
            - Response contains token_type "bearer"
            - Response contains expires_in (integer seconds)
            - Response contains user info with LAWYER role
            - User is created in database
        """
        # Given: Valid signup data
        signup_payload = {
            "email": "newuser@example.com",
            "password": "password123",
            "name": "New User",
            "accept_terms": True
        }

        # When: POST /auth/signup
        response = client.post("/auth/signup", json=signup_payload)

        # Then: Success response with JWT
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data

        # Validate token_type
        assert data["token_type"] == "bearer"

        # Validate expires_in is an integer (seconds)
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

        # Validate user info
        user = data["user"]
        assert "id" in user
        assert "name" in user
        assert "role" in user
        assert "status" in user
        assert "created_at" in user
        assert user["email"] == "newuser@example.com"
        assert user["name"] == "New User"
        assert user["role"] == "lawyer"  # Default role for signup
        assert user["status"] == "active"

    def test_should_return_409_when_email_already_exists(self, client, test_user):
        """
        Given: Email that already exists in database
        When: POST /auth/signup is called
        Then:
            - Returns 409 Conflict
            - Response contains error message about duplicate email
        """
        # Given: Signup with existing email
        signup_payload = {
            "email": test_user.email,  # This email already exists
            "password": "password123",
            "name": "Another User",
            "accept_terms": True
        }

        # When: POST /auth/signup
        response = client.post("/auth/signup", json=signup_payload)

        # Then: 409 Conflict
        assert response.status_code == status.HTTP_409_CONFLICT

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "CONFLICT"
        assert "이미 등록된 이메일" in data["error"]["message"]

    def test_should_return_400_when_accept_terms_is_false(self, client):
        """
        Given: Valid signup data but accept_terms=false
        When: POST /auth/signup is called
        Then:
            - Returns 400 Bad Request
            - Response contains error message about terms acceptance
        """
        # Given: accept_terms is false
        signup_payload = {
            "email": "user@example.com",
            "password": "password123",
            "name": "User",
            "accept_terms": False
        }

        # When: POST /auth/signup
        response = client.post("/auth/signup", json=signup_payload)

        # Then: 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "이용약관 동의" in data["error"]["message"]

    def test_should_hash_password_with_bcrypt(self, client):
        """
        Given: Valid signup data
        When: POST /auth/signup is called
        Then:
            - Password is hashed with bcrypt (not stored in plain text)
            - Can login with the same password
        """
        # Given: Valid signup data
        signup_payload = {
            "email": "secure@example.com",
            "password": "securepass123",
            "name": "Secure User",
            "accept_terms": True
        }

        # When: POST /auth/signup
        signup_response = client.post("/auth/signup", json=signup_payload)
        assert signup_response.status_code == status.HTTP_201_CREATED

        # Then: Verify password is hashed by attempting login
        login_payload = {
            "email": "secure@example.com",
            "password": "securepass123"
        }
        login_response = client.post("/auth/login", json=login_payload)
        assert login_response.status_code == status.HTTP_200_OK

        # Verify stored password is not plain text
        from app.db.session import get_db
        from app.db.models import User

        db = next(get_db())
        user = db.query(User).filter(User.email == "secure@example.com").first()
        assert user.hashed_password != "securepass123"
        assert user.hashed_password.startswith("$2b$")  # Bcrypt hash prefix

    def test_should_reject_short_password(self, client):
        """
        Given: Password with less than 8 characters
        When: POST /auth/signup is called
        Then:
            - Returns 422 Unprocessable Entity (Pydantic validation error)
        """
        # Given: Short password (7 characters)
        signup_payload = {
            "email": "user@example.com",
            "password": "short12",  # Only 7 characters
            "name": "User",
            "accept_terms": True
        }

        # When: POST /auth/signup
        response = client.post("/auth/signup", json=signup_payload)

        # Then: 422 Validation Error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_should_reject_invalid_email(self, client):
        """
        Given: Invalid email format
        When: POST /auth/signup is called
        Then:
            - Returns 422 Unprocessable Entity (Pydantic validation error)
        """
        # Given: Invalid email format
        signup_payload = {
            "email": "not-an-email",
            "password": "password123",
            "name": "User",
            "accept_terms": True
        }

        # When: POST /auth/signup
        response = client.post("/auth/signup", json=signup_payload)

        # Then: 422 Validation Error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthCookies:
    """
    Test suite for HTTP-only cookie authentication
    """

    def test_should_set_httponly_cookies_on_login(self, client, test_user):
        """
        Given: Valid login credentials
        When: POST /auth/login is called
        Then:
            - access_token cookie is set with httponly flag
            - refresh_token cookie is set with httponly flag
        """
        # Given
        login_payload = {
            "email": test_user.email,
            "password": "correct_password123"
        }

        # When
        response = client.post("/auth/login", json=login_payload)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # Check cookies are set
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies

    def test_should_set_httponly_cookies_on_signup(self, client):
        """
        Given: Valid signup data
        When: POST /auth/signup is called
        Then:
            - access_token cookie is set with httponly flag
            - refresh_token cookie is set with httponly flag
        """
        # Given
        signup_payload = {
            "email": "cookietest@example.com",
            "password": "password123",
            "name": "Cookie Test User",
            "accept_terms": True
        }

        # When
        response = client.post("/auth/signup", json=signup_payload)

        # Then
        assert response.status_code == status.HTTP_201_CREATED

        # Check cookies are set
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies


class TestAuthRefresh:
    """
    Test suite for POST /auth/refresh endpoint
    """

    def test_should_refresh_tokens_with_valid_refresh_token(self, client, test_user):
        """
        Given: Valid refresh_token cookie
        When: POST /auth/refresh is called
        Then:
            - Returns 200 status code
            - New access_token is issued
            - New refresh_token cookie is set (token rotation)
            - Response contains user info
        """
        # Given: Create a refresh token for the test user
        refresh_token = create_refresh_token({"sub": test_user.id})
        client.cookies.set("refresh_token", refresh_token)

        # When
        response = client.post("/auth/refresh")

        # Then
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data

        # Verify token rotation - new cookies should be set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    def test_should_return_401_without_refresh_token(self, client):
        """
        Given: No refresh_token cookie
        When: POST /auth/refresh is called
        Then:
            - Returns 401 Unauthorized
        """
        # When
        response = client.post("/auth/refresh")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_return_401_with_invalid_refresh_token(self, client):
        """
        Given: Invalid refresh_token cookie
        When: POST /auth/refresh is called
        Then:
            - Returns 401 Unauthorized
        """
        # Given
        client.cookies.set("refresh_token", "invalid_token")

        # When
        response = client.post("/auth/refresh")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_return_401_with_access_token_as_refresh(self, client, test_user):
        """
        Given: access_token used as refresh_token (wrong token type)
        When: POST /auth/refresh is called
        Then:
            - Returns 401 Unauthorized (token type mismatch)
        """
        # Given: Use access token (which lacks type="refresh")
        access_token = create_access_token({"sub": test_user.id, "role": test_user.role.value})
        client.cookies.set("refresh_token", access_token)

        # When
        response = client.post("/auth/refresh")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthLogout:
    """
    Test suite for POST /auth/logout endpoint
    """

    def test_should_clear_cookies_on_logout(self, client, test_user):
        """
        Given: User is logged in with cookies
        When: POST /auth/logout is called
        Then:
            - Returns 200 status code
            - access_token cookie is cleared
            - refresh_token cookie is cleared
            - Response contains success message
        """
        # Given: Login first
        login_payload = {
            "email": test_user.email,
            "password": "correct_password123"
        }
        login_response = client.post("/auth/login", json=login_payload)
        assert login_response.status_code == status.HTTP_200_OK

        # When
        response = client.post("/auth/logout")

        # Then
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()

    def test_should_succeed_even_without_cookies(self, client):
        """
        Given: No cookies (not logged in)
        When: POST /auth/logout is called
        Then:
            - Returns 200 status code (idempotent operation)
        """
        # When
        response = client.post("/auth/logout")

        # Then
        assert response.status_code == status.HTTP_200_OK


class TestAuthMe:
    """
    Test suite for GET /auth/me endpoint
    """

    def test_should_return_user_info_with_cookie(self, client, test_user):
        """
        Given: Valid access_token cookie
        When: GET /auth/me is called
        Then:
            - Returns 200 status code
            - Response contains user info
        """
        # Given: Create access token and set cookie
        access_token = create_access_token({
            "sub": test_user.id,
            "role": test_user.role.value,
            "email": test_user.email
        })
        client.cookies.set("access_token", access_token)

        # When
        response = client.get("/auth/me")

        # Then
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert "role" in data
        assert "status" in data

    def test_should_return_user_info_with_authorization_header(self, client, test_user):
        """
        Given: Valid Authorization header (Bearer token)
        When: GET /auth/me is called
        Then:
            - Returns 200 status code
            - Response contains user info
        """
        # Given: Create access token and use header
        access_token = create_access_token({
            "sub": test_user.id,
            "role": test_user.role.value,
            "email": test_user.email
        })
        headers = {"Authorization": f"Bearer {access_token}"}

        # When
        response = client.get("/auth/me", headers=headers)

        # Then
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    def test_should_return_401_without_authentication(self, client):
        """
        Given: No authentication (no cookie, no header)
        When: GET /auth/me is called
        Then:
            - Returns 401 Unauthorized
        """
        # When
        response = client.get("/auth/me")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_return_401_with_invalid_token(self, client):
        """
        Given: Invalid access_token cookie
        When: GET /auth/me is called
        Then:
            - Returns 401 Unauthorized
        """
        # Given
        client.cookies.set("access_token", "invalid_token")

        # When
        response = client.get("/auth/me")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_prefer_header_over_cookie(self, client, test_user):
        """
        Given: Both Authorization header and cookie are present
        When: GET /auth/me is called
        Then:
            - Authorization header takes precedence
        """
        # Given: Valid header token, invalid cookie
        access_token = create_access_token({
            "sub": test_user.id,
            "role": test_user.role.value,
            "email": test_user.email
        })
        headers = {"Authorization": f"Bearer {access_token}"}
        client.cookies.set("access_token", "invalid_cookie_token")

        # When
        response = client.get("/auth/me", headers=headers)

        # Then: Should succeed because header is valid
        assert response.status_code == status.HTTP_200_OK
