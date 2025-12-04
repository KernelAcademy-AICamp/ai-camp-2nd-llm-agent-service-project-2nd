"""
Client Portal API Router
003-role-based-ui Feature - US4 (T061-T066)

API endpoints for client portal including dashboard, case viewing, and evidence upload.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user_id, require_role
from app.services.client_portal_service import ClientPortalService
from app.schemas.client_portal import (
    ClientDashboardResponse,
    ClientCaseListResponse,
    ClientCaseDetailResponse,
    EvidenceUploadRequest,
    EvidenceUploadResponse,
    EvidenceConfirmRequest,
    EvidenceConfirmResponse,
)

router = APIRouter(prefix="/client", tags=["client-portal"])


# ============== T062: Dashboard Endpoint ==============

@router.get("/dashboard", response_model=ClientDashboardResponse)
async def get_client_dashboard(
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["client"])),
):
    """
    Get client dashboard data.

    Returns:
        - User name and greeting
        - Current case summary with progress
        - Progress steps visualization
        - Assigned lawyer contact info
        - Recent activities
        - Unread message count
    """
    service = ClientPortalService(db)
    try:
        return service.get_dashboard(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============== T063: Case List Endpoint ==============

@router.get("/cases", response_model=ClientCaseListResponse)
async def get_client_cases(
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["client"])),
):
    """
    Get list of client's cases.

    Returns list of cases where the client is a member.
    """
    service = ClientPortalService(db)
    return service.get_case_list(user_id)


# ============== T064: Case Detail Endpoint ==============

@router.get("/cases/{case_id}", response_model=ClientCaseDetailResponse)
async def get_client_case_detail(
    case_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["client"])),
):
    """
    Get detailed case information.

    Args:
        case_id: Case ID to retrieve

    Returns:
        Detailed case information including:
        - Case metadata and status
        - Progress steps
        - Lawyer info
        - Evidence list
        - Recent activities
    """
    service = ClientPortalService(db)
    try:
        return service.get_case_detail(user_id, case_id)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this case"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ============== T065: Evidence Upload Endpoint ==============

@router.post("/cases/{case_id}/evidence", response_model=EvidenceUploadResponse)
async def request_evidence_upload(
    case_id: str,
    request: EvidenceUploadRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["client"])),
):
    """
    Request presigned URL for evidence upload.

    Args:
        case_id: Case ID to upload evidence to
        request: Upload request with file metadata

    Returns:
        Evidence ID and presigned S3 upload URL

    Note:
        - File size limit: 100MB
        - URL expires in 5 minutes
        - Evidence is marked as 'pending' until confirmed
    """
    # Validate file size (100MB limit)
    max_size = 100 * 1024 * 1024  # 100MB
    if request.file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds limit of {max_size // (1024*1024)}MB"
        )

    service = ClientPortalService(db)
    try:
        response = service.request_evidence_upload(
            user_id=user_id,
            case_id=case_id,
            file_name=request.file_name,
            file_type=request.file_type,
            file_size=request.file_size,
            description=request.description,
        )

        # T066: Audit logging for evidence upload
        service.log_evidence_upload(
            user_id=user_id,
            case_id=case_id,
            evidence_id=response.evidence_id,
            file_name=request.file_name,
        )

        return response

    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this case"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/cases/{case_id}/evidence/{evidence_id}/confirm", response_model=EvidenceConfirmResponse)
async def confirm_evidence_upload(
    case_id: str,
    evidence_id: str,
    request: EvidenceConfirmRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["client"])),
):
    """
    Confirm evidence upload completion.

    Call this after successfully uploading to S3 to mark
    the evidence as ready for processing.
    """
    from app.db.models import Evidence

    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()

    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found"
        )

    if evidence.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evidence does not belong to this case"
        )

    if evidence.uploaded_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to confirm this upload"
        )

    if request.uploaded:
        evidence.status = "uploaded"
        db.commit()

        return EvidenceConfirmResponse(
            success=True,
            message="Evidence upload confirmed. Processing will begin shortly.",
            evidence_id=evidence_id,
        )
    else:
        # Upload was cancelled, remove the pending record
        db.delete(evidence)
        db.commit()

        return EvidenceConfirmResponse(
            success=True,
            message="Upload cancelled",
            evidence_id=evidence_id,
        )
