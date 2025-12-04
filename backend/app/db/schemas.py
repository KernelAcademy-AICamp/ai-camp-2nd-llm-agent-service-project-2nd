"""
Pydantic schemas (DTOs) for request/response validation
Separated from SQLAlchemy models per BACKEND_SERVICE_REPOSITORY_GUIDE.md
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.db.models import (
    UserRole, UserStatus, CaseStatus, CaseMemberRole,
    CalendarEventType, InvestigationRecordType, InvoiceStatus,
    PropertyType, PropertyOwner, ConfidenceLevel
)


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
    role: Optional[UserRole] = Field(
        default=None,
        description="User role (CLIENT, DETECTIVE only for self-signup; LAWYER, STAFF, ADMIN require invitation)"
    )


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


class DraftDocumentType(str, Enum):
    """Draft document type options"""
    COMPLAINT = "complaint"      # 소장
    MOTION = "motion"            # 신청서
    BRIEF = "brief"              # 준비서면
    RESPONSE = "response"        # 답변서


class DraftDocumentStatus(str, Enum):
    """Draft document status options"""
    DRAFT = "draft"              # Initial AI-generated
    REVIEWED = "reviewed"        # Lawyer has reviewed/edited
    EXPORTED = "exported"        # Has been exported at least once


class DraftContentSection(BaseModel):
    """Draft content section schema"""
    title: str
    content: str
    order: int


class DraftContent(BaseModel):
    """Structured draft content schema"""
    header: Optional[dict] = None
    sections: List[DraftContentSection] = Field(default_factory=list)
    citations: List[DraftCitation] = Field(default_factory=list)
    footer: Optional[dict] = None


class DraftCreate(BaseModel):
    """Draft creation request schema"""
    title: str = Field(..., min_length=1, max_length=255)
    document_type: DraftDocumentType = DraftDocumentType.BRIEF
    content: DraftContent


class DraftUpdate(BaseModel):
    """Draft update request schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    document_type: Optional[DraftDocumentType] = None
    content: Optional[DraftContent] = None
    status: Optional[DraftDocumentStatus] = None


class DraftResponse(BaseModel):
    """Draft response schema"""
    id: str
    case_id: str
    title: str
    document_type: DraftDocumentType
    content: dict  # Structured content with sections
    version: int
    status: DraftDocumentStatus
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DraftListItem(BaseModel):
    """Draft list item schema (summary)"""
    id: str
    case_id: str
    title: str
    document_type: DraftDocumentType
    version: int
    status: DraftDocumentStatus
    updated_at: datetime

    class Config:
        from_attributes = True


class DraftListResponse(BaseModel):
    """Draft list response schema"""
    drafts: List[DraftListItem]
    total: int


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
    EXPORT_DRAFT = "EXPORT_DRAFT"
    UPDATE_DRAFT = "UPDATE_DRAFT"


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


# ============================================
# Messaging Schemas
# ============================================
class MessageCreate(BaseModel):
    """Message creation request schema"""
    case_id: str
    recipient_id: str
    content: str = Field(..., min_length=1)
    attachments: Optional[List[str]] = None  # List of attachment URLs


class MessageOut(BaseModel):
    """Message output schema"""
    id: str
    case_id: str
    sender_id: str
    sender_name: Optional[str] = None
    recipient_id: str
    recipient_name: Optional[str] = None
    content: str
    attachments: Optional[List[str]] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Message list response schema"""
    messages: List[MessageOut]
    total: int
    unread_count: int = 0


class MarkMessageReadRequest(BaseModel):
    """Mark message as read request"""
    message_ids: List[str]


# ============================================
# Calendar Event Schemas
# ============================================
class CalendarEventCreate(BaseModel):
    """Calendar event creation request schema"""
    case_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    event_type: CalendarEventType = CalendarEventType.OTHER
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    reminder_minutes: int = 30


class CalendarEventUpdate(BaseModel):
    """Calendar event update request schema"""
    case_id: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    event_type: Optional[CalendarEventType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    reminder_minutes: Optional[int] = None


class CalendarEventOut(BaseModel):
    """Calendar event output schema"""
    id: str
    user_id: str
    case_id: Optional[str] = None
    case_title: Optional[str] = None  # Joined from Case table
    title: str
    description: Optional[str] = None
    event_type: CalendarEventType
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    reminder_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True


class CalendarEventListResponse(BaseModel):
    """Calendar event list response schema"""
    events: List[CalendarEventOut]
    total: int


# ============================================
# Investigation Record Schemas (Detective)
# ============================================
class InvestigationRecordCreate(BaseModel):
    """Investigation record creation request schema"""
    case_id: str
    record_type: InvestigationRecordType
    content: Optional[str] = None
    location_lat: Optional[str] = None
    location_lng: Optional[str] = None
    location_address: Optional[str] = None
    attachments: Optional[List[str]] = None
    recorded_at: datetime


class InvestigationRecordOut(BaseModel):
    """Investigation record output schema"""
    id: str
    case_id: str
    detective_id: str
    detective_name: Optional[str] = None
    record_type: InvestigationRecordType
    content: Optional[str] = None
    location_lat: Optional[str] = None
    location_lng: Optional[str] = None
    location_address: Optional[str] = None
    attachments: Optional[List[str]] = None
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InvestigationRecordListResponse(BaseModel):
    """Investigation record list response schema"""
    records: List[InvestigationRecordOut]
    total: int


class InvestigationReportSubmit(BaseModel):
    """Investigation report submission schema"""
    case_id: str
    summary: str = Field(..., min_length=10)
    findings: str
    evidence_ids: List[str] = Field(default_factory=list)
    recommendations: Optional[str] = None


# ============================================
# Invoice/Billing Schemas
# ============================================
class InvoiceCreate(BaseModel):
    """Invoice creation request schema"""
    case_id: str
    client_id: str
    amount: str = Field(..., description="Amount in KRW")
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class InvoiceUpdate(BaseModel):
    """Invoice update request schema"""
    amount: Optional[str] = None
    description: Optional[str] = None
    status: Optional[InvoiceStatus] = None
    due_date: Optional[datetime] = None


class InvoiceOut(BaseModel):
    """Invoice output schema"""
    id: str
    case_id: str
    case_title: Optional[str] = None
    client_id: str
    client_name: Optional[str] = None
    lawyer_id: str
    lawyer_name: Optional[str] = None
    amount: str
    description: Optional[str] = None
    status: InvoiceStatus
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Invoice list response schema"""
    invoices: List[InvoiceOut]
    total: int
    total_pending: str = "0"  # Total pending amount
    total_paid: str = "0"  # Total paid amount


class InvoicePaymentRequest(BaseModel):
    """Invoice payment request schema"""
    payment_method: str = Field(..., description="Payment method (card, bank, etc.)")
    payment_reference: Optional[str] = None


# ============================================
# Dashboard Schemas
# ============================================
class LawyerDashboardStats(BaseModel):
    """Lawyer dashboard statistics"""
    active_cases: int = 0
    pending_review: int = 0
    completed_cases: int = 0
    total_evidence: int = 0
    upcoming_events: int = 0
    unread_messages: int = 0


class ClientDashboardStats(BaseModel):
    """Client dashboard statistics"""
    total_cases: int = 0
    active_cases: int = 0
    pending_invoices: int = 0
    total_evidence: int = 0
    unread_messages: int = 0


class DetectiveDashboardStats(BaseModel):
    """Detective dashboard statistics"""
    assigned_cases: int = 0
    pending_cases: int = 0
    completed_cases: int = 0
    total_records: int = 0
    pending_reports: int = 0
    total_earnings: str = "0"  # Total earnings in KRW


# ============================================
# Role Permission Configuration
# ============================================
class PortalAccess(BaseModel):
    """Portal access configuration per role"""
    role: UserRole
    portal_path: str
    allowed_features: List[str]
    restricted_features: List[str] = Field(default_factory=list)


# Default role permissions configuration
ROLE_PORTAL_CONFIG = {
    UserRole.ADMIN: PortalAccess(
        role=UserRole.ADMIN,
        portal_path="/admin",
        allowed_features=["*"],  # All access
        restricted_features=[]
    ),
    UserRole.LAWYER: PortalAccess(
        role=UserRole.LAWYER,
        portal_path="/lawyer",
        allowed_features=[
            "dashboard", "cases", "evidence", "timeline", "draft",
            "clients", "investigators", "calendar", "billing", "messages"
        ],
        restricted_features=["admin"]
    ),
    UserRole.STAFF: PortalAccess(
        role=UserRole.STAFF,
        portal_path="/lawyer",  # Same as lawyer
        allowed_features=[
            "dashboard", "cases", "evidence", "timeline",
            "calendar", "messages"
        ],
        restricted_features=["admin", "billing", "draft"]
    ),
    UserRole.CLIENT: PortalAccess(
        role=UserRole.CLIENT,
        portal_path="/client",
        allowed_features=[
            "dashboard", "cases", "evidence", "timeline",
            "messages", "billing"
        ],
        restricted_features=["admin", "draft", "investigators"]
    ),
    UserRole.DETECTIVE: PortalAccess(
        role=UserRole.DETECTIVE,
        portal_path="/detective",
        allowed_features=[
            "dashboard", "cases", "field", "evidence", "report",
            "messages", "calendar", "earnings"
        ],
        restricted_features=["admin", "billing", "draft", "clients"]
    )
}


# ============================================
# Property Division Schemas (재산분할)
# ============================================
class PropertyCreate(BaseModel):
    """Property creation request schema"""
    property_type: PropertyType
    description: Optional[str] = Field(None, max_length=255)
    estimated_value: int = Field(..., ge=0, description="Estimated value in KRW")
    owner: PropertyOwner = PropertyOwner.JOINT
    is_premarital: bool = False
    acquisition_date: Optional[datetime] = None
    notes: Optional[str] = None


class PropertyUpdate(BaseModel):
    """Property update request schema"""
    property_type: Optional[PropertyType] = None
    description: Optional[str] = Field(None, max_length=255)
    estimated_value: Optional[int] = Field(None, ge=0)
    owner: Optional[PropertyOwner] = None
    is_premarital: Optional[bool] = None
    acquisition_date: Optional[datetime] = None
    notes: Optional[str] = None


class PropertyOut(BaseModel):
    """Property output schema"""
    id: str
    case_id: str
    property_type: PropertyType
    description: Optional[str] = None
    estimated_value: int
    owner: PropertyOwner
    is_premarital: bool
    acquisition_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    """Property list response schema"""
    properties: List[PropertyOut]
    total: int
    total_assets: int = 0  # Sum of all positive values
    total_debts: int = 0   # Sum of all debt values
    net_value: int = 0     # Assets - Debts


class PropertySummary(BaseModel):
    """Property summary for dashboard"""
    total_assets: int
    total_debts: int
    net_value: int
    by_type: dict  # {property_type: total_value}
    by_owner: dict  # {owner: total_value}


# ============================================
# Division Prediction Schemas (재산분할 예측)
# ============================================
class EvidenceImpact(BaseModel):
    """Single evidence impact on division"""
    evidence_id: str
    evidence_type: str  # 'chat_log', 'photo', etc.
    impact_type: str    # 'adultery', 'violence', etc.
    impact_percent: float
    direction: str      # 'plaintiff_favor', 'defendant_favor', 'neutral'
    reason: str
    confidence: float = 0.8


class SimilarCase(BaseModel):
    """Similar precedent case"""
    case_ref: str       # e.g., "서울가정법원 2023드합1234"
    similarity_score: float
    division_ratio: str  # e.g., "60:40"
    key_factors: List[str] = Field(default_factory=list)


class DivisionPredictionOut(BaseModel):
    """Division prediction output schema"""
    id: str
    case_id: str
    total_property_value: int
    total_debt_value: int
    net_value: int
    plaintiff_ratio: int  # 0-100
    defendant_ratio: int  # 0-100
    plaintiff_amount: int
    defendant_amount: int
    evidence_impacts: List[EvidenceImpact] = Field(default_factory=list)
    similar_cases: List[SimilarCase] = Field(default_factory=list)
    confidence_level: ConfidenceLevel
    version: int
    created_at: datetime
    updated_at: datetime
    disclaimer: str = "본 예측은 참고용이며 실제 판결과 다를 수 있습니다."

    class Config:
        from_attributes = True


class DivisionPredictionRequest(BaseModel):
    """Request to trigger new prediction calculation"""
    force_recalculate: bool = False  # Force recalculation even if recent prediction exists
