"""
Source Location Schema
원본 파일 내 위치 정보 - 법적 증거 추적의 핵심

"카카오톡_배우자.txt 247번째 줄" 같은 정확한 위치 참조를 가능하게 함
"""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class FileType(str, Enum):
    """지원하는 파일 유형"""
    KAKAOTALK = "kakaotalk"
    IMAGE = "image"
    PDF = "pdf"
    AUDIO = "audio"
    TEXT = "text"
    VIDEO = "video"


class SourceLocation(BaseModel):
    """
    원본 파일 내 위치 정보

    법적 증거로 사용 시 "원본 파일 N번째 줄/페이지" 참조 가능하게 함

    Examples:
        카카오톡: file_name="카톡_배우자.txt", line_number=247
        PDF: file_name="진단서.pdf", page_number=2
        음성: file_name="녹음.m4a", segment_start_sec=134.5
        이미지: file_name="IMG_001.jpg", image_index=15
    """

    # 파일 식별
    file_name: str = Field(..., description="원본 파일명")
    file_type: FileType = Field(..., description="파일 유형")

    # ========================================
    # 카카오톡/텍스트용 위치 정보
    # ========================================
    line_number: Optional[int] = Field(
        None,
        ge=1,
        description="원본 파일의 라인 번호 (1부터 시작)"
    )
    line_number_end: Optional[int] = Field(
        None,
        ge=1,
        description="멀티라인 메시지의 끝 라인 번호"
    )

    # ========================================
    # PDF용 위치 정보
    # ========================================
    page_number: Optional[int] = Field(
        None,
        ge=1,
        description="PDF 페이지 번호 (1부터 시작)"
    )
    section_title: Optional[str] = Field(
        None,
        description="PDF 섹션/제목 (있는 경우)"
    )

    # ========================================
    # 음성/동영상용 위치 정보
    # ========================================
    segment_start_sec: Optional[float] = Field(
        None,
        ge=0,
        description="구간 시작 시간 (초)"
    )
    segment_end_sec: Optional[float] = Field(
        None,
        ge=0,
        description="구간 종료 시간 (초)"
    )

    # ========================================
    # 이미지용 위치 정보
    # ========================================
    image_index: Optional[int] = Field(
        None,
        ge=1,
        description="이미지 순번 (같은 케이스 내 N번째 이미지)"
    )

    def to_citation(self) -> str:
        """
        법정에서 인용 가능한 형식으로 변환

        Returns:
            str: "파일명 N번째 줄" 또는 "파일명 N페이지" 형식
        """
        if self.file_type == FileType.KAKAOTALK or self.file_type == FileType.TEXT:
            if self.line_number_end and self.line_number_end != self.line_number:
                return f"{self.file_name} {self.line_number}~{self.line_number_end}번째 줄"
            return f"{self.file_name} {self.line_number}번째 줄"

        elif self.file_type == FileType.PDF:
            citation = f"{self.file_name} {self.page_number}페이지"
            if self.section_title:
                citation += f" ({self.section_title})"
            return citation

        elif self.file_type == FileType.AUDIO or self.file_type == FileType.VIDEO:
            start = self._format_time(self.segment_start_sec)
            end = self._format_time(self.segment_end_sec)
            return f"{self.file_name} {start}~{end} 구간"

        elif self.file_type == FileType.IMAGE:
            return f"{self.file_name} (증거사진 {self.image_index}번)"

        return self.file_name

    def _format_time(self, seconds: Optional[float]) -> str:
        """초를 MM:SS 형식으로 변환"""
        if seconds is None:
            return "00:00"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    class Config:
        use_enum_values = True
