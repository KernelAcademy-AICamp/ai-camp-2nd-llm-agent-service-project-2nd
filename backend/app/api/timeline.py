"""
Timeline API Router - Evidence Timeline endpoints

Feature: 002-evidence-timeline
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.schemas.timeline import TimelineResult, TimelineFilter, TimelineEventType
from app.services.timeline_service import TimelineService
from app.core.dependencies import get_current_user_id


router = APIRouter()


@router.get("/{case_id}/timeline", response_model=TimelineResult)
def get_timeline(
    case_id: str,
    date_start: Optional[str] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="Filter end date (YYYY-MM-DD)"),
    labels: Optional[str] = Query(None, description="Filter by labels (comma-separated)"),
    speakers: Optional[str] = Query(None, description="Filter by speakers (comma-separated)"),
    event_types: Optional[str] = Query(None, description="Filter by event types (comma-separated)"),
    key_only: bool = Query(False, description="Show only key evidence"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_order: str = Query("asc", description="Sort order: asc (oldest first) or desc (newest first)"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> TimelineResult:
    """
    Get evidence timeline for a case

    Retrieves all evidence for a case arranged chronologically with optional filtering.

    **Authentication**: Required (JWT)
    **Authorization**: User must have VIEWER, MEMBER, or OWNER role on the case

    **Query Parameters**:
    - `date_start`: Filter start date (YYYY-MM-DD)
    - `date_end`: Filter end date (YYYY-MM-DD)
    - `labels`: Filter by Article 840 labels (comma-separated)
    - `speakers`: Filter by speaker (comma-separated: 원고,피고,제3자)
    - `event_types`: Filter by event type (comma-separated: message,document,image,audio,video)
    - `key_only`: Show only key evidence (significance >= 4)
    - `limit`: Items per page (1-100, default 50)
    - `offset`: Pagination offset (default 0)
    - `sort_order`: Sort order - "asc" (oldest first) or "desc" (newest first)

    **Returns**: TimelineResult with events and statistics
    """
    service = TimelineService(db)

    # Parse comma-separated values
    parsed_labels = labels.split(",") if labels else None
    parsed_speakers = speakers.split(",") if speakers else None
    parsed_event_types = None
    if event_types:
        try:
            parsed_event_types = [
                TimelineEventType(t.strip()) for t in event_types.split(",")
            ]
        except ValueError:
            # Invalid event type - ignore filter
            parsed_event_types = None

    # Validate sort order
    if sort_order not in ("asc", "desc"):
        sort_order = "asc"

    # Build filter
    filter = TimelineFilter(
        date_start=date_start,
        date_end=date_end,
        labels=parsed_labels,
        speakers=parsed_speakers,
        event_types=parsed_event_types,
        key_only=key_only,
        limit=limit,
        offset=offset,
        sort_order=sort_order,  # type: ignore
    )

    return service.get_timeline(case_id, user_id, filter)
