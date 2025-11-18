"""
Image OCR Parser Module
이미지에서 텍스트 추출 (OCR)
"""

from typing import List, Optional
from datetime import datetime
from pathlib import Path
from PIL import Image
import pytesseract
from src.parsers.base import BaseParser, Message


class ImageOCRParser(BaseParser):
    """
    이미지 OCR 파서

    Given: 이미지 파일 경로
    When: parse() 호출
    Then: OCR로 텍스트 추출 후 Message 객체 리스트 반환

    기능:
    - 이미지 전처리 (그레이스케일 변환 등)
    - Tesseract OCR로 텍스트 추출
    - 한글/영어 텍스트 인식
    - 줄 단위로 Message 객체 생성
    """

    def __init__(self, ocr_engine: str = "tesseract"):
        """
        초기화

        Args:
            ocr_engine: OCR 엔진 선택 (기본: tesseract)
        """
        self.ocr_engine = ocr_engine

    def parse(
        self,
        file_path: str,
        default_sender: str = "Unknown",
        default_timestamp: Optional[datetime] = None
    ) -> List[Message]:
        """
        이미지 파일 파싱

        Given: 이미지 파일 경로
        When: OCR 텍스트 추출 실행
        Then: Message 객체 리스트 반환

        Args:
            file_path: 이미지 파일 경로
            default_sender: 기본 발신자
            default_timestamp: 기본 타임스탬프

        Returns:
            List[Message]: 추출된 메시지 리스트

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
        """
        # 파일 존재 확인
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        # 이미지 전처리
        processed_image = self._preprocess_image(file_path)

        # 텍스트 추출
        text = self._extract_text(processed_image, lang='kor+eng')

        # 기본 타임스탬프 설정
        if default_timestamp is None:
            default_timestamp = datetime.now()

        # Message 객체 생성
        messages = self._create_messages_from_text(
            text,
            sender=default_sender,
            timestamp=default_timestamp
        )

        return messages

    def _preprocess_image(self, file_path: str) -> Image.Image:
        """
        이미지 전처리

        Given: 이미지 파일 경로
        When: 이미지 로드 및 전처리 실행
        Then: 전처리된 이미지 반환

        Args:
            file_path: 이미지 파일 경로

        Returns:
            Image.Image: 전처리된 PIL Image 객체
        """
        # 이미지 로드
        image = Image.open(file_path)

        # 그레이스케일 변환 (OCR 정확도 향상)
        gray_image = image.convert('L')

        return gray_image

    def _extract_text(
        self,
        image: Image.Image,
        lang: str = 'kor+eng'
    ) -> str:
        """
        이미지에서 텍스트 추출

        Given: 전처리된 이미지
        When: Tesseract OCR 실행
        Then: 추출된 텍스트 반환

        Args:
            image: PIL Image 객체
            lang: OCR 언어 설정 (기본: 한글+영어)

        Returns:
            str: 추출된 텍스트
        """
        # Tesseract OCR 실행
        text = pytesseract.image_to_string(image, lang=lang)

        return text

    def _create_messages_from_text(
        self,
        text: str,
        sender: str = "Unknown",
        timestamp: Optional[datetime] = None
    ) -> List[Message]:
        """
        추출된 텍스트에서 Message 객체 생성

        Given: OCR로 추출된 텍스트
        When: 줄 단위로 분리
        Then: Message 객체 리스트 반환

        Args:
            text: 추출된 텍스트
            sender: 발신자
            timestamp: 타임스탬프

        Returns:
            List[Message]: Message 객체 리스트
        """
        if timestamp is None:
            timestamp = datetime.now()

        messages = []

        # 줄 단위로 분리
        lines = text.split('\n')

        for line in lines:
            # 빈 줄 제외
            if line.strip():
                message = Message(
                    content=line.strip(),
                    sender=sender,
                    timestamp=timestamp
                )
                messages.append(message)

        return messages
