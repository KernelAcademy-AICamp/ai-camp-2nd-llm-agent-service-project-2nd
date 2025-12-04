"""
Detective Portal Schemas
Task T095 - US5 Implementation

Pydantic schemas for detective portal API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


# ============== Enums ==============


class InvestigationStatus(str, Enum):
    """Investigation status enum"""
    PENDING = "pending"
    ACTIVE = "active"
    REVIEW = "review"
    COMPLETED = "completed"


class RecordType(str, Enum):
    """Field record type enum"""
    OBSERVATION = "observation"
    PHOTO = "photo"
    NOTE = "note"
    VIDEO = "video"
    AUDIO = "audio"


class TransactionStatus(str, Enum):
    """Transaction status enum"""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ScheduleEventType(str, Enum):
    """Schedule event type enum"""
    FIELD = "field"
    MEETING = "meeting"
    DEADLINE = "deadline"
    OTHER = "other"


# ============== Dashboard Schemas ==============


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    active_investigations: int = Field(..., description="Number of active investigations")
    pending_requests: int = Field(..., description="Number of pending requests")
    completed_this_month: int = Field(..., description="Completed investigations this month")
    monthly_earnings: float = Field(..., description="Monthly earnings in KRW")


class InvestigationSummary(BaseModel):
    """Investigation summary for dashboard"""
    id: str
    title: str
    lawyer_name: Optional[str] = None
    status: InvestigationStatus
    deadline: Optional[str] = None
    record_count: int = 0


class ScheduleItem(BaseModel):
    """Schedule item for dashboard"""
    id: str
    time: str
    title: str
    type: ScheduleEventType = ScheduleEventType.OTHER


class DetectiveDashboardResponse(BaseModel):
    """Response for GET /detective/dashboard"""
    user_name: str
    stats: DashboardStats
    active_investigations: List[InvestigationSummary]
    today_schedule: List[ScheduleItem]


# ============== Cases Schemas ==============


class CaseListItem(BaseModel):
    """Case list item"""
    id: str
    title: str
    status: InvestigationStatus
    lawyer_name: Optional[str] = None
    client_name: Optional[str] = None
    deadline: Optional[str] = None
    record_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CaseListResponse(BaseModel):
    """Response for GET /detective/cases"""
    items: List[CaseListItem]
    total: int


class CaseDetailResponse(BaseModel):
    """Response for GET /detective/cases/{id}"""
    id: str
    title: str
    description: Optional[str] = None
    status: InvestigationStatus
    lawyer_name: Optional[str] = None
    lawyer_email: Optional[str] = None
    client_name: Optional[str] = None
    deadline: Optional[str] = None
    records: List["FieldRecordResponse"] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============== Actions Schemas ==============


class AcceptRejectResponse(BaseModel):
    """Response for accept/reject actions"""
    success: bool
    message: str
    case_id: str
    new_status: InvestigationStatus


class RejectRequest(BaseModel):
    """Request body for reject action"""
    reason: str = Field(..., min_length=1, description="Reason for rejection")


# ============== Records Schemas ==============


class FieldRecordRequest(BaseModel):
    """Request body for creating field record"""
    record_type: RecordType
    content: str = Field(..., min_length=1, description="Record content")
    gps_lat: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    gps_lng: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    photo_url: Optional[str] = None


class FieldRecordResponse(BaseModel):
    """Response for field record"""
    id: str
    record_type: RecordType
    content: str
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    photo_url: Optional[str] = None
    created_at: datetime


class CreateRecordResponse(BaseModel):
    """Response for POST /detective/cases/{id}/records"""
    success: bool
    record_id: str
    message: str


# ============== Report Schemas ==============


class ReportRequest(BaseModel):
    """Request body for submitting report"""
    summary: str = Field(..., min_length=1, description="Investigation summary")
    findings: str = Field(..., min_length=1, description="Key findings")
    conclusion: str = Field(..., min_length=1, description="Final conclusion")
    attachments: Optional[List[str]] = None


class ReportResponse(BaseModel):
    """Response for POST /detective/cases/{id}/report"""
    success: bool
    report_id: str
    message: str
    case_status: InvestigationStatus


# ============== Earnings Schemas ==============


class EarningsSummary(BaseModel):
    """Earnings summary"""
    total_earned: float = Field(..., description="Total earnings")
    pending_payment: float = Field(..., description="Pending payment amount")
    this_month: float = Field(..., description="This month earnings")


class Transaction(BaseModel):
    """Transaction record"""
    id: str
    case_id: Optional[str] = None
    case_title: Optional[str] = None
    amount: float
    status: TransactionStatus
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class EarningsResponse(BaseModel):
    """Response for GET /detective/earnings"""
    summary: EarningsSummary
    transactions: List[Transaction]


# Update forward references
CaseDetailResponse.model_rebuild()
