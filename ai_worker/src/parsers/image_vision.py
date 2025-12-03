"""
Image Vision Parser (GPT-4o Vision Integration)

이미지 감정/맥락 분석 모듈

Given: 이미지 파일
When: GPT-4o Vision API로 분석
Then: 감정, 맥락, 분위기 정보 추출 + OCR 텍스트
"""

from typing import List, Optional
from datetime import datetime
from pathlib import Path
import json
import base64
from PIL import Image
import pytesseract
import openai
from pydantic import BaseModel, Field

from src.parsers.base import BaseParser, Message


class VisionAnalysis(BaseModel):
    """
    이미지 비전 분석 결과

    Attributes:
        emotions: 감지된 감정 리스트 (happy, sad, angry, neutral 등)
        context: 이미지 맥락/장면 설명
        atmosphere: 전체적인 분위기
        confidence: 분석 신뢰도 (0.0-1.0)
    """
    emotions: List[str] = Field(default_factory=list)
    context: str = ""
    atmosphere: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ImageVisionParser(BaseParser):
    """
    이미지 비전 파서 (OCR + GPT-4o Vision)

    Given: 이미지 파일
    When: parse() 호출
    Then: OCR 텍스트 + 감정/맥락 분석 결과 반환

    Features:
    - OCR 텍스트 추출 (Tesseract)
    - GPT-4o Vision으로 감정 분석
    - 이미지 맥락/장면 설명
    - 분위기 분석
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
        default_timestamp: Optional[datetime] = None,
        include_vision: bool = False
    ) -> List[Message]:
        """
        이미지 파일 파싱 (OCR + Vision)

        Given: 이미지 파일 경로
        When: OCR + Vision 분석 실행
        Then: Message 객체 리스트 반환 (vision_analysis 메타데이터 포함)

        Args:
            file_path: 이미지 파일 경로
            default_sender: 기본 발신자
            default_timestamp: 기본 타임스탬프
            include_vision: GPT-4o Vision 분석 포함 여부 (기본: False)

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

        # OCR 텍스트 추출
        text = self._extract_text(processed_image, lang='kor+eng')

        # 기본 타임스탬프 설정
        if default_timestamp is None:
            default_timestamp = datetime.now()

        # Message 객체 생성
        messages = self._create_messages_from_text(
            text,
            file_path=file_path,
            sender=default_sender,
            timestamp=default_timestamp
        )

        # Vision 분석 추가 (옵션)
        if include_vision:
            vision_analysis = self.analyze_vision(file_path)
            # 첫 번째 메시지에 vision_analysis 메타데이터 추가
            if messages and len(messages) > 0:
                # Message 객체를 직접 수정할 수 없으므로, content에 추가 정보 포함
                first_msg = messages[0]
                enhanced_content = f"{first_msg.content}\n[Vision: {vision_analysis.context}]"
                # 기존 메타데이터 유지하면서 vision 정보 추가
                enhanced_metadata = {**first_msg.metadata}
                enhanced_metadata["vision_emotions"] = vision_analysis.emotions
                enhanced_metadata["vision_context"] = vision_analysis.context
                enhanced_metadata["vision_atmosphere"] = vision_analysis.atmosphere
                enhanced_metadata["vision_confidence"] = vision_analysis.confidence
                messages[0] = Message(
                    content=enhanced_content,
                    sender=first_msg.sender,
                    timestamp=first_msg.timestamp,
                    metadata=enhanced_metadata
                )

        return messages

    def analyze_vision(self, file_path: str) -> VisionAnalysis:
        """
        GPT-4o Vision API로 이미지 분석

        Given: 이미지 파일 경로
        When: GPT-4o Vision API 호출
        Then: VisionAnalysis 반환 (감정, 맥락, 분위기)

        Args:
            file_path: 이미지 파일 경로

        Returns:
            VisionAnalysis: 비전 분석 결과

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
        """
        # 파일 존재 확인
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        try:
            # 이미지를 base64로 인코딩
            with open(file_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # GPT-4o Vision API 호출
            prompt = """이 이미지를 분석하고 다음 정보를 JSON 형식으로 제공해주세요:
1. emotions: 감지된 감정 리스트 (예: happy, sad, angry, neutral, suspicious, tense 등)
2. context: 이미지의 맥락과 장면 설명 (한국어로)
3. atmosphere: 전체적인 분위기 설명 (한국어로)

응답 형식:
{
  "emotions": ["emotion1", "emotion2"],
  "context": "장면 설명",
  "atmosphere": "분위기 설명"
}"""

            response = openai.chat.completions.create(
                model="gpt-4o",  # or "gpt-4-vision-preview"
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            # 응답 파싱
            content = response.choices[0].message.content

            # JSON 파싱
            try:
                data = json.loads(content)
                return VisionAnalysis(
                    emotions=data.get("emotions", []),
                    context=data.get("context", ""),
                    atmosphere=data.get("atmosphere", ""),
                    confidence=0.8  # GPT-4o는 기본적으로 높은 신뢰도
                )
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본값 반환
                return VisionAnalysis(
                    emotions=[],
                    context=content[:100] if content else "",
                    atmosphere="",
                    confidence=0.5
                )

        except Exception as e:
            # API 에러 발생 시 예외 발생
            raise Exception(f"GPT-4o Vision API error: {e}")

    def _preprocess_image(self, file_path: str) -> Image.Image:
        """
        이미지 전처리

        Args:
            file_path: 이미지 파일 경로

        Returns:
            Image.Image: 전처리된 PIL Image 객체
        """
        image = Image.open(file_path)
        gray_image = image.convert('L')
        return gray_image

    def _extract_text(
        self,
        image: Image.Image,
        lang: str = 'kor+eng'
    ) -> str:
        """
        이미지에서 텍스트 추출 (OCR)

        Args:
            image: PIL Image 객체
            lang: OCR 언어 설정

        Returns:
            str: 추출된 텍스트
        """
        text = pytesseract.image_to_string(image, lang=lang)
        return text

    def _create_messages_from_text(
        self,
        text: str,
        file_path: str,
        sender: str = "Unknown",
        timestamp: Optional[datetime] = None
    ) -> List[Message]:
        """
        추출된 텍스트에서 Message 객체 생성

        Args:
            text: 추출된 텍스트
            file_path: 이미지 파일 경로
            sender: 발신자
            timestamp: 타임스탬프

        Returns:
            List[Message]: Message 객체 리스트
        """
        if timestamp is None:
            timestamp = datetime.now()

        messages = []
        lines = text.split('\n')

        for line_index, line in enumerate(lines):
            if line.strip():
                # 표준 메타데이터 생성
                metadata = self._create_standard_metadata(
                    filepath=file_path,
                    source_type="image",
                    line_index=line_index
                )

                message = Message(
                    content=line.strip(),
                    sender=sender,
                    timestamp=timestamp,
                    metadata=metadata
                )
                messages.append(message)

        return messages
