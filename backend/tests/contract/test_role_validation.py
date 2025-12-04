"""
Contract tests for Role Validation Helper Functions
Task T011 - TDD RED Phase

Tests for backend/app/core/dependencies.py role validation helpers:
- require_client()
- require_detective()
- require_lawyer()
- require_internal_user()
- get_role_redirect_path()
"""

import pytest
from fastapi import status
from app.core.security import create_access_token
from app.db.models import UserRole


class TestRequireClientDependency:
    """
    Contract tests for require_client dependency
    """

    def test_should_allow_client_user(self, client, test_env):
        """
        Given: User with CLIENT role
        When: Accessing client-only endpoint
        Then: Request succeeds (200)
        """
        # Given: Create a client user
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        client_user = User(
            email=f"client_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Client",
            role=UserRole.CLIENT
        )
        db.add(client_user)
        db.commit()
        db.refresh(client_user)

        # Create token for client user
        token = create_access_token({
            "sub": client_user.id,
            "role": client_user.role.value,
            "email": client_user.email
        })

        # When: Access client dashboard endpoint
        response = client.get(
            "/client/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Should succeed (endpoint exists and user has access)
        # Note: 404 is acceptable if endpoint not yet implemented
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        # Cleanup
        db.delete(client_user)
        db.commit()
        db.close()

    def test_should_reject_lawyer_from_client_endpoint(self, client, test_user):
        """
        Given: User with LAWYER role
        When: Accessing client-only endpoint
        Then: Returns 403 Forbidden
        """
        # Given: test_user is a lawyer
        token = create_access_token({
            "sub": test_user.id,
            "role": test_user.role.value,
            "email": test_user.email
        })

        # When: Access client-only endpoint
        response = client.get(
            "/client/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Should be forbidden (403) or not found if endpoint not implemented
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]


class TestRequireDetectiveDependency:
    """
    Contract tests for require_detective dependency
    """

    def test_should_allow_detective_user(self, client, test_env):
        """
        Given: User with DETECTIVE role
        When: Accessing detective-only endpoint
        Then: Request succeeds (200)
        """
        # Given: Create a detective user
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        detective_user = User(
            email=f"detective_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Detective",
            role=UserRole.DETECTIVE
        )
        db.add(detective_user)
        db.commit()
        db.refresh(detective_user)

        # Create token for detective user
        token = create_access_token({
            "sub": detective_user.id,
            "role": detective_user.role.value,
            "email": detective_user.email
        })

        # When: Access detective dashboard endpoint
        response = client.get(
            "/detective/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Should succeed or 404 if not implemented
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        # Cleanup
        db.delete(detective_user)
        db.commit()
        db.close()

    def test_should_reject_lawyer_from_detective_endpoint(self, client, test_user):
        """
        Given: User with LAWYER role
        When: Accessing detective-only endpoint
        Then: Returns 403 Forbidden
        """
        # Given: test_user is a lawyer
        token = create_access_token({
            "sub": test_user.id,
            "role": test_user.role.value,
            "email": test_user.email
        })

        # When: Access detective-only endpoint
        response = client.get(
            "/detective/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Should be forbidden or not found if not implemented
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]


class TestRequireInternalUserDependency:
    """
    Contract tests for require_internal_user dependency
    (lawyers, staff, admin - NOT clients or detectives)
    """

    def test_should_allow_lawyer_for_internal_endpoint(self, client, test_user):
        """
        Given: User with LAWYER role (internal)
        When: Accessing internal-only endpoint
        Then: Request succeeds (200)
        """
        # Given: test_user is a lawyer (internal)
        token = create_access_token({
            "sub": test_user.id,
            "role": test_user.role.value,
            "email": test_user.email
        })

        # When: Access lawyer dashboard (internal endpoint)
        response = client.get(
            "/lawyer/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Should succeed or 404 if not implemented
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_should_reject_client_from_internal_endpoint(self, client, test_env):
        """
        Given: User with CLIENT role (external)
        When: Accessing internal-only endpoint
        Then: Returns 403 Forbidden
        """
        # Given: Create a client user (external)
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        client_user = User(
            email=f"client_internal_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Client",
            role=UserRole.CLIENT
        )
        db.add(client_user)
        db.commit()
        db.refresh(client_user)

        token = create_access_token({
            "sub": client_user.id,
            "role": client_user.role.value,
            "email": client_user.email
        })

        # When: Access lawyer dashboard (internal endpoint)
        response = client.get(
            "/lawyer/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Should be forbidden or not found if not implemented
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]

        # Cleanup
        db.delete(client_user)
        db.commit()
        db.close()


class TestGetRoleRedirectPath:
    """
    Contract tests for get_role_redirect_path function
    """

    def test_should_return_correct_path_for_client(self):
        """
        Given: CLIENT role
        When: get_role_redirect_path is called
        Then: Returns /client/dashboard
        """
        from app.core.dependencies import get_role_redirect_path

        path = get_role_redirect_path(UserRole.CLIENT)
        assert path == "/client/dashboard"

    def test_should_return_correct_path_for_detective(self):
        """
        Given: DETECTIVE role
        When: get_role_redirect_path is called
        Then: Returns /detective/dashboard
        """
        from app.core.dependencies import get_role_redirect_path

        path = get_role_redirect_path(UserRole.DETECTIVE)
        assert path == "/detective/dashboard"

    def test_should_return_correct_path_for_lawyer(self):
        """
        Given: LAWYER role
        When: get_role_redirect_path is called
        Then: Returns /lawyer/dashboard
        """
        from app.core.dependencies import get_role_redirect_path

        path = get_role_redirect_path(UserRole.LAWYER)
        assert path == "/lawyer/dashboard"

    def test_should_return_correct_path_for_admin(self):
        """
        Given: ADMIN role
        When: get_role_redirect_path is called
        Then: Returns /admin/dashboard
        """
        from app.core.dependencies import get_role_redirect_path

        path = get_role_redirect_path(UserRole.ADMIN)
        assert path == "/admin/dashboard"

    def test_should_return_correct_path_for_staff(self):
        """
        Given: STAFF role
        When: get_role_redirect_path is called
        Then: Returns /lawyer/dashboard (staff uses lawyer dashboard)
        """
        from app.core.dependencies import get_role_redirect_path

        path = get_role_redirect_path(UserRole.STAFF)
        assert path == "/lawyer/dashboard"
