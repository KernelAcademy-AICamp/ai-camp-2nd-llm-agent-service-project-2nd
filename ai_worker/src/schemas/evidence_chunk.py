"""
Evidence Chunk Schema
증거 청크 - 개별 메시지/페이지/세그먼트 단위

법정에서 "이 파일의 N번째 줄"로 직접 인용 가능한 최소 단위
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid

from .source_location import SourceLocation
from .legal_analysis import LegalAnalysis


class EvidenceChunk(BaseModel):
    """
    증거 청크

    파일 내의 개별 단위 (메시지, 페이지, 음성 구간 등)
    법적 증거로 인용될 수 있는 최소 단위

    Examples:
        카카오톡: 개별 메시지 1개
        PDF: 페이지 1개 또는 섹션 1개
        음성: 발화 구간 1개 (세그먼트)
        이미지: 이미지 1개 전체 설명
    """

    # ========================================
    # 식별자
    # ========================================
    chunk_id: str = Field(
        default_factory=lambda: f"chunk_{uuid.uuid4().hex[:12]}",
        description="청크 고유 ID"
    )

    file_id: str = Field(
        ...,
        description="소속 파일 ID"
    )

    case_id: str = Field(
        ...,
        description="소속 케이스 ID"
    )

    # ========================================
    # 원본 위치 (핵심!)
    # ========================================
    source_location: SourceLocation = Field(
        ...,
        description="원본 파일 내 위치 정보"
    )

    # ========================================
    # 내용
    # ========================================
    content: str = Field(
        ...,
        description="청크 내용 (메시지 텍스트, OCR 결과 등)"
    )

    content_hash: str = Field(
        ...,
        description="내용의 SHA-256 해시 (중복 검사용)"
    )

    # ========================================
    # 메시지 정보 (카카오톡/대화용)
    # ========================================
    sender: Optional[str] = Field(
        None,
        description="발신자 이름"
    )

    timestamp: Optional[datetime] = Field(
        None,
        description="메시지/발화 시간"
    )

    # ========================================
    # 법적 분석 결과
    # ========================================
    legal_analysis: LegalAnalysis = Field(
        default_factory=LegalAnalysis,
        description="법적 분석 결과"
    )

    # ========================================
    # 벡터 검색용
    # ========================================
    vector_id: Optional[str] = Field(
        None,
        description="Qdrant 벡터 ID"
    )

    embedding: Optional[List[float]] = Field(
        None,
        description="텍스트 임베딩 벡터 (저장하지 않고 Qdrant에만)"
    )

    # ========================================
    # 연결 정보
    # ========================================
    related_chunk_ids: List[str] = Field(
        default_factory=list,
        description="연결된 다른 청크 ID들"
    )

    event_ids: List[str] = Field(
        default_factory=list,
        description="소속된 이벤트/클러스터 ID들"
    )

    # ========================================
    # 추가 메타데이터
    # ========================================
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="파일 유형별 추가 메타데이터"
    )

    # ========================================
    # 타임스탬프
    # ========================================
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="레코드 생성 시간"
    )

    def to_citation(self) -> str:
        """
        법정 인용 형식으로 변환

        Returns:
            str: "파일명 N번째 줄: 내용 요약"
        """
        location = self.source_location.to_citation()
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{location}: \"{content_preview}\""

    def to_search_payload(self) -> Dict[str, Any]:
        """
        Qdrant 검색용 payload 변환

        Returns:
            dict: Qdrant에 저장할 메타데이터
        """
        return {
            "chunk_id": self.chunk_id,
            "file_id": self.file_id,
            "case_id": self.case_id,
            "content": self.content,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "file_name": self.source_location.file_name,
            "file_type": self.source_location.file_type,
            "line_number": self.source_location.line_number,
            "page_number": self.source_location.page_number,
            "legal_categories": [cat for cat in self.legal_analysis.categories],
            "confidence_level": self.legal_analysis.confidence_level,
        }

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
