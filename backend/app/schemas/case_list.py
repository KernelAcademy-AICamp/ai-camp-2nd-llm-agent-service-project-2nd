"""
Case List Schemas
003-role-based-ui Feature - US3

Pydantic schemas for lawyer case list and bulk action APIs.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class CaseSortField(str, Enum):
    """Sortable fields for case list"""
    UPDATED_AT = "updated_at"
    CREATED_AT = "created_at"
    TITLE = "title"
    CLIENT_NAME = "client_name"
    STATUS = "status"


class SortOrder(str, Enum):
    """Sort order"""
    ASC = "asc"
    DESC = "desc"


class BulkActionType(str, Enum):
    """Types of bulk actions available"""
    REQUEST_AI_ANALYSIS = "request_ai_analysis"
    CHANGE_STATUS = "change_status"
    ASSIGN_MEMBER = "assign_member"
    EXPORT = "export"
    DELETE = "delete"


class CaseFilter(BaseModel):
    """Filter parameters for case list"""
    status: Optional[List[str]] = None  # Filter by status(es)
    client_name: Optional[str] = None  # Search by client name
    search: Optional[str] = None  # General search (title, description)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_evidence: Optional[bool] = None  # Filter by evidence presence
    assigned_to: Optional[str] = None  # Filter by assigned user


class CaseListItem(BaseModel):
    """Single case item in list view"""
    id: str
    title: str
    client_name: Optional[str] = None
    status: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Computed fields
    evidence_count: int = 0
    member_count: int = 0
    progress: int = 0  # 0-100 percentage
    days_since_update: int = 0

    # Related info
    owner_name: Optional[str] = None
    last_activity: Optional[str] = None

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    """Paginated case list response"""
    items: List[CaseListItem]
    total: int
    page: int
    page_size: int
    total_pages: int

    # Summary stats
    status_counts: dict = {}  # {"active": 5, "open": 3, ...}


class BulkActionRequest(BaseModel):
    """Request for bulk action on cases"""
    case_ids: List[str] = Field(..., min_length=1, description="List of case IDs")
    action: BulkActionType
    params: Optional[dict] = None  # Action-specific parameters
    # e.g., {"new_status": "in_progress"} for CHANGE_STATUS


class BulkActionResult(BaseModel):
    """Result for a single case in bulk action"""
    case_id: str
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class BulkActionResponse(BaseModel):
    """Response for bulk action"""
    action: BulkActionType
    total_requested: int
    successful: int
    failed: int
    results: List[BulkActionResult]


class CaseDetailResponse(BaseModel):
    """Detailed case response for case detail page"""
    id: str
    title: str
    client_name: Optional[str] = None
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Owner info
    owner_id: str
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None

    # Evidence summary
    evidence_count: int = 0
    evidence_summary: List[dict] = []  # [{type: "image", count: 5}, ...]

    # AI analysis
    ai_summary: Optional[str] = None
    ai_labels: List[str] = []

    # Timeline
    recent_activities: List[dict] = []

    # Members
    members: List[dict] = []

    class Config:
        from_attributes = True
