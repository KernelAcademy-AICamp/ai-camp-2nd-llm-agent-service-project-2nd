"""
Text Parser Module
Parses plain text and PDF files
Auto-detects KakaoTalk format and delegates to KakaoTalkParser
"""

import re
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
        KakaoTalk 형식 자동 감지 및 위임

        Args:
            filepath: 텍스트/PDF 파일 경로

        Returns:
            List[Message]: 파싱된 메시지

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            ValueError: 지원하지 않는 파일 형식일 때
        """
        self._validate_file_exists(filepath)

        extension = self._get_file_extension(filepath)
        path = Path(filepath)

        if extension == ".txt":
            # 먼저 파일 내용을 읽어서 KakaoTalk 형식인지 확인
            content = self._parse_text_file(filepath)

            # KakaoTalk 형식이면 KakaoTalkParser로 위임
            if self._is_kakaotalk_format(content):
                from .kakaotalk import KakaoTalkParser
                kakao_parser = KakaoTalkParser()
                return kakao_parser.parse(filepath)

            # 일반 텍스트 처리
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

        elif extension == ".csv":
            # CSV 파일 처리 (텍스트로 읽음)
            content = self._parse_csv_file(filepath)
            message = Message(
                content=content,
                sender="System",
                timestamp=datetime.now(),
                metadata={
                    "source_type": "csv",
                    "filename": path.name,
                    "filepath": str(path.absolute()),
                    "extension": extension
                }
            )
            return [message]

        elif extension == ".json":
            # JSON 파일 처리 (텍스트로 읽음)
            content = self._parse_text_file(filepath)
            message = Message(
                content=content,
                sender="System",
                timestamp=datetime.now(),
                metadata={
                    "source_type": "json",
                    "filename": path.name,
                    "filepath": str(path.absolute()),
                    "extension": extension
                }
            )
            return [message]

        elif extension == ".pdf":
            content = self._parse_pdf_file(filepath)
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

        else:
            raise ValueError(f"Unsupported file format: {extension}")

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

    def _parse_csv_file(self, filepath: str) -> str:
        """
        CSV 파일 파싱 (텍스트로 변환)

        Args:
            filepath: CSV 파일 경로

        Returns:
            str: CSV 내용을 읽기 쉬운 형태로 변환
        """
        import csv

        rows = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = None
            for idx, row in enumerate(reader):
                if idx == 0:
                    headers = row
                    continue
                if headers:
                    # "헤더1: 값1, 헤더2: 값2" 형식으로 변환
                    formatted = ", ".join(
                        f"{h}: {v}" for h, v in zip(headers, row) if v
                    )
                    rows.append(formatted)
                else:
                    rows.append(", ".join(row))

        return "\n".join(rows)

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

    def _is_kakaotalk_format(self, content: str) -> bool:
        """
        KakaoTalk 채팅 형식인지 감지

        Args:
            content: 파일 내용

        Returns:
            bool: KakaoTalk 형식이면 True
        """
        # KakaoTalk 형식 패턴: "YYYY년 M월 D일 오전/오후 H:MM, 발신자 : 내용"
        kakao_pattern = re.compile(
            r"\d{4}년 \d{1,2}월 \d{1,2}일 (오전|오후) \d{1,2}:\d{2}, .+ : "
        )

        # 첫 100줄 정도만 검사 (성능 최적화)
        lines = content.split('\n')[:100]

        # 최소 2개 이상의 메시지 패턴이 있으면 KakaoTalk 형식으로 판단
        match_count = sum(1 for line in lines if kakao_pattern.search(line))
        return match_count >= 2
