"""
Tests for Admin User Management API
Testing POST /admin/users/invite, GET /admin/users, DELETE /admin/users/{user_id}
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def admin_user(test_env):
    """
    Create admin user in the database for admin tests

    Password: admin_password123
    """
    from app.db.session import get_db
    from app.db.models import User, Case, CaseMember, InviteToken
    from app.core.security import hash_password
    from sqlalchemy.orm import Session

    # Database is already initialized by test_env fixture
    # Create admin user
    db: Session = next(get_db())
    try:
        admin = User(
            email="admin@example.com",
            hashed_password=hash_password("admin_password123"),
            name="Admin User",
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        yield admin

        # Cleanup - delete in correct order to respect foreign keys
        try:
            db.query(InviteToken).filter(InviteToken.created_by == admin.id).delete()
        except Exception:
            pass
        db.query(CaseMember).filter(CaseMember.user_id == admin.id).delete()
        db.query(Case).filter(Case.created_by == admin.id).delete()
        db.delete(admin)
        db.commit()
    finally:
        db.close()
        # Note: Tables are NOT dropped to allow other fixtures/tests to reuse the schema


@pytest.fixture
def admin_auth_headers(admin_user):
    """
    Generate authentication headers with JWT token for admin_user

    Returns:
        dict: Headers with Authorization Bearer token
    """
    from app.core.security import create_access_token

    # Create JWT token for admin user
    token = create_access_token(data={"sub": admin_user.id, "role": admin_user.role})

    return {
        "Authorization": f"Bearer {token}"
    }


class TestPostAdminUsersInvite:
    """
    Tests for POST /admin/users/invite endpoint
    """

    def test_should_create_invite_token_when_admin_invites_user(
        self, client: TestClient, admin_auth_headers
    ):
        """
        Given: Admin user with valid credentials
        When: POST /admin/users/invite with email and role
        Then: Returns 201 with invite_token and invite_url
        """
        # Given
        invite_payload = {
            "email": "newuser@example.com",
            "role": "lawyer"
        }

        # When
        response = client.post(
            "/admin/users/invite",
            json=invite_payload,
            headers=admin_auth_headers
        )

        # Then
        assert response.status_code == 201
        data = response.json()
        assert "invite_token" in data
        assert "invite_url" in data
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "lawyer"
        assert "expires_at" in data
        assert "http://localhost:3000/signup?token=" in data["invite_url"]

    def test_should_return_400_when_inviting_existing_user(
        self, client: TestClient, admin_auth_headers, admin_user
    ):
        """
        Given: User already exists with email
        When: POST /admin/users/invite with duplicate email
        Then: Returns 400 with validation error
        """
        # Given
        invite_payload = {
            "email": admin_user.email,  # Already registered
            "role": "lawyer"
        }

        # When
        response = client.post(
            "/admin/users/invite",
            json=invite_payload,
            headers=admin_auth_headers
        )

        # Then
        assert response.status_code == 400
        data = response.json()
        # Handle both error formats: {"detail": ...} and {"error": {"message": ...}}
        if "error" in data:
            message = data["error"].get("message", "")
        else:
            detail = data.get("detail", "")
            message = detail.get("message", str(detail)) if isinstance(detail, dict) else str(detail)
        assert "이미" in message  # "이미 등록된 이메일" or "이미 초대된 사용자입니다"

    def test_should_return_403_when_non_admin_tries_to_invite(
        self, client: TestClient, auth_headers
    ):
        """
        Given: Non-admin user (LAWYER role)
        When: POST /admin/users/invite
        Then: Returns 403 permission error
        """
        # Given
        invite_payload = {
            "email": "newuser@example.com",
            "role": "lawyer"
        }

        # When
        response = client.post(
            "/admin/users/invite",
            json=invite_payload,
            headers=auth_headers
        )

        # Then
        assert response.status_code == 403
        data = response.json()
        # Handle both error formats: {"detail": ...} and {"error": {"message": ...}}
        if "error" in data:
            message = data["error"].get("message", "")
        else:
            detail = data.get("detail", "")
            message = detail.get("message", str(detail)) if isinstance(detail, dict) else str(detail)
        assert "권한" in message  # "권한이 없습니다" or "Admin 권한"

    def test_should_return_401_when_not_authenticated(
        self, client: TestClient
    ):
        """
        Given: No authentication token
        When: POST /admin/users/invite
        Then: Returns 401 authentication error
        """
        # Given
        invite_payload = {
            "email": "newuser@example.com",
            "role": "lawyer"
        }

        # When
        response = client.post(
            "/admin/users/invite",
            json=invite_payload
        )

        # Then
        assert response.status_code == 401


class TestGetAdminUsers:
    """
    Tests for GET /admin/users endpoint
    """

    def test_should_list_all_users_when_admin_requests(
        self, client: TestClient, admin_auth_headers, admin_user, test_user
    ):
        """
        Given: Multiple users in database
        When: GET /admin/users
        Then: Returns 200 with list of all users
        """
        # When
        response = client.get(
            "/admin/users",
            headers=admin_auth_headers
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 2  # At least admin and test_user

        # Check user fields
        user = data["users"][0]
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "role" in user
        assert "status" in user
        assert "created_at" in user

    def test_should_filter_by_email_when_query_provided(
        self, client: TestClient, admin_auth_headers, admin_user
    ):
        """
        Given: Multiple users in database
        When: GET /admin/users?email=admin
        Then: Returns only users matching email filter
        """
        # When
        response = client.get(
            "/admin/users?email=admin",
            headers=admin_auth_headers
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for user in data["users"]:
            assert "admin" in user["email"].lower()

    def test_should_filter_by_role_when_query_provided(
        self, client: TestClient, admin_auth_headers, admin_user
    ):
        """
        Given: Multiple users in database
        When: GET /admin/users?role=admin
        Then: Returns only admin users
        """
        # When
        response = client.get(
            "/admin/users?role=admin",
            headers=admin_auth_headers
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        for user in data["users"]:
            assert user["role"] == "admin"

    def test_should_return_403_when_non_admin_tries_to_list_users(
        self, client: TestClient, auth_headers
    ):
        """
        Given: Non-admin user
        When: GET /admin/users
        Then: Returns 403 permission error
        """
        # When
        response = client.get(
            "/admin/users",
            headers=auth_headers
        )

        # Then
        assert response.status_code == 403


class TestDeleteAdminUsersUserId:
    """
    Tests for DELETE /admin/users/{user_id} endpoint
    """

    def test_should_soft_delete_user_when_admin_deletes(
        self, client: TestClient, admin_auth_headers, test_user
    ):
        """
        Given: User exists in database
        When: DELETE /admin/users/{user_id}
        Then: Returns 200 and user status becomes INACTIVE
        """
        # When
        response = client.delete(
            f"/admin/users/{test_user.id}",
            headers=admin_auth_headers
        )

        # Then
        assert response.status_code == 200

        # Verify soft delete (status = INACTIVE)
        from app.db.session import get_db
        from app.db.models import User, UserStatus
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == test_user.id).first()
            assert user is not None
            assert user.status == UserStatus.INACTIVE
        finally:
            db.close()

    def test_should_return_400_when_admin_tries_to_delete_self(
        self, client: TestClient, admin_auth_headers, admin_user
    ):
        """
        Given: Admin user
        When: DELETE /admin/users/{own_id}
        Then: Returns 400 validation error
        """
        # When
        response = client.delete(
            f"/admin/users/{admin_user.id}",
            headers=admin_auth_headers
        )

        # Then
        assert response.status_code == 400
        data = response.json()
        # Handle both error formats: {"detail": ...} and {"error": {"message": ...}}
        if "error" in data:
            message = data["error"].get("message", "")
        else:
            detail = data.get("detail", "")
            message = detail.get("message", str(detail)) if isinstance(detail, dict) else str(detail)
        assert "자기 자신을 삭제할 수 없습니다" in message

    def test_should_return_404_when_user_not_found(
        self, client: TestClient, admin_auth_headers
    ):
        """
        Given: Non-existent user ID
        When: DELETE /admin/users/{invalid_id}
        Then: Returns 404 not found error
        """
        # When
        response = client.delete(
            "/admin/users/user_nonexistent",
            headers=admin_auth_headers
        )

        # Then
        assert response.status_code == 404

    def test_should_return_403_when_non_admin_tries_to_delete(
        self, client: TestClient, auth_headers, test_user
    ):
        """
        Given: Non-admin user
        When: DELETE /admin/users/{user_id}
        Then: Returns 403 permission error
        """
        # When
        response = client.delete(
            f"/admin/users/{test_user.id}",
            headers=auth_headers
        )

        # Then
        assert response.status_code == 403
