"""
Contract tests for Detective Dashboard API
Task T077 - US5 Tests

Tests for detective dashboard endpoint:
- GET /detective/dashboard
"""

import pytest
from fastapi import status
from app.core.security import create_access_token
from app.db.models import UserRole


# ============== T077: GET /detective/dashboard Contract Tests ==============


class TestGetDetectiveDashboard:
    """
    Contract tests for GET /detective/dashboard
    """

    def test_should_return_dashboard_for_detective(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective user
        When: GET /detective/dashboard
        Then:
            - Returns 200 status code
            - Response contains user_name
            - Response contains stats object
            - Response contains active_investigations array
            - Response contains today_schedule array
        """
        # When: GET /detective/dashboard
        response = client.get("/detective/dashboard", headers=detective_auth_headers)

        # Then: Success with dashboard data
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify required fields
        assert "user_name" in data
        assert isinstance(data["user_name"], str)

        # stats should be an object with specific fields
        assert "stats" in data
        stats = data["stats"]
        assert "active_investigations" in stats
        assert "pending_requests" in stats
        assert "completed_this_month" in stats
        assert "monthly_earnings" in stats

        # active_investigations should be a list
        assert "active_investigations" in data
        assert isinstance(data["active_investigations"], list)

        # today_schedule should be a list
        assert "today_schedule" in data
        assert isinstance(data["today_schedule"], list)

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: GET /detective/dashboard
        Then: Returns 401 Unauthorized
        """
        # When: GET without auth
        response = client.get("/detective/dashboard")

        # Then: Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_user, client_auth_headers):
        """
        Given: User with CLIENT role
        When: GET /detective/dashboard
        Then: Returns 403 Forbidden
        """
        # When: GET /detective/dashboard as client
        response = client.get("/detective/dashboard", headers=client_auth_headers)

        # Then: Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: GET /detective/dashboard
        Then: Returns 403 Forbidden
        """
        # When: GET /detective/dashboard as lawyer
        response = client.get("/detective/dashboard", headers=auth_headers)

        # Then: Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDetectiveDashboardStats:
    """
    Contract tests for stats structure in detective dashboard
    """

    def test_stats_should_have_numeric_values(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: GET /detective/dashboard
        Then: Stats values are appropriate types
        """
        response = client.get("/detective/dashboard", headers=detective_auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        stats = data["stats"]

        # Numeric counts
        assert isinstance(stats["active_investigations"], int)
        assert isinstance(stats["pending_requests"], int)
        assert isinstance(stats["completed_this_month"], int)

        # Earnings can be int or float
        assert isinstance(stats["monthly_earnings"], (int, float))


class TestDetectiveDashboardInvestigations:
    """
    Contract tests for active_investigations in detective dashboard
    """

    def test_active_investigations_should_have_required_fields(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective with investigations
        When: GET /detective/dashboard
        Then: Each investigation has required fields
        """
        response = client.get("/detective/dashboard", headers=detective_auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for investigation in data["active_investigations"]:
            assert "id" in investigation
            assert "title" in investigation
            assert "status" in investigation
            assert investigation["status"] in ["pending", "active", "review", "completed"]


class TestDetectiveDashboardSchedule:
    """
    Contract tests for today_schedule in detective dashboard
    """

    def test_schedule_items_should_have_required_fields(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: GET /detective/dashboard
        Then: Each schedule item has time, title
        """
        response = client.get("/detective/dashboard", headers=detective_auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for item in data["today_schedule"]:
            assert "time" in item
            assert "title" in item
