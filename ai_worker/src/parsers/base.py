"""
Base Parser Module
Provides abstract base class and data models for all parsers
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    """
    메시지 데이터 모델

    Attributes:
        content: 메시지 내용
        sender: 발신자 이름
        timestamp: 발신 시간
        score: 증거 점수 (0-10, 선택적)
        metadata: 추가 메타데이터 (선택적)
    """
    content: str
    sender: str
    timestamp: datetime
    score: Optional[float] = None
    metadata: dict = Field(default_factory=dict)

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: Optional[float]) -> Optional[float]:
        """점수는 0-10 범위여야 함"""
        if v is not None and (v < 0 or v > 10):
            raise ValueError(f"Score must be between 0 and 10, got {v}")
        return v

    class Config:
        # datetime 직렬화 지원
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseParser(ABC):
    """
    파서 추상 베이스 클래스

    모든 파서는 이 클래스를 상속받아 parse() 메서드를 구현해야 함
    """

    @abstractmethod
    def parse(self, filepath: str) -> list[Message]:
        """
        파일을 파싱하여 Message 리스트 반환

        Args:
            filepath: 파싱할 파일 경로

        Returns:
            list[Message]: 파싱된 메시지 리스트

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            ValueError: 파일 형식이 잘못되었을 때
        """
        pass

    def _validate_file_exists(self, filepath: str) -> None:
        """
        파일 존재 여부 검증

        Args:
            filepath: 검증할 파일 경로

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {filepath}")

    def _get_file_extension(self, filepath: str) -> str:
        """
        파일 확장자 추출

        Args:
            filepath: 파일 경로

        Returns:
            str: 확장자 (예: '.txt', '.pdf')
        """
        return Path(filepath).suffix.lower()
