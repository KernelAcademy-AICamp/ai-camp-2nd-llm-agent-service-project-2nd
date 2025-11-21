"""
Data Schemas for Storage Module
Defines Pydantic models for evidence files and chunks
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class EvidenceFile(BaseModel):
    """
    증거 파일 메타데이터

    Attributes:
        file_id: 파일 고유 ID (UUID)
        filename: 파일명
        file_type: 파일 타입 (kakaotalk/text/pdf/image)
        parsed_at: 파싱 완료 시간
        total_messages: 총 메시지/청크 개수
        case_id: 케이스 ID (사건 구분)
        filepath: 원본 파일 경로 (선택)
    """
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: str  # kakaotalk | text | pdf | image
    parsed_at: datetime = Field(default_factory=datetime.now)
    total_messages: int
    case_id: str
    filepath: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EvidenceChunk(BaseModel):
    """
    증거 청크/메시지 메타데이터

    Attributes:
        chunk_id: 청크 고유 ID (UUID)
        file_id: 소속 파일 ID
        content: 메시지 내용
        score: 증거 점수 (0-10, 선택적 - Week 3에서 추가)
        timestamp: 메시지 발생 시간
        sender: 발신자
        vector_id: ChromaDB 벡터 ID (저장 후 설정)
        case_id: 케이스 ID
    """
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str
    content: str
    score: Optional[float] = None
    timestamp: datetime
    sender: str
    vector_id: Optional[str] = None
    case_id: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 헬퍼 함수
def generate_file_id() -> str:
    """새 파일 ID 생성"""
    return str(uuid.uuid4())


def generate_chunk_id() -> str:
    """새 청크 ID 생성"""
    return str(uuid.uuid4())


class SearchResult(BaseModel):
    """
    검색 결과 모델

    Attributes:
        chunk_id: 청크 ID
        file_id: 파일 ID
        content: 내용
        distance: 유사도 거리 (낮을수록 유사)
        timestamp: 메시지 시간
        sender: 발신자
        case_id: 케이스 ID
        metadata: 추가 메타데이터
        context_before: 이전 컨텍스트 청크 목록 (선택)
        context_after: 이후 컨텍스트 청크 목록 (선택)
    """
    chunk_id: str
    file_id: str
    content: str
    distance: float
    timestamp: datetime
    sender: str
    case_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    context_before: Optional[List[str]] = None
    context_after: Optional[List[str]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
