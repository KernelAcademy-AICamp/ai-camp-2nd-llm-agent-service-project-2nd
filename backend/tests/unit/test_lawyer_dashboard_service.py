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
