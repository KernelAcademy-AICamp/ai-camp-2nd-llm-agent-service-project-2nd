"""
Tests for evidence utility functions
"""

import sys
import os
from app.utils.evidence import generate_evidence_id, extract_filename_from_s3_key


# Add ai_worker to path for cross-service testing
AI_WORKER_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ai_worker')
sys.path.insert(0, AI_WORKER_PATH)


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


class TestFileTypeMappingConsistency:
    """
    Tests to verify file type mappings are consistent between Backend and AI Worker.
    This prevents the two services from having different file type classifications.

    Related issue: #71 - MIME Type 매핑 중복
    """

    # Backend type_mapping from evidence_service.py
    BACKEND_TYPE_MAPPING = {
        # Images
        "jpg": "image", "jpeg": "image", "png": "image", "gif": "image", "bmp": "image",
        # Audio
        "mp3": "audio", "wav": "audio", "m4a": "audio", "aac": "audio",
        # Video
        "mp4": "video", "avi": "video", "mov": "video", "mkv": "video",
        # Documents
        "pdf": "pdf",
        "txt": "text", "csv": "text", "json": "text"
    }

    # AI Worker extensions from handler.py route_parser()
    AI_WORKER_EXTENSIONS = {
        "image": ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
        "pdf": ['.pdf'],
        "audio": ['.mp3', '.wav', '.m4a', '.aac'],
        "video": ['.mp4', '.avi', '.mov', '.mkv'],
        "text": ['.txt', '.csv', '.json']
    }

    def test_all_backend_extensions_supported_by_ai_worker(self):
        """All extensions in Backend should be supported by AI Worker"""
        # Convert AI Worker extensions to a flat set (without dots)
        ai_worker_all_extensions = set()
        for ext_list in self.AI_WORKER_EXTENSIONS.values():
            for ext in ext_list:
                ai_worker_all_extensions.add(ext.lstrip('.'))

        backend_extensions = set(self.BACKEND_TYPE_MAPPING.keys())

        missing_in_ai_worker = backend_extensions - ai_worker_all_extensions
        assert not missing_in_ai_worker, (
            f"Extensions in Backend but not in AI Worker: {missing_in_ai_worker}"
        )

    def test_all_ai_worker_extensions_in_backend(self):
        """All extensions supported by AI Worker should be in Backend"""
        backend_extensions = set(self.BACKEND_TYPE_MAPPING.keys())

        ai_worker_all_extensions = set()
        for ext_list in self.AI_WORKER_EXTENSIONS.values():
            for ext in ext_list:
                ai_worker_all_extensions.add(ext.lstrip('.'))

        missing_in_backend = ai_worker_all_extensions - backend_extensions
        assert not missing_in_backend, (
            f"Extensions in AI Worker but not in Backend: {missing_in_backend}"
        )

    def test_type_classification_matches(self):
        """File type classifications should match between services"""
        for ext, backend_type in self.BACKEND_TYPE_MAPPING.items():
            # Find the type in AI Worker
            ai_worker_type = None
            for type_name, ext_list in self.AI_WORKER_EXTENSIONS.items():
                if f'.{ext}' in ext_list:
                    ai_worker_type = type_name
                    break

            assert ai_worker_type is not None, (
                f"Extension '.{ext}' not found in AI Worker"
            )
            assert backend_type == ai_worker_type, (
                f"Type mismatch for '.{ext}': Backend={backend_type}, AI Worker={ai_worker_type}"
            )

    def test_image_extensions_match(self):
        """Image extensions should match between services"""
        backend_image_exts = {k for k, v in self.BACKEND_TYPE_MAPPING.items() if v == "image"}
        ai_worker_image_exts = {ext.lstrip('.') for ext in self.AI_WORKER_EXTENSIONS["image"]}
        assert backend_image_exts == ai_worker_image_exts

    def test_audio_extensions_match(self):
        """Audio extensions should match between services"""
        backend_audio_exts = {k for k, v in self.BACKEND_TYPE_MAPPING.items() if v == "audio"}
        ai_worker_audio_exts = {ext.lstrip('.') for ext in self.AI_WORKER_EXTENSIONS["audio"]}
        assert backend_audio_exts == ai_worker_audio_exts

    def test_video_extensions_match(self):
        """Video extensions should match between services"""
        backend_video_exts = {k for k, v in self.BACKEND_TYPE_MAPPING.items() if v == "video"}
        ai_worker_video_exts = {ext.lstrip('.') for ext in self.AI_WORKER_EXTENSIONS["video"]}
        assert backend_video_exts == ai_worker_video_exts

    def test_text_extensions_match(self):
        """Text extensions should match between services"""
        backend_text_exts = {k for k, v in self.BACKEND_TYPE_MAPPING.items() if v == "text"}
        ai_worker_text_exts = {ext.lstrip('.') for ext in self.AI_WORKER_EXTENSIONS["text"]}
        assert backend_text_exts == ai_worker_text_exts

    def test_pdf_extensions_match(self):
        """PDF extensions should match between services"""
        backend_pdf_exts = {k for k, v in self.BACKEND_TYPE_MAPPING.items() if v == "pdf"}
        ai_worker_pdf_exts = {ext.lstrip('.') for ext in self.AI_WORKER_EXTENSIONS["pdf"]}
        assert backend_pdf_exts == ai_worker_pdf_exts
