"""
Lawyer Portal API endpoints
003-role-based-ui Feature - US2, US3

GET /lawyer/dashboard - Dashboard statistics
GET /lawyer/cases - Case list with filters
POST /lawyer/cases/bulk-action - Bulk actions on cases
GET /lawyer/analytics - Extended analytics
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models import User, CaseStatus
from app.core.dependencies import require_internal_user
from app.services.lawyer_dashboard_service import LawyerDashboardService
from app.schemas.lawyer_dashboard import (
    LawyerDashboardResponse,
    LawyerAnalyticsResponse,
)

router = APIRouter()


@router.get("/dashboard", response_model=LawyerDashboardResponse)
def get_dashboard(
    current_user: User = Depends(require_internal_user),
    db: Session = Depends(get_db)
):
    """
    Get lawyer dashboard data.

    **Response:**
    - stats: Dashboard statistics (total cases, active, pending, completed)
    - recent_cases: List of recently updated cases
    - upcoming_events: List of upcoming calendar events

    **Authentication:**
    - Requires valid JWT token
    - Only internal users (lawyer, staff, admin) can access

    **Stats Cards:**
    - 전체 케이스: Total non-closed cases
    - 진행 중: Cases with OPEN status
    - 검토 대기: Cases with IN_PROGRESS status
    - 이번 달 완료: Cases closed this month
    """
    service = LawyerDashboardService(db)
    return service.get_dashboard_data(current_user.id)


@router.get("/analytics", response_model=LawyerAnalyticsResponse)
def get_analytics(
    current_user: User = Depends(require_internal_user),
    db: Session = Depends(get_db)
):
    """
    Get extended analytics for lawyer dashboard.

    **Response:**
    - status_distribution: Case count by status
    - monthly_stats: New/completed cases per month (last 6 months)
    - total_evidence: Total evidence items
    - avg_case_duration_days: Average case duration

    **Authentication:**
    - Requires valid JWT token
    - Only internal users (lawyer, staff, admin) can access
    """
    service = LawyerDashboardService(db)
    return service.get_analytics(current_user.id)
