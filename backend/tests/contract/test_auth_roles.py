"""
Contract tests for Signup with CLIENT/DETECTIVE Roles
Task T012 - TDD RED Phase

Tests for POST /auth/signup endpoint with new roles:
- Signup as CLIENT role
- Signup as DETECTIVE role
- Validate role is correctly saved and returned
"""

import pytest
from fastapi import status
from app.db.models import UserRole


class TestSignupWithClientRole:
    """
    Contract tests for signup with CLIENT role
    """

    def test_should_create_user_with_client_role(self, client):
        """
        Given: Valid signup data with role="client"
        When: POST /auth/signup is called
        Then:
            - Returns 201 status code
            - Response contains user with role="client"
            - User can login with client role
        """
        # Given: Signup data with CLIENT role
        signup_payload = {
            "email": "newclient@example.com",
            "password": "password123",
            "name": "New Client User",
            "accept_terms": True,
            "role": "client"
        }

        # When: POST /auth/signup
        response = client.post("/auth/signup", json=signup_payload)

        # Then: Success response with CLIENT role
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert "user" in data
        assert data["user"]["role"] == "client"
        assert data["user"]["email"] == "newclient@example.com"

    def test_should_allow_client_to_login_after_signup(self, client):
        """
        Given: User signed up with CLIENT role
        When: POST /auth/login is called with same credentials
        Then:
            - Returns 200 status code
            - Response contains user with role="client"
        """
        # Given: First signup as client
        signup_payload = {
            "email": "client_login_test@example.com",
            "password": "password123",
            "name": "Client Login Test",
            "accept_terms": True,
            "role": "client"
        }
        signup_response = client.post("/auth/signup", json=signup_payload)
        assert signup_response.status_code == status.HTTP_201_CREATED

        # When: Login with same credentials
        login_payload = {
            "email": "client_login_test@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", json=login_payload)

        # Then: Success with client role
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["user"]["role"] == "client"


class TestSignupWithDetectiveRole:
    """
    Contract tests for signup with DETECTIVE role
    """

    def test_should_create_user_with_detective_role(self, client):
        """
        Given: Valid signup data with role="detective"
        When: POST /auth/signup is called
        Then:
            - Returns 201 status code
            - Response contains user with role="detective"
        """
        # Given: Signup data with DETECTIVE role
        signup_payload = {
            "email": "newdetective@example.com",
            "password": "password123",
            "name": "New Detective User",
            "accept_terms": True,
            "role": "detective"
        }

        # When: POST /auth/signup
        response = client.post("/auth/signup", json=signup_payload)

        # Then: Success response with DETECTIVE role
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert "user" in data
        assert data["user"]["role"] == "detective"
        assert data["user"]["email"] == "newdetective@example.com"

    def test_should_allow_detective_to_login_after_signup(self, client):
        """
        Given: User signed up with DETECTIVE role
        When: POST /auth/login is called with same credentials
        Then:
            - Returns 200 status code
            - Response contains user with role="detective"
        """
        # Given: First signup as detective
        signup_payload = {
            "email": "detective_login_test@example.com",
            "password": "password123",
            "name": "Detective Login Test",
            "accept_terms": True,
            "role": "detective"
        }
        signup_response = client.post("/auth/signup", json=signup_payload)
        assert signup_response.status_code == status.HTTP_201_CREATED

        # When: Login with same credentials
        login_payload = {
            "email": "detective_login_test@example.com",
            "password": "password123"
        }
        response = client.post("/auth/login", json=login_payload)

        # Then: Success with detective role
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["user"]["role"] == "detective"


class TestSignupDefaultRole:
    """
    Contract tests for default role behavior
    """

    def test_should_default_to_lawyer_when_no_role_specified(self, client):
        """
        Given: Valid signup data WITHOUT role field
        When: POST /auth/signup is called
        Then:
            - Returns 201 status code
            - Response contains user with role="lawyer" (default)
        """
        # Given: Signup data without role (default behavior)
        signup_payload = {
            "email": "defaultrole@example.com",
            "password": "password123",
            "name": "Default Role User",
            "accept_terms": True
            # No role specified
        }

        # When: POST /auth/signup
        response = client.post("/auth/signup", json=signup_payload)

        # Then: Success with LAWYER role (default)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["user"]["role"] == "lawyer"


class TestSignupInvalidRole:
    """
    Contract tests for invalid role handling
    """

    def test_should_reject_invalid_role(self, client):
        """
        Given: Signup data with invalid role value
        When: POST /auth/signup is called
        Then:
            - Returns 422 Unprocessable Entity
            - Response contains validation error
        """
        # Given: Invalid role
        signup_payload = {
            "email": "invalidrole@example.com",
            "password": "password123",
            "name": "Invalid Role User",
            "accept_terms": True,
            "role": "invalid_role"  # This role doesn't exist
        }

        # When: POST /auth/signup
        response = client.post("/auth/signup", json=signup_payload)

        # Then: Validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRoleEnumValues:
    """
    Contract tests for UserRole enum
    """

    def test_user_role_enum_contains_client(self):
        """
        Given: UserRole enum
        When: Checking for CLIENT value
        Then: CLIENT exists in enum
        """
        assert hasattr(UserRole, 'CLIENT')
        assert UserRole.CLIENT.value == "client"

    def test_user_role_enum_contains_detective(self):
        """
        Given: UserRole enum
        When: Checking for DETECTIVE value
        Then: DETECTIVE exists in enum
        """
        assert hasattr(UserRole, 'DETECTIVE')
        assert UserRole.DETECTIVE.value == "detective"

    def test_user_role_enum_has_all_expected_roles(self):
        """
        Given: UserRole enum
        When: Checking all role values
        Then: All 5 roles exist (lawyer, staff, admin, client, detective)
        """
        expected_roles = {"lawyer", "staff", "admin", "client", "detective"}
        actual_roles = {role.value for role in UserRole}

        assert expected_roles == actual_roles
