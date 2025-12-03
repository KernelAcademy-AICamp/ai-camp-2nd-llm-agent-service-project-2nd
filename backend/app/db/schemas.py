"""
Pydantic schemas (DTOs) for request/response validation
Separated from SQLAlchemy models per BACKEND_SERVICE_REPOSITORY_GUIDE.md
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.db.models import UserRole, UserStatus, CaseStatus, CaseMemberRole


# ============================================
# Auth Schemas
# ============================================
class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)


class SignupRequest(BaseModel):
    """Signup request schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)
    accept_terms: bool = Field(..., description="이용약관 동의 필수")


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
# Password Reset Schemas
# ============================================
class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema"""
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Forgot password response schema"""
    message: str


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    token: str
    new_password: str = Field(..., min_length=8)


class ResetPasswordResponse(BaseModel):
    """Reset password response schema"""
    message: str


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
# RBAC / Permission Schemas
# ============================================
class ResourcePermission(BaseModel):
    """Permission for a specific resource"""
    view: bool = False
    edit: bool = False
    delete: bool = False


class RolePermissions(BaseModel):
    """Complete permission set for a role"""
    role: UserRole
    cases: ResourcePermission
    evidence: ResourcePermission
    admin: ResourcePermission
    billing: ResourcePermission


class RolePermissionsResponse(BaseModel):
    """Response schema for GET /admin/roles"""
    roles: list[RolePermissions]


class UpdateRolePermissionsRequest(BaseModel):
    """Request schema for PUT /admin/roles/{role}/permissions"""
    cases: ResourcePermission
    evidence: ResourcePermission
    admin: ResourcePermission
    billing: ResourcePermission


# ============================================
# Case Schemas
# ============================================
class CaseCreate(BaseModel):
    """Case creation request schema"""
    title: str = Field(..., min_length=1, max_length=200)
    client_name: Optional[str] = Field(None, max_length=100)  # 의뢰인 이름
    description: Optional[str] = None


class CaseUpdate(BaseModel):
    """Case update request schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    client_name: Optional[str] = Field(None, max_length=100)  # 의뢰인 이름
    description: Optional[str] = None


class CaseOut(BaseModel):
    """Case output schema"""
    id: str
    title: str
    client_name: Optional[str] = None  # 의뢰인 이름
    description: Optional[str]
    status: CaseStatus
    created_by: str
    created_at: datetime
    updated_at: datetime

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
# Case Member Schemas
# ============================================
class CaseMemberPermission(str, Enum):
    """Case member permission level"""
    READ = "read"  # Viewer - can only view
    READ_WRITE = "read_write"  # Member - can view and edit


class CaseMemberAdd(BaseModel):
    """Schema for adding a member to a case"""
    user_id: str
    permission: CaseMemberPermission = Field(default=CaseMemberPermission.READ)


class CaseMemberOut(BaseModel):
    """Schema for case member output"""
    user_id: str
    name: str
    email: str
    permission: CaseMemberPermission
    role: CaseMemberRole  # Actual DB role (owner/member/viewer)

    class Config:
        from_attributes = True


class AddCaseMembersRequest(BaseModel):
    """Request schema for adding multiple members to a case"""
    members: List[CaseMemberAdd]


class CaseMembersListResponse(BaseModel):
    """Response schema for listing case members"""
    members: List[CaseMemberOut]
    total: int


# ============================================
# Evidence Schemas
# ============================================
class Article840Category(str, Enum):
    """
    민법 840조 이혼 사유 카테고리

    Korean Civil Code Article 840 - Grounds for Divorce
    """
    ADULTERY = "adultery"  # 제1호: 배우자의 부정행위
    DESERTION = "desertion"  # 제2호: 악의의 유기
    MISTREATMENT_BY_INLAWS = "mistreatment_by_inlaws"  # 제3호: 배우자 직계존속의 부당대우
    HARM_TO_OWN_PARENTS = "harm_to_own_parents"  # 제4호: 자기 직계존속 피해
    UNKNOWN_WHEREABOUTS = "unknown_whereabouts"  # 제5호: 생사불명 3년
    IRRECONCILABLE_DIFFERENCES = "irreconcilable_differences"  # 제6호: 혼인 지속 곤란사유
    GENERAL = "general"  # 일반 증거 (특정 조항에 해당하지 않음)


class Article840Tags(BaseModel):
    """Article 840 tagging result schema"""
    categories: list[Article840Category] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_keywords: list[str] = Field(default_factory=list)


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
    s3_key: str


class UploadCompleteRequest(BaseModel):
    """Upload complete request schema"""
    case_id: str
    evidence_temp_id: str
    s3_key: str
    file_size: int = 0  # File size in bytes
    note: Optional[str] = None


class UploadCompleteResponse(BaseModel):
    """Upload complete response schema"""
    evidence_id: str
    case_id: str
    filename: str
    s3_key: str
    status: str  # pending (waiting for AI processing)
    created_at: datetime


class EvidenceSummary(BaseModel):
    """Evidence summary schema (for list view)"""
    id: str
    case_id: str
    type: str  # text, image, audio, video, pdf
    filename: str
    size: int  # File size in bytes
    created_at: datetime
    status: str  # pending, processing, done, error
    ai_summary: Optional[str] = None  # AI-generated summary
    article_840_tags: Optional[Article840Tags] = None  # Article 840 tagging


class EvidenceListResponse(BaseModel):
    """Evidence list response wrapper (matches frontend expectation)"""
    evidence: list[EvidenceSummary]
    total: int


class EvidenceDetail(BaseModel):
    """Evidence detail schema (for detail view with AI analysis)"""
    id: str
    case_id: str
    type: str
    filename: str
    size: int  # File size in bytes
    s3_key: str
    content_type: str
    created_at: datetime
    status: str

    # AI analysis results (available when status="done")
    ai_summary: Optional[str] = None
    labels: Optional[list[str]] = None  # Mapped from article_840_tags.categories
    insights: Optional[list[str]] = None
    content: Optional[str] = None  # Full STT/OCR text
    speaker: Optional[str] = None  # For audio/video
    timestamp: Optional[datetime] = None  # Event timestamp in evidence
    qdrant_id: Optional[str] = None  # RAG index reference (Qdrant point ID)
    article_840_tags: Optional[Article840Tags] = None  # Article 840 tagging


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


class DraftExportFormat(str, Enum):
    """Draft export format options"""
    DOCX = "docx"
    PDF = "pdf"


# ============================================
# Audit Log Schemas
# ============================================
class AuditAction(str, Enum):
    """Audit action types"""
    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    SIGNUP = "SIGNUP"

    # Case actions
    CREATE_CASE = "CREATE_CASE"
    VIEW_CASE = "VIEW_CASE"
    UPDATE_CASE = "UPDATE_CASE"
    DELETE_CASE = "DELETE_CASE"

    # Evidence actions
    UPLOAD_EVIDENCE = "UPLOAD_EVIDENCE"
    VIEW_EVIDENCE = "VIEW_EVIDENCE"
    DELETE_EVIDENCE = "DELETE_EVIDENCE"

    # Admin actions
    INVITE_USER = "INVITE_USER"
    DELETE_USER = "DELETE_USER"
    UPDATE_PERMISSIONS = "UPDATE_PERMISSIONS"

    # Draft actions
    GENERATE_DRAFT = "GENERATE_DRAFT"


class AuditLogOut(BaseModel):
    """Audit log output schema"""
    id: str
    user_id: str
    user_email: Optional[str] = None  # Joined from User table
    user_name: Optional[str] = None  # Joined from User table
    action: str
    object_id: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogListRequest(BaseModel):
    """Audit log list request schema with filters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    actions: Optional[List[AuditAction]] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class AuditLogListResponse(BaseModel):
    """Audit log list response schema"""
    logs: List[AuditLogOut]
    total: int
    page: int
    page_size: int
    total_pages: int
