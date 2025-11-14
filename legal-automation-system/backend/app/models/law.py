"""
법률 조항 데이터베이스 모델
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database.base import Base


class Law(Base):
    """법률 조항 모델"""
    __tablename__ = "laws"

    # 기본 정보
    id = Column(Integer, primary_key=True, index=True)
    law_id = Column(String(50), unique=True, index=True)  # 법령 ID
    law_name = Column(String(255), nullable=False, index=True)  # 법령명
    law_name_abbr = Column(String(100))  # 법령 약칭

    # 분류
    category = Column(String(100), index=True)  # 대분류 (민법, 형법 등)
    subcategory = Column(String(100))  # 중분류
    law_type = Column(String(50))  # 법령 종류 (법률, 시행령, 시행규칙 등)

    # 조항 정보
    article_number = Column(String(50))  # 조항 번호 (예: 제1조)
    article_title = Column(String(255))  # 조항 제목
    article_content = Column(Text, nullable=False)  # 조항 내용
    article_paragraph = Column(Integer)  # 항
    article_subparagraph = Column(Integer)  # 호
    article_item = Column(Integer)  # 목

    # 메타데이터
    enforcement_date = Column(DateTime)  # 시행일
    revision_date = Column(DateTime)  # 개정일
    abolition_date = Column(DateTime)  # 폐지일
    is_active = Column(Boolean, default=True)  # 현행 여부

    # 관련 정보
    related_laws = Column(JSON)  # 관련 법령 목록
    precedents = Column(JSON)  # 관련 판례
    interpretations = Column(JSON)  # 법령 해석례

    # 검색 최적화
    keywords = Column(JSON)  # 키워드 목록
    search_text = Column(Text)  # 전문 검색용 텍스트
    importance_score = Column(Float, default=0.5)  # 중요도 점수

    # 벡터 임베딩
    embedding_id = Column(String(100))  # Pinecone 벡터 ID
    embedding_version = Column(String(20))  # 임베딩 버전

    # 출처
    source_url = Column(String(500))  # 원본 URL
    source_file = Column(String(500))  # 원본 파일 경로

    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_crawled_at = Column(DateTime(timezone=True))  # 마지막 크롤링 시간

    # 통계
    view_count = Column(Integer, default=0)  # 조회수
    reference_count = Column(Integer, default=0)  # 참조 횟수

    def __repr__(self):
        return f"<Law(id={self.id}, name={self.law_name}, article={self.article_number})>"


class LawCategory(Base):
    """법률 카테고리"""
    __tablename__ = "law_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    parent_id = Column(Integer)  # 상위 카테고리
    description = Column(Text)
    icon = Column(String(50))
    display_order = Column(Integer)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class LawCase(Base):
    """판례 정보"""
    __tablename__ = "law_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(100), unique=True, index=True)  # 사건번호
    court_name = Column(String(100))  # 법원명
    case_type = Column(String(50))  # 사건 유형
    judgment_date = Column(DateTime)  # 판결일

    # 내용
    title = Column(String(500))  # 판례 제목
    summary = Column(Text)  # 판결 요지
    full_text = Column(Text)  # 전문
    decision = Column(String(100))  # 판결 (원고승, 피고승 등)

    # 관련 법령
    related_laws = Column(JSON)  # 관련 법령 목록
    keywords = Column(JSON)  # 키워드

    # 벡터 임베딩
    embedding_id = Column(String(100))

    # 출처
    source_url = Column(String(500))

    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 통계
    view_count = Column(Integer, default=0)
    reference_count = Column(Integer, default=0)


class LawInterpretation(Base):
    """법령 해석례"""
    __tablename__ = "law_interpretations"

    id = Column(Integer, primary_key=True, index=True)
    interpretation_number = Column(String(100), unique=True)  # 해석례 번호
    requesting_agency = Column(String(200))  # 질의 기관
    responding_agency = Column(String(200))  # 회신 기관
    request_date = Column(DateTime)  # 질의일
    response_date = Column(DateTime)  # 회신일

    # 내용
    question = Column(Text)  # 질의 내용
    answer = Column(Text)  # 회신 내용
    summary = Column(Text)  # 요약

    # 관련 법령
    related_laws = Column(JSON)
    keywords = Column(JSON)

    # 벡터 임베딩
    embedding_id = Column(String(100))

    # 출처
    source_url = Column(String(500))

    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 통계
    view_count = Column(Integer, default=0)
    reference_count = Column(Integer, default=0)


class LawUpdate(Base):
    """법령 업데이트 이력"""
    __tablename__ = "law_updates"

    id = Column(Integer, primary_key=True, index=True)
    law_id = Column(String(50), index=True)
    update_type = Column(String(50))  # 제정, 개정, 폐지
    update_date = Column(DateTime)
    update_content = Column(Text)  # 변경 내용
    before_content = Column(Text)  # 변경 전
    after_content = Column(Text)  # 변경 후
    reason = Column(Text)  # 변경 사유

    created_at = Column(DateTime(timezone=True), server_default=func.now())