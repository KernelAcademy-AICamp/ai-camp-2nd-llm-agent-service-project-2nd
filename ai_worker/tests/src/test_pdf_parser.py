"""
Test suite for PDFParser
Following TDD approach: RED-GREEN-REFACTOR
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.parsers.pdf_parser import PDFParser
from src.parsers.base import Message


class TestPDFParserInitialization:
    """Test PDFParser initialization"""

    def test_parser_creation(self):
        """PDFParser 생성 테스트"""
        parser = PDFParser()

        assert parser is not None

    def test_parser_is_base_parser(self):
        """BaseParser 상속 확인"""
        from src.parsers.base import BaseParser
        parser = PDFParser()

        assert isinstance(parser, BaseParser)


class TestPDFParsing:
    """Test PDF parsing"""

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_parse_simple_pdf(self, mock_path, mock_pdf_reader):
        """간단한 PDF 파싱 테스트"""
        # Mock file exists
        mock_path.return_value.exists.return_value = True

        # Mock PDF pages
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "첫 번째 페이지 내용"

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "두 번째 페이지 내용"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        parser = PDFParser()
        messages = parser.parse("test.pdf")

        assert len(messages) == 2
        assert isinstance(messages[0], Message)
        assert "첫 번째 페이지" in messages[0].content

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_parse_creates_messages(self, mock_path, mock_pdf_reader):
        """Message 객체 생성 확인"""
        mock_path.return_value.exists.return_value = True

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF 텍스트 내용"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        parser = PDFParser()
        messages = parser.parse("test.pdf")

        assert all(isinstance(m, Message) for m in messages)
        assert all(hasattr(m, 'content') for m in messages)
        assert all(hasattr(m, 'sender') for m in messages)
        assert all(hasattr(m, 'timestamp') for m in messages)

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_parse_with_metadata(self, mock_path, mock_pdf_reader):
        """메타데이터 포함 파싱 테스트"""
        mock_path.return_value.exists.return_value = True

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF 내용"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        parser = PDFParser()
        messages = parser.parse(
            "test.pdf",
            default_sender="문서작성자",
            default_timestamp=datetime(2024, 1, 1, 12, 0)
        )

        assert messages[0].sender == "문서작성자"
        assert messages[0].timestamp == datetime(2024, 1, 1, 12, 0)


class TestPageNumbering:
    """Test page numbering"""

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_page_numbers_in_content(self, mock_path, mock_pdf_reader):
        """페이지 번호 포함 확인"""
        mock_path.return_value.exists.return_value = True

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "첫 페이지"

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "둘째 페이지"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        parser = PDFParser()
        messages = parser.parse("test.pdf")

        assert "[Page 1]" in messages[0].content
        assert "[Page 2]" in messages[1].content


class TestMultiPagePDF:
    """Test multi-page PDF handling"""

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_parse_multi_page_pdf(self, mock_path, mock_pdf_reader):
        """여러 페이지 PDF 파싱"""
        mock_path.return_value.exists.return_value = True

        # 5페이지 PDF
        pages = []
        for i in range(5):
            mock_page = MagicMock()
            mock_page.extract_text.return_value = f"페이지 {i+1} 내용"
            pages.append(mock_page)

        mock_reader = MagicMock()
        mock_reader.pages = pages
        mock_pdf_reader.return_value = mock_reader

        parser = PDFParser()
        messages = parser.parse("test.pdf")

        assert len(messages) == 5
        assert "[Page 5]" in messages[4].content


class TestEdgeCases:
    """Test edge cases"""

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_empty_pages(self, mock_path, mock_pdf_reader):
        """빈 페이지 처리"""
        mock_path.return_value.exists.return_value = True

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "내용 있음"

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = ""  # 빈 페이지

        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "   "  # 공백만

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf_reader.return_value = mock_reader

        parser = PDFParser()
        messages = parser.parse("test.pdf")

        # 빈 페이지는 제외되어야 함
        assert len(messages) == 1
        assert "내용 있음" in messages[0].content

    def test_invalid_file_path(self):
        """잘못된 파일 경로 처리"""
        parser = PDFParser()

        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent.pdf")

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_pdf_read_error(self, mock_path, mock_pdf_reader):
        """PDF 읽기 오류 처리"""
        mock_path.return_value.exists.return_value = True
        mock_pdf_reader.side_effect = Exception("Corrupted PDF")

        parser = PDFParser()

        with pytest.raises(Exception, match="Corrupted PDF"):
            parser.parse("test.pdf")


class TestTextExtraction:
    """Test text extraction quality"""

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_korean_text_extraction(self, mock_path, mock_pdf_reader):
        """한글 텍스트 추출 테스트"""
        mock_path.return_value.exists.return_value = True

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "이혼 소송 관련 증거 자료입니다."

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        parser = PDFParser()
        messages = parser.parse("test.pdf")

        assert "이혼 소송" in messages[0].content
        assert "증거 자료" in messages[0].content

    @patch('src.parsers.pdf_parser.PdfReader')
    @patch('src.parsers.pdf_parser.Path')
    def test_whitespace_handling(self, mock_path, mock_pdf_reader):
        """공백 처리 테스트"""
        mock_path.return_value.exists.return_value = True

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "   텍스트   \n\n   내용   "

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        parser = PDFParser()
        messages = parser.parse("test.pdf")

        # 공백이 정리되어야 함
        assert messages[0].content.strip() != ""
        assert "텍스트" in messages[0].content
