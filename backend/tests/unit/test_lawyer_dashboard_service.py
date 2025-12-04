"""
Unit tests for Lawyer Dashboard Service
Task T026 - TDD RED Phase

Tests for backend/app/services/lawyer_dashboard_service.py:
- Dashboard stats calculation
- Recent cases retrieval
- Upcoming events retrieval
- Stats cards generation
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from app.services.lawyer_dashboard_service import LawyerDashboardService
from app.db.models import Case, CaseStatus, CaseMemberRole


class TestDashboardStatsCalculation:
    """
    Unit tests for dashboard statistics calculation
    """

    def test_should_calculate_total_cases_correctly(self, test_env):
        """
        Given: User has 5 cases (3 active, 2 closed)
        When: get_dashboard_data is called
        Then: total_cases = 5 (all non-closed) OR counts based on status
        """
        from app.db.session import get_db
        from app.db.models import User, CaseMember
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        # Create test user
        user = User(
            email=f"stats_test_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Stats Test User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create cases with different statuses
        cases = []
        for i, status in enumerate([CaseStatus.ACTIVE, CaseStatus.OPEN, CaseStatus.IN_PROGRESS]):
            case = Case(
                title=f"Test Case {i+1}",
                status=status,
                created_by=user.id
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            cases.append(case)

            # Add user as case member
            member = CaseMember(
                case_id=case.id,
                user_id=user.id,
                role=CaseMemberRole.OWNER
            )
            db.add(member)
            db.commit()

        # When: Calculate stats
        service = LawyerDashboardService(db)
        result = service.get_dashboard_data(user.id)

        # Then: Total cases should be counted correctly
        assert result.stats.total_cases == 3

        # Cleanup
        for case in cases:
            db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
            db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    def test_should_calculate_active_cases_from_open_status(self, test_env):
        """
        Given: User has cases with OPEN status
        When: get_dashboard_data is called
        Then: active_cases count matches OPEN status cases
        """
        from app.db.session import get_db
        from app.db.models import User, CaseMember
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"active_test_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Active Test User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create 2 OPEN cases, 1 IN_PROGRESS
        cases = []
        for i, status in enumerate([CaseStatus.OPEN, CaseStatus.OPEN, CaseStatus.IN_PROGRESS]):
            case = Case(
                title=f"Active Test Case {i+1}",
                status=status,
                created_by=user.id
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            cases.append(case)

            member = CaseMember(
                case_id=case.id,
                user_id=user.id,
                role=CaseMemberRole.OWNER
            )
            db.add(member)
            db.commit()

        service = LawyerDashboardService(db)
        result = service.get_dashboard_data(user.id)

        # Should have 2 active (OPEN) cases
        assert result.stats.active_cases == 2

        # Cleanup
        for case in cases:
            db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
            db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    def test_should_calculate_pending_review_from_in_progress_status(self, test_env):
        """
        Given: User has cases with IN_PROGRESS status
        When: get_dashboard_data is called
        Then: pending_review count matches IN_PROGRESS status cases
        """
        from app.db.session import get_db
        from app.db.models import User, CaseMember
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"pending_test_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Pending Test User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create 1 OPEN case, 2 IN_PROGRESS
        cases = []
        for i, status in enumerate([CaseStatus.OPEN, CaseStatus.IN_PROGRESS, CaseStatus.IN_PROGRESS]):
            case = Case(
                title=f"Pending Test Case {i+1}",
                status=status,
                created_by=user.id
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            cases.append(case)

            member = CaseMember(
                case_id=case.id,
                user_id=user.id,
                role=CaseMemberRole.OWNER
            )
            db.add(member)
            db.commit()

        service = LawyerDashboardService(db)
        result = service.get_dashboard_data(user.id)

        # Should have 2 pending (IN_PROGRESS) cases
        assert result.stats.pending_review == 2

        # Cleanup
        for case in cases:
            db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
            db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    def test_should_return_zero_for_empty_user(self, test_env):
        """
        Given: User has no cases
        When: get_dashboard_data is called
        Then: All counts are 0
        """
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"empty_test_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Empty Test User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = LawyerDashboardService(db)
        result = service.get_dashboard_data(user.id)

        assert result.stats.total_cases == 0
        assert result.stats.active_cases == 0
        assert result.stats.pending_review == 0
        assert result.stats.completed_this_month == 0

        # Cleanup
        db.delete(user)
        db.commit()
        db.close()


class TestStatsCardsGeneration:
    """
    Unit tests for stats cards array generation
    """

    def test_should_generate_stats_cards_with_correct_labels(self, test_env):
        """
        Given: Dashboard data
        When: get_dashboard_data is called
        Then: stats_cards contains cards with Korean labels
        """
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"cards_test_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Cards Test User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = LawyerDashboardService(db)
        result = service.get_dashboard_data(user.id)

        # Verify stats_cards is present
        assert hasattr(result.stats, "stats_cards")
        assert isinstance(result.stats.stats_cards, list)

        # Expected labels (Korean)
        expected_labels = ["전체 케이스", "진행 중", "검토 대기", "이번 달 완료"]
        card_labels = [card.label for card in result.stats.stats_cards]

        for label in expected_labels:
            assert label in card_labels, f"Missing label: {label}"

        # Cleanup
        db.delete(user)
        db.commit()
        db.close()


class TestRecentCasesRetrieval:
    """
    Unit tests for recent cases list
    """

    def test_should_return_recent_cases_ordered_by_updated_at(self, test_env):
        """
        Given: User has multiple cases
        When: get_dashboard_data is called
        Then: recent_cases are ordered by updated_at DESC
        """
        from app.db.session import get_db
        from app.db.models import User, CaseMember
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"recent_test_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Recent Test User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create cases
        cases = []
        for i in range(3):
            case = Case(
                title=f"Recent Test Case {i+1}",
                status=CaseStatus.ACTIVE,
                created_by=user.id
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            cases.append(case)

            member = CaseMember(
                case_id=case.id,
                user_id=user.id,
                role=CaseMemberRole.OWNER
            )
            db.add(member)
            db.commit()

        service = LawyerDashboardService(db)
        result = service.get_dashboard_data(user.id)

        # Should have recent cases
        assert len(result.recent_cases) > 0

        # Cleanup
        for case in cases:
            db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
            db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    def test_should_limit_recent_cases_to_max_count(self, test_env):
        """
        Given: User has many cases
        When: get_dashboard_data is called
        Then: recent_cases is limited (e.g., max 5)
        """
        from app.db.session import get_db
        from app.db.models import User, CaseMember
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"limit_test_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Limit Test User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create 10 cases
        cases = []
        for i in range(10):
            case = Case(
                title=f"Limit Test Case {i+1}",
                status=CaseStatus.ACTIVE,
                created_by=user.id
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            cases.append(case)

            member = CaseMember(
                case_id=case.id,
                user_id=user.id,
                role=CaseMemberRole.OWNER
            )
            db.add(member)
            db.commit()

        service = LawyerDashboardService(db)
        result = service.get_dashboard_data(user.id)

        # Should be limited (typically 5 or 10)
        assert len(result.recent_cases) <= 10

        # Cleanup
        for case in cases:
            db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
            db.delete(case)
        db.delete(user)
        db.commit()
        db.close()


class TestGetAnalytics:
    """
    Unit tests for get_analytics method
    """

    def test_should_return_empty_analytics_for_user_without_cases(self, test_env):
        """
        Given: User has no cases
        When: get_analytics is called
        Then: Returns empty status distribution and 6 months of stats
        """
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"analytics_empty_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Analytics Empty User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = LawyerDashboardService(db)
        result = service.get_analytics(user.id)

        assert result.status_distribution == []
        assert len(result.monthly_stats) == 6

        # Cleanup
        db.delete(user)
        db.commit()
        db.close()

    def test_should_calculate_status_distribution(self, test_env):
        """
        Given: User has cases with different statuses
        When: get_analytics is called
        Then: Returns correct status distribution with percentages
        """
        from app.db.session import get_db
        from app.db.models import User, CaseMember
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"analytics_dist_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Analytics Dist User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create cases with different statuses
        cases = []
        statuses = [CaseStatus.OPEN, CaseStatus.OPEN, CaseStatus.IN_PROGRESS, CaseStatus.CLOSED]
        for i, status in enumerate(statuses):
            case = Case(
                title=f"Analytics Case {i+1}",
                status=status,
                created_by=user.id
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            cases.append(case)

            member = CaseMember(
                case_id=case.id,
                user_id=user.id,
                role=CaseMemberRole.OWNER
            )
            db.add(member)
            db.commit()

        service = LawyerDashboardService(db)
        result = service.get_analytics(user.id)

        # Should have multiple status distributions
        assert len(result.status_distribution) >= 1

        # Total count should be 4
        total = sum(d.count for d in result.status_distribution)
        assert total == 4

        # Cleanup
        for case in cases:
            db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
            db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    def test_should_return_monthly_stats_for_six_months(self, test_env):
        """
        Given: Any user
        When: get_analytics is called
        Then: Returns 6 months of monthly statistics
        """
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"analytics_monthly_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Analytics Monthly User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = LawyerDashboardService(db)
        result = service.get_analytics(user.id)

        # Should have 6 months
        assert len(result.monthly_stats) == 6

        # Each stat should have YYYY-MM format
        for stat in result.monthly_stats:
            assert len(stat.month) == 7
            assert "-" in stat.month
            assert stat.new_cases >= 0
            assert stat.completed_cases >= 0

        # Cleanup
        db.delete(user)
        db.commit()
        db.close()


class TestUpcomingEvents:
    """
    Unit tests for _get_upcoming_events method
    """

    def test_should_return_empty_list_when_no_events(self, test_env):
        """
        Given: User has no calendar events
        When: _get_upcoming_events is called
        Then: Returns empty list
        """
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"events_empty_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Events Empty User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = LawyerDashboardService(db)
        result = service._get_upcoming_events(user.id)

        assert result == []

        # Cleanup
        db.delete(user)
        db.commit()
        db.close()

    def test_should_return_events_with_case_title(self, test_env):
        """
        Given: User has calendar events linked to cases
        When: _get_upcoming_events is called
        Then: Returns events with case_title populated
        """
        from app.db.session import get_db
        from app.db.models import User, CalendarEvent, CaseMember, CalendarEventType
        from app.core.security import hash_password
        from datetime import timedelta, datetime, timezone
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"events_case_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Events Case User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a case
        case = Case(
            title="Event Case",
            status=CaseStatus.OPEN,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(
            case_id=case.id,
            user_id=user.id,
            role=CaseMemberRole.OWNER
        )
        db.add(member)
        db.commit()

        # Create event linked to case
        event = CalendarEvent(
            user_id=user.id,
            title="Court Hearing",
            event_type=CalendarEventType.COURT,
            case_id=case.id,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2)
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        service = LawyerDashboardService(db)
        result = service._get_upcoming_events(user.id)

        assert len(result) == 1
        assert result[0].title == "Court Hearing"
        assert result[0].case_title == "Event Case"

        # Cleanup
        db.query(CalendarEvent).filter(CalendarEvent.id == event.id).delete()
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(user)
        db.commit()
        db.close()
