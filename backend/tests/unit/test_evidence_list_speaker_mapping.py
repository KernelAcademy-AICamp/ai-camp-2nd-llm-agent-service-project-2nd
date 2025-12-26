"""
Unit tests for has_speaker_mapping field in evidence list
015-evidence-speaker-mapping: T023
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.evidence_service import EvidenceService


class TestEvidenceListHasSpeakerMapping:
    """Unit tests for has_speaker_mapping field in evidence list response"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service_with_mocks(self, mock_db):
        """Create EvidenceService with mocked dependencies"""
        with patch.object(EvidenceService, '__init__', lambda self, db: None):
            service = EvidenceService.__new__(EvidenceService)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.case_repo.get_by_id.return_value = MagicMock(id="case_123")
            service.member_repo = MagicMock()
            service.member_repo.has_access.return_value = True
            service.user_repo = MagicMock()
            service.party_repo = MagicMock()
            return service

    @patch('app.services.evidence_service.get_evidence_by_case')
    def test_evidence_with_speaker_mapping_has_flag_true(
        self, mock_get_evidence, service_with_mocks
    ):
        """Evidence with speaker_mapping should have has_speaker_mapping=True"""
        mock_get_evidence.return_value = [
            {
                "evidence_id": "evt_001",
                "case_id": "case_123",
                "type": "image",
                "filename": "test.jpg",
                "size": 1024,
                "created_at": "2024-01-15T10:00:00",
                "status": "completed",
                "ai_summary": "테스트 요약",
                "speaker_mapping": {
                    "나": {"party_id": "party_001", "party_name": "김동우"}
                }
            }
        ]

        result = service_with_mocks.get_evidence_list("case_123", "user_001")

        assert len(result) == 1
        assert result[0].has_speaker_mapping is True

    @patch('app.services.evidence_service.get_evidence_by_case')
    def test_evidence_without_speaker_mapping_has_flag_false(
        self, mock_get_evidence, service_with_mocks
    ):
        """Evidence without speaker_mapping should have has_speaker_mapping=False"""
        mock_get_evidence.return_value = [
            {
                "evidence_id": "evt_001",
                "case_id": "case_123",
                "type": "image",
                "filename": "test.jpg",
                "size": 1024,
                "created_at": "2024-01-15T10:00:00",
                "status": "completed",
                "ai_summary": "테스트 요약",
                # No speaker_mapping field
            }
        ]

        result = service_with_mocks.get_evidence_list("case_123", "user_001")

        assert len(result) == 1
        assert result[0].has_speaker_mapping is False

    @patch('app.services.evidence_service.get_evidence_by_case')
    def test_evidence_with_empty_speaker_mapping_has_flag_false(
        self, mock_get_evidence, service_with_mocks
    ):
        """Evidence with empty speaker_mapping should have has_speaker_mapping=False"""
        mock_get_evidence.return_value = [
            {
                "evidence_id": "evt_001",
                "case_id": "case_123",
                "type": "image",
                "filename": "test.jpg",
                "size": 1024,
                "created_at": "2024-01-15T10:00:00",
                "status": "completed",
                "speaker_mapping": {}  # Empty mapping
            }
        ]

        result = service_with_mocks.get_evidence_list("case_123", "user_001")

        assert len(result) == 1
        assert result[0].has_speaker_mapping is False

    @patch('app.services.evidence_service.get_evidence_by_case')
    def test_evidence_with_none_speaker_mapping_has_flag_false(
        self, mock_get_evidence, service_with_mocks
    ):
        """Evidence with None speaker_mapping should have has_speaker_mapping=False"""
        mock_get_evidence.return_value = [
            {
                "evidence_id": "evt_001",
                "case_id": "case_123",
                "type": "image",
                "filename": "test.jpg",
                "size": 1024,
                "created_at": "2024-01-15T10:00:00",
                "status": "completed",
                "speaker_mapping": None
            }
        ]

        result = service_with_mocks.get_evidence_list("case_123", "user_001")

        assert len(result) == 1
        assert result[0].has_speaker_mapping is False

    @patch('app.services.evidence_service.get_evidence_by_case')
    def test_mixed_evidence_list(self, mock_get_evidence, service_with_mocks):
        """Mixed evidence list should have correct has_speaker_mapping for each item"""
        mock_get_evidence.return_value = [
            {
                "evidence_id": "evt_001",
                "case_id": "case_123",
                "type": "image",
                "filename": "with_mapping.jpg",
                "size": 1024,
                "created_at": "2024-01-15T10:00:00",
                "status": "completed",
                "speaker_mapping": {
                    "나": {"party_id": "party_001", "party_name": "김동우"}
                }
            },
            {
                "evidence_id": "evt_002",
                "case_id": "case_123",
                "type": "audio",
                "filename": "without_mapping.mp3",
                "size": 2048,
                "created_at": "2024-01-16T10:00:00",
                "status": "completed",
                # No speaker_mapping
            },
            {
                "evidence_id": "evt_003",
                "case_id": "case_123",
                "type": "image",
                "filename": "empty_mapping.jpg",
                "size": 512,
                "created_at": "2024-01-17T10:00:00",
                "status": "completed",
                "speaker_mapping": {}
            },
        ]

        result = service_with_mocks.get_evidence_list("case_123", "user_001")

        assert len(result) == 3

        # First has mapping
        evt_001 = next(e for e in result if e.id == "evt_001")
        assert evt_001.has_speaker_mapping is True

        # Second has no mapping field
        evt_002 = next(e for e in result if e.id == "evt_002")
        assert evt_002.has_speaker_mapping is False

        # Third has empty mapping
        evt_003 = next(e for e in result if e.id == "evt_003")
        assert evt_003.has_speaker_mapping is False
