"""
Calendar API Router (T129-T133, T136)

Endpoints:
- GET /calendar/events - List events with date range filter
- POST /calendar/events - Create new event
- PUT /calendar/events/{id} - Update event
- DELETE /calendar/events/{id} - Delete event
- GET /calendar/upcoming - Upcoming events (next N days)
- GET /calendar/reminders - Get due reminders
"""

from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user_id, require_role
from app.db.models import CalendarEventType, UserRole
from app.db.schemas import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventOut,
    CalendarEventListResponse,
)
from app.services.calendar_service import CalendarService, create_audit_log

router = APIRouter(prefix="/calendar", tags=["calendar"])


# Response schemas
from pydantic import BaseModel


class CalendarEventResponse(BaseModel):
    """Single event response with color"""
    id: str
    user_id: str
    case_id: Optional[str] = None
    case_title: Optional[str] = None
    title: str
    description: Optional[str] = None
    event_type: str
    start_time: str
    end_time: Optional[str] = None
    location: Optional[str] = None
    reminder_minutes: int
    color: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Event list response"""
    events: List[CalendarEventResponse]
    total: int


class UpcomingEventsResponse(BaseModel):
    """Upcoming events response"""
    events: List[CalendarEventResponse]


class ReminderResponse(CalendarEventResponse):
    """Reminder response with additional fields"""
    reminder_due: bool = True
    minutes_until_start: int


class RemindersResponse(BaseModel):
    """Reminders list response"""
    reminders: List[ReminderResponse]


class DeleteResponse(BaseModel):
    """Delete operation response"""
    success: bool
    message: str


# ============================================
# GET /calendar/events - List events (T130)
# ============================================
@router.get("/events", response_model=EventListResponse)
async def get_calendar_events(
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter until this date"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get calendar events for the current user

    - **start_date**: Optional start date filter (ISO format)
    - **end_date**: Optional end date filter (ISO format)

    Returns events sorted by start_time ascending.
    """
    service = CalendarService(db)
    events = service.get_events(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    return EventListResponse(
        events=events,
        total=len(events)
    )


# ============================================
# POST /calendar/events - Create event (T131)
# ============================================
@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    event_data: CalendarEventCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Create a new calendar event

    Required fields:
    - **title**: Event title (1-255 characters)
    - **start_time**: Event start time (ISO format)
    - **event_type**: court, meeting, deadline, internal, or other

    Optional fields:
    - **case_id**: Link to a case
    - **description**: Event description
    - **end_time**: Event end time
    - **location**: Event location
    - **reminder_minutes**: Minutes before event for reminder (default: 30)
    """
    service = CalendarService(db)

    try:
        event = service.create_event(user_id=user_id, event_data=event_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Audit log (T136)
    create_audit_log(
        db=db,
        user_id=user_id,
        action="create",
        entity_type="calendar_event",
        entity_id=event["id"],
        details={"title": event["title"], "event_type": event["event_type"]}
    )

    return event


# ============================================
# PUT /calendar/events/{id} - Update event (T131)
# ============================================
@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event(
    event_id: str,
    event_data: CalendarEventUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Update a calendar event

    Only the event owner can update it.
    All fields are optional - only provided fields will be updated.
    """
    service = CalendarService(db)

    # Check if event exists and belongs to user
    existing = service.get_event_by_id(event_id, user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    try:
        event = service.update_event(
            event_id=event_id,
            user_id=user_id,
            event_data=event_data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Audit log (T136)
    create_audit_log(
        db=db,
        user_id=user_id,
        action="update",
        entity_type="calendar_event",
        entity_id=event_id,
        details={"updated_fields": [k for k, v in event_data.model_dump().items() if v is not None]}
    )

    return event


# ============================================
# DELETE /calendar/events/{id} - Delete event (T131)
# ============================================
@router.delete("/events/{event_id}", response_model=DeleteResponse)
async def delete_calendar_event(
    event_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Delete a calendar event

    Only the event owner can delete it.
    """
    service = CalendarService(db)

    # Get event info for audit log before deletion
    existing = service.get_event_by_id(event_id, user_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    success = service.delete_event(event_id=event_id, user_id=user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found or already deleted"
        )

    # Audit log (T136)
    create_audit_log(
        db=db,
        user_id=user_id,
        action="delete",
        entity_type="calendar_event",
        entity_id=event_id,
        details={"title": existing["title"]}
    )

    return DeleteResponse(
        success=True,
        message="Event deleted successfully"
    )


# ============================================
# GET /calendar/upcoming - Upcoming events (T132)
# ============================================
@router.get("/upcoming", response_model=UpcomingEventsResponse)
async def get_upcoming_events(
    days: int = Query(7, ge=1, le=90, description="Number of days to look ahead"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get upcoming events within specified days

    - **days**: Number of days to look ahead (default: 7, max: 90)

    Returns events sorted by start_time ascending.
    """
    service = CalendarService(db)
    events = service.get_upcoming_events(user_id=user_id, days=days)

    return UpcomingEventsResponse(events=events)


# ============================================
# GET /calendar/reminders - Due reminders (T133)
# ============================================
@router.get("/reminders", response_model=RemindersResponse)
async def get_reminders(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get events with reminders currently due

    A reminder is due when:
    - Event hasn't started yet
    - Current time is within the reminder window (start_time - reminder_minutes)

    Each reminder includes:
    - **reminder_due**: Always true (filtered to only due reminders)
    - **minutes_until_start**: Minutes remaining until event starts
    """
    service = CalendarService(db)
    reminders = service.get_reminders(user_id=user_id)

    return RemindersResponse(reminders=reminders)


# ============================================
# GET /calendar/event-types - Get event type colors
# ============================================
@router.get("/event-types")
async def get_event_types():
    """
    Get all event types with their colors

    Useful for UI color coding:
    - **court**: Red (#ef4444) - 재판/출석
    - **meeting**: Blue (#3b82f6) - 상담/회의
    - **deadline**: Amber (#f59e0b) - 마감
    - **internal**: Purple (#8b5cf6) - 내부 업무
    - **other**: Gray (#6b7280) - 기타
    """
    return {
        "event_types": [
            {"type": "court", "label": "재판/출석", "color": "#ef4444"},
            {"type": "meeting", "label": "상담/회의", "color": "#3b82f6"},
            {"type": "deadline", "label": "마감", "color": "#f59e0b"},
            {"type": "internal", "label": "내부 업무", "color": "#8b5cf6"},
            {"type": "other", "label": "기타", "color": "#6b7280"},
        ]
    }
