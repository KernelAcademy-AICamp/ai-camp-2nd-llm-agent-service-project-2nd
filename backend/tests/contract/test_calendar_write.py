"""
Contract tests for Calendar WRITE operations (T126)

Tests:
- POST /calendar/events - Create new event
- PUT /calendar/events/{id} - Update event
- DELETE /calendar/events/{id} - Delete event
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.db.models import CalendarEvent, CalendarEventType, AuditLog


class TestCreateCalendarEvent:
    """Tests for POST /calendar/events endpoint"""

    def test_create_event_minimal(self, client: TestClient, lawyer_token: str):
        """Should create event with minimal required fields"""
        now = datetime.now(timezone.utc)
        event_data = {
            "title": "Simple meeting",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "event_type": "meeting"
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Simple meeting"
        assert data["event_type"] == "meeting"
        assert "id" in data

    def test_create_event_full(
        self, client: TestClient, lawyer_token: str, test_case
    ):
        """Should create event with all fields"""
        now = datetime.now(timezone.utc)
        event_data = {
            "title": "Court hearing",
            "description": "Initial hearing for divorce case",
            "case_id": test_case.id,
            "event_type": "court",
            "start_time": (now + timedelta(days=5)).isoformat(),
            "end_time": (now + timedelta(days=5, hours=2)).isoformat(),
            "location": "Seoul Family Court, Room 301",
            "reminder_minutes": 60
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Court hearing"
        assert data["description"] == "Initial hearing for divorce case"
        assert data["case_id"] == test_case.id
        assert data["event_type"] == "court"
        assert data["location"] == "Seoul Family Court, Room 301"
        assert data["reminder_minutes"] == 60

    def test_create_event_invalid_type(
        self, client: TestClient, lawyer_token: str
    ):
        """Should reject invalid event type"""
        now = datetime.now(timezone.utc)
        event_data = {
            "title": "Invalid event",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "event_type": "invalid_type"
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 422

    def test_create_event_missing_title(
        self, client: TestClient, lawyer_token: str
    ):
        """Should require title field"""
        now = datetime.now(timezone.utc)
        event_data = {
            "start_time": (now + timedelta(days=1)).isoformat(),
            "event_type": "meeting"
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 422

    def test_create_event_missing_start_time(
        self, client: TestClient, lawyer_token: str
    ):
        """Should require start_time field"""
        event_data = {
            "title": "No time event",
            "event_type": "meeting"
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 422

    def test_create_event_requires_auth(self, client: TestClient):
        """Should require authentication"""
        event_data = {
            "title": "Unauthorized event",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "event_type": "meeting"
        }

        response = client.post(
            "/calendar/events",
            json=event_data
        )

        assert response.status_code in [401, 403]

    def test_create_event_invalid_case_id(
        self, client: TestClient, lawyer_token: str
    ):
        """Should handle invalid case_id gracefully"""
        now = datetime.now(timezone.utc)
        event_data = {
            "title": "Event with bad case",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "event_type": "meeting",
            "case_id": "nonexistent_case_id"
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        # Either 404 or 422 for invalid reference
        assert response.status_code in [404, 422, 400]

    def test_create_event_default_reminder(
        self, client: TestClient, lawyer_token: str
    ):
        """Should use default reminder_minutes if not provided"""
        now = datetime.now(timezone.utc)
        event_data = {
            "title": "Default reminder event",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "event_type": "deadline"
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["reminder_minutes"] == 30  # Default value


class TestUpdateCalendarEvent:
    """Tests for PUT /calendar/events/{id} endpoint"""

    def test_update_event_title(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should update event title"""
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=lawyer_user.id,
            title="Original title",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.put(
            f"/calendar/events/{event.id}",
            json={"title": "Updated title"},
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated title"

    def test_update_event_type(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should update event type"""
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=lawyer_user.id,
            title="Type change event",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.put(
            f"/calendar/events/{event.id}",
            json={"event_type": "court"},
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "court"

    def test_update_event_time(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should update event start and end time"""
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=lawyer_user.id,
            title="Rescheduled event",
            event_type=CalendarEventType.COURT,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        new_start = now + timedelta(days=3)
        new_end = now + timedelta(days=3, hours=2)

        response = client.put(
            f"/calendar/events/{event.id}",
            json={
                "start_time": new_start.isoformat(),
                "end_time": new_end.isoformat()
            },
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Verify time was updated (compare date parts)
        assert new_start.date().isoformat() in data["start_time"]

    def test_update_event_link_case(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user, test_case
    ):
        """Should link event to a case"""
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=lawyer_user.id,
            title="Event to link",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.put(
            f"/calendar/events/{event.id}",
            json={"case_id": test_case.id},
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["case_id"] == test_case.id

    def test_update_nonexistent_event(
        self, client: TestClient, lawyer_token: str
    ):
        """Should return 404 for nonexistent event"""
        response = client.put(
            "/calendar/events/nonexistent_event_id",
            json={"title": "Updated"},
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 404

    def test_update_event_requires_auth(
        self, client: TestClient
    ):
        """Should require authentication"""
        response = client.put(
            "/calendar/events/some_event_id",
            json={"title": "Unauthorized update"}
        )

        assert response.status_code in [401, 403]

    def test_cannot_update_others_event(
        self, client: TestClient, lawyer_token: str, db_session
    ):
        """Should not allow updating another user's event"""
        from app.db.models import User, UserRole

        now = datetime.now(timezone.utc)

        # Create another user
        other_user = User(
            id="user_other456",
            email="other2@example.com",
            name="Other User 2",
            hashed_password="hashed",
            role=UserRole.LAWYER
        )
        db_session.add(other_user)

        # Other user's event
        other_event = CalendarEvent(
            user_id=other_user.id,
            title="Other's event",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(other_event)
        db_session.commit()
        db_session.refresh(other_event)

        response = client.put(
            f"/calendar/events/{other_event.id}",
            json={"title": "Hijacked title"},
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code in [403, 404]


class TestDeleteCalendarEvent:
    """Tests for DELETE /calendar/events/{id} endpoint"""

    def test_delete_event_success(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should delete event successfully"""
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=lawyer_user.id,
            title="Event to delete",
            event_type=CalendarEventType.OTHER,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        event_id = event.id

        response = client.delete(
            f"/calendar/events/{event_id}",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code in [200, 204]

        # Verify event is deleted
        deleted_event = db_session.query(CalendarEvent).filter(
            CalendarEvent.id == event_id
        ).first()
        assert deleted_event is None

    def test_delete_nonexistent_event(
        self, client: TestClient, lawyer_token: str
    ):
        """Should return 404 for nonexistent event"""
        response = client.delete(
            "/calendar/events/nonexistent_id",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 404

    def test_delete_event_requires_auth(self, client: TestClient):
        """Should require authentication"""
        response = client.delete("/calendar/events/some_id")

        assert response.status_code in [401, 403]

    def test_cannot_delete_others_event(
        self, client: TestClient, lawyer_token: str, db_session
    ):
        """Should not allow deleting another user's event"""
        from app.db.models import User, UserRole

        now = datetime.now(timezone.utc)

        other_user = User(
            id="user_other789",
            email="other3@example.com",
            name="Other User 3",
            hashed_password="hashed",
            role=UserRole.LAWYER
        )
        db_session.add(other_user)

        other_event = CalendarEvent(
            user_id=other_user.id,
            title="Cannot delete this",
            event_type=CalendarEventType.DEADLINE,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(other_event)
        db_session.commit()
        db_session.refresh(other_event)

        response = client.delete(
            f"/calendar/events/{other_event.id}",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code in [403, 404]


class TestAuditLogging:
    """Tests for audit logging on calendar operations (T136)"""

    def test_create_event_audit_logged(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should create audit log entry when event is created"""
        now = datetime.now(timezone.utc)
        event_data = {
            "title": "Audited event",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "event_type": "court"
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 201
        event_id = response.json()["id"]

        # Check audit log - AuditLog uses 'action' (combined) and 'object_id'
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.object_id == event_id,
            AuditLog.action == "CREATE_CALENDAR_EVENT"
        ).first()

        assert audit_log is not None
        assert audit_log.user_id == lawyer_user.id

    def test_update_event_audit_logged(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should create audit log entry when event is updated"""
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=lawyer_user.id,
            title="Original",
            event_type=CalendarEventType.MEETING,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)

        response = client.put(
            f"/calendar/events/{event.id}",
            json={"title": "Updated for audit"},
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 200

        # Check audit log - AuditLog uses 'action' (combined) and 'object_id'
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.object_id == event.id,
            AuditLog.action == "UPDATE_CALENDAR_EVENT"
        ).first()

        assert audit_log is not None
        assert audit_log.user_id == lawyer_user.id

    def test_delete_event_audit_logged(
        self, client: TestClient, lawyer_token: str, db_session, lawyer_user
    ):
        """Should create audit log entry when event is deleted"""
        now = datetime.now(timezone.utc)
        event = CalendarEvent(
            user_id=lawyer_user.id,
            title="To be deleted and logged",
            event_type=CalendarEventType.OTHER,
            start_time=now + timedelta(days=1),
            reminder_minutes="30"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        event_id = event.id

        response = client.delete(
            f"/calendar/events/{event_id}",
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code in [200, 204]

        # Check audit log - AuditLog uses 'action' (combined) and 'object_id'
        audit_log = db_session.query(AuditLog).filter(
            AuditLog.object_id == event_id,
            AuditLog.action == "DELETE_CALENDAR_EVENT"
        ).first()

        assert audit_log is not None
        assert audit_log.user_id == lawyer_user.id


class TestEventValidation:
    """Tests for event data validation"""

    def test_title_max_length(
        self, client: TestClient, lawyer_token: str
    ):
        """Should reject title exceeding max length"""
        now = datetime.now(timezone.utc)
        event_data = {
            "title": "x" * 300,  # Exceeds 255 limit
            "start_time": (now + timedelta(days=1)).isoformat(),
            "event_type": "meeting"
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 422

    def test_title_empty_string(
        self, client: TestClient, lawyer_token: str
    ):
        """Should reject empty title"""
        now = datetime.now(timezone.utc)
        event_data = {
            "title": "",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "event_type": "meeting"
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 422

    def test_korean_title_supported(
        self, client: TestClient, lawyer_token: str
    ):
        """Should support Korean characters in title"""
        now = datetime.now(timezone.utc)
        event_data = {
            "title": "서울가정법원 재판 출석",
            "description": "이혼 소송 1차 변론기일",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "event_type": "court",
            "location": "서울가정법원 301호"
        }

        response = client.post(
            "/calendar/events",
            json=event_data,
            headers={"Authorization": f"Bearer {lawyer_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "서울가정법원 재판 출석"
        assert data["location"] == "서울가정법원 301호"
