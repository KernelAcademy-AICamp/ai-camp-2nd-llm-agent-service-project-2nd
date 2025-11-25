"""
Tests for Article 840 Tag Integration (1.9)

Tests the following endpoints:
- GET /evidence/{evidence_id} - with article_840_tags field
- GET /cases/{case_id}/evidence - with categories filter
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.db.schemas import Article840Category


class TestArticle840Tags:
    """Test suite for Article 840 tag integration"""

    @pytest.fixture
    def sample_evidence_with_tags(self):
        """Sample evidence data with Article 840 tags from DynamoDB"""
        return {
            "id": "ev_test123",
            "case_id": "case_abc",
            "type": "text",
            "filename": "kakao_chat.txt",
            "s3_key": "cases/case_abc/raw/ev_test123_kakao_chat.txt",
            "content_type": "text/plain",
            "created_at": "2024-12-25T10:00:00+00:00",
            "status": "done",
            "ai_summary": "배우자의 외도 증거 - 제3자와의 부적절한 대화",
            "labels": ["adultery"],
            "insights": ["외도 의심 정황", "명확한 불륜 증거"],
            "content": "카카오톡 대화 내용...",
            "timestamp": "2024-12-20T15:30:00+00:00",
            "article_840_tags": {
                "categories": ["adultery", "irreconcilable_differences"],
                "confidence": 0.95,
                "matched_keywords": ["외도", "불륜", "제3자"]
            }
        }

    @pytest.fixture
    def sample_evidence_without_tags(self):
        """Sample evidence data without Article 840 tags (pending processing)"""
        return {
            "id": "ev_pending456",
            "case_id": "case_abc",
            "type": "image",
            "filename": "photo.jpg",
            "s3_key": "cases/case_abc/raw/ev_pending456_photo.jpg",
            "content_type": "image/jpeg",
            "created_at": "2024-12-25T11:00:00+00:00",
            "status": "pending",
        }

    @pytest.fixture
    def mock_case_member_access(self):
        """Mock case member access check"""
        with patch("app.services.evidence_service.CaseMemberRepository") as mock_repo:
            mock_instance = Mock()
            mock_instance.has_access.return_value = True
            mock_repo.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_case_exists(self):
        """Mock case existence check"""
        with patch("app.services.evidence_service.CaseRepository") as mock_repo:
            mock_instance = Mock()
            mock_case = Mock()
            mock_case.id = "case_abc"
            mock_case.title = "Test Case"
            mock_instance.get_by_id.return_value = mock_case
            mock_repo.return_value = mock_instance
            yield mock_instance

    def test_get_evidence_detail_with_article_840_tags(
        self,
        client,
        auth_headers,
        sample_evidence_with_tags,
        mock_case_member_access,
    ):
        """
        Test GET /evidence/{evidence_id} returns article_840_tags field

        Given: Evidence with Article 840 tags in DynamoDB
        When: GET /evidence/{evidence_id}
        Then: Response includes article_840_tags with categories, confidence, matched_keywords
        """
        evidence_id = sample_evidence_with_tags["id"]

        # Mock DynamoDB get_evidence_by_id
        with patch("app.utils.dynamo.get_evidence_by_id") as mock_get_evidence:
            mock_get_evidence.return_value = sample_evidence_with_tags

            # Call API
            response = client.get(
                f"/evidence/{evidence_id}",
                headers=auth_headers
            )

        # Assert response
        assert response.status_code == 200
        data = response.json()

        # Check article_840_tags field
        assert "article_840_tags" in data
        assert data["article_840_tags"] is not None

        tags = data["article_840_tags"]
        assert "categories" in tags
        assert "confidence" in tags
        assert "matched_keywords" in tags

        # Check categories
        assert len(tags["categories"]) == 2
        assert "adultery" in tags["categories"]
        assert "irreconcilable_differences" in tags["categories"]

        # Check confidence
        assert tags["confidence"] == 0.95

        # Check matched keywords
        assert len(tags["matched_keywords"]) == 3
        assert "외도" in tags["matched_keywords"]

        # Check labels field is mapped from categories
        assert "labels" in data
        assert "adultery" in data["labels"]

    def test_get_evidence_detail_without_article_840_tags(
        self,
        client,
        auth_headers,
        sample_evidence_without_tags,
        mock_case_member_access,
    ):
        """
        Test GET /evidence/{evidence_id} handles evidence without tags gracefully

        Given: Evidence without Article 840 tags (status=pending)
        When: GET /evidence/{evidence_id}
        Then: Response includes article_840_tags as null
        """
        evidence_id = sample_evidence_without_tags["id"]

        # Mock DynamoDB get_evidence_by_id
        with patch("app.utils.dynamo.get_evidence_by_id") as mock_get_evidence:
            mock_get_evidence.return_value = sample_evidence_without_tags

            # Call API
            response = client.get(
                f"/evidence/{evidence_id}",
                headers=auth_headers
            )

        # Assert response
        assert response.status_code == 200
        data = response.json()

        # Check article_840_tags field is present but null
        assert "article_840_tags" in data
        assert data["article_840_tags"] is None

    def test_list_case_evidence_includes_article_840_tags(
        self,
        client,
        auth_headers,
        sample_evidence_with_tags,
        sample_evidence_without_tags,
        mock_case_exists,
        mock_case_member_access,
    ):
        """
        Test GET /cases/{case_id}/evidence returns article_840_tags for each item

        Given: Multiple evidence items with/without tags
        When: GET /cases/{case_id}/evidence
        Then: Each item includes article_840_tags field
        """
        case_id = "case_abc"

        # Mock DynamoDB get_evidence_by_case
        with patch("app.utils.dynamo.get_evidence_by_case") as mock_get_evidence:
            mock_get_evidence.return_value = [
                sample_evidence_with_tags,
                sample_evidence_without_tags
            ]

            # Call API
            response = client.get(
                f"/cases/{case_id}/evidence",
                headers=auth_headers
            )

        # Assert response
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2

        # First evidence has tags
        assert data[0]["article_840_tags"] is not None
        assert len(data[0]["article_840_tags"]["categories"]) == 2

        # Second evidence has no tags
        assert data[1]["article_840_tags"] is None

    def test_filter_evidence_by_single_category(
        self,
        client,
        auth_headers,
        mock_case_exists,
        mock_case_member_access,
    ):
        """
        Test GET /cases/{case_id}/evidence?categories=adultery filters correctly

        Given: Evidence with various Article 840 categories
        When: GET /cases/{case_id}/evidence?categories=adultery
        Then: Only returns evidence tagged with "adultery"
        """
        case_id = "case_abc"

        # Create evidence with different categories
        evidence_list = [
            {
                "id": "ev_001",
                "case_id": case_id,
                "type": "text",
                "filename": "chat1.txt",
                "created_at": "2024-12-25T10:00:00+00:00",
                "status": "done",
                "article_840_tags": {
                    "categories": ["adultery"],
                    "confidence": 0.9,
                    "matched_keywords": ["외도"]
                }
            },
            {
                "id": "ev_002",
                "case_id": case_id,
                "type": "text",
                "filename": "chat2.txt",
                "created_at": "2024-12-25T11:00:00+00:00",
                "status": "done",
                "article_840_tags": {
                    "categories": ["desertion"],
                    "confidence": 0.85,
                    "matched_keywords": ["유기"]
                }
            },
            {
                "id": "ev_003",
                "case_id": case_id,
                "type": "text",
                "filename": "chat3.txt",
                "created_at": "2024-12-25T12:00:00+00:00",
                "status": "done",
                "article_840_tags": {
                    "categories": ["adultery", "irreconcilable_differences"],
                    "confidence": 0.95,
                    "matched_keywords": ["외도", "불화"]
                }
            }
        ]

        # Mock DynamoDB get_evidence_by_case
        with patch("app.utils.dynamo.get_evidence_by_case") as mock_get_evidence:
            mock_get_evidence.return_value = evidence_list

            # Call API with categories filter
            response = client.get(
                f"/cases/{case_id}/evidence?categories=adultery",
                headers=auth_headers
            )

        # Assert response
        assert response.status_code == 200
        data = response.json()

        # Should return only ev_001 and ev_003 (both have "adultery")
        assert len(data) == 2
        assert data[0]["id"] == "ev_001"
        assert data[1]["id"] == "ev_003"

    def test_filter_evidence_by_multiple_categories(
        self,
        client,
        auth_headers,
        mock_case_exists,
        mock_case_member_access,
    ):
        """
        Test GET /cases/{case_id}/evidence with multiple categories filter

        Given: Evidence with various Article 840 categories
        When: GET /cases/{case_id}/evidence?categories=adultery&categories=desertion
        Then: Returns evidence tagged with either "adultery" OR "desertion"
        """
        case_id = "case_abc"

        # Create evidence with different categories
        evidence_list = [
            {
                "id": "ev_001",
                "case_id": case_id,
                "type": "text",
                "filename": "chat1.txt",
                "created_at": "2024-12-25T10:00:00+00:00",
                "status": "done",
                "article_840_tags": {
                    "categories": ["adultery"],
                    "confidence": 0.9,
                    "matched_keywords": ["외도"]
                }
            },
            {
                "id": "ev_002",
                "case_id": case_id,
                "type": "text",
                "filename": "chat2.txt",
                "created_at": "2024-12-25T11:00:00+00:00",
                "status": "done",
                "article_840_tags": {
                    "categories": ["desertion"],
                    "confidence": 0.85,
                    "matched_keywords": ["유기"]
                }
            },
            {
                "id": "ev_003",
                "case_id": case_id,
                "type": "text",
                "filename": "chat3.txt",
                "created_at": "2024-12-25T12:00:00+00:00",
                "status": "done",
                "article_840_tags": {
                    "categories": ["mistreatment_by_inlaws"],
                    "confidence": 0.8,
                    "matched_keywords": ["시댁"]
                }
            }
        ]

        # Mock DynamoDB get_evidence_by_case
        with patch("app.utils.dynamo.get_evidence_by_case") as mock_get_evidence:
            mock_get_evidence.return_value = evidence_list

            # Call API with multiple categories filter
            response = client.get(
                f"/cases/{case_id}/evidence?categories=adultery&categories=desertion",
                headers=auth_headers
            )

        # Assert response
        assert response.status_code == 200
        data = response.json()

        # Should return ev_001 (adultery) and ev_002 (desertion)
        assert len(data) == 2
        assert data[0]["id"] == "ev_001"
        assert data[1]["id"] == "ev_002"

    def test_filter_evidence_excludes_untagged_items(
        self,
        client,
        auth_headers,
        mock_case_exists,
        mock_case_member_access,
    ):
        """
        Test categories filter excludes evidence without tags

        Given: Mix of evidence with and without Article 840 tags
        When: GET /cases/{case_id}/evidence?categories=adultery
        Then: Only returns evidence with tags (excludes pending/no-tags items)
        """
        case_id = "case_abc"

        # Create evidence with and without tags
        evidence_list = [
            {
                "id": "ev_001",
                "case_id": case_id,
                "type": "text",
                "filename": "chat1.txt",
                "created_at": "2024-12-25T10:00:00+00:00",
                "status": "done",
                "article_840_tags": {
                    "categories": ["adultery"],
                    "confidence": 0.9,
                    "matched_keywords": ["외도"]
                }
            },
            {
                "id": "ev_002",
                "case_id": case_id,
                "type": "image",
                "filename": "photo.jpg",
                "created_at": "2024-12-25T11:00:00+00:00",
                "status": "pending",
                # No article_840_tags
            }
        ]

        # Mock DynamoDB get_evidence_by_case
        with patch("app.utils.dynamo.get_evidence_by_case") as mock_get_evidence:
            mock_get_evidence.return_value = evidence_list

            # Call API with categories filter
            response = client.get(
                f"/cases/{case_id}/evidence?categories=adultery",
                headers=auth_headers
            )

        # Assert response
        assert response.status_code == 200
        data = response.json()

        # Should return only ev_001 (has tags), exclude ev_002 (no tags)
        assert len(data) == 1
        assert data[0]["id"] == "ev_001"

    def test_article_840_category_enum_values(self):
        """
        Test Article840Category enum has all 7 required categories

        Given: Article840Category enum
        When: Check enum values
        Then: Contains all 7 민법 840조 categories
        """
        expected_categories = [
            "adultery",
            "desertion",
            "mistreatment_by_inlaws",
            "harm_to_own_parents",
            "unknown_whereabouts",
            "irreconcilable_differences",
            "general"
        ]

        # Get all enum values
        actual_categories = [cat.value for cat in Article840Category]

        # Assert all expected categories are present
        for expected in expected_categories:
            assert expected in actual_categories

        # Assert exactly 7 categories
        assert len(actual_categories) == 7
