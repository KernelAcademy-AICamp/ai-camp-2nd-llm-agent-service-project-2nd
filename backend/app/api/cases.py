"""
Cases API endpoints
POST /cases - Create new case
GET /cases - List cases for current user
GET /cases/{id} - Get case detail
GET /cases/{id}/evidence - List evidence for a case
POST /cases/{id}/draft-preview - Generate draft preview
PUT /cases/{id} - Update case
DELETE /cases/{id} - Soft delete case
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.schemas import (
    CaseCreate,
    CaseOut,
    EvidenceSummary,
    DraftPreviewRequest,
    DraftPreviewResponse,
    Article840Category
)
from app.services.case_service import CaseService
from app.services.evidence_service import EvidenceService
from app.services.draft_service import DraftService
from app.core.dependencies import get_current_user_id


router = APIRouter()


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    case_data: CaseCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new case

    **Request Body:**
    - title: Case title (required)
    - description: Case description (optional)

    **Response:**
    - 201: Case created successfully
    - id, title, description, status, created_by, created_at

    **Authentication:**
    - Requires valid JWT token
    - Creator is automatically added as case owner
    """
    case_service = CaseService(db)
    return case_service.create_case(case_data, user_id)


@router.get("", response_model=List[CaseOut])
def list_cases(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all cases accessible by current user

    **Response:**
    - 200: List of cases (may be empty)
    - Only returns cases where user is a member (owner, member, or viewer)

    **Authentication:**
    - Requires valid JWT token
    """
    case_service = CaseService(db)
    return case_service.get_cases_for_user(user_id)


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get case detail by ID

    **Path Parameters:**
    - case_id: Case ID

    **Response:**
    - 200: Case detail
    - 403: User does not have access to this case
    - 404: Case not found

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the case
    """
    case_service = CaseService(db)
    return case_service.get_case_by_id(case_id, user_id)


@router.get("/{case_id}/evidence", response_model=List[EvidenceSummary])
def list_case_evidence(
    case_id: str,
    categories: Optional[List[Article840Category]] = Query(None, description="Filter by Article 840 categories"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get list of all evidence for a case

    **Path Parameters:**
    - case_id: Case ID

    **Query Parameters:**
    - categories: Filter by Article 840 categories (optional, multiple allowed)
      - adultery: 배우자의 부정행위
      - desertion: 악의의 유기
      - mistreatment_by_inlaws: 배우자 직계존속의 부당대우
      - harm_to_own_parents: 자기 직계존속 피해
      - unknown_whereabouts: 생사불명 3년
      - irreconcilable_differences: 혼인 지속 곤란사유
      - general: 일반 증거

    **Response:**
    - 200: List of evidence summary (may be empty)
    - Each item contains: id, type, filename, status, created_at, article_840_tags

    **Errors:**
    - 401: Not authenticated
    - 403: User does not have access to case
    - 404: Case not found

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the case

    **Notes:**
    - Returns evidence in reverse chronological order (newest first)
    - Only returns metadata, not full file content
    - AI analysis results (including article_840_tags) available when status="done"
    - Filtering by categories returns only evidence tagged with at least one of the specified categories
    """
    evidence_service = EvidenceService(db)
    return evidence_service.get_evidence_list(case_id, user_id, categories=categories)


@router.post("/{case_id}/draft-preview", response_model=DraftPreviewResponse)
def generate_draft_preview(
    case_id: str,
    request: DraftPreviewRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Generate draft preview using RAG + GPT-4o

    **Path Parameters:**
    - case_id: Case ID

    **Request Body:**
    - sections: List of sections to generate (default: ["청구취지", "청구원인"])
    - language: Language code (default: "ko")
    - style: Writing style (default: "법원 제출용_표준")

    **Response:**
    - 200: Draft preview generated successfully
    - draft_text: Generated draft text
    - citations: List of evidence citations used
    - generated_at: Timestamp of generation

    **Errors:**
    - 401: Not authenticated
    - 403: User does not have access to case
    - 404: Case not found

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the case

    **Process:**
    1. Retrieve evidence metadata from DynamoDB
    2. Perform semantic search in OpenSearch (RAG)
    3. Build GPT-4o prompt with RAG context
    4. Generate draft text
    5. Extract citations

    **Important:**
    - This is a PREVIEW ONLY - not auto-submitted
    - Requires lawyer review and approval
    - Based on AI analysis of evidence
    - May require manual editing
    """
    draft_service = DraftService(db)
    return draft_service.generate_draft_preview(case_id, request, user_id)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Soft delete a case (set status to closed)

    **Path Parameters:**
    - case_id: Case ID

    **Response:**
    - 204: Case deleted successfully (no content)
    - 403: User is not the case owner
    - 404: Case not found

    **Authentication:**
    - Requires valid JWT token
    - Only case owner can delete the case

    **Note:**
    - This is a soft delete - case status is set to "closed"
    - OpenSearch index for the case will be deleted
    """
    case_service = CaseService(db)
    case_service.delete_case(case_id, user_id)
    return None
