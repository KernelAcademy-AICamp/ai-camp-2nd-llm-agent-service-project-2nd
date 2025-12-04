"""
SQLAlchemy ORM Models for LEH Backend
Database tables: users, cases, case_members, audit_logs
"""

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum


Base = declarative_base()


# ============================================
# Enums
# ============================================
class UserRole(str, enum.Enum):
    """User role enum"""
    LAWYER = "lawyer"
    STAFF = "staff"
    ADMIN = "admin"
    CLIENT = "client"          # 의뢰인
    DETECTIVE = "detective"    # 탐정/조사원


class UserStatus(str, enum.Enum):
    """User status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class CaseStatus(str, enum.Enum):
    """Case status enum"""
    ACTIVE = "active"
    CLOSED = "closed"


class CaseMemberRole(str, enum.Enum):
    """Case member role enum"""
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class CalendarEventType(str, enum.Enum):
    """Calendar event type enum"""
    COURT = "court"          # 재판/출석
    MEETING = "meeting"      # 상담/회의
    DEADLINE = "deadline"    # 마감
    INTERNAL = "internal"    # 내부 업무
    OTHER = "other"


class InvestigationRecordType(str, enum.Enum):
    """Investigation record type enum"""
    LOCATION = "location"    # 위치 기록
    PHOTO = "photo"          # 사진
    VIDEO = "video"          # 영상
    AUDIO = "audio"          # 음성 메모
    MEMO = "memo"            # 텍스트 메모
    EVIDENCE = "evidence"    # 증거 수집


class InvoiceStatus(str, enum.Enum):
    """Invoice status enum"""
    PENDING = "pending"      # 대기중
    PAID = "paid"            # 결제완료
    OVERDUE = "overdue"      # 연체
    CANCELLED = "cancelled"  # 취소


# ============================================
# Models
# ============================================
class User(Base):
    """
    User model - lawyers, staff, admins
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.LAWYER)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    created_cases = relationship("Case", back_populates="owner", foreign_keys="Case.created_by")
    case_memberships = relationship("CaseMember", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class Case(Base):
    """
    Case model - divorce cases
    """
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=lambda: f"case_{uuid.uuid4().hex[:12]}")
    title = Column(String, nullable=False)
    client_name = Column(String, nullable=True)  # 의뢰인 이름
    description = Column(String, nullable=True)
    status = Column(SQLEnum(CaseStatus), nullable=False, default=CaseStatus.ACTIVE)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="created_cases", foreign_keys=[created_by])
    members = relationship("CaseMember", back_populates="case")

    def __repr__(self):
        return f"<Case(id={self.id}, title={self.title}, status={self.status})>"


class CaseMember(Base):
    """
    Case membership model - user access to cases
    """
    __tablename__ = "case_members"

    case_id = Column(String, ForeignKey("cases.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    role = Column(SQLEnum(CaseMemberRole), nullable=False, default=CaseMemberRole.VIEWER)

    # Relationships
    case = relationship("Case", back_populates="members")
    user = relationship("User", back_populates="case_memberships")

    def __repr__(self):
        return f"<CaseMember(case_id={self.case_id}, user_id={self.user_id}, role={self.role})>"


class InviteToken(Base):
    """
    Invite token model - user invitation tokens
    """
    __tablename__ = "invite_tokens"

    id = Column(String, primary_key=True, default=lambda: f"invite_{uuid.uuid4().hex[:12]}")
    email = Column(String, nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.LAWYER)
    token = Column(String, unique=True, nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<InviteToken(id={self.id}, email={self.email}, token={self.token[:8]}...)>"


class PasswordResetToken(Base):
    """
    Password reset token model - for password recovery
    """
    __tablename__ = "password_reset_tokens"

    id = Column(String, primary_key=True, default=lambda: f"pwreset_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id})>"


class AuditLog(Base):
    """
    Audit log model - tracks all user actions
    """
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: f"audit_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., "VIEW_EVIDENCE", "CREATE_CASE"
    object_id = Column(String, nullable=True)  # evidence_id or case_id
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action={self.action})>"


class Message(Base):
    """
    Message model - real-time communication between users
    """
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(String, nullable=False)
    attachments = Column(String, nullable=True)  # JSON string of attachment URLs
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])

    def __repr__(self):
        return f"<Message(id={self.id}, sender_id={self.sender_id}, case_id={self.case_id})>"


class CalendarEvent(Base):
    """
    Calendar event model - for scheduling court dates, meetings, deadlines
    """
    __tablename__ = "calendar_events"

    id = Column(String, primary_key=True, default=lambda: f"event_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    event_type = Column(SQLEnum(CalendarEventType), nullable=False, default=CalendarEventType.OTHER)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    location = Column(String, nullable=True)
    reminder_minutes = Column(String, default="30")  # Minutes before event
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User")
    case = relationship("Case")

    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title={self.title}, type={self.event_type})>"


class InvestigationRecord(Base):
    """
    Investigation record model - for detective field recordings
    GPS tracking, photos, memos, evidence collection
    """
    __tablename__ = "investigation_records"

    id = Column(String, primary_key=True, default=lambda: f"inv_{uuid.uuid4().hex[:12]}")
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    detective_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    record_type = Column(SQLEnum(InvestigationRecordType), nullable=False)
    content = Column(String, nullable=True)  # Text content or description
    location_lat = Column(String, nullable=True)  # Latitude
    location_lng = Column(String, nullable=True)  # Longitude
    location_address = Column(String, nullable=True)
    attachments = Column(String, nullable=True)  # JSON string of file URLs
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    case = relationship("Case")
    detective = relationship("User")

    def __repr__(self):
        return f"<InvestigationRecord(id={self.id}, type={self.record_type}, case_id={self.case_id})>"


class Invoice(Base):
    """
    Invoice model - billing and payment tracking
    """
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=lambda: f"inv_{uuid.uuid4().hex[:12]}")
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    client_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    lawyer_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(String, nullable=False)  # Amount in KRW (stored as string for precision)
    description = Column(String, nullable=True)
    status = Column(SQLEnum(InvoiceStatus), nullable=False, default=InvoiceStatus.PENDING)
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    case = relationship("Case")
    client = relationship("User", foreign_keys=[client_id])
    lawyer = relationship("User", foreign_keys=[lawyer_id])

    def __repr__(self):
        return f"<Invoice(id={self.id}, amount={self.amount}, status={self.status})>"
