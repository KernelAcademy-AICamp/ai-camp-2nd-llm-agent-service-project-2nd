"""
Drafts API endpoints
GET /cases/{case_id}/drafts - List drafts for a case
POST /cases/{case_id}/drafts - Create a new draft
GET /cases/{case_id}/drafts/{draft_id} - Get draft detail
PATCH /cases/{case_id}/drafts/{draft_id} - Update draft
POST /cases/{case_id}/drafts/{draft_id}/export - Export draft to DOCX/PDF
"""

from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.db.session import get_db
from app.db.schemas import (
    DraftCreate,
    DraftUpdate,
    DraftResponse,
    DraftListItem,
    DraftListResponse,
    DraftExportFormat,
    AuditAction
)
from app.services.draft_service import DraftService
from app.core.dependencies import get_current_user_id
from app.utils.audit import log_audit_event


router = APIRouter()


@router.get("", response_model=DraftListResponse, status_code=status.HTTP_200_OK)
def list_drafts(
    case_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all drafts for a case

    **Path Parameters:**
    - case_id: Case ID

    **Response:**
    - 200: List of draft summaries
    - drafts: List of DraftListItem
    - total: Total number of drafts

    **Errors:**
    - 401: Not authenticated
    - 403: User does not have access to case
    - 404: Case not found

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the case
    """
    draft_service = DraftService(db)
    drafts = draft_service.list_drafts(case_id, user_id)
    return DraftListResponse(drafts=drafts, total=len(drafts))


@router.post("", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
def create_draft(
    case_id: str,
    draft_data: DraftCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new draft document

    **Path Parameters:**
    - case_id: Case ID

    **Request Body:**
    - title: Draft title (required)
    - document_type: Type of document (complaint/motion/brief/response)
    - content: Structured content with header, sections, citations, footer

    **Response:**
    - 201: Draft created successfully
    - Returns full draft with id, version, timestamps

    **Errors:**
    - 401: Not authenticated
    - 403: User does not have write access to case
    - 404: Case not found

    **Authentication:**
    - Requires valid JWT token
    - User must have write access to the case (owner or member)
    """
    draft_service = DraftService(db)
    draft = draft_service.create_draft(case_id, draft_data, user_id)

    # Log audit event
    log_audit_event(
        db=db,
        user_id=user_id,
        action=AuditAction.GENERATE_DRAFT,
        object_id=draft.id
    )

    return draft


@router.get("/{draft_id}", response_model=DraftResponse, status_code=status.HTTP_200_OK)
def get_draft(
    case_id: str,
    draft_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get draft detail by ID

    **Path Parameters:**
    - case_id: Case ID
    - draft_id: Draft ID

    **Response:**
    - 200: Draft detail with full content
    - id, case_id, title, document_type, content, version, status, timestamps

    **Errors:**
    - 401: Not authenticated
    - 403: User does not have access to case
    - 404: Case or draft not found

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the case
    """
    draft_service = DraftService(db)
    return draft_service.get_draft(case_id, draft_id, user_id)


@router.patch("/{draft_id}", response_model=DraftResponse, status_code=status.HTTP_200_OK)
def update_draft(
    case_id: str,
    draft_id: str,
    update_data: DraftUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update an existing draft

    **Path Parameters:**
    - case_id: Case ID
    - draft_id: Draft ID

    **Request Body (all optional):**
    - title: New title
    - document_type: New document type
    - content: Updated content (increments version)
    - status: New status (draft/reviewed/exported)

    **Response:**
    - 200: Updated draft data
    - Version is incremented when content changes

    **Errors:**
    - 401: Not authenticated
    - 403: User does not have write access to case
    - 404: Case or draft not found

    **Authentication:**
    - Requires valid JWT token
    - User must have write access to the case (owner or member)

    **Notes:**
    - Content changes increment the version number
    - Status can be updated independently of content
    - Partial updates are supported (only provided fields are changed)
    """
    draft_service = DraftService(db)
    draft = draft_service.update_draft(case_id, draft_id, update_data, user_id)

    # Log audit event
    log_audit_event(
        db=db,
        user_id=user_id,
        action=AuditAction.UPDATE_DRAFT,
        object_id=draft_id
    )

    return draft


@router.post("/{draft_id}/export")
def export_draft(
    case_id: str,
    draft_id: str,
    format: DraftExportFormat = Query(DraftExportFormat.DOCX, description="Export format (docx or pdf)"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Export a specific draft as DOCX or PDF

    **Path Parameters:**
    - case_id: Case ID
    - draft_id: Draft ID

    **Query Parameters:**
    - format: Export format - "docx" (default) or "pdf"

    **Response:**
    - 200: File download (StreamingResponse)
    - Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document (DOCX)
                   or application/pdf (PDF)
    - Content-Disposition: attachment; filename="draft_*.docx"

    **Errors:**
    - 401: Not authenticated
    - 403: User does not have access to case
    - 404: Case or draft not found
    - 422: Missing dependencies (python-docx or weasyprint)

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the case

    **Notes:**
    - Uses saved draft content (not regenerated)
    - Marks draft status as 'exported' after successful export
    - Supports Korean legal document formatting
    """
    draft_service = DraftService(db)

    # Get the saved draft
    draft = draft_service.get_draft(case_id, draft_id, user_id)

    # Import generators
    from app.utils.docx_generator import generate_docx
    from app.utils.pdf_generator import generate_pdf

    # Generate file based on format
    if format == DraftExportFormat.DOCX:
        file_bytes = generate_docx(draft.content, draft.document_type.value)
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ext = "docx"
    else:
        file_bytes = generate_pdf(draft.content, draft.document_type.value)
        content_type = "application/pdf"
        ext = "pdf"

    # Update draft status to exported
    from app.db.schemas import DraftDocumentStatus
    draft_service.update_draft(
        case_id,
        draft_id,
        DraftUpdate(status=DraftDocumentStatus.EXPORTED),
        user_id
    )

    # Log audit event
    log_audit_event(
        db=db,
        user_id=user_id,
        action=AuditAction.EXPORT_DRAFT,
        object_id=draft_id
    )

    # Generate filename
    safe_title = draft.title.replace(" ", "_")[:30]
    filename = f"{safe_title}_v{draft.version}.{ext}"

    return StreamingResponse(
        BytesIO(file_bytes),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
