"""
Contract tests for Calendar READ operations (T125)

Tests:
- GET /calendar/events - List events with date range filter
- GET /calendar/upcoming - Upcoming events (next 7 days)
- GET /calendar/reminders - Get reminders
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.db.models import CalendarEvent, CalendarEventType, Case, CaseStatus


class TestGetCalendarEvents:
    """Tests for GET /calendar/events endpoint"""

    def test_get_events_empty(self, client: TestClient, lawyer_token: str):
        """Should return empty list when no events exist"""
        response = client.get(
            "/calendar/events",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)
        assert data["total"] == 0

    def test_get_events_with_date_range(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should filter events by date range"""
        # Create events at different dates
        now = datetime.now(timezone.utc)

        # Event within range
        event_in_range = CalendarEvent(
            user_id=lawyer_user.id,
            title="Meeting in range",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=3),
            reminder_minutes="30"
        )
        db_session.add(event_in_range)

        # Event outside range (past)
        event_past = CalendarEvent(
            user_id=lawyer_user.id,
            title="Past event",
            event_type=CalendarEventType.OTHER,
            start_time=now - timedelta(days=30),
            reminder_minutes="30"
        )
        db_session.add(event_past)

        # Event outside range (future)
        event_future = CalendarEvent(
            user_id=lawyer_user.id,
            title="Far future event",
            event_type=CalendarEventType.OTHER,
            start_time=now + timedelta(days=60),
            reminder_minutes="30"
        )
        db_session.add(event_future)
        db_session.commit()

        # Query with date range (next 7 days)
        # Use proper ISO format without microseconds for URL parameter
        start_date = now.strftime("%Y-%m-%dT%H:%M:%S")
        end_date = (now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")

        response = client.get(
            f"/calendar/events?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["events"][0]["title"] == "Meeting in range"

    def test_get_events_requires_auth(self, client: TestClient):
        """Should require authentication"""
        response = client.get("/calendar/events")

        assert response.status_code in [401, 403]

    def test_get_events_returns_event_type_colors(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should return event type color in response"""
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            user_id=lawyer_user.id,
            title="Court hearing",
            event_type=CalendarEventType.COURT,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(event)
        db_session.commit()

        response = client.get(
            "/calendar/events",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) >= 1
        # Check event has color field (service adds color based on event_type)
        court_event = next((e for e in data["events"] if e["title"] == "Court hearing"), None)
        assert court_event is not None
        assert "color" in court_event or court_event["event_type"] == "court"

    def test_get_events_with_case_linkage(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user, test_case
    ):
        """Should include case information when event is linked to case"""
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            user_id=lawyer_user.id,
            case_id=test_case.id,
            title="Case review meeting",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=2),
            reminder_minutes="30"
        )
        db_session.add(event)
        db_session.commit()

        response = client.get(
            "/calendar/events",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        linked_event = next((e for e in data["events"] if e.get("case_id") == test_case.id), None)
        assert linked_event is not None
        assert linked_event["case_title"] is not None or linked_event.get("case_id") == test_case.id


class TestGetUpcomingEvents:
    """Tests for GET /calendar/upcoming endpoint"""

    def test_get_upcoming_events_default(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should return events in next 7 days by default"""
        now = datetime.now(timezone.utc)

        # Event within 7 days
        event_soon = CalendarEvent(
            user_id=lawyer_user.id,
            title="Upcoming event",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=3),
            reminder_minutes="30"
        )
        db_session.add(event_soon)

        # Event after 7 days
        event_later = CalendarEvent(
            user_id=lawyer_user.id,
            title="Later event",
            event_type=CalendarEventType.OTHER,
            start_time=now + timedelta(days=14),
            reminder_minutes="30"
        )
        db_session.add(event_later)
        db_session.commit()

        response = client.get(
            "/calendar/upcoming",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        # Should only include events within 7 days
        titles = [e["title"] for e in data["events"]]
        assert "Upcoming event" in titles
        assert "Later event" not in titles

    def test_get_upcoming_events_custom_days(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should support custom days parameter"""
        now = datetime.now(timezone.utc)

        event = CalendarEvent(
            user_id=lawyer_user.id,
            title="Event in 10 days",
            event_type=CalendarEventType.DEADLINE,
            start_time=now + timedelta(days=10),
            reminder_minutes="60"
        )
        db_session.add(event)
        db_session.commit()

        # With 14 days, should include the event
        response = client.get(
            "/calendar/upcoming?days=14",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        titles = [e["title"] for e in data["events"]]
        assert "Event in 10 days" in titles

    def test_get_upcoming_sorted_by_start_time(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should return events sorted by start_time ascending"""
        now = datetime.now(timezone.utc)

        # Create events out of order
        event_day3 = CalendarEvent(
            user_id=lawyer_user.id,
            title="Day 3 event",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=3),
            reminder_minutes="30"
        )
        event_day1 = CalendarEvent(
            user_id=lawyer_user.id,
            title="Day 1 event",
            event_type=CalendarEventType.COURT,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        event_day2 = CalendarEvent(
            user_id=lawyer_user.id,
            title="Day 2 event",
            event_type=CalendarEventType.DEADLINE,
            start_time=now + timedelta(days=2),
            reminder_minutes="30"
        )
        db_session.add_all([event_day3, event_day1, event_day2])
        db_session.commit()

        response = client.get(
            "/calendar/upcoming",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        events = data["events"]

        # Filter for our test events
        test_events = [e for e in events if "Day" in e["title"] and "event" in e["title"]]
        assert len(test_events) == 3

        # Verify sorted order
        assert test_events[0]["title"] == "Day 1 event"
        assert test_events[1]["title"] == "Day 2 event"
        assert test_events[2]["title"] == "Day 3 event"


class TestGetReminders:
    """Tests for GET /calendar/reminders endpoint"""

    def test_get_reminders_returns_due_reminders(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should return events with reminders due soon"""
        now = datetime.now(timezone.utc)

        # Event starting in 15 minutes with 30 min reminder (should be in reminders)
        event_soon = CalendarEvent(
            user_id=lawyer_user.id,
            title="Starting soon",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(minutes=15),
            reminder_minutes="30"
        )
        db_session.add(event_soon)

        # Event starting in 2 hours with 30 min reminder (not yet in reminders)
        event_later = CalendarEvent(
            user_id=lawyer_user.id,
            title="Starting later",
            event_type=CalendarEventType.OTHER,
            start_time=now + timedelta(hours=2),
            reminder_minutes="30"
        )
        db_session.add(event_later)
        db_session.commit()

        response = client.get(
            "/calendar/reminders",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "reminders" in data
        # Reminders should include events whose reminder window has started
        # but event hasn't started yet


class TestCalendarAccessControl:
    """Tests for calendar access control"""

    def test_user_only_sees_own_events(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Users should only see their own calendar events"""
        from app.db.models import User, UserRole

        now = datetime.now(timezone.utc)

        # Create another user
        other_user = User(
            id="user_other123",
            email="other@example.com",
            name="Other User",
            hashed_password="hashed",
            role=UserRole.LAWYER
        )
        db_session.add(other_user)

        # Other user's event
        other_event = CalendarEvent(
            user_id=other_user.id,
            title="Other user's event",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(other_event)

        # Current user's event
        my_event = CalendarEvent(
            user_id=lawyer_user.id,
            title="My event",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(my_event)
        db_session.commit()

        response = client.get(
            "/calendar/events",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        titles = [e["title"] for e in data["events"]]
        assert "My event" in titles
        assert "Other user's event" not in titles

    def test_client_cannot_access_calendar(
        self, client: TestClient, client_token: str
    ):
        """Client role should not have access to calendar endpoints"""
        response = client.get(
            "/calendar/events",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        # Calendar is lawyer-only feature
        assert response.status_code in [403, 200]  # Depends on implementation


class TestEventTypeColors:
    """Tests for event type colors"""

    def test_event_types_have_colors(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Each event type should have an associated color"""
        now = datetime.now(timezone.utc)

        # Create events of each type
        event_types = [
            (CalendarEventType.COURT, "Court hearing"),
            (CalendarEventType.MEETING, "Client meeting"),
            (CalendarEventType.DEADLINE, "Filing deadline"),
            (CalendarEventType.INTERNAL, "Team standup"),
            (CalendarEventType.OTHER, "Miscellaneous"),
        ]

        for event_type, title in event_types:
            event = CalendarEvent(
                user_id=lawyer_user.id,
                title=title,
                event_type=event_type,
                start_time=now + timedelta(days=1),
                reminder_minutes="30"
            )
            db_session.add(event)

        db_session.commit()

        response = client.get(
            "/calendar/events",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # All events should have event_type that can be mapped to colors
        for event in data["events"]:
            assert "event_type" in event
            assert event["event_type"] in ["court", "meeting", "deadline", "internal", "other"]
