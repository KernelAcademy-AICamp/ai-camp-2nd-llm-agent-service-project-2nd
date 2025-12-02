"""
Tests for evidence utility functions
"""

import pytest
from app.utils.evidence import generate_evidence_id, extract_filename_from_s3_key


class TestGenerateEvidenceId:
    """Tests for generate_evidence_id function"""

    def test_returns_string(self):
        """Should return a string"""
        result = generate_evidence_id()
        assert isinstance(result, str)

    def test_starts_with_ev_prefix(self):
        """Should start with 'ev_' prefix"""
        result = generate_evidence_id()
        assert result.startswith("ev_")

    def test_correct_length(self):
        """Should have correct length (ev_ + 12 hex chars = 15 chars)"""
        result = generate_evidence_id()
        assert len(result) == 15

    def test_unique_ids(self):
        """Should generate unique IDs"""
        ids = [generate_evidence_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_hex_characters_after_prefix(self):
        """Should contain only hex characters after prefix"""
        result = generate_evidence_id()
        hex_part = result[3:]  # Remove 'ev_' prefix
        assert all(c in "0123456789abcdef" for c in hex_part)


class TestExtractFilenameFromS3Key:
    """Tests for extract_filename_from_s3_key function"""

    def test_simple_filename(self):
        """Should extract filename from simple S3 key"""
        s3_key = "cases/case_123/raw/document.pdf"
        result = extract_filename_from_s3_key(s3_key)
        assert result == "document.pdf"

    def test_with_evidence_temp_id_prefix(self):
        """Should remove evidence temp ID prefix"""
        s3_key = "cases/case_123/raw/ev_temp123abc_document.pdf"
        result = extract_filename_from_s3_key(s3_key)
        assert result == "document.pdf"

    def test_filename_with_underscores(self):
        """Should handle filenames with underscores correctly"""
        s3_key = "cases/case_123/raw/ev_temp123abc_my_document_file.pdf"
        result = extract_filename_from_s3_key(s3_key)
        assert result == "my_document_file.pdf"

    def test_filename_without_ev_prefix(self):
        """Should return filename as-is if no ev_ prefix"""
        s3_key = "cases/case_123/raw/regular_file.pdf"
        result = extract_filename_from_s3_key(s3_key)
        assert result == "regular_file.pdf"

    def test_ev_prefix_without_underscore_after(self):
        """Should not strip ev_ if there's no underscore after the ID part"""
        s3_key = "cases/case_123/raw/ev_abc.pdf"
        result = extract_filename_from_s3_key(s3_key)
        # 'ev_abc.pdf' has 'ev_' and no '_' after position 3, so no stripping
        assert result == "ev_abc.pdf"

    def test_deeply_nested_path(self):
        """Should handle deeply nested S3 paths"""
        s3_key = "bucket/prefix/cases/case_123/raw/ev_temp123abc_file.jpg"
        result = extract_filename_from_s3_key(s3_key)
        assert result == "file.jpg"

    def test_filename_with_multiple_extensions(self):
        """Should handle filenames with multiple dots"""
        s3_key = "cases/case_123/raw/ev_temp123abc_archive.tar.gz"
        result = extract_filename_from_s3_key(s3_key)
        assert result == "archive.tar.gz"

    def test_korean_filename(self):
        """Should handle Korean filenames"""
        s3_key = "cases/case_123/raw/ev_temp123abc_증거자료.pdf"
        result = extract_filename_from_s3_key(s3_key)
        assert result == "증거자료.pdf"
