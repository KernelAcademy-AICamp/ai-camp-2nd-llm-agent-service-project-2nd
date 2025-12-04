"""
Contract tests for Detective Cases API
Task T078 - US5 Tests

Tests for detective case endpoints:
- GET /detective/cases
- GET /detective/cases/{id}
"""

import pytest
from fastapi import status


# ============== T078: GET /detective/cases Contract Tests ==============


class TestGetDetectiveCases:
    """
    Contract tests for GET /detective/cases
    """

    def test_should_return_case_list_for_detective(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective user
        When: GET /detective/cases
        Then:
            - Returns 200 status code
            - Response contains items array
            - Response contains total count
        """
        # When: GET /detective/cases
        response = client.get("/detective/cases", headers=detective_auth_headers)

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

    def test_should_filter_by_status(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: GET /detective/cases?status=active
        Then: Returns filtered results
        """
        response = client.get(
            "/detective/cases?status=active", headers=detective_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "items" in data

        # If items exist, they should have status=active
        for item in data["items"]:
            assert item["status"] == "active"

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: GET /detective/cases
        Then: Returns 401 Unauthorized
        """
        response = client.get("/detective/cases")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_user, client_auth_headers):
        """
        Given: User with CLIENT role
        When: GET /detective/cases
        Then: Returns 403 Forbidden
        """
        response = client.get("/detective/cases", headers=client_auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: GET /detective/cases
        Then: Returns 403 Forbidden
        """
        response = client.get("/detective/cases", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetDetectiveCaseDetail:
    """
    Contract tests for GET /detective/cases/{id}
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: GET /detective/cases/{id}
        Then: Returns 401 Unauthorized
        """
        response = client.get("/detective/cases/some-case-id")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_user, client_auth_headers):
        """
        Given: User with CLIENT role
        When: GET /detective/cases/{id}
        Then: Returns 403 Forbidden
        """
        response = client.get(
            "/detective/cases/some-case-id", headers=client_auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_return_404_for_nonexistent_case(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: GET /detective/cases/{nonexistent_id}
        Then: Returns 404 Not Found
        """
        response = client.get(
            "/detective/cases/nonexistent-case-id", headers=detective_auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDetectiveCaseListItems:
    """
    Contract tests for case list item structure
    """

    def test_case_items_should_have_required_fields(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: GET /detective/cases
        Then: Each case item has id, title, status, lawyer_name
        """
        response = client.get("/detective/cases", headers=detective_auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for item in data["items"]:
            assert "id" in item
            assert "title" in item
            assert "status" in item
            assert item["status"] in ["pending", "active", "review", "completed"]
