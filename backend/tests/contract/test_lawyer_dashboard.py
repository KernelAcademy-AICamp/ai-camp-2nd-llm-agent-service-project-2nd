"""
Contract tests for Lawyer Dashboard API
Task T025 - TDD RED Phase

Tests for GET /lawyer/dashboard endpoint:
- Returns dashboard statistics for authenticated lawyer
- Returns recent cases and upcoming events
- Role-based access (only internal users)
"""

import pytest
from fastapi import status
from app.core.security import create_access_token
from app.db.models import UserRole


class TestGetLawyerDashboard:
    """
    Contract tests for GET /lawyer/dashboard
    """

    def test_should_return_dashboard_stats_for_lawyer(self, client, test_user, auth_headers):
        """
        Given: Authenticated lawyer user
        When: GET /lawyer/dashboard
        Then:
            - Returns 200 status code
            - Response contains stats object with required fields
            - Response contains recent_cases array
            - Response contains upcoming_events array
        """
        # When: GET /lawyer/dashboard
        response = client.get("/lawyer/dashboard", headers=auth_headers)

        # Then: Success with dashboard data
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify stats structure
        assert "stats" in data
        stats = data["stats"]
        assert "total_cases" in stats
        assert "active_cases" in stats
        assert "pending_review" in stats
        assert "completed_this_month" in stats
        assert isinstance(stats["total_cases"], int)
        assert isinstance(stats["active_cases"], int)

        # Verify recent_cases array
        assert "recent_cases" in data
        assert isinstance(data["recent_cases"], list)

        # Verify upcoming_events array
        assert "upcoming_events" in data
        assert isinstance(data["upcoming_events"], list)

    def test_should_return_stats_cards_array(self, client, auth_headers):
        """
        Given: Authenticated lawyer user
        When: GET /lawyer/dashboard
        Then:
            - stats.stats_cards is an array
            - Each card has label, value fields
        """
        # When: GET /lawyer/dashboard
        response = client.get("/lawyer/dashboard", headers=auth_headers)

        # Then: Stats cards present
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        stats = data["stats"]

        # Verify stats_cards array
        assert "stats_cards" in stats
        assert isinstance(stats["stats_cards"], list)

        # If cards exist, verify structure
        for card in stats["stats_cards"]:
            assert "label" in card
            assert "value" in card

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: GET /lawyer/dashboard
        Then: Returns 401 Unauthorized
        """
        # When: GET without auth
        response = client.get("/lawyer/dashboard")

        # Then: Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, test_env):
        """
        Given: User with CLIENT role
        When: GET /lawyer/dashboard
        Then: Returns 403 Forbidden
        """
        # Given: Create client user
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        client_user = User(
            email=f"client_dash_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Client",
            role=UserRole.CLIENT
        )
        db.add(client_user)
        db.commit()
        db.refresh(client_user)

        token = create_access_token({
            "sub": client_user.id,
            "role": client_user.role.value,
            "email": client_user.email
        })

        # When: GET /lawyer/dashboard as client
        response = client.get(
            "/lawyer/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Cleanup
        db.delete(client_user)
        db.commit()
        db.close()

    def test_should_reject_detective_role(self, client, test_env):
        """
        Given: User with DETECTIVE role
        When: GET /lawyer/dashboard
        Then: Returns 403 Forbidden
        """
        # Given: Create detective user
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        detective_user = User(
            email=f"detective_dash_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Detective",
            role=UserRole.DETECTIVE
        )
        db.add(detective_user)
        db.commit()
        db.refresh(detective_user)

        token = create_access_token({
            "sub": detective_user.id,
            "role": detective_user.role.value,
            "email": detective_user.email
        })

        # When: GET /lawyer/dashboard as detective
        response = client.get(
            "/lawyer/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Cleanup
        db.delete(detective_user)
        db.commit()
        db.close()

    def test_should_allow_admin_access(self, client, admin_user, admin_auth_headers):
        """
        Given: User with ADMIN role
        When: GET /lawyer/dashboard
        Then: Returns 200 OK (admin can access all portals)
        """
        # When: GET /lawyer/dashboard as admin
        response = client.get("/lawyer/dashboard", headers=admin_auth_headers)

        # Then: Success (admin has access)
        assert response.status_code == status.HTTP_200_OK

    def test_should_allow_staff_access(self, client, test_env):
        """
        Given: User with STAFF role
        When: GET /lawyer/dashboard
        Then: Returns 200 OK
        """
        # Given: Create staff user
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        staff_user = User(
            email=f"staff_dash_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Staff",
            role=UserRole.STAFF
        )
        db.add(staff_user)
        db.commit()
        db.refresh(staff_user)

        token = create_access_token({
            "sub": staff_user.id,
            "role": staff_user.role.value,
            "email": staff_user.email
        })

        # When: GET /lawyer/dashboard as staff
        response = client.get(
            "/lawyer/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Success
        assert response.status_code == status.HTTP_200_OK

        # Cleanup
        db.delete(staff_user)
        db.commit()
        db.close()


class TestRecentCasesInDashboard:
    """
    Contract tests for recent cases in dashboard response
    """

    def test_recent_cases_should_have_required_fields(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: GET /lawyer/dashboard
        Then: Each recent case has id, title, status, updated_at
        """
        response = client.get("/lawyer/dashboard", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for case in data["recent_cases"]:
            assert "id" in case
            assert "title" in case
            assert "status" in case
            assert "updated_at" in case


class TestUpcomingEventsInDashboard:
    """
    Contract tests for upcoming events in dashboard response
    """

    def test_upcoming_events_should_have_required_fields(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: GET /lawyer/dashboard
        Then: Each event has id, title, event_type, start_time
        """
        response = client.get("/lawyer/dashboard", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for event in data["upcoming_events"]:
            assert "id" in event
            assert "title" in event
            assert "event_type" in event
            assert "start_time" in event
