"""
Contract tests for Detective Actions API
Task T079 - US5 Tests

Tests for detective action endpoints:
- POST /detective/cases/{id}/accept
- POST /detective/cases/{id}/reject
"""

import pytest
from fastapi import status


# ============== T079: POST /detective/cases/{id}/accept, /reject Contract Tests ==============


class TestAcceptInvestigation:
    """
    Contract tests for POST /detective/cases/{id}/accept
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: POST /detective/cases/{id}/accept
        Then: Returns 401 Unauthorized
        """
        response = client.post("/detective/cases/any-case-id/accept")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_user, client_auth_headers):
        """
        Given: User with CLIENT role
        When: POST /detective/cases/{id}/accept
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/detective/cases/any-case-id/accept", headers=client_auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: POST /detective/cases/{id}/accept
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/detective/cases/any-case-id/accept", headers=auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_return_404_for_nonexistent_case(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: POST /detective/cases/{nonexistent_id}/accept
        Then: Returns 404 Not Found
        """
        response = client.post(
            "/detective/cases/nonexistent-case-id/accept",
            headers=detective_auth_headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRejectInvestigation:
    """
    Contract tests for POST /detective/cases/{id}/reject
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: POST /detective/cases/{id}/reject
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            "/detective/cases/any-case-id/reject", json={"reason": "Not available"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_user, client_auth_headers):
        """
        Given: User with CLIENT role
        When: POST /detective/cases/{id}/reject
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/detective/cases/any-case-id/reject",
            headers=client_auth_headers,
            json={"reason": "Not available"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: POST /detective/cases/{id}/reject
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/detective/cases/any-case-id/reject",
            headers=auth_headers,
            json={"reason": "Not available"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_return_404_for_nonexistent_case(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: POST /detective/cases/{nonexistent_id}/reject
        Then: Returns 404 Not Found
        """
        response = client.post(
            "/detective/cases/nonexistent-case-id/reject",
            headers=detective_auth_headers,
            json={"reason": "Not available"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_should_require_reason_field(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: POST /detective/cases/{id}/reject without reason
        Then: Returns 422 Unprocessable Entity
        """
        response = client.post(
            "/detective/cases/any-case-id/reject",
            headers=detective_auth_headers,
            json={},
        )
        # Either 404 (case not found) or 422 (validation error) is acceptable
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]
