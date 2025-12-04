"""
Lawyer Portal API endpoints
003-role-based-ui Feature - US2, US3

GET /lawyer/dashboard - Dashboard statistics
GET /lawyer/cases - Case list with filters
GET /lawyer/cases/{case_id} - Case detail
POST /lawyer/cases/bulk-action - Bulk actions on cases
GET /lawyer/analytics - Extended analytics
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models import User, CaseStatus
from app.core.dependencies import require_internal_user
from app.services.lawyer_dashboard_service import LawyerDashboardService
from app.services.case_list_service import CaseListService
from app.schemas.lawyer_dashboard import (
    LawyerDashboardResponse,
    LawyerAnalyticsResponse,
)
from app.schemas.case_list import (
    CaseFilter,
    CaseListResponse,
    CaseSortField,
    SortOrder,
    BulkActionRequest,
    BulkActionResponse,
    CaseDetailResponse,
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


@router.get("/cases", response_model=CaseListResponse)
def get_cases(
    current_user: User = Depends(require_internal_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: CaseSortField = Query(CaseSortField.UPDATED_AT, description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    status: Optional[List[str]] = Query(None, description="Filter by status(es)"),
    search: Optional[str] = Query(None, description="Search in title, description, client name"),
    client_name: Optional[str] = Query(None, description="Filter by client name"),
):
    """
    Get paginated case list with filters.

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - sort_by: Sort field (updated_at, created_at, title, client_name, status)
    - sort_order: Sort direction (asc, desc)
    - status: Filter by status(es) - can be multiple
    - search: Search in title, description, client name
    - client_name: Filter by client name

    **Response:**
    - items: List of cases
    - total: Total count
    - page, page_size, total_pages: Pagination info
    - status_counts: Count per status for filter badges

    **Authentication:**
    - Requires valid JWT token
    - Only internal users (lawyer, staff, admin) can access
    """
    filters = CaseFilter(
        status=status,
        search=search,
        client_name=client_name,
    )

    service = CaseListService(db)
    return service.get_cases(
        user_id=current_user.id,
        filters=filters,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
def get_case_detail(
    case_id: str,
    current_user: User = Depends(require_internal_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed case information.

    **Path Parameters:**
    - case_id: Case ID

    **Response:**
    - Full case details including owner, members, evidence summary

    **Authentication:**
    - Requires valid JWT token
    - Only internal users (lawyer, staff, admin) can access
    - Must have access to the case (owner or member)
    """
    service = CaseListService(db)
    result = service.get_case_detail(current_user.id, case_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="케이스를 찾을 수 없거나 접근 권한이 없습니다."
        )

    return result


@router.post("/cases/bulk-action", response_model=BulkActionResponse)
def execute_bulk_action(
    request: BulkActionRequest,
    current_user: User = Depends(require_internal_user),
    db: Session = Depends(get_db),
):
    """
    Execute bulk action on multiple cases.

    **Request Body:**
    - case_ids: List of case IDs to act on (required)
    - action: Action type (request_ai_analysis, change_status, assign_member, export, delete)
    - params: Action-specific parameters (optional)

    **Action Types:**
    - request_ai_analysis: Queue AI analysis for selected cases
    - change_status: Change status (params: {"new_status": "..."})
    - assign_member: Assign user to cases (params: {"user_id": "..."})
    - export: Export cases to file
    - delete: Soft delete (close) cases

    **Response:**
    - action: Action performed
    - total_requested: Number of cases requested
    - successful: Number of successful operations
    - failed: Number of failed operations
    - results: Individual results per case

    **Authentication:**
    - Requires valid JWT token
    - Only internal users (lawyer, staff, admin) can access
    """
    service = CaseListService(db)
    return service.execute_bulk_action(
        user_id=current_user.id,
        case_ids=request.case_ids,
        action=request.action,
        params=request.params,
    )
