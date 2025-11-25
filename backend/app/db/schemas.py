"""
Pydantic schemas (DTOs) for request/response validation
Separated from SQLAlchemy models per BACKEND_SERVICE_REPOSITORY_GUIDE.md
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.db.models import UserRole, UserStatus, CaseStatus


# ============================================
# Auth Schemas
# ============================================
class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    """User output schema (without sensitive data)"""
    id: str
    email: str
    name: str
    role: UserRole
    status: UserStatus
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserOut


# ============================================
# User Management Schemas
# ============================================
class UserInviteRequest(BaseModel):
    """User invitation request schema"""
    email: EmailStr
    role: UserRole = Field(default=UserRole.LAWYER)


class InviteResponse(BaseModel):
    """Invite token response schema"""
    invite_token: str
    invite_url: str
    email: str
    role: UserRole
    expires_at: datetime


class UserListResponse(BaseModel):
    """User list response schema"""
    users: list[UserOut]
    total: int


# ============================================
# Case Schemas
# ============================================
class CaseCreate(BaseModel):
    """Case creation request schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class CaseOut(BaseModel):
    """Case output schema"""
    id: str
    title: str
    description: Optional[str]
    status: CaseStatus
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class CaseSummary(BaseModel):
    """Case summary for list view"""
    id: str
    title: str
    status: CaseStatus
    updated_at: datetime
    evidence_count: int = 0
    draft_status: str = "none"  # none | partial | ready


# ============================================
# Evidence Schemas
# ============================================
class PresignedUrlRequest(BaseModel):
    """Presigned URL request schema"""
    case_id: str
    filename: str
    content_type: str


class PresignedUrlResponse(BaseModel):
    """Presigned URL response schema"""
    upload_url: str
    fields: dict
    evidence_temp_id: str


class EvidenceSummary(BaseModel):
    """Evidence summary schema (for list view)"""
    id: str
    case_id: str
    type: str  # text, image, audio, video, pdf
    filename: str
    created_at: datetime
    status: str  # pending, processing, done, error


class EvidenceDetail(BaseModel):
    """Evidence detail schema (for detail view with AI analysis)"""
    id: str
    case_id: str
    type: str
    filename: str
    s3_key: str
    content_type: str
    created_at: datetime
    status: str

    # AI analysis results (available when status="done")
    ai_summary: Optional[str] = None
    labels: Optional[list[str]] = None
    insights: Optional[list[str]] = None
    content: Optional[str] = None  # Full STT/OCR text
    speaker: Optional[str] = None  # For audio/video
    timestamp: Optional[datetime] = None  # Event timestamp in evidence
    opensearch_id: Optional[str] = None  # RAG index reference


# ============================================
# Draft Schemas
# ============================================
class DraftPreviewRequest(BaseModel):
    """Draft preview request schema"""
    sections: list[str] = Field(default=["청구취지", "청구원인"])
    language: str = "ko"
    style: str = "법원 제출용_표준"


class DraftCitation(BaseModel):
    """Draft citation schema"""
    evidence_id: str
    snippet: str
    labels: list[str]


class DraftPreviewResponse(BaseModel):
    """Draft preview response schema"""
    case_id: str
    draft_text: str
    citations: list[DraftCitation]
    generated_at: datetime
