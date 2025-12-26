"""
Smoke tests for RAG Search API
009-mvp-gap-closure: US2 (RAG Search Validation)

These tests validate search endpoint connectivity and basic functionality.
Marked as integration tests to run in CI pipeline.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestSearchSmoke:
    """
    Smoke tests for search endpoints.

    These tests validate:
    - Search endpoint connectivity
    - Basic response structure
    - Authentication requirements
    """

    def test_global_search_endpoint_responds(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Smoke test: Global search endpoint should respond with 200.

        Given: Authenticated user
        When: GET /search?q=test is called
        Then: Returns 200 with valid response structure
        """
        response = client.get("/search?q=test", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert isinstance(data["results"], list)

    def test_search_quick_access_endpoint_responds(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Smoke test: Quick access endpoint should respond with 200.

        Given: Authenticated user
        When: GET /search/quick-access is called
        Then: Returns 200 with valid response structure
        """
        response = client.get("/search/quick-access", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "todays_events" in data
        assert "todays_events_count" in data

    def test_search_recent_endpoint_responds(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Smoke test: Recent searches endpoint should respond with 200.

        Given: Authenticated user
        When: GET /search/recent is called
        Then: Returns 200 with valid response structure
        """
        response = client.get("/search/recent", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "recent_searches" in data
        assert isinstance(data["recent_searches"], list)

    @patch('app.api.search.search_evidence_by_semantic')
    def test_semantic_search_endpoint_responds(
        self,
        mock_qdrant: MagicMock,
        client: TestClient,
        auth_headers: dict,
        test_case
    ):
        """
        Smoke test: Semantic search endpoint should respond with 200.

        Given: Authenticated user with case access
        When: GET /search/semantic?q=test&case_id={id} is called
        Then: Returns 200 with valid response structure

        Note: Mocks Qdrant to avoid external dependency in CI.
        """
        mock_qdrant.return_value = []

        response = client.get(
            f"/search/semantic?q=test&case_id={test_case.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "case_id" in data
        assert "results" in data
        assert "total" in data

    def test_search_requires_authentication(self, client: TestClient):
        """
        Smoke test: All search endpoints should require authentication.

        Given: No authentication
        When: Search endpoints are called
        Then: Returns 401 Unauthorized
        """
        endpoints = [
            "/search?q=test",
            "/search/quick-access",
            "/search/recent",
            "/search/semantic?q=test&case_id=case_123"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Expected 401 for {endpoint}"


@pytest.mark.integration
class TestDraftPreviewSmoke:
    """
    Smoke tests for draft preview endpoint.

    These tests validate draft generation connectivity.
    """

    @patch('app.services.draft_service.get_case_fact_summary')
    @patch('app.services.draft_service.get_evidence_by_case')
    @patch('app.services.draft.rag_orchestrator.search_evidence_by_semantic')
    @patch('app.services.draft.rag_orchestrator.search_legal_knowledge')
    @patch('app.services.draft_service.get_template_by_type')
    @patch('app.services.draft_service.generate_chat_completion')
    def test_draft_preview_endpoint_responds(
        self,
        mock_gpt: MagicMock,
        mock_template: MagicMock,
        mock_legal: MagicMock,
        mock_evidence: MagicMock,
        mock_dynamo: MagicMock,
        mock_fact_summary: MagicMock,
        client: TestClient,
        auth_headers: dict,
        test_case
    ):
        """
        Smoke test: Draft preview endpoint should respond.

        Given: Authenticated user with case access and evidence
        When: POST /cases/{id}/draft-preview is called
        Then: Returns 200 with draft content

        Note: Mocks external services to avoid dependencies in CI.
        """
        # Mock fact summary (required since 016-draft-fact-summary)
        # Note: _get_fact_summary_context expects 'ai_summary' or 'modified_summary' field
        mock_fact_summary.return_value = {
            "case_id": str(test_case.id),
            "ai_summary": "테스트 사실관계 요약입니다.",
            "key_facts": ["사실1", "사실2"],
            "timeline": [],
            "generated_at": "2024-01-15T10:00:00"
        }

        # Mock evidence data
        mock_dynamo.return_value = [
            {
                "evidence_id": "ev_001",
                "status": "done",
                "type": "text",
                "content": "테스트 증거 내용"
            }
        ]
        mock_evidence.return_value = [
            {
                "evidence_id": "ev_001",
                "content": "테스트 증거",
                "_score": 0.9
            }
        ]
        mock_legal.return_value = []
        mock_template.return_value = None  # Use text output mode
        mock_gpt.return_value = "테스트 초안 내용입니다."

        response = client.post(
            f"/cases/{test_case.id}/draft-preview",
            json={"sections": ["청구취지"]},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "draft_text" in data
        assert "citations" in data
        assert "generated_at" in data

    def test_draft_preview_requires_authentication(self, client: TestClient):
        """
        Smoke test: Draft preview should require authentication.

        Given: No authentication
        When: POST /cases/{id}/draft-preview is called
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            "/cases/case_123/draft-preview",
            json={}
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestDraftExportSmoke:
    """
    Smoke tests for draft export endpoint.
    """

    @patch('app.services.draft_service.DraftService.export_draft')
    def test_draft_export_endpoint_responds(
        self,
        mock_export: MagicMock,
        client: TestClient,
        auth_headers: dict,
        test_case
    ):
        """
        Smoke test: Draft export endpoint should respond.

        Given: Authenticated user with case access
        When: GET /cases/{id}/draft-export is called
        Then: Returns file response

        Note: Mocks export service to avoid full generation in CI.
        """
        from io import BytesIO

        # Mock export response
        mock_export.return_value = (
            BytesIO(b"mock docx content"),
            "test_draft.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        response = client.get(
            f"/cases/{test_case.id}/draft-export",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "content-disposition" in response.headers

    def test_draft_export_requires_authentication(self, client: TestClient):
        """
        Smoke test: Draft export should require authentication.

        Given: No authentication
        When: GET /cases/{id}/draft-export is called
        Then: Returns 401 Unauthorized
        """
        response = client.get("/cases/case_123/draft-export")
        assert response.status_code == 401
