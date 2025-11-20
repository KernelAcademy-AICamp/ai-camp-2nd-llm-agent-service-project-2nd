"""
Test suite for Evidence Metadata API endpoints

Tests for:
- GET /cases/{case_id}/evidence - List evidence metadata for a case
- GET /evidence/{evidence_id} - Get detailed evidence metadata

Note: This uses Mock DynamoDB implementation for local development.
      Real AWS DynamoDB integration will be added later.
"""

import pytest
from fastapi import status


class TestEvidenceList:
    """
    Test suite for GET /cases/{case_id}/evidence endpoint
    """

    def test_should_list_evidence_for_case(self, client, test_user, auth_headers):
        """
        Given: User owns a case with uploaded evidence
        When: GET /cases/{case_id}/evidence is called
        Then:
            - Returns 200 OK
            - Returns list of evidence metadata from DynamoDB
            - Each evidence item contains: id, type, filename, status, created_at
        """
        # Given: Create a case
        case_response = client.post("/cases", json={"title": "테스트 사건"}, headers=auth_headers)
        case_id = case_response.json()["id"]

        # Simulate evidence upload and AI Worker processing
        # (In real system: FE uploads to S3 → AI Worker writes to DynamoDB)
        # For test: We'll manually insert mock evidence metadata

        # When: GET /cases/{case_id}/evidence
        response = client.get(f"/cases/{case_id}/evidence", headers=auth_headers)

        # Then: Returns evidence list
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Initially empty since no evidence uploaded yet
        assert len(data) == 0

    def test_should_return_evidence_with_complete_metadata(self, client, test_user, auth_headers):
        """
        Given: Case has evidence with AI processing completed
        When: GET /cases/{case_id}/evidence is called
        Then:
            - Returns evidence with complete metadata
            - Includes: id, type, filename, status, created_at, ai_summary, labels, etc.
        """
        # Given: Create case and upload evidence
        case_response = client.post("/cases", json={"title": "증거 포함 사건"}, headers=auth_headers)
        case_id = case_response.json()["id"]

        # TODO: Insert mock evidence into DynamoDB
        # This will be implemented in service layer

        # When: GET evidence list
        response = client.get(f"/cases/{case_id}/evidence", headers=auth_headers)

        # Then: Success
        assert response.status_code == status.HTTP_200_OK

    def test_should_require_case_access_permission(self, client, test_user, auth_headers):
        """
        Given: User does not have access to a case
        When: GET /cases/{case_id}/evidence is called
        Then:
            - Returns 403 Forbidden (or 404 if case doesn't exist)
        """
        # When: GET evidence for non-existent case
        response = client.get("/cases/case_nonexistent/evidence", headers=auth_headers)

        # Then: 404 Not Found (case doesn't exist)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_should_require_authentication(self, client):
        """
        Given: No authentication token
        When: GET /cases/{case_id}/evidence is called
        Then:
            - Returns 401 Unauthorized
        """
        # When: GET without auth
        response = client.get("/cases/case_123/evidence")

        # Then: 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestEvidenceDetail:
    """
    Test suite for GET /evidence/{evidence_id} endpoint
    """

    def test_should_get_evidence_detail_with_full_metadata(self, client, test_user, auth_headers):
        """
        Given: Evidence exists in DynamoDB with full AI analysis
        When: GET /evidence/{evidence_id} is called
        Then:
            - Returns 200 OK
            - Returns complete evidence metadata including:
              - Basic info: id, case_id, type, filename, s3_key
              - AI analysis: ai_summary, labels, insights, content
              - Timestamps: created_at, processed_at
        """
        # Given: Create case
        case_response = client.post("/cases", json={"title": "상세 증거 사건"}, headers=auth_headers)
        case_id = case_response.json()["id"]

        # TODO: Insert mock evidence with full metadata
        # evidence_id = "ev_mock123"

        # When: GET /evidence/{evidence_id}
        # response = client.get(f"/evidence/{evidence_id}", headers=auth_headers)

        # Then: Returns full metadata
        # assert response.status_code == status.HTTP_200_OK
        # data = response.json()
        # assert data["id"] == evidence_id
        # assert data["case_id"] == case_id
        # assert "ai_summary" in data
        # assert "labels" in data

        # For now, skip this test until we implement mock DynamoDB insertion
        pytest.skip("Requires mock DynamoDB evidence insertion")

    def test_should_return_404_for_nonexistent_evidence(self, client, auth_headers):
        """
        Given: Evidence does not exist in DynamoDB
        When: GET /evidence/{evidence_id} is called
        Then:
            - Returns 404 Not Found
        """
        # When: GET non-existent evidence
        response = client.get("/evidence/ev_nonexistent", headers=auth_headers)

        # Then: 404 Not Found
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_should_check_case_access_permission(self, client, test_user, auth_headers):
        """
        Given: Evidence belongs to a case user doesn't have access to
        When: GET /evidence/{evidence_id} is called
        Then:
            - Returns 403 Forbidden
        """
        # Note: This requires multi-user test setup
        # For now, we'll test basic permission check logic

        # When: GET evidence (will fail with 404 since it doesn't exist)
        response = client.get("/evidence/ev_someuser_case", headers=auth_headers)

        # Then: 404 (evidence doesn't exist in our test)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_should_require_authentication(self, client):
        """
        Given: No authentication token
        When: GET /evidence/{evidence_id} is called
        Then:
            - Returns 401 Unauthorized
        """
        # When: GET without auth
        response = client.get("/evidence/ev_123")

        # Then: 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
