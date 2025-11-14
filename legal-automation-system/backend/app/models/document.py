"""
법률 문서 데이터베이스 모델
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database.base import Base


class DocumentType(enum.Enum):
    """문서 타입"""
    CONTRACT = "contract"              # 계약서
    LAWSUIT = "lawsuit"                # 소장
    NOTICE = "notice"                  # 내용증명
    AGREEMENT = "agreement"            # 합의서
    APPLICATION = "application"        # 신청서
    PETITION = "petition"              # 탄원서
    CERTIFICATE = "certificate"        # 증명서
    OTHER = "other"                    # 기타


class DocumentStatus(enum.Enum):
    """문서 상태"""
    DRAFT = "draft"                    # 초안
    IN_REVIEW = "in_review"            # 검토중
    APPROVED = "approved"              # 승인됨
    REJECTED = "rejected"              # 거부됨
    FINALIZED = "finalized"            # 최종본
    ARCHIVED = "archived"              # 보관


class RiskLevel(enum.Enum):
    """리스크 레벨"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Document(Base):
    """법률 문서 모델"""
    __tablename__ = "documents"

    # 기본 정보
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)

    # 내용
    content = Column(Text, nullable=False)
    summary = Column(Text)
    metadata = Column(JSON)  # 추가 메타데이터

    # 템플릿 정보
    template_id = Column(Integer, ForeignKey("templates.id"))
    template_version = Column(String(20))

    # 사용자 정보
    user_id = Column(Integer, ForeignKey("users.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))

    # 리스크 분석
    risk_level = Column(Enum(RiskLevel))
    risk_score = Column(Float)
    risk_analysis = Column(JSON)  # 상세 리스크 분석 결과

    # 법률 참조
    referenced_laws = Column(JSON)  # 참조된 법률 조항 목록
    legal_review = Column(Text)     # 법률 검토 의견

    # 파일 정보
    file_path = Column(String(500))
    file_format = Column(String(10))  # pdf, docx, hwp 등
    file_size = Column(Integer)       # bytes

    # 버전 관리
    version = Column(Integer, default=1)
    parent_document_id = Column(Integer, ForeignKey("documents.id"))

    # 시간 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))

    # 추가 플래그
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=False)
    is_signed = Column(Boolean, default=False)

    # 관계
    template = relationship("Template", back_populates="documents")
    user = relationship("User", foreign_keys=[user_id], back_populates="documents")
    revisions = relationship("DocumentRevision", back_populates="document")
    signatures = relationship("DocumentSignature", back_populates="document")
    comments = relationship("DocumentComment", back_populates="document")

    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title}, type={self.document_type.value})>"


class DocumentRevision(Base):
    """문서 개정 이력"""
    __tablename__ = "document_revisions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    changes = Column(JSON)  # 변경 사항 상세
    changed_by = Column(Integer, ForeignKey("users.id"))
    change_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계
    document = relationship("Document", back_populates="revisions")
    user = relationship("User")


class DocumentSignature(Base):
    """문서 서명"""
    __tablename__ = "document_signatures"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    signer_id = Column(Integer, ForeignKey("users.id"))
    signature_type = Column(String(50))  # electronic, digital
    signature_data = Column(Text)  # 서명 데이터
    signed_at = Column(DateTime(timezone=True))
    ip_address = Column(String(45))
    verification_code = Column(String(100))
    is_verified = Column(Boolean, default=False)

    # 관계
    document = relationship("Document", back_populates="signatures")
    signer = relationship("User")


class DocumentComment(Base):
    """문서 코멘트"""
    __tablename__ = "document_comments"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    document = relationship("Document", back_populates="comments")
    user = relationship("User")