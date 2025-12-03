"""
Test suite for StandardMetadata
Following TDD approach: RED-GREEN-REFACTOR

Issue #12: Parser 메타데이터 구조 표준화
- StandardMetadata 스키마 정의
- 각 파서에서 표준 메타데이터 포함
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from pathlib import Path

# Check for optional dependencies
try:
    import ffmpeg
    HAS_FFMPEG = True
except ImportError:
    HAS_FFMPEG = False

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


class TestStandardMetadataSchema:
    """StandardMetadata 스키마 정의 테스트"""

    def test_standard_metadata_exists(self):
        """
        Given: StandardMetadata 클래스가 정의됨
        When: base 모듈에서 import
        Then: StandardMetadata 클래스를 사용할 수 있음
        """
        from src.parsers.base import StandardMetadata

        assert StandardMetadata is not None

    def test_standard_metadata_has_required_fields(self):
        """
        Given: StandardMetadata 인스턴스
        When: 필수 필드 확인
        Then: source_type, filename, filepath, parser_class, parsed_at 필드 존재
        """
        from src.parsers.base import StandardMetadata

        metadata = StandardMetadata(
            source_type="pdf",
            filename="test.pdf",
            filepath="/tmp/test.pdf",
            parser_class="PDFParser",
            parsed_at="2024-01-01T12:00:00"
        )

        assert metadata["source_type"] == "pdf"
        assert metadata["filename"] == "test.pdf"
        assert metadata["filepath"] == "/tmp/test.pdf"
        assert metadata["parser_class"] == "PDFParser"
        assert metadata["parsed_at"] == "2024-01-01T12:00:00"


class TestPDFParserMetadata:
    """PDFParser 메타데이터 테스트"""

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_pdf_parser_includes_standard_metadata(self, mock_path, mock_pdf_reader):
        """
        Given: PDF 파일
        When: PDFParser.parse() 호출
        Then: Message.metadata에 표준 메타데이터 포함
        """
        mock_path.return_value.exists.return_value = True

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF 내용"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        from src.parsers.pdf_parser import PDFParser

        parser = PDFParser()
        messages = parser.parse("/tmp/test.pdf")

        assert len(messages) > 0
        metadata = messages[0].metadata

        assert metadata["source_type"] == "pdf"
        assert metadata["filename"] == "test.pdf"
        assert metadata["filepath"] == "/tmp/test.pdf"
        assert metadata["parser_class"] == "PDFParser"
        assert "parsed_at" in metadata

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_pdf_parser_includes_page_number(self, mock_path, mock_pdf_reader):
        """
        Given: 여러 페이지 PDF 파일
        When: PDFParser.parse() 호출
        Then: 각 메시지 metadata에 page_number 포함
        """
        mock_path.return_value.exists.return_value = True

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "첫 페이지"

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "둘째 페이지"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        from src.parsers.pdf_parser import PDFParser

        parser = PDFParser()
        messages = parser.parse("/tmp/test.pdf")

        assert len(messages) == 2
        assert messages[0].metadata["page_number"] == 1
        assert messages[1].metadata["page_number"] == 2


class TestAudioParserMetadata:
    """AudioParser 메타데이터 테스트"""

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_audio_parser_includes_standard_metadata(self, mock_file, mock_path, mock_openai):
        """
        Given: 오디오 파일
        When: AudioParser.parse() 호출
        Then: Message.metadata에 표준 메타데이터 포함
        """
        mock_path.return_value.exists.return_value = True

        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[{'start': 0.0, 'text': '테스트 음성'}]
        )

        from src.parsers.audio_parser import AudioParser

        parser = AudioParser()
        messages = parser.parse("/tmp/test.mp3")

        assert len(messages) > 0
        metadata = messages[0].metadata

        assert metadata["source_type"] == "audio"
        assert metadata["filename"] == "test.mp3"
        assert metadata["filepath"] == "/tmp/test.mp3"
        assert metadata["parser_class"] == "AudioParser"
        assert "parsed_at" in metadata

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_audio_parser_includes_segment_info(self, mock_file, mock_path, mock_openai):
        """
        Given: 여러 세그먼트가 있는 오디오 파일
        When: AudioParser.parse() 호출
        Then: 각 메시지 metadata에 segment_start, segment_index 포함
        """
        mock_path.return_value.exists.return_value = True

        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[
                {'start': 0.0, 'text': '첫 번째'},
                {'start': 5.5, 'text': '두 번째'}
            ]
        )

        from src.parsers.audio_parser import AudioParser

        parser = AudioParser()
        messages = parser.parse("/tmp/test.mp3")

        assert len(messages) == 2
        assert messages[0].metadata["segment_start"] == 0.0
        assert messages[0].metadata["segment_index"] == 0
        assert messages[1].metadata["segment_start"] == 5.5
        assert messages[1].metadata["segment_index"] == 1


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg-python not installed")
class TestVideoParserMetadata:
    """VideoParser 메타데이터 테스트"""

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('tempfile.NamedTemporaryFile')
    def test_video_parser_includes_standard_metadata(
        self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser_class
    ):
        """
        Given: 비디오 파일
        When: VideoParser.parse() 호출
        Then: Message.metadata에 표준 메타데이터 포함 (source_type='video')
        """
        mock_path.return_value.exists.return_value = True

        # Mock temp file
        mock_temp = MagicMock()
        mock_temp.name = "/tmp/temp_audio.mp3"
        mock_temp.__enter__ = MagicMock(return_value=mock_temp)
        mock_temp.__exit__ = MagicMock(return_value=False)
        mock_tempfile.return_value = mock_temp

        # Mock ffmpeg
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value.output.return_value.overwrite_output.return_value = mock_stream

        # Mock AudioParser - return messages with video metadata
        from src.parsers.base import Message
        mock_audio_parser = MagicMock()
        mock_audio_parser.parse.return_value = [
            Message(
                content="테스트 음성",
                sender="Speaker",
                timestamp=datetime.now(),
                metadata={
                    "source_type": "video",
                    "filename": "test.mp4",
                    "filepath": "/tmp/test.mp4",
                    "parser_class": "VideoParser",
                    "parsed_at": datetime.now().isoformat(),
                    "segment_start": 0.0,
                    "segment_index": 0
                }
            )
        ]
        mock_audio_parser_class.return_value = mock_audio_parser

        from src.parsers.video_parser import VideoParser

        parser = VideoParser()
        messages = parser.parse("/tmp/test.mp4")

        assert len(messages) > 0
        metadata = messages[0].metadata

        # VideoParser should override source_type to 'video'
        assert metadata["source_type"] == "video"
        assert metadata["filename"] == "test.mp4"
        assert metadata["parser_class"] == "VideoParser"


@pytest.mark.skipif(not HAS_PYTESSERACT, reason="pytesseract not installed")
class TestImageVisionParserMetadata:
    """ImageVisionParser 메타데이터 테스트"""

    @patch('src.parsers.image_vision.pytesseract')
    @patch('src.parsers.image_vision.Image')
    @patch('src.parsers.image_vision.Path')
    def test_image_parser_includes_standard_metadata(
        self, mock_path, mock_image, mock_tesseract
    ):
        """
        Given: 이미지 파일
        When: ImageVisionParser.parse() 호출
        Then: Message.metadata에 표준 메타데이터 포함
        """
        mock_path.return_value.exists.return_value = True

        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.convert.return_value = mock_img
        mock_image.open.return_value = mock_img

        # Mock tesseract OCR
        mock_tesseract.image_to_string.return_value = "OCR 추출 텍스트"

        from src.parsers.image_vision import ImageVisionParser

        parser = ImageVisionParser()
        messages = parser.parse("/tmp/test.jpg")

        assert len(messages) > 0
        metadata = messages[0].metadata

        assert metadata["source_type"] == "image"
        assert metadata["filename"] == "test.jpg"
        assert metadata["filepath"] == "/tmp/test.jpg"
        assert metadata["parser_class"] == "ImageVisionParser"
        assert "parsed_at" in metadata


class TestMetadataValidation:
    """메타데이터 유효성 검사 테스트"""

    def test_create_standard_metadata_helper(self):
        """
        Given: BaseParser의 _create_standard_metadata 헬퍼
        When: 파일 경로와 파서 클래스명으로 호출
        Then: 표준 메타데이터 딕셔너리 반환
        """
        from src.parsers.base import BaseParser

        # BaseParser 서브클래스 생성 (추상 클래스이므로)
        class TestParser(BaseParser):
            def parse(self, filepath):
                return []

        parser = TestParser()
        metadata = parser._create_standard_metadata(
            filepath="/tmp/test.pdf",
            source_type="pdf"
        )

        assert metadata["source_type"] == "pdf"
        assert metadata["filename"] == "test.pdf"
        assert metadata["filepath"] == "/tmp/test.pdf"
        assert metadata["parser_class"] == "TestParser"
        assert "parsed_at" in metadata

        # parsed_at는 ISO8601 형식이어야 함
        from datetime import datetime
        datetime.fromisoformat(metadata["parsed_at"])  # 파싱 가능해야 함
