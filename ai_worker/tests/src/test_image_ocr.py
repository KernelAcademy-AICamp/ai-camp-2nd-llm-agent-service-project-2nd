"""
Test suite for ImageOCRParser
Following TDD approach: RED-GREEN-REFACTOR
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.parsers.image_ocr import ImageOCRParser
from src.parsers.base import Message


class TestImageOCRParserInitialization:
    """Test ImageOCRParser initialization"""

    def test_parser_creation(self):
        """ImageOCRParser 생성 테스트"""
        parser = ImageOCRParser()

        assert parser is not None

    def test_parser_has_ocr_engine(self):
        """OCR 엔진 초기화 확인"""
        parser = ImageOCRParser()

        assert hasattr(parser, 'ocr_engine')


class TestImageParsing:
    """Test image parsing"""

    @patch('src.parsers.image_ocr.Path')
    @patch('src.parsers.image_ocr.Image')
    @patch('src.parsers.image_ocr.pytesseract')
    def test_parse_simple_image(self, mock_pytesseract, mock_image, mock_path):
        """간단한 이미지 파싱 테스트"""
        # Mock file exists
        mock_path.return_value.exists.return_value = True

        # Mock OCR result
        mock_pytesseract.image_to_string.return_value = "안녕하세요\n이혼 상담 요청합니다"

        parser = ImageOCRParser()
        messages = parser.parse("test_image.png")

        assert len(messages) > 0
        assert isinstance(messages[0], Message)
        assert "안녕하세요" in messages[0].content or "이혼" in messages[0].content

    @patch('src.parsers.image_ocr.Path')
    @patch('src.parsers.image_ocr.Image')
    @patch('src.parsers.image_ocr.pytesseract')
    def test_parse_creates_messages(self, mock_pytesseract, mock_image, mock_path):
        """Message 객체 생성 확인"""
        mock_path.return_value.exists.return_value = True
        mock_pytesseract.image_to_string.return_value = "테스트 메시지\n발신자: A"

        parser = ImageOCRParser()
        messages = parser.parse("test.png")

        assert all(isinstance(m, Message) for m in messages)
        assert all(hasattr(m, 'content') for m in messages)
        assert all(hasattr(m, 'sender') for m in messages)
        assert all(hasattr(m, 'timestamp') for m in messages)

    @patch('src.parsers.image_ocr.Path')
    @patch('src.parsers.image_ocr.Image')
    @patch('src.parsers.image_ocr.pytesseract')
    def test_parse_with_metadata(self, mock_pytesseract, mock_image, mock_path):
        """메타데이터 포함 파싱 테스트"""
        mock_path.return_value.exists.return_value = True
        mock_pytesseract.image_to_string.return_value = "이미지 내용"

        parser = ImageOCRParser()
        messages = parser.parse(
            "test.png",
            default_sender="사용자A",
            default_timestamp=datetime(2024, 1, 1, 12, 0)
        )

        assert messages[0].sender == "사용자A"
        assert messages[0].timestamp == datetime(2024, 1, 1, 12, 0)


class TestImagePreprocessing:
    """Test image preprocessing"""

    @patch('src.parsers.image_ocr.Image')
    def test_preprocess_image(self, mock_image):
        """이미지 전처리 테스트"""
        mock_img = MagicMock()
        mock_image.open.return_value = mock_img

        parser = ImageOCRParser()
        processed = parser._preprocess_image("test.png")

        assert processed is not None

    @patch('src.parsers.image_ocr.Image')
    def test_preprocess_converts_to_grayscale(self, mock_image):
        """그레이스케일 변환 확인"""
        mock_img = MagicMock()
        mock_image.open.return_value = mock_img

        parser = ImageOCRParser()
        parser._preprocess_image("test.png")

        # convert 호출 확인
        mock_img.convert.assert_called()


class TestTextExtraction:
    """Test text extraction"""

    @patch('src.parsers.image_ocr.Image')
    @patch('src.parsers.image_ocr.pytesseract')
    def test_extract_text_from_image(self, mock_pytesseract, mock_image):
        """이미지에서 텍스트 추출 테스트"""
        mock_pytesseract.image_to_string.return_value = "추출된 텍스트"

        parser = ImageOCRParser()
        text = parser._extract_text(Mock())

        assert text == "추출된 텍스트"

    @patch('src.parsers.image_ocr.Image')
    @patch('src.parsers.image_ocr.pytesseract')
    def test_extract_korean_text(self, mock_pytesseract, mock_image):
        """한글 텍스트 추출 테스트"""
        mock_pytesseract.image_to_string.return_value = "안녕하세요"

        parser = ImageOCRParser()
        text = parser._extract_text(Mock(), lang='kor')

        mock_pytesseract.image_to_string.assert_called()
        assert text == "안녕하세요"


class TestMessageCreation:
    """Test message creation from OCR text"""

    def test_create_messages_from_text(self):
        """텍스트에서 Message 생성 테스트"""
        parser = ImageOCRParser()
        text = "첫 번째 줄\n두 번째 줄\n세 번째 줄"

        messages = parser._create_messages_from_text(
            text,
            sender="테스터",
            timestamp=datetime(2024, 1, 1)
        )

        assert len(messages) > 0
        assert all(isinstance(m, Message) for m in messages)

    def test_filter_empty_lines(self):
        """빈 줄 필터링 테스트"""
        parser = ImageOCRParser()
        text = "내용\n\n\n또 다른 내용"

        messages = parser._create_messages_from_text(text)

        # 빈 줄은 제외되어야 함
        assert all(m.content.strip() != "" for m in messages)


class TestEdgeCases:
    """Test edge cases"""

    @patch('src.parsers.image_ocr.Path')
    @patch('src.parsers.image_ocr.Image')
    @patch('src.parsers.image_ocr.pytesseract')
    def test_empty_image(self, mock_pytesseract, mock_image, mock_path):
        """빈 이미지 처리"""
        mock_path.return_value.exists.return_value = True
        mock_pytesseract.image_to_string.return_value = ""

        parser = ImageOCRParser()
        messages = parser.parse("empty.png")

        assert len(messages) == 0

    def test_invalid_file_path(self):
        """잘못된 파일 경로 처리"""
        parser = ImageOCRParser()

        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent.png")

    @patch('src.parsers.image_ocr.Path')
    @patch('src.parsers.image_ocr.Image')
    @patch('src.parsers.image_ocr.pytesseract')
    def test_ocr_failure(self, mock_pytesseract, mock_image, mock_path):
        """OCR 실패 처리"""
        mock_path.return_value.exists.return_value = True
        mock_pytesseract.image_to_string.side_effect = Exception("OCR failed")

        parser = ImageOCRParser()

        with pytest.raises(Exception, match="OCR failed"):
            parser.parse("test.png")
