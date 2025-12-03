"""
PDF Parser Module
PDF 문서에서 텍스트 추출
"""

from typing import List, Optional
from datetime import datetime
from pathlib import Path
from PyPDF2 import PdfReader
from src.parsers.base import BaseParser, Message


class PDFParser(BaseParser):
    """
    PDF 파일 파서

    Given: PDF 파일 경로
    When: parse() 호출
    Then: 페이지별 텍스트를 Message 객체 리스트로 반환

    기능:
    - 페이지별 텍스트 추출
    - 페이지 번호 자동 태깅
    - 빈 페이지 필터링
    - 한글/영어 텍스트 지원
    """

    def parse(
        self,
        file_path: str,
        default_sender: str = "Document",
        default_timestamp: Optional[datetime] = None
    ) -> List[Message]:
        """
        PDF 파일 파싱

        Given: PDF 파일 경로
        When: PyPDF2로 페이지별 텍스트 추출
        Then: Message 객체 리스트 반환

        Args:
            file_path: PDF 파일 경로
            default_sender: 기본 발신자 (기본값: "Document")
            default_timestamp: 기본 타임스탬프

        Returns:
            List[Message]: 페이지별 메시지 리스트

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
        """
        # 파일 존재 확인
        if not Path(file_path).exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # 기본 타임스탬프 설정
        if default_timestamp is None:
            default_timestamp = datetime.now()

        # PDF 읽기
        reader = PdfReader(file_path)
        messages = []

        # 페이지별 처리
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            # 빈 페이지 제외
            if text.strip():
                # 페이지 번호 포함
                content = f"[Page {page_num}]\n{text.strip()}"

                # 표준 메타데이터 생성
                metadata = self._create_standard_metadata(
                    filepath=file_path,
                    source_type="pdf",
                    page_number=page_num
                )

                message = Message(
                    content=content,
                    sender=default_sender,
                    timestamp=default_timestamp,
                    metadata=metadata
                )
                messages.append(message)

        return messages
