"""
Case Schemas - Case CRUD, Members
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.db.models import CaseStatus, CaseMemberRole


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

    def to_role(self) -> CaseMemberRole:
        """Converts CaseMemberPermission to CaseMemberRole."""
        if self == CaseMemberPermission.READ_WRITE:
            return CaseMemberRole.MEMBER
        return CaseMemberRole.VIEWER


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
