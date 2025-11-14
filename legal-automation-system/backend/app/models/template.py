"""
법률 문서 템플릿 모델
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database.base import Base
from app.models.document import DocumentType


class TemplateCategory(enum.Enum):
    """템플릿 카테고리"""
    CONTRACT = "contract"          # 계약서
    LABOR = "labor"               # 근로/노동
    REAL_ESTATE = "real_estate"   # 부동산
    BUSINESS = "business"          # 사업/상거래
    FAMILY = "family"              # 가족/상속
    CIVIL = "civil"                # 민사
    CRIMINAL = "criminal"          # 형사
    ADMINISTRATIVE = "administrative"  # 행정
    OTHER = "other"                # 기타


class Template(Base):
    """법률 문서 템플릿"""
    __tablename__ = "templates"

    # 기본 정보
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)  # 표시명
    description = Column(Text)
    category = Column(Enum(TemplateCategory), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)

    # 템플릿 내용
    template_content = Column(Text, nullable=False)  # 템플릿 본문
    sample_content = Column(Text)  # 예시 내용
    instructions = Column(Text)  # 작성 안내
    required_fields = Column(JSON)  # 필수 입력 필드
    optional_fields = Column(JSON)  # 선택 입력 필드
    field_validations = Column(JSON)  # 필드 검증 규칙

    # 법률 정보
    applicable_laws = Column(JSON)  # 적용 법률
    legal_requirements = Column(JSON)  # 법적 요구사항
    disclaimers = Column(Text)  # 면책 조항
    warnings = Column(JSON)  # 주의사항

    # 버전 관리
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)  # 프리미엄 템플릿 여부

    # 메타데이터
    tags = Column(JSON)  # 태그
    keywords = Column(JSON)  # 검색 키워드
    difficulty_level = Column(String(20))  # easy, medium, hard
    estimated_time = Column(Integer)  # 예상 작성 시간 (분)

    # 사용 통계
    usage_count = Column(Integer, default=0)
    rating = Column(String(10))  # 평점
    review_count = Column(Integer, default=0)

    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_reviewed_at = Column(DateTime(timezone=True))  # 마지막 법률 검토일

    # 관계
    documents = relationship("Document", back_populates="template")

    def __repr__(self):
        return f"<Template(id={self.id}, name={self.name}, category={self.category.value})>"


class TemplateField(Base):
    """템플릿 필드 정의"""
    __tablename__ = "template_fields"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, index=True)
    field_name = Column(String(100), nullable=False)  # 필드명
    field_label = Column(String(255))  # 표시 라벨
    field_type = Column(String(50))  # text, number, date, select, checkbox
    field_format = Column(String(100))  # 형식 (예: YYYY-MM-DD)

    # 필드 속성
    is_required = Column(Boolean, default=False)
    default_value = Column(String(500))
    placeholder = Column(String(500))
    help_text = Column(Text)

    # 검증 규칙
    validation_rules = Column(JSON)  # min, max, pattern 등
    options = Column(JSON)  # select, checkbox의 옵션

    # 조건부 표시
    conditional_display = Column(JSON)  # 다른 필드 값에 따른 표시 조건

    # 순서
    display_order = Column(Integer)
    group_name = Column(String(100))  # 필드 그룹

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TemplateExample(Base):
    """템플릿 예시"""
    __tablename__ = "template_examples"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, index=True)
    title = Column(String(255))  # 예시 제목
    description = Column(Text)  # 예시 설명
    example_data = Column(JSON)  # 예시 데이터
    example_output = Column(Text)  # 예시 결과
    use_case = Column(Text)  # 사용 사례
    is_featured = Column(Boolean, default=False)  # 대표 예시 여부

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TemplateClauses(Base):
    """템플릿 조항 라이브러리"""
    __tablename__ = "template_clauses"

    id = Column(Integer, primary_key=True, index=True)
    clause_name = Column(String(255), nullable=False)  # 조항명
    clause_category = Column(String(100))  # 조항 카테고리
    clause_content = Column(Text, nullable=False)  # 조항 내용
    applicable_templates = Column(JSON)  # 적용 가능한 템플릿
    legal_basis = Column(JSON)  # 법적 근거
    variations = Column(JSON)  # 변형 조항

    # 사용 조건
    conditions = Column(JSON)  # 사용 조건
    incompatible_clauses = Column(JSON)  # 양립 불가능한 조항

    # 메타데이터
    tags = Column(JSON)
    is_mandatory = Column(Boolean, default=False)  # 필수 조항 여부
    is_recommended = Column(Boolean, default=False)  # 추천 조항 여부

    # 통계
    usage_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())