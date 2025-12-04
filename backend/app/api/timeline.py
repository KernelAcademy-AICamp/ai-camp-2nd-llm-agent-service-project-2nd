"""
Timeline API endpoints
GET /cases/{case_id}/timeline - Get evidence timeline for a case

Feature: 002-evidence-timeline
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.timeline import TimelineFilter, TimelineResult, TimelineEventType
from app.services.timeline_service import TimelineService
from app.core.dependencies import get_current_user_id


router = APIRouter()


@router.get("/cases/{case_id}/timeline", response_model=TimelineResult)
def get_timeline(
    case_id: str,
    date_start: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    labels: Optional[str] = Query(None, description="Comma-separated labels to filter by"),
    speakers: Optional[str] = Query(None, description="Comma-separated speakers to filter by"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types to filter by"),
    key_only: bool = Query(False, description="Show only key evidence"),
    limit: int = Query(50, ge=1, le=200, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order: asc or desc"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get evidence timeline for a case

    **Path Parameters:**
    - case_id: Case ID

    **Query Parameters:**
    - date_start: Filter by start date (YYYY-MM-DD)
    - date_end: Filter by end date (YYYY-MM-DD)
    - labels: Comma-separated Article 840 labels
    - speakers: Comma-separated speaker names
    - event_types: Comma-separated event types (message, document, image, audio, video, incident)
    - key_only: Show only key evidence (significance >= 4)
    - limit: Max results per page (default: 50, max: 200)
    - offset: Pagination offset (default: 0)
    - sort_order: Chronological order - asc (oldest first) or desc (newest first)

    **Response:**
    - case_id: Case ID
    - events: List of timeline events
    - total_count: Total evidence count (before filtering)
    - filtered_count: Count after filtering
    - has_more: Whether more results exist
    - date_range: Date range of events
    - events_by_type: Event count by type
    - events_by_label: Event count by label
    - key_events_count: Number of key evidence items
    - generated_at: Timestamp when result was generated

    **Errors:**
    - 401: Not authenticated
    - 403: User does not have access to case
    """
    # Parse comma-separated filter values
    filter_params = TimelineFilter(
        date_start=date_start,
        date_end=date_end,
        labels=_parse_csv(labels),
        speakers=_parse_csv(speakers),
        event_types=_parse_event_types(event_types),
        key_only=key_only,
        limit=limit,
        offset=offset,
        sort_order=sort_order,
    )

    timeline_service = TimelineService(db)

    try:
        return timeline_service.get_timeline(case_id, user_id, filter_params)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


def _parse_csv(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated string to list"""
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def _parse_event_types(value: Optional[str]) -> Optional[List[TimelineEventType]]:
    """Parse comma-separated event types to enum list"""
    if not value:
        return None
    types = []
    for v in value.split(","):
        v = v.strip().lower()
        try:
            types.append(TimelineEventType(v))
        except ValueError:
            continue  # Skip invalid types
    return types if types else None
