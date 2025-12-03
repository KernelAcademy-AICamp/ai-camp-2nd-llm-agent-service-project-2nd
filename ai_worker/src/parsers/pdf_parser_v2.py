"""
PDF Parser V2
PDF 문서 파서 - 법적 증거용

핵심 기능:
- 페이지 번호 추적 (법적 증거 인용용)
- 해시값 생성 (무결성 증명)
- 스캔 문서 OCR 지원 (선택적)
"""

import hashlib
from datetime import datetime
from typing import List, Tuple
from pathlib import Path
from dataclasses import dataclass

from PyPDF2 import PdfReader

from src.schemas import (
    SourceLocation,
    FileType,
    EvidenceChunk,
    LegalAnalysis,
    FileMetadata,
)


@dataclass
class ParsedPage:
    """파싱된 페이지"""
    page_number: int
    content: str
    is_empty: bool = False
    char_count: int = 0


@dataclass
class PDFParsingResult:
    """PDF 파싱 결과"""
    pages: List[ParsedPage]
    file_name: str
    total_pages: int
    parsed_pages: int
    empty_pages: List[int]
    error_pages: List[Tuple[int, str]]  # (page_num, error_reason)
    file_hash: str
    file_size_bytes: int


class PDFParserV2:
    """
    PDF 문서 파서 V2

    모든 페이지에 페이지 번호를 기록하고,
    법적 증거로 인용 가능한 형식으로 변환합니다.

    Usage:
        parser = PDFParserV2()
        result = parser.parse("document.pdf")

        for page in result.pages:
            print(f"Page {page.page_number}: {page.content[:100]}...")
    """

    def __init__(self, min_content_length: int = 10):
        """
        Args:
            min_content_length: 빈 페이지 판정 기준 (문자 수)
        """
        self.min_content_length = min_content_length

    def parse(self, filepath: str) -> PDFParsingResult:
        """
        PDF 파일 파싱

        Args:
            filepath: PDF 파일 경로

        Returns:
            PDFParsingResult: 파싱 결과

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # 파일 해시 계산
        file_hash = self._calculate_file_hash(filepath)
        file_size = path.stat().st_size

        pages: List[ParsedPage] = []
        empty_pages: List[int] = []
        error_pages: List[Tuple[int, str]] = []

        try:
            reader = PdfReader(filepath)
            total_pages = len(reader.pages)

            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text() or ""
                    text = text.strip()

                    is_empty = len(text) < self.min_content_length
                    if is_empty:
                        empty_pages.append(page_num)

                    parsed_page = ParsedPage(
                        page_number=page_num,
                        content=text,
                        is_empty=is_empty,
                        char_count=len(text)
                    )
                    pages.append(parsed_page)

                except Exception as e:
                    error_pages.append((page_num, str(e)))
                    # 오류 페이지도 빈 내용으로 추가
                    pages.append(ParsedPage(
                        page_number=page_num,
                        content="",
                        is_empty=True,
                        char_count=0
                    ))

        except Exception as e:
            raise ValueError(f"Failed to read PDF: {e}")

        return PDFParsingResult(
            pages=pages,
            file_name=path.name,
            total_pages=total_pages,
            parsed_pages=len([p for p in pages if not p.is_empty]),
            empty_pages=empty_pages,
            error_pages=error_pages,
            file_hash=file_hash,
            file_size_bytes=file_size
        )

    def parse_to_chunks(
        self,
        filepath: str,
        case_id: str,
        file_id: str,
        include_empty_pages: bool = False
    ) -> Tuple[List[EvidenceChunk], PDFParsingResult]:
        """
        파싱 후 EvidenceChunk 리스트로 변환

        Args:
            filepath: 파일 경로
            case_id: 케이스 ID
            file_id: 파일 ID
            include_empty_pages: 빈 페이지도 포함할지 여부

        Returns:
            Tuple[List[EvidenceChunk], PDFParsingResult]: 청크 리스트와 파싱 결과
        """
        result = self.parse(filepath)
        chunks: List[EvidenceChunk] = []

        for page in result.pages:
            if page.is_empty and not include_empty_pages:
                continue

            # 원본 위치 정보
            source_location = SourceLocation(
                file_name=result.file_name,
                file_type=FileType.PDF,
                page_number=page.page_number
            )

            # 내용 해시
            content_hash = hashlib.sha256(page.content.encode('utf-8')).hexdigest()[:16]

            chunk = EvidenceChunk(
                file_id=file_id,
                case_id=case_id,
                source_location=source_location,
                content=page.content,
                content_hash=content_hash,
                sender="Document",  # PDF는 발신자 개념 없음
                timestamp=datetime.now(),  # 파싱 시점
                legal_analysis=LegalAnalysis(),
                extra_metadata={
                    "page_number": page.page_number,
                    "char_count": page.char_count,
                    "is_empty": page.is_empty
                }
            )
            chunks.append(chunk)

        return chunks, result

    def get_file_metadata(self, filepath: str) -> FileMetadata:
        """
        PDF 파일 메타데이터 추출

        Args:
            filepath: 파일 경로

        Returns:
            FileMetadata: 파일 메타데이터
        """
        path = Path(filepath)
        file_hash = self._calculate_file_hash(filepath)
        file_size = path.stat().st_size

        # PDF 메타데이터 추출
        total_pages = 0
        try:
            reader = PdfReader(filepath)
            total_pages = len(reader.pages)
        except Exception:
            pass

        return FileMetadata(
            file_hash_sha256=file_hash,
            file_size_bytes=file_size,
            total_pages=total_pages
        )

    def _calculate_file_hash(self, filepath: str) -> str:
        """파일 SHA-256 해시 계산"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# 간편 함수
def parse_pdf(filepath: str) -> PDFParsingResult:
    """PDF 파일 파싱 (간편 함수)"""
    parser = PDFParserV2()
    return parser.parse(filepath)
