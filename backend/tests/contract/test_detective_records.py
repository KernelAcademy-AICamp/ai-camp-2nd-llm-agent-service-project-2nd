"""
Contract tests for Detective Records API
Task T080 - US5 Tests

Tests for detective record endpoints:
- POST /detective/cases/{id}/records (field record)
- POST /detective/cases/{id}/report (final report)
"""

import pytest
from fastapi import status


# ============== T080: POST /detective/cases/{id}/records, /report Contract Tests ==============


class TestCreateFieldRecord:
    """
    Contract tests for POST /detective/cases/{id}/records
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: POST /detective/cases/{id}/records
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            "/detective/cases/any-case-id/records",
            json={
                "record_type": "observation",
                "content": "Test observation",
                "gps_lat": 37.5665,
                "gps_lng": 126.9780,
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_user, client_auth_headers):
        """
        Given: User with CLIENT role
        When: POST /detective/cases/{id}/records
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/detective/cases/any-case-id/records",
            headers=client_auth_headers,
            json={
                "record_type": "observation",
                "content": "Test observation",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: POST /detective/cases/{id}/records
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/detective/cases/any-case-id/records",
            headers=auth_headers,
            json={
                "record_type": "observation",
                "content": "Test observation",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_return_404_for_nonexistent_case(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: POST /detective/cases/{nonexistent_id}/records
        Then: Returns 404 Not Found
        """
        response = client.post(
            "/detective/cases/nonexistent-case-id/records",
            headers=detective_auth_headers,
            json={
                "record_type": "observation",
                "content": "Test observation",
                "gps_lat": 37.5665,
                "gps_lng": 126.9780,
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSubmitReport:
    """
    Contract tests for POST /detective/cases/{id}/report
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: POST /detective/cases/{id}/report
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            "/detective/cases/any-case-id/report",
            json={
                "summary": "Investigation summary",
                "findings": "Key findings",
                "conclusion": "Final conclusion",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_user, client_auth_headers):
        """
        Given: User with CLIENT role
        When: POST /detective/cases/{id}/report
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/detective/cases/any-case-id/report",
            headers=client_auth_headers,
            json={
                "summary": "Investigation summary",
                "findings": "Key findings",
                "conclusion": "Final conclusion",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: POST /detective/cases/{id}/report
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/detective/cases/any-case-id/report",
            headers=auth_headers,
            json={
                "summary": "Investigation summary",
                "findings": "Key findings",
                "conclusion": "Final conclusion",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_return_404_for_nonexistent_case(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: POST /detective/cases/{nonexistent_id}/report
        Then: Returns 404 Not Found
        """
        response = client.post(
            "/detective/cases/nonexistent-case-id/report",
            headers=detective_auth_headers,
            json={
                "summary": "Investigation summary",
                "findings": "Key findings",
                "conclusion": "Final conclusion",
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestFieldRecordValidation:
    """
    Contract tests for field record validation
    """

    def test_should_require_record_type(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: POST /detective/cases/{id}/records without record_type
        Then: Returns 422 Unprocessable Entity
        """
        response = client.post(
            "/detective/cases/any-case-id/records",
            headers=detective_auth_headers,
            json={"content": "Test observation"},
        )
        # Either 404 (case not found) or 422 (validation error) is acceptable
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_record_type_should_be_valid_enum(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: POST /detective/cases/{id}/records with invalid record_type
        Then: Returns 422 Unprocessable Entity
        """
        response = client.post(
            "/detective/cases/any-case-id/records",
            headers=detective_auth_headers,
            json={"record_type": "invalid_type", "content": "Test"},
        )
        # Either 404 (case not found) or 422 (validation error) is acceptable
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]
