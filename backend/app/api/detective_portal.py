"""
Detective Portal API Router
003-role-based-ui Feature - US5 (T085-T093)

API endpoints for detective portal including dashboard, case management,
field records, reports, and earnings.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user_id, require_role
from app.services.detective_portal_service import DetectivePortalService
from app.services.audit_log_service import AuditLogService
from app.schemas.detective_portal import (
    DetectiveDashboardResponse,
    CaseListResponse,
    CaseDetailResponse,
    AcceptRejectResponse,
    RejectRequest,
    FieldRecordRequest,
    CreateRecordResponse,
    ReportRequest,
    ReportResponse,
    EarningsResponse,
)

router = APIRouter(prefix="/detective", tags=["detective-portal"])


# ============== T086: Dashboard Endpoint ==============

@router.get("/dashboard", response_model=DetectiveDashboardResponse)
async def get_detective_dashboard(
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["detective"])),
):
    """
    Get detective dashboard data.

    Returns:
        - User name
        - Dashboard stats (active/pending/completed/earnings)
        - Active investigations list
        - Today's schedule
    """
    service = DetectivePortalService(db)
    try:
        return service.get_dashboard(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============== T087: Case List Endpoint ==============

@router.get("/cases", response_model=CaseListResponse)
async def get_detective_cases(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["detective"])),
):
    """
    Get list of detective's cases with optional filtering.

    Args:
        status: Filter by investigation status (pending/active/review/completed)
        page: Page number (default 1)
        limit: Items per page (default 20)

    Returns:
        List of cases assigned to the detective
    """
    service = DetectivePortalService(db)
    return service.get_cases(user_id, status=status, page=page, limit=limit)


# ============== T088: Case Detail Endpoint ==============

@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
async def get_detective_case_detail(
    case_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["detective"])),
):
    """
    Get detailed case information for detective.

    Args:
        case_id: Case ID to retrieve

    Returns:
        Detailed case information including records
    """
    service = DetectivePortalService(db)
    try:
        return service.get_case_detail(user_id, case_id)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this case"
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============== T089: Accept/Reject Endpoints ==============

@router.post("/cases/{case_id}/accept", response_model=AcceptRejectResponse)
async def accept_case(
    case_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["detective"])),
):
    """
    Accept an investigation case.

    Args:
        case_id: Case ID to accept

    Returns:
        Success response with new status
    """
    service = DetectivePortalService(db)
    audit_service = AuditLogService(db)

    try:
        result = service.accept_case(user_id, case_id)

        # T091: Audit logging
        audit_service.log_action(
            user_id=user_id,
            action="case_accept",
            resource_type="case",
            resource_id=case_id,
            details={"action": "accept"}
        )

        return result
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/cases/{case_id}/reject", response_model=AcceptRejectResponse)
async def reject_case(
    case_id: str,
    request: RejectRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["detective"])),
):
    """
    Reject an investigation case.

    Args:
        case_id: Case ID to reject
        request: Rejection reason

    Returns:
        Success response with reason
    """
    service = DetectivePortalService(db)
    audit_service = AuditLogService(db)

    try:
        result = service.reject_case(user_id, case_id, request.reason)

        # T091: Audit logging
        audit_service.log_action(
            user_id=user_id,
            action="case_reject",
            resource_type="case",
            resource_id=case_id,
            details={"reason": request.reason}
        )

        return result
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============== T090: Field Record Endpoint ==============

@router.post("/cases/{case_id}/records", response_model=CreateRecordResponse)
async def create_field_record(
    case_id: str,
    request: FieldRecordRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["detective"])),
):
    """
    Create a new field record for a case.

    Args:
        case_id: Case ID to add record to
        request: Record data (type, content, GPS, photo)

    Returns:
        Created record ID and success message
    """
    service = DetectivePortalService(db)
    audit_service = AuditLogService(db)

    try:
        result = service.create_field_record(
            detective_id=user_id,
            case_id=case_id,
            record_type=request.record_type,
            content=request.content,
            gps_lat=request.gps_lat,
            gps_lng=request.gps_lng,
            photo_url=request.photo_url
        )

        # T091: Audit logging
        audit_service.log_action(
            user_id=user_id,
            action="field_record_create",
            resource_type="investigation_record",
            resource_id=result.record_id,
            details={
                "case_id": case_id,
                "record_type": request.record_type.value,
                "has_gps": request.gps_lat is not None,
                "has_photo": request.photo_url is not None
            }
        )

        return result
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============== T092: Report Submission Endpoint ==============

@router.post("/cases/{case_id}/report", response_model=ReportResponse)
async def submit_report(
    case_id: str,
    request: ReportRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["detective"])),
):
    """
    Submit final investigation report for a case.

    Args:
        case_id: Case ID to submit report for
        request: Report data (summary, findings, conclusion, attachments)

    Returns:
        Report ID and success message
    """
    service = DetectivePortalService(db)
    audit_service = AuditLogService(db)

    try:
        result = service.submit_report(
            detective_id=user_id,
            case_id=case_id,
            summary=request.summary,
            findings=request.findings,
            conclusion=request.conclusion,
            attachments=request.attachments
        )

        # T091: Audit logging
        audit_service.log_action(
            user_id=user_id,
            action="report_submit",
            resource_type="investigation_report",
            resource_id=result.report_id,
            details={
                "case_id": case_id,
                "has_attachments": bool(request.attachments)
            }
        )

        return result
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============== T093: Earnings Endpoint ==============

@router.get("/earnings", response_model=EarningsResponse)
async def get_detective_earnings(
    period: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["detective"])),
):
    """
    Get detective's earnings and transaction history.

    Args:
        period: Optional filter (this_month, last_month, this_year)

    Returns:
        Earnings summary and transaction list
    """
    service = DetectivePortalService(db)
    return service.get_earnings(user_id, period=period)
