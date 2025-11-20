"""
Evidence API endpoints
POST /evidence/presigned-url - Generate S3 presigned upload URL
GET /evidence/{evidence_id} - Get evidence detail with AI analysis

Note: GET /cases/{case_id}/evidence is in cases.py (follows REST resource nesting)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.schemas import (
    PresignedUrlRequest,
    PresignedUrlResponse,
    EvidenceDetail
)
from app.services.evidence_service import EvidenceService
from app.core.dependencies import get_current_user_id


router = APIRouter()


@router.post("/presigned-url", response_model=PresignedUrlResponse, status_code=status.HTTP_200_OK)
def generate_presigned_upload_url(
    request: PresignedUrlRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Generate S3 presigned URL for evidence file upload

    **Request Body:**
    - case_id: Case ID (required)
    - filename: Original filename (required)
    - content_type: MIME type (required)

    **Response:**
    - upload_url: S3 presigned POST URL
    - fields: Form fields for multipart upload
    - evidence_temp_id: Temporary evidence ID

    **Errors:**
    - 401: Not authenticated
    - 403: User does not have access to case
    - 404: Case not found

    **Security:**
    - Requires valid JWT token
    - User must be a member of the case
    - Presigned URL expires in 5 minutes max
    - Direct upload to S3 (no proxy through backend)

    **Usage:**
    Frontend should use the returned upload_url and fields to POST
    the file directly to S3 using multipart/form-data.
    """
    evidence_service = EvidenceService(db)
    return evidence_service.generate_upload_presigned_url(request, user_id)


@router.get("/{evidence_id}", response_model=EvidenceDetail, status_code=status.HTTP_200_OK)
def get_evidence_detail(
    evidence_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get detailed evidence metadata with AI analysis results

    **Path Parameters:**
    - evidence_id: Evidence ID

    **Response:**
    - Complete evidence metadata including:
      - Basic info: id, case_id, type, filename, s3_key
      - AI analysis: ai_summary, labels, insights, content (STT/OCR)
      - Timestamps: created_at, timestamp (event time in evidence)

    **Errors:**
    - 401: Not authenticated
    - 403: User does not have access to case
    - 404: Evidence not found

    **Security:**
    - Requires valid JWT token
    - User must be a member of the case that owns this evidence

    **Notes:**
    - AI analysis fields (ai_summary, labels, insights, content) are available
      only when status="done" (AI Worker processing completed)
    - For pending/processing evidence, these fields will be null
    - Full text content (STT/OCR) is included for display and manual review
    """
    evidence_service = EvidenceService(db)
    return evidence_service.get_evidence_detail(evidence_id, user_id)
