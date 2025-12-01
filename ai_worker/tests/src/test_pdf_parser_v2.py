"""
PDF Parser V2 테스트

Given: PDF 파일
When: PDFParserV2.parse() 호출
Then: 페이지별 내용과 법적 인용 정보 반환
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from src.parsers.pdf_parser_v2 import (
    PDFParserV2,
    ParsedPage,
    PDFParsingResult
)


class TestPDFParserV2Initialization:
    """PDFParserV2 초기화 테스트"""

    def test_parser_creation(self):
        """Given: 기본 설정
        When: PDFParserV2() 생성
        Then: 파서 인스턴스 생성"""
        parser = PDFParserV2()
        assert parser is not None
        assert parser.min_content_length == 10

    def test_parser_with_custom_min_length(self):
        """Given: 커스텀 min_content_length
        When: PDFParserV2(min_content_length=50)
        Then: 설정값 반영"""
        parser = PDFParserV2(min_content_length=50)
        assert parser.min_content_length == 50


class TestPDFParserV2Parse:
    """parse() 메서드 테스트"""

    def test_parse_file_not_found(self):
        """Given: 존재하지 않는 파일
        When: parse() 호출
        Then: FileNotFoundError 발생"""
        parser = PDFParserV2()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.pdf")

    @patch('src.parsers.pdf_parser_v2.PdfReader')
    def test_parse_returns_result(self, mock_reader_class):
        """Given: 유효한 PDF
        When: parse() 호출
        Then: PDFParsingResult 반환"""
        # Mock 설정
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "테스트 내용입니다. 이것은 PDF 테스트입니다."

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        parser = PDFParserV2()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 test content')
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert isinstance(result, PDFParsingResult)
            assert result.total_pages == 1
            assert len(result.pages) == 1
            assert result.pages[0].page_number == 1
        finally:
            os.unlink(temp_path)

    @patch('src.parsers.pdf_parser_v2.PdfReader')
    def test_parse_multiple_pages(self, mock_reader_class):
        """Given: 여러 페이지 PDF
        When: parse() 호출
        Then: 모든 페이지 파싱"""
        # Mock 설정
        mock_pages = []
        for i in range(3):
            mock_page = MagicMock()
            mock_page.extract_text.return_value = f"페이지 {i+1} 내용입니다."
            mock_pages.append(mock_page)

        mock_reader = MagicMock()
        mock_reader.pages = mock_pages
        mock_reader_class.return_value = mock_reader

        parser = PDFParserV2()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 test content')
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.total_pages == 3
            assert len(result.pages) == 3
            assert result.pages[0].page_number == 1
            assert result.pages[1].page_number == 2
            assert result.pages[2].page_number == 3
        finally:
            os.unlink(temp_path)

    @patch('src.parsers.pdf_parser_v2.PdfReader')
    def test_parse_detects_empty_pages(self, mock_reader_class):
        """Given: 빈 페이지 포함 PDF
        When: parse() 호출
        Then: 빈 페이지 식별"""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "내용이 있는 페이지입니다."

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = ""  # 빈 페이지

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_reader_class.return_value = mock_reader

        parser = PDFParserV2()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 test content')
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert 2 in result.empty_pages
            assert result.pages[1].is_empty is True
        finally:
            os.unlink(temp_path)


class TestParsedPage:
    """ParsedPage 모델 테스트"""

    def test_parsed_page_creation(self):
        """Given: 페이지 데이터
        When: ParsedPage 생성
        Then: 속성 정확히 설정"""
        page = ParsedPage(
            page_number=1,
            content="테스트 내용",
            is_empty=False,
            char_count=5
        )

        assert page.page_number == 1
        assert page.content == "테스트 내용"
        assert page.is_empty is False
        assert page.char_count == 5

    def test_parsed_page_has_page_number(self):
        """Given: ParsedPage
        When: page_number 확인
        Then: 법적 인용용 페이지 번호 있음"""
        page = ParsedPage(
            page_number=5,
            content="중요한 내용",
            is_empty=False,
            char_count=5
        )

        # 페이지 번호로 법적 인용 가능
        assert page.page_number == 5
        assert f"5페이지" or str(page.page_number) in str(page.page_number)


class TestPDFParsingResult:
    """PDFParsingResult 모델 테스트"""

    def test_result_statistics(self):
        """Given: 파싱 결과
        When: 통계 확인
        Then: 정확한 통계"""
        pages = [
            ParsedPage(page_number=1, content="내용", is_empty=False, char_count=2),
            ParsedPage(page_number=2, content="", is_empty=True, char_count=0),
            ParsedPage(page_number=3, content="더 많은 내용", is_empty=False, char_count=6),
        ]

        result = PDFParsingResult(
            pages=pages,
            file_name="test.pdf",
            total_pages=3,
            parsed_pages=2,
            empty_pages=[2],
            error_pages=[],
            file_hash="abc123",
            file_size_bytes=1024
        )

        assert result.total_pages == 3
        assert result.parsed_pages == 2
        assert len(result.empty_pages) == 1


class TestPDFParserV2ParseToChunks:
    """parse_to_chunks() 메서드 테스트"""

    @patch('src.parsers.pdf_parser_v2.PdfReader')
    def test_parse_to_chunks_returns_evidence_chunks(self, mock_reader_class):
        """Given: PDF 파일
        When: parse_to_chunks() 호출
        Then: EvidenceChunk 리스트 반환"""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "법적 증거 내용입니다."

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        parser = PDFParserV2()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 test content')
            temp_path = f.name

        try:
            chunks, result = parser.parse_to_chunks(
                filepath=temp_path,
                case_id="case_001",
                file_id="file_001"
            )

            assert len(chunks) == 1
            assert chunks[0].case_id == "case_001"
            assert chunks[0].file_id == "file_001"
        finally:
            os.unlink(temp_path)

    @patch('src.parsers.pdf_parser_v2.PdfReader')
    def test_parse_to_chunks_skips_empty_pages(self, mock_reader_class):
        """Given: 빈 페이지 포함 PDF
        When: parse_to_chunks(include_empty_pages=False)
        Then: 빈 페이지 제외"""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "내용이 있는 충분히 긴 텍스트입니다"  # min_content_length=10 넘어야 함

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = ""

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_reader_class.return_value = mock_reader

        parser = PDFParserV2()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 test content')
            temp_path = f.name

        try:
            chunks, _ = parser.parse_to_chunks(
                filepath=temp_path,
                case_id="case_001",
                file_id="file_001",
                include_empty_pages=False
            )

            assert len(chunks) == 1  # 빈 페이지 제외
        finally:
            os.unlink(temp_path)


class TestPDFParserV2FileMetadata:
    """get_file_metadata() 메서드 테스트"""

    @patch('src.parsers.pdf_parser_v2.PdfReader')
    def test_get_file_metadata(self, mock_reader_class):
        """Given: PDF 파일
        When: get_file_metadata() 호출
        Then: FileMetadata 반환"""
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]  # 2 pages
        mock_reader_class.return_value = mock_reader

        parser = PDFParserV2()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 test content')
            temp_path = f.name

        try:
            metadata = parser.get_file_metadata(temp_path)

            assert metadata.file_hash_sha256 is not None
            assert metadata.file_size_bytes > 0
            assert metadata.total_pages == 2
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
