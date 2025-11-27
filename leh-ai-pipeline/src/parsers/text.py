"""
Text Parser Module
Parses plain text and PDF files
"""

from datetime import datetime
from pathlib import Path
from typing import List
from .base import BaseParser, Message


class TextParser(BaseParser):
    """
    텍스트 파일 파서

    지원 형식:
    - .txt (UTF-8 인코딩)
    - .pdf (PyPDF2 사용)

    전체 파일 내용을 하나의 Message로 반환합니다.
    """

    def parse(self, filepath: str) -> List[Message]:
        """
        텍스트 파일 파싱

        Args:
            filepath: 텍스트/PDF 파일 경로

        Returns:
            List[Message]: 파싱된 메시지 (1개)

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            ValueError: 지원하지 않는 파일 형식일 때
        """
        self._validate_file_exists(filepath)

        extension = self._get_file_extension(filepath)
        path = Path(filepath)

        if extension == ".txt":
            content = self._parse_text_file(filepath)
        elif extension == ".pdf":
            content = self._parse_pdf_file(filepath)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

        message = Message(
            content=content,
            sender="System",
            timestamp=datetime.now(),
            metadata={
                "source_type": "text",
                "filename": path.name,
                "filepath": str(path.absolute()),
                "extension": extension
            }
        )

        return [message]

    def _parse_text_file(self, filepath: str) -> str:
        """
        텍스트 파일 파싱

        Args:
            filepath: 텍스트 파일 경로

        Returns:
            str: 파일 내용
        """
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return content.strip()

    def _parse_pdf_file(self, filepath: str) -> str:
        """
        PDF 파일 파싱

        Args:
            filepath: PDF 파일 경로

        Returns:
            str: 추출된 텍스트

        Raises:
            ImportError: PyPDF2가 설치되지 않았을 때
        """
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF parsing. "
                "Install it with: pip install PyPDF2"
            )

        reader = PdfReader(filepath)
        text_parts = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        content = "\n".join(text_parts)
        return content.strip()
