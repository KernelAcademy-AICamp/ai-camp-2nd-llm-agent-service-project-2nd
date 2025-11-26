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


# ============================================================
# 법률 양식 템플릿 스키마 (DraftGenerator용)
# ============================================================

class TemplateSection(BaseModel):
    """
    양식 섹션

    Attributes:
        section_name: 섹션명 (예: "당사자", "청구취지")
        content_template: 내용 템플릿 (플레이스홀더 포함)
        required: 필수 여부
        order: 섹션 순서
    """
    section_name: str
    content_template: str
    required: bool = True
    order: int = 0


class LegalTemplate(BaseModel):
    """
    법률 양식 템플릿

    Attributes:
        template_id: 템플릿 고유 ID
        template_type: 양식 유형 (divorce_complaint, response, evidence_list)
        title: 양식 제목
        description: 양식 설명
        sections: 섹션 목록
        placeholders: 플레이스홀더 목록
        example: 작성 예시
    """
    template_id: str
    template_type: str  # "divorce_complaint", "response", "evidence_list"
    title: str
    description: str = ""
    sections: List[TemplateSection] = Field(default_factory=list)
    placeholders: List[str] = Field(default_factory=list)
    example: Optional[str] = None


class DraftDocument(BaseModel):
    """
    생성된 초안 문서

    Attributes:
        document_type: 문서 유형
        title: 문서 제목
        content: 문서 내용 (Markdown 형식)
        legal_grounds: 인용된 법적 근거
        evidence_references: 참조된 증거 목록
        case_id: 관련 케이스 ID
        created_at: 생성 시간
        metadata: 추가 메타데이터
    """
    document_type: str
    title: str
    content: str
    legal_grounds: List[str] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    case_id: Optional[str] = None
    created_at: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class PartyInfo(BaseModel):
    """
    당사자 정보

    Attributes:
        name: 성명
        resident_number: 주민등록번호 (선택)
        address: 주소
        phone: 연락처 (선택)
        role: 역할 (원고/피고)
    """
    name: str
    resident_number: Optional[str] = None
    address: str
    phone: Optional[str] = None
    role: str  # "plaintiff" or "defendant"
