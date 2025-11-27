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
