"""
Contract tests for Client Portal API
Tasks T055-T057 - US4 Tests

Tests for client portal endpoints:
- GET /client/dashboard (T055)
- GET /client/cases (T056)
- POST /client/cases/{id}/evidence (T057)
"""

import pytest
from fastapi import status
from app.core.security import create_access_token
from app.db.models import UserRole


# ============== T055: GET /client/dashboard Contract Tests ==============


class TestGetClientDashboard:
    """
    Contract tests for GET /client/dashboard
    """

    def test_should_return_dashboard_for_client(self, client, client_user, client_auth_headers):
        """
        Given: Authenticated client user
        When: GET /client/dashboard
        Then:
            - Returns 200 status code
            - Response contains user_name
            - Response contains case_summary (nullable)
            - Response contains progress_steps array
            - Response contains unread_messages count
        """
        # When: GET /client/dashboard
        response = client.get("/client/dashboard", headers=client_auth_headers)

        # Then: Success with dashboard data
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify required fields
        assert "user_name" in data
        assert isinstance(data["user_name"], str)

        # case_summary can be null
        assert "case_summary" in data

        # progress_steps should be a list
        assert "progress_steps" in data
        assert isinstance(data["progress_steps"], list)

        # recent_activities should be a list
        assert "recent_activities" in data
        assert isinstance(data["recent_activities"], list)

        # unread_messages should be an integer
        assert "unread_messages" in data
        assert isinstance(data["unread_messages"], int)
        assert data["unread_messages"] >= 0

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: GET /client/dashboard
        Then: Returns 401 Unauthorized
        """
        # When: GET without auth
        response = client.get("/client/dashboard")

        # Then: Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: GET /client/dashboard
        Then: Returns 403 Forbidden
        """
        # When: GET /client/dashboard as lawyer
        response = client.get("/client/dashboard", headers=auth_headers)

        # Then: Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_detective_role(self, client, test_env):
        """
        Given: User with DETECTIVE role
        When: GET /client/dashboard
        Then: Returns 403 Forbidden
        """
        # Given: Create detective user
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        detective_user = User(
            email=f"detective_client_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Detective",
            role=UserRole.DETECTIVE
        )
        db.add(detective_user)
        db.commit()
        db.refresh(detective_user)

        token = create_access_token({
            "sub": detective_user.id,
            "role": detective_user.role.value,
            "email": detective_user.email
        })

        # When: GET /client/dashboard as detective
        response = client.get(
            "/client/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Cleanup
        db.delete(detective_user)
        db.commit()
        db.close()


class TestClientDashboardProgressSteps:
    """
    Contract tests for progress_steps in client dashboard
    """

    def test_progress_steps_should_have_required_fields(self, client, client_user, client_auth_headers):
        """
        Given: Authenticated client
        When: GET /client/dashboard
        Then: Each progress step has step, title, status
        """
        response = client.get("/client/dashboard", headers=client_auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for step in data["progress_steps"]:
            assert "step" in step
            assert "title" in step
            assert "status" in step
            assert step["status"] in ["completed", "current", "pending"]


class TestClientDashboardRecentActivities:
    """
    Contract tests for recent_activities in client dashboard
    """

    def test_recent_activities_should_have_required_fields(self, client, client_user, client_auth_headers):
        """
        Given: Authenticated client
        When: GET /client/dashboard
        Then: Each activity has id, title, activity_type, timestamp
        """
        response = client.get("/client/dashboard", headers=client_auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for activity in data["recent_activities"]:
            assert "id" in activity
            assert "title" in activity
            assert "activity_type" in activity
            assert "timestamp" in activity


# ============== T056: GET /client/cases Contract Tests ==============


class TestGetClientCases:
    """
    Contract tests for GET /client/cases
    """

    def test_should_return_case_list_for_client(self, client, client_user, client_auth_headers):
        """
        Given: Authenticated client user
        When: GET /client/cases
        Then:
            - Returns 200 status code
            - Response contains items array
            - Response contains total count
        """
        # When: GET /client/cases
        response = client.get("/client/cases", headers=client_auth_headers)

        # Then: Success with case list
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify items array
        assert "items" in data
        assert isinstance(data["items"], list)

        # Verify total count
        assert "total" in data
        assert isinstance(data["total"], int)
        assert data["total"] >= 0

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: GET /client/cases
        Then: Returns 401 Unauthorized
        """
        response = client.get("/client/cases")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: GET /client/cases
        Then: Returns 403 Forbidden
        """
        response = client.get("/client/cases", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============== T057: POST /client/cases/{id}/evidence Contract Tests ==============


class TestPostEvidenceUpload:
    """
    Contract tests for POST /client/cases/{id}/evidence
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: POST /client/cases/{id}/evidence
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            "/client/cases/any_case_id/evidence",
            json={
                "file_name": "test.pdf",
                "file_type": "application/pdf",
                "file_size": 1024
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: POST /client/cases/{id}/evidence
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/client/cases/any_case_id/evidence",
            headers=auth_headers,
            json={
                "file_name": "test.pdf",
                "file_type": "application/pdf",
                "file_size": 1024
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_invalid_case_id(self, client, client_user, client_auth_headers):
        """
        Given: Authenticated client
        When: POST /client/cases/{invalid_id}/evidence
        Then: Returns 403 or 404 (no access to non-existent case)
        """
        response = client.post(
            "/client/cases/nonexistent_case_id/evidence",
            headers=client_auth_headers,
            json={
                "file_name": "test.pdf",
                "file_type": "application/pdf",
                "file_size": 1024
            }
        )
        # Should return 403 (access denied) or 404 (case not found)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


class TestEvidenceUploadConfirmation:
    """
    Contract tests for POST /client/cases/{id}/evidence/{evidence_id}/confirm
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: POST /client/cases/{id}/evidence/{evidence_id}/confirm
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            "/client/cases/case_id/evidence/ev_id/confirm",
            json={"uploaded": True}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_invalid_case_for_confirm(self, client, client_user, client_auth_headers):
        """
        Given: Authenticated client
        When: POST /client/cases/{invalid_id}/evidence/invalid_id/confirm
        Then: Returns 403 or 404
        """
        response = client.post(
            "/client/cases/invalid_case/evidence/invalid_evidence_id/confirm",
            headers=client_auth_headers,
            json={"uploaded": True}
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
