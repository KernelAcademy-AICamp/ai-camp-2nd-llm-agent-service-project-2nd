"""
Lawyer Dashboard Schemas
003-role-based-ui Feature - US2

Pydantic schemas for lawyer dashboard API responses.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class CaseStatusSummary(str, Enum):
    """Case status for dashboard display"""
    ACTIVE = "active"
    PENDING = "pending"
    COMPLETED = "completed"
    CLOSED = "closed"


class StatsCardData(BaseModel):
    """Individual stats card data"""
    label: str
    value: int
    change: Optional[int] = None  # Change from last period
    trend: Optional[str] = None  # "up", "down", "stable"


class RecentCaseItem(BaseModel):
    """Recent case item for dashboard"""
    id: str
    title: str
    status: str
    client_name: Optional[str] = None
    updated_at: datetime
    evidence_count: int = 0
    progress: int = 0  # 0-100 percentage


class CalendarEventItem(BaseModel):
    """Calendar event for dashboard preview"""
    id: str
    title: str
    event_type: str
    start_time: datetime
    case_id: Optional[str] = None
    case_title: Optional[str] = None


class LawyerDashboardStats(BaseModel):
    """Main dashboard statistics"""
    total_cases: int
    active_cases: int
    pending_review: int
    completed_this_month: int

    # Trends
    cases_change: Optional[int] = None  # New cases this week

    # Stats cards array for flexible display
    stats_cards: List[StatsCardData] = []


class LawyerDashboardResponse(BaseModel):
    """Complete lawyer dashboard response"""
    stats: LawyerDashboardStats
    recent_cases: List[RecentCaseItem]
    upcoming_events: List[CalendarEventItem]

    class Config:
        from_attributes = True


class CaseStatusDistribution(BaseModel):
    """Case status distribution for charts"""
    status: str
    count: int
    percentage: float


class MonthlyStats(BaseModel):
    """Monthly statistics for charts"""
    month: str  # "2024-01", "2024-02", etc.
    new_cases: int
    completed_cases: int
    evidence_uploaded: int


class LawyerAnalyticsResponse(BaseModel):
    """Extended analytics for lawyer dashboard"""
    status_distribution: List[CaseStatusDistribution]
    monthly_stats: List[MonthlyStats]
    total_evidence: int
    avg_case_duration_days: float
