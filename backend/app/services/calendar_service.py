"""
Calendar Service - Business logic for calendar management (T134)

Handles:
- Event CRUD operations
- Event type colors
- Date range filtering
- Upcoming events
- Reminders
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models import CalendarEvent, CalendarEventType, Case, AuditLog
from app.db.schemas import CalendarEventCreate, CalendarEventUpdate, CalendarEventOut


# Event type color mapping
EVENT_TYPE_COLORS: Dict[CalendarEventType, str] = {
    CalendarEventType.COURT: "#ef4444",     # Red - 재판/출석
    CalendarEventType.MEETING: "#3b82f6",   # Blue - 상담/회의
    CalendarEventType.DEADLINE: "#f59e0b",  # Amber - 마감
    CalendarEventType.INTERNAL: "#8b5cf6",  # Purple - 내부 업무
    CalendarEventType.OTHER: "#6b7280",     # Gray - 기타
}


class CalendarService:
    """Service for calendar operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_event_color(self, event_type: CalendarEventType) -> str:
        """Get color for event type"""
        return EVENT_TYPE_COLORS.get(event_type, "#6b7280")

    def get_events(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get calendar events for user with optional date range filter

        Args:
            user_id: ID of the user
            start_date: Filter events starting from this date
            end_date: Filter events ending before this date

        Returns:
            List of events with color and case information
        """
        query = self.db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id
        )

        # Apply date range filter
        if start_date:
            query = query.filter(CalendarEvent.start_time >= start_date)
        if end_date:
            query = query.filter(CalendarEvent.start_time <= end_date)

        # Order by start_time
        query = query.order_by(CalendarEvent.start_time.asc())

        events = query.all()

        # Transform to response format with color and case info
        result = []
        for event in events:
            event_dict = self._event_to_dict(event)
            result.append(event_dict)

        return result

    def get_event_by_id(
        self, event_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get single event by ID (owned by user)"""
        event = self.db.query(CalendarEvent).filter(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == user_id
        ).first()

        if not event:
            return None

        return self._event_to_dict(event)

    def create_event(
        self,
        user_id: str,
        event_data: CalendarEventCreate
    ) -> Dict[str, Any]:
        """
        Create a new calendar event

        Args:
            user_id: ID of the user creating the event
            event_data: Event creation data

        Returns:
            Created event with color info
        """
        # Validate case_id if provided
        if event_data.case_id:
            case = self.db.query(Case).filter(
                Case.id == event_data.case_id
            ).first()
            if not case:
                raise ValueError(f"Case not found: {event_data.case_id}")

        # Create event
        event = CalendarEvent(
            user_id=user_id,
            case_id=event_data.case_id,
            title=event_data.title,
            description=event_data.description,
            event_type=event_data.event_type,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            location=event_data.location,
            reminder_minutes=str(event_data.reminder_minutes),
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return self._event_to_dict(event)

    def update_event(
        self,
        event_id: str,
        user_id: str,
        event_data: CalendarEventUpdate
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing calendar event

        Args:
            event_id: ID of the event to update
            user_id: ID of the user (for ownership check)
            event_data: Update data

        Returns:
            Updated event or None if not found
        """
        event = self.db.query(CalendarEvent).filter(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == user_id
        ).first()

        if not event:
            return None

        # Validate case_id if being updated
        if event_data.case_id is not None:
            if event_data.case_id:  # Not empty string
                case = self.db.query(Case).filter(
                    Case.id == event_data.case_id
                ).first()
                if not case:
                    raise ValueError(f"Case not found: {event_data.case_id}")
            event.case_id = event_data.case_id

        # Update fields if provided
        if event_data.title is not None:
            event.title = event_data.title
        if event_data.description is not None:
            event.description = event_data.description
        if event_data.event_type is not None:
            event.event_type = event_data.event_type
        if event_data.start_time is not None:
            event.start_time = event_data.start_time
        if event_data.end_time is not None:
            event.end_time = event_data.end_time
        if event_data.location is not None:
            event.location = event_data.location
        if event_data.reminder_minutes is not None:
            event.reminder_minutes = str(event_data.reminder_minutes)

        self.db.commit()
        self.db.refresh(event)

        return self._event_to_dict(event)

    def delete_event(self, event_id: str, user_id: str) -> bool:
        """
        Delete a calendar event

        Args:
            event_id: ID of the event to delete
            user_id: ID of the user (for ownership check)

        Returns:
            True if deleted, False if not found
        """
        event = self.db.query(CalendarEvent).filter(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == user_id
        ).first()

        if not event:
            return False

        self.db.delete(event)
        self.db.commit()

        return True

    def get_upcoming_events(
        self, user_id: str, days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming events within specified days

        Args:
            user_id: ID of the user
            days: Number of days to look ahead (default 7)

        Returns:
            List of upcoming events sorted by start_time
        """
        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=days)

        events = self.db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= now,
            CalendarEvent.start_time <= end_date
        ).order_by(CalendarEvent.start_time.asc()).all()

        return [self._event_to_dict(event) for event in events]

    def get_reminders(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get events with reminders due

        An event's reminder is due when:
        - Event hasn't started yet
        - Current time is within reminder window (start_time - reminder_minutes)

        Args:
            user_id: ID of the user

        Returns:
            List of events with due reminders
        """
        now = datetime.now(timezone.utc)

        # Get all upcoming events
        upcoming = self.db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
        ).all()

        reminders = []
        for event in upcoming:
            # Ensure start_time is timezone-aware for comparison
            start_time = event.start_time
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)

            # Skip past events
            if start_time <= now:
                continue

            try:
                reminder_minutes = int(event.reminder_minutes)
            except (ValueError, TypeError):
                reminder_minutes = 30

            reminder_time = start_time - timedelta(minutes=reminder_minutes)

            # Check if we're in the reminder window
            if reminder_time <= now < start_time:
                event_dict = self._event_to_dict(event)
                event_dict["reminder_due"] = True
                event_dict["minutes_until_start"] = int(
                    (start_time - now).total_seconds() / 60
                )
                reminders.append(event_dict)

        return reminders

    def _event_to_dict(self, event: CalendarEvent) -> Dict[str, Any]:
        """Convert event model to dictionary with color and case info"""
        # Get case title if linked
        case_title = None
        if event.case_id and event.case:
            case_title = event.case.title

        # Parse reminder_minutes
        try:
            reminder_minutes = int(event.reminder_minutes)
        except (ValueError, TypeError):
            reminder_minutes = 30

        return {
            "id": event.id,
            "user_id": event.user_id,
            "case_id": event.case_id,
            "case_title": case_title,
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type.value if event.event_type else "other",
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "location": event.location,
            "reminder_minutes": reminder_minutes,
            "color": self.get_event_color(event.event_type),
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }


def create_audit_log(
    db: Session,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Create audit log entry for calendar operations (T136)

    Note: AuditLog model has limited fields (action, object_id, user_id, timestamp)
    Combine entity_type and action for the action field.
    """
    # Combine action and entity_type for meaningful action name
    full_action = f"{action.upper()}_{entity_type.upper()}"

    audit_log = AuditLog(
        user_id=user_id,
        action=full_action,
        object_id=entity_id,
    )
    db.add(audit_log)
    db.commit()
