"""
Client Portal Schemas
003-role-based-ui Feature - US4 (T068)

Pydantic schemas for client portal API endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============== Progress Step Schema ==============

class ProgressStep(BaseModel):
    """Progress step for case visualization"""
    step: int = Field(..., description="Step number")
    title: str = Field(..., description="Step title")
    status: str = Field(..., description="completed | current | pending")
    date: Optional[str] = Field(None, description="Date of completion or status")


# ============== Dashboard Schemas ==============

class CaseSummary(BaseModel):
    """Summary of client's case for dashboard"""
    id: str = Field(..., description="Case ID")
    title: str = Field(..., description="Case title")
    status: str = Field(..., description="Case status")
    progress_percent: int = Field(0, ge=0, le=100, description="Progress percentage")
    lawyer_name: Optional[str] = Field(None, description="Assigned lawyer name")
    next_action: Optional[str] = Field(None, description="Next action required")
    updated_at: datetime = Field(..., description="Last update timestamp")


class LawyerInfo(BaseModel):
    """Lawyer contact information"""
    id: str = Field(..., description="Lawyer user ID")
    name: str = Field(..., description="Lawyer name")
    firm: Optional[str] = Field(None, description="Law firm name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: str = Field(..., description="Email address")


class RecentActivity(BaseModel):
    """Recent activity item"""
    id: str = Field(..., description="Activity ID")
    title: str = Field(..., description="Activity title")
    description: str = Field(..., description="Activity description")
    activity_type: str = Field(..., description="evidence | message | document | status")
    timestamp: datetime = Field(..., description="Activity timestamp")
    time_ago: str = Field(..., description="Human-readable time ago string")


class ClientDashboardResponse(BaseModel):
    """GET /client/dashboard response"""
    user_name: str = Field(..., description="Client's name")
    case_summary: Optional[CaseSummary] = Field(None, description="Current case summary")
    progress_steps: List[ProgressStep] = Field(default_factory=list, description="Progress steps")
    lawyer_info: Optional[LawyerInfo] = Field(None, description="Assigned lawyer info")
    recent_activities: List[RecentActivity] = Field(default_factory=list, description="Recent activities")
    unread_messages: int = Field(0, description="Count of unread messages")


# ============== Case List/Detail Schemas ==============

class ClientCaseListItem(BaseModel):
    """Case list item for client view"""
    id: str
    title: str
    status: str
    progress_percent: int = 0
    evidence_count: int = 0
    lawyer_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ClientCaseListResponse(BaseModel):
    """GET /client/cases response"""
    items: List[ClientCaseListItem] = Field(default_factory=list)
    total: int = Field(0)


class EvidenceSummary(BaseModel):
    """Evidence summary for case detail"""
    id: str
    file_name: str
    file_type: str  # image | audio | video | document
    uploaded_at: datetime
    status: str  # pending | processed | verified
    ai_labels: List[str] = Field(default_factory=list)


class ClientCaseDetailResponse(BaseModel):
    """GET /client/cases/{id} response"""
    id: str
    title: str
    description: Optional[str] = None
    status: str
    progress_percent: int = 0
    progress_steps: List[ProgressStep] = Field(default_factory=list)
    lawyer_info: Optional[LawyerInfo] = None
    evidence_list: List[EvidenceSummary] = Field(default_factory=list)
    evidence_count: int = 0
    recent_activities: List[RecentActivity] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    can_upload_evidence: bool = True


# ============== Evidence Upload Schemas ==============

class EvidenceUploadRequest(BaseModel):
    """POST /client/cases/{id}/evidence request"""
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    description: Optional[str] = Field(None, description="Evidence description")


class EvidenceUploadResponse(BaseModel):
    """POST /client/cases/{id}/evidence response"""
    evidence_id: str = Field(..., description="Created evidence ID")
    upload_url: str = Field(..., description="Presigned S3 upload URL")
    expires_in: int = Field(300, description="URL expiration in seconds")


class EvidenceConfirmRequest(BaseModel):
    """POST /client/cases/{id}/evidence/{evidence_id}/confirm request"""
    uploaded: bool = Field(True, description="Confirm upload completed")


class EvidenceConfirmResponse(BaseModel):
    """POST /client/cases/{id}/evidence/{evidence_id}/confirm response"""
    success: bool
    message: str
    evidence_id: str
