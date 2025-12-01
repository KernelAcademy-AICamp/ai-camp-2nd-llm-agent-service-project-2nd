"""
Legal Document Schemas
법률 문서 (법령, 판례) 데이터 모델
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class Statute(BaseModel):
    """
    법령 모델

    Attributes:
        statute_id: 법령 고유 ID
        name: 법령명 (예: "민법", "가사소송법")
        statute_number: 법령 번호 (예: "법률 제14965호")
        article_number: 조항 번호 (예: "제840조")
        content: 조문 내용
        effective_date: 시행일
        category: 법령 분류 (민법, 형법, 가족관계법 등)
    """
    statute_id: str
    name: str
    statute_number: Optional[str] = None
    article_number: str
    content: str
    effective_date: Optional[date] = None
    category: str = "일반"


class CaseLaw(BaseModel):
    """
    판례 모델

    Attributes:
        case_id: 판례 고유 ID
        case_number: 사건번호 (예: "2019다12345")
        court: 법원 (대법원, 고등법원 등)
        decision_date: 선고일
        case_name: 사건명
        summary: 판결 요지
        full_text: 판결 전문
        related_statutes: 관련 법령 조항 목록
        category: 사건 분류 (가사, 민사, 형사 등)
    """
    case_id: str
    case_number: str
    court: str
    decision_date: date
    case_name: str
    summary: str
    full_text: Optional[str] = None
    related_statutes: List[str] = Field(default_factory=list)
    category: str = "가사"


class LegalChunk(BaseModel):
    """
    법률 지식 청크 (벡터 DB 저장용)

    Attributes:
        chunk_id: 청크 고유 ID
        doc_type: 문서 유형 ("statute" or "case_law")
        doc_id: 원본 문서 ID (statute_id or case_id)
        content: 청크 내용
        metadata: 추가 메타데이터 (법령명, 조항, 판례번호 등)
    """
    chunk_id: str
    doc_type: str  # "statute" or "case_law"
    doc_id: str
    content: str
    metadata: dict = Field(default_factory=dict)


class LegalSearchResult(BaseModel):
    """
    법률 검색 결과

    Attributes:
        chunk_id: 청크 ID
        doc_type: 문서 유형
        doc_id: 원본 문서 ID
        content: 내용
        distance: 유사도 거리 (낮을수록 유사)
        metadata: 메타데이터
    """
    chunk_id: str
    doc_type: str
    doc_id: str
    content: str
    distance: float
    metadata: dict = Field(default_factory=dict)
