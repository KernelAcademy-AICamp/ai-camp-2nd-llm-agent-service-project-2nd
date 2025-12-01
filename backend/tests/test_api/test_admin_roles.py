"""
Tests for Admin RBAC API
Testing GET /admin/roles, PUT /admin/roles/{role}/permissions
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def admin_user(test_env):
    """
    Create admin user for RBAC tests

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
    """
    from app.core.security import create_access_token

    token = create_access_token(data={"sub": admin_user.id, "role": admin_user.role})

    return {
        "Authorization": f"Bearer {token}"
    }


class TestGetAdminRoles:
    """
    Tests for GET /admin/roles endpoint
    """

    def test_should_return_all_role_permissions_when_admin_requests(
        self, client: TestClient, admin_auth_headers
    ):
        """
        Given: Admin user
        When: GET /admin/roles
        Then: Returns 200 with permission matrix for all roles (ADMIN, LAWYER, STAFF)
        """
        # When
        response = client.get(
            "/admin/roles",
            headers=admin_auth_headers
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "roles" in data
        assert len(data["roles"]) == 3

        # Check ADMIN permissions
        admin_role = next(r for r in data["roles"] if r["role"] == "admin")
        assert admin_role["cases"]["view"]
        assert admin_role["cases"]["edit"]
        assert admin_role["cases"]["delete"]
        assert admin_role["admin"]["view"]

        # Check LAWYER permissions
        lawyer_role = next(r for r in data["roles"] if r["role"] == "lawyer")
        assert lawyer_role["cases"]["view"]
        assert lawyer_role["cases"]["edit"]
        assert not lawyer_role["admin"]["view"]

        # Check STAFF permissions
        staff_role = next(r for r in data["roles"] if r["role"] == "staff")
        assert staff_role["cases"]["view"]
        assert not staff_role["cases"]["edit"]
        assert not staff_role["cases"]["delete"]

    def test_should_return_403_when_non_admin_tries_to_get_roles(
        self, client: TestClient, auth_headers
    ):
        """
        Given: Non-admin user
        When: GET /admin/roles
        Then: Returns 403 permission error
        """
        # When
        response = client.get(
            "/admin/roles",
            headers=auth_headers
        )

        # Then
        assert response.status_code == 403

    def test_should_return_401_when_not_authenticated(
        self, client: TestClient
    ):
        """
        Given: No authentication
        When: GET /admin/roles
        Then: Returns 401 authentication error
        """
        # When
        response = client.get("/admin/roles")

        # Then
        assert response.status_code == 401


class TestPutAdminRolesPermissions:
    """
    Tests for PUT /admin/roles/{role}/permissions endpoint
    """

    def test_should_update_role_permissions_when_admin_requests(
        self, client: TestClient, admin_auth_headers
    ):
        """
        Given: Admin user with new permission settings
        When: PUT /admin/roles/lawyer/permissions
        Then: Returns 200 with updated permissions
        """
        # Given
        new_permissions = {
            "cases": {"view": True, "edit": True, "delete": False},
            "evidence": {"view": True, "edit": False, "delete": False},
            "admin": {"view": False, "edit": False, "delete": False},
            "billing": {"view": False, "edit": False, "delete": False}
        }

        # When
        response = client.put(
            "/admin/roles/lawyer/permissions",
            json=new_permissions,
            headers=admin_auth_headers
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "lawyer"
        assert data["cases"]["view"]
        assert not data["cases"]["delete"]
        assert not data["evidence"]["edit"]

    def test_should_return_403_when_non_admin_tries_to_update_permissions(
        self, client: TestClient, auth_headers
    ):
        """
        Given: Non-admin user
        When: PUT /admin/roles/staff/permissions
        Then: Returns 403 permission error
        """
        # Given
        new_permissions = {
            "cases": {"view": True, "edit": True, "delete": True},
            "evidence": {"view": True, "edit": True, "delete": True},
            "admin": {"view": False, "edit": False, "delete": False},
            "billing": {"view": False, "edit": False, "delete": False}
        }

        # When
        response = client.put(
            "/admin/roles/staff/permissions",
            json=new_permissions,
            headers=auth_headers
        )

        # Then
        assert response.status_code == 403

    def test_should_return_401_when_not_authenticated(
        self, client: TestClient
    ):
        """
        Given: No authentication
        When: PUT /admin/roles/admin/permissions
        Then: Returns 401 authentication error
        """
        # Given
        new_permissions = {
            "cases": {"view": True, "edit": True, "delete": True},
            "evidence": {"view": True, "edit": True, "delete": True},
            "admin": {"view": True, "edit": True, "delete": True},
            "billing": {"view": True, "edit": True, "delete": True}
        }

        # When
        response = client.put(
            "/admin/roles/admin/permissions",
            json=new_permissions
        )

        # Then
        assert response.status_code == 401
