"""
Integration tests for AWS services (S3, DynamoDB)
Requires: AWS credentials configured (~/.aws/credentials)
"""

import pytest
import uuid
from datetime import datetime
from app.utils.s3 import generate_presigned_upload_url
from app.utils.dynamo import (
    put_evidence_metadata,
    get_evidence_by_id,
    get_evidence_by_case,
    delete_evidence_metadata
)
from app.core.config import settings


class TestS3Integration:
    """Integration tests for S3 operations"""

    @pytest.mark.integration
    @pytest.mark.requires_aws
    def test_generate_presigned_url_success(self):
        """Test generating S3 presigned upload URL"""
        bucket = settings.S3_EVIDENCE_BUCKET
        key = f"test/integration_test_{uuid.uuid4().hex[:8]}.txt"

        result = generate_presigned_upload_url(
            bucket=bucket,
            key=key,
            content_type="text/plain",
            expires_in=300
        )

        assert "upload_url" in result
        assert "fields" in result
        assert result["upload_url"].startswith("https://")
        assert settings.S3_EVIDENCE_BUCKET in result["upload_url"]

    @pytest.mark.integration
    @pytest.mark.requires_aws
    def test_generate_presigned_url_with_different_content_types(self):
        """Test presigned URL generation for different content types"""
        bucket = settings.S3_EVIDENCE_BUCKET

        content_types = [
            ("image/jpeg", "test.jpg"),
            ("audio/mpeg", "test.mp3"),
            ("application/pdf", "test.pdf"),
            ("video/mp4", "test.mp4")
        ]

        for content_type, filename in content_types:
            key = f"test/integration_{filename}"
            result = generate_presigned_upload_url(
                bucket=bucket,
                key=key,
                content_type=content_type,
                expires_in=60
            )

            assert "upload_url" in result
            assert "fields" in result


class TestDynamoDBIntegration:
    """Integration tests for DynamoDB operations"""

    @pytest.fixture
    def test_evidence_id(self):
        """Generate unique evidence ID for testing"""
        return f"ev_test_{uuid.uuid4().hex[:12]}"

    @pytest.fixture
    def test_case_id(self):
        """Generate unique case ID for testing"""
        return f"case_test_{uuid.uuid4().hex[:12]}"

    @pytest.fixture(autouse=True)
    def cleanup_evidence(self, test_evidence_id):
        """Cleanup evidence after each test"""
        yield
        # Try to delete test evidence
        try:
            delete_evidence_metadata(test_evidence_id)
        except Exception:
            pass

    @pytest.mark.integration
    @pytest.mark.requires_aws
    def test_put_and_get_evidence_metadata(self, test_evidence_id, test_case_id):
        """Test creating and retrieving evidence metadata"""
        evidence = {
            "id": test_evidence_id,
            "case_id": test_case_id,
            "type": "audio",
            "filename": "test_recording.mp3",
            "s3_key": f"cases/{test_case_id}/raw/test.mp3",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "user_test_123"
        }

        # Put evidence
        put_evidence_metadata(evidence)

        # Get evidence
        result = get_evidence_by_id(test_evidence_id)

        assert result is not None
        assert result["id"] == test_evidence_id
        assert result["case_id"] == test_case_id
        assert result["type"] == "audio"
        assert result["status"] == "pending"

    @pytest.mark.integration
    @pytest.mark.requires_aws
    def test_get_evidence_by_case(self, test_case_id):
        """Test retrieving all evidence for a case"""
        # Create multiple evidence items
        evidence_ids = []
        for i in range(3):
            ev_id = f"ev_test_{uuid.uuid4().hex[:12]}"
            evidence_ids.append(ev_id)

            evidence = {
                "id": ev_id,
                "case_id": test_case_id,
                "type": "image",
                "filename": f"test_{i}.jpg",
                "s3_key": f"cases/{test_case_id}/raw/test_{i}.jpg",
                "status": "done",
                "created_at": datetime.utcnow().isoformat()
            }
            put_evidence_metadata(evidence)

        # Get all evidence for case
        results = get_evidence_by_case(test_case_id)

        assert len(results) >= 3
        result_ids = [r["id"] for r in results]
        for ev_id in evidence_ids:
            assert ev_id in result_ids

        # Cleanup
        for ev_id in evidence_ids:
            try:
                delete_evidence_metadata(ev_id)
            except Exception:
                pass

    @pytest.mark.integration
    @pytest.mark.requires_aws
    def test_get_nonexistent_evidence(self):
        """Test retrieving non-existent evidence returns None"""
        result = get_evidence_by_id("ev_nonexistent_xyz123")

        assert result is None

    @pytest.mark.integration
    @pytest.mark.requires_aws
    def test_update_evidence_metadata(self, test_evidence_id, test_case_id):
        """Test updating evidence metadata"""
        # Create initial evidence
        evidence = {
            "id": test_evidence_id,
            "case_id": test_case_id,
            "type": "audio",
            "filename": "test.mp3",
            "s3_key": f"cases/{test_case_id}/raw/test.mp3",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        put_evidence_metadata(evidence)

        # Update with AI analysis results
        evidence["status"] = "done"
        evidence["ai_summary"] = "배우자의 폭언이 담긴 녹음 파일입니다."
        evidence["labels"] = ["폭언", "욕설"]
        evidence["content"] = "녹취 텍스트 내용..."
        put_evidence_metadata(evidence)

        # Verify update
        result = get_evidence_by_id(test_evidence_id)

        assert result["status"] == "done"
        assert result["ai_summary"] == "배우자의 폭언이 담긴 녹음 파일입니다."
        assert "폭언" in result["labels"]

    @pytest.mark.integration
    @pytest.mark.requires_aws
    def test_evidence_with_article_840_tags(self, test_evidence_id, test_case_id):
        """Test evidence with Article 840 tagging"""
        evidence = {
            "id": test_evidence_id,
            "case_id": test_case_id,
            "type": "audio",
            "filename": "recording.mp3",
            "s3_key": f"cases/{test_case_id}/raw/recording.mp3",
            "status": "done",
            "created_at": datetime.utcnow().isoformat(),
            "article_840_tags": {
                "categories": ["adultery", "irreconcilable_differences"],
                "confidence": 0.85,
                "matched_keywords": ["부정행위", "외도", "혼인 파탄"]
            }
        }
        put_evidence_metadata(evidence)

        result = get_evidence_by_id(test_evidence_id)

        assert result["article_840_tags"] is not None
        assert "adultery" in result["article_840_tags"]["categories"]
        assert result["article_840_tags"]["confidence"] == 0.85

    @pytest.mark.integration
    @pytest.mark.requires_aws
    def test_delete_evidence_metadata(self, test_case_id):
        """Test deleting evidence metadata"""
        ev_id = f"ev_delete_test_{uuid.uuid4().hex[:8]}"

        evidence = {
            "id": ev_id,
            "case_id": test_case_id,
            "type": "document",
            "filename": "delete_test.pdf",
            "s3_key": f"cases/{test_case_id}/raw/delete_test.pdf",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        put_evidence_metadata(evidence)

        # Verify it exists
        assert get_evidence_by_id(ev_id) is not None

        # Delete
        delete_evidence_metadata(ev_id)

        # Verify it's gone
        assert get_evidence_by_id(ev_id) is None
