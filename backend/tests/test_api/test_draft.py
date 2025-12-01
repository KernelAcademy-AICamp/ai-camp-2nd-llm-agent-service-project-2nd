"""
Test suite for Draft Preview API endpoint

Tests for:
- POST /cases/{case_id}/draft-preview - Generate draft preview with RAG

Note: This uses Qdrant (in-memory mode) and OpenAI for RAG search.
"""

from unittest.mock import patch
from fastapi import status


class TestDraftPreview:
    """
    Test suite for POST /cases/{case_id}/draft-preview endpoint
    """

    def test_should_generate_draft_preview_with_rag(self, client, test_user, auth_headers):
        """
        Given: User owns a case with processed evidence
        When: POST /cases/{case_id}/draft-preview is called
        Then:
            - Returns 200 OK
            - Response contains draft_text with generated content
            - Response contains citations referencing evidence
            - Response includes generated_at timestamp
        """
        # Given: Create a case
        case_response = client.post("/cases", json={"title": "Draft 생성 테스트 사건"}, headers=auth_headers)
        case_id = case_response.json()["id"]

        # Mock evidence data
        mock_evidence = [{
            "id": f"ev_test_{case_id}",
            "case_id": case_id,
            "type": "text",
            "filename": "test_evidence.txt",
            "s3_key": f"cases/{case_id}/raw/test_evidence.txt",
            "status": "done",
            "ai_summary": "테스트 증거입니다",
            "labels": ["폭언", "불화"],
            "content": "테스트 증거 내용입니다"
        }]

        # When: POST /cases/{case_id}/draft-preview with mocked DynamoDB and RAG
        with patch("app.services.draft_service.get_evidence_by_case") as mock_get_evidence, \
             patch("app.services.draft_service.search_evidence_by_semantic") as mock_search, \
             patch("app.services.draft_service.generate_chat_completion") as mock_gpt:
            mock_get_evidence.return_value = mock_evidence
            mock_search.return_value = mock_evidence
            mock_gpt.return_value = "테스트 준비서면 초안입니다. [증거 1]을 기반으로 작성되었습니다."

            draft_request = {
                "sections": ["청구취지", "청구원인"],
                "language": "ko",
                "style": "법원 제출용_표준"
            }
            response = client.post(f"/cases/{case_id}/draft-preview", json=draft_request, headers=auth_headers)

        # Then: Returns draft with citations
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "draft_text" in data
        assert "citations" in data
        assert "generated_at" in data
        assert data["case_id"] == case_id

        # Draft text should not be empty
        assert len(data["draft_text"]) > 0

    def test_should_return_400_when_no_evidence(self, client, test_user, auth_headers):
        """
        Given: User owns a case with no evidence
        When: POST /cases/{case_id}/draft-preview is called
        Then:
            - Returns 400 Bad Request
            - Error message indicates evidence is required
        """
        # Given: Create a case with no evidence
        case_response = client.post("/cases", json={"title": "증거 없는 사건"}, headers=auth_headers)
        case_id = case_response.json()["id"]

        # When: POST /cases/{case_id}/draft-preview with empty evidence list
        with patch("app.services.draft_service.get_evidence_by_case") as mock_get_evidence:
            mock_get_evidence.return_value = []  # No evidence

            draft_request = {"sections": ["청구취지"]}
            response = client.post(f"/cases/{case_id}/draft-preview", json=draft_request, headers=auth_headers)

        # Then: Returns 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "증거" in data["error"]["message"]

    def test_should_use_default_sections_when_not_specified(self, client, test_user, auth_headers):
        """
        Given: User owns a case with evidence
        When: POST /cases/{case_id}/draft-preview with no sections specified
        Then:
            - Uses default sections ["청구취지", "청구원인"]
            - Returns 200 OK with draft
        """
        # Given: Create a case with evidence
        case_response = client.post("/cases", json={"title": "기본 섹션 테스트"}, headers=auth_headers)
        case_id = case_response.json()["id"]

        # Mock evidence data
        mock_evidence = [{
            "id": f"ev_default_{case_id}",
            "case_id": case_id,
            "type": "text",
            "filename": "default_test.txt",
            "s3_key": f"cases/{case_id}/raw/default_test.txt",
            "status": "done",
            "content": "기본 섹션 테스트 증거"
        }]

        # When: POST with empty request body with mocked services
        with patch("app.services.draft_service.get_evidence_by_case") as mock_get_evidence, \
             patch("app.services.draft_service.search_evidence_by_semantic") as mock_search, \
             patch("app.services.draft_service.generate_chat_completion") as mock_gpt:
            mock_get_evidence.return_value = mock_evidence
            mock_search.return_value = mock_evidence
            mock_gpt.return_value = "기본 섹션으로 작성된 초안입니다."

            response = client.post(f"/cases/{case_id}/draft-preview", json={}, headers=auth_headers)

        # Then: Success with default sections
        assert response.status_code == status.HTTP_200_OK

    def test_should_return_404_for_nonexistent_case(self, client, auth_headers):
        """
        Given: Case does not exist
        When: POST /cases/{case_id}/draft-preview is called
        Then:
            - Returns 404 Not Found
        """
        # When: POST to non-existent case
        response = client.post("/cases/case_nonexistent/draft-preview", json={}, headers=auth_headers)

        # Then: 404 Not Found
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_should_require_case_access_permission(self, client, test_user, auth_headers):
        """
        Given: User does not have access to a case
        When: POST /cases/{case_id}/draft-preview is called
        Then:
            - Returns 403 Forbidden (or 404 if case doesn't exist)
        """
        # When: POST to non-existent case (no permission)
        response = client.post("/cases/case_other_user/draft-preview", json={}, headers=auth_headers)

        # Then: 404 (case doesn't exist)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_should_require_authentication(self, client):
        """
        Given: No authentication token
        When: POST /cases/{case_id}/draft-preview is called
        Then:
            - Returns 401 Unauthorized
        """
        # When: POST without auth
        response = client.post("/cases/case_123/draft-preview", json={})

        # Then: 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_validate_request_body(self, client, test_user, auth_headers):
        """
        Given: User owns a case
        When: POST with invalid request body (invalid sections type)
        Then:
            - Returns 422 Unprocessable Entity (Pydantic validation error)
        """
        # Given: Create a case
        case_response = client.post("/cases", json={"title": "검증 테스트"}, headers=auth_headers)
        case_id = case_response.json()["id"]

        # When: POST with invalid sections (not a list)
        response = client.post(
            f"/cases/{case_id}/draft-preview",
            json={"sections": "invalid_not_a_list"},
            headers=auth_headers
        )

        # Then: 422 Validation Error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
