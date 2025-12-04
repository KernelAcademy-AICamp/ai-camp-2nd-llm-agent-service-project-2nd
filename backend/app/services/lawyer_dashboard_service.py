"""
Lawyer Dashboard Service
003-role-based-ui Feature - US2

Business logic for lawyer dashboard statistics and data.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.models import Case, CaseMember, CaseStatus, CalendarEvent, User, UserRole
from app.schemas.lawyer_dashboard import (
    LawyerDashboardStats,
    LawyerDashboardResponse,
    RecentCaseItem,
    CalendarEventItem,
    StatsCardData,
    CaseStatusDistribution,
    MonthlyStats,
    LawyerAnalyticsResponse,
)


class LawyerDashboardService:
    """
    Service for lawyer dashboard operations.
    Provides statistics, recent cases, and upcoming events.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_dashboard_data(self, user_id: str) -> LawyerDashboardResponse:
        """
        Get complete dashboard data for a lawyer.

        Args:
            user_id: The lawyer's user ID

        Returns:
            LawyerDashboardResponse with stats, recent cases, and events
        """
        stats = self._get_dashboard_stats(user_id)
        recent_cases = self._get_recent_cases(user_id, limit=5)
        upcoming_events = self._get_upcoming_events(user_id, limit=5)

        return LawyerDashboardResponse(
            stats=stats,
            recent_cases=recent_cases,
            upcoming_events=upcoming_events,
        )

    def _get_dashboard_stats(self, user_id: str) -> LawyerDashboardStats:
        """Calculate dashboard statistics for a lawyer."""
        # Get all cases where user is a member
        case_ids = (
            self.session.query(CaseMember.case_id)
            .filter(CaseMember.user_id == user_id)
            .subquery()
        )

        # Total cases
        total_cases = (
            self.session.query(func.count(Case.id))
            .filter(Case.id.in_(case_ids))
            .filter(Case.status != CaseStatus.CLOSED)
            .scalar()
            or 0
        )

        # Active cases (open status)
        active_cases = (
            self.session.query(func.count(Case.id))
            .filter(Case.id.in_(case_ids))
            .filter(Case.status == CaseStatus.OPEN)
            .scalar()
            or 0
        )

        # Pending review (in_progress status)
        pending_review = (
            self.session.query(func.count(Case.id))
            .filter(Case.id.in_(case_ids))
            .filter(Case.status == CaseStatus.IN_PROGRESS)
            .scalar()
            or 0
        )

        # Completed this month
        first_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_this_month = (
            self.session.query(func.count(Case.id))
            .filter(Case.id.in_(case_ids))
            .filter(Case.status == CaseStatus.CLOSED)
            .filter(Case.updated_at >= first_of_month)
            .scalar()
            or 0
        )

        # New cases this week
        one_week_ago = datetime.now() - timedelta(days=7)
        cases_change = (
            self.session.query(func.count(Case.id))
            .filter(Case.id.in_(case_ids))
            .filter(Case.created_at >= one_week_ago)
            .scalar()
            or 0
        )

        # Build stats cards
        stats_cards = [
            StatsCardData(
                label="전체 케이스",
                value=total_cases,
                change=cases_change,
                trend="up" if cases_change > 0 else "stable",
            ),
            StatsCardData(
                label="진행 중",
                value=active_cases,
            ),
            StatsCardData(
                label="검토 대기",
                value=pending_review,
            ),
            StatsCardData(
                label="이번 달 완료",
                value=completed_this_month,
            ),
        ]

        return LawyerDashboardStats(
            total_cases=total_cases,
            active_cases=active_cases,
            pending_review=pending_review,
            completed_this_month=completed_this_month,
            cases_change=cases_change,
            stats_cards=stats_cards,
        )

    def _get_recent_cases(self, user_id: str, limit: int = 5) -> List[RecentCaseItem]:
        """Get recent cases for the lawyer."""
        # Get cases with membership
        cases = (
            self.session.query(Case)
            .join(CaseMember, Case.id == CaseMember.case_id)
            .filter(CaseMember.user_id == user_id)
            .filter(Case.status != CaseStatus.CLOSED)
            .order_by(Case.updated_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for case in cases:
            # Calculate progress based on status
            progress = 0
            if case.status == CaseStatus.OPEN:
                progress = 25
            elif case.status == CaseStatus.IN_PROGRESS:
                progress = 50
            elif case.status == CaseStatus.CLOSED:
                progress = 100

            result.append(
                RecentCaseItem(
                    id=case.id,
                    title=case.title,
                    status=case.status.value,
                    client_name=None,  # TODO: Get from case members
                    updated_at=case.updated_at or case.created_at,
                    evidence_count=0,  # TODO: Get from DynamoDB
                    progress=progress,
                )
            )

        return result

    def _get_upcoming_events(self, user_id: str, limit: int = 5) -> List[CalendarEventItem]:
        """Get upcoming calendar events for the lawyer."""
        now = datetime.now()

        try:
            events = (
                self.session.query(CalendarEvent)
                .filter(CalendarEvent.user_id == user_id)
                .filter(CalendarEvent.start_time >= now)
                .order_by(CalendarEvent.start_time.asc())
                .limit(limit)
                .all()
            )

            result = []
            for event in events:
                # Get case title if linked
                case_title = None
                if event.case_id:
                    case = self.session.query(Case).filter(Case.id == event.case_id).first()
                    if case:
                        case_title = case.title

                result.append(
                    CalendarEventItem(
                        id=str(event.id),
                        title=event.title,
                        event_type=event.event_type.value,
                        start_time=event.start_time,
                        case_id=event.case_id,
                        case_title=case_title,
                    )
                )

            return result
        except Exception:
            # CalendarEvent table might not exist yet
            return []

    def get_analytics(self, user_id: str) -> LawyerAnalyticsResponse:
        """Get extended analytics for the lawyer dashboard."""
        # Get case IDs
        case_ids = (
            self.session.query(CaseMember.case_id)
            .filter(CaseMember.user_id == user_id)
            .subquery()
        )

        # Status distribution
        status_counts = (
            self.session.query(Case.status, func.count(Case.id))
            .filter(Case.id.in_(case_ids))
            .group_by(Case.status)
            .all()
        )

        total = sum(count for _, count in status_counts)
        status_distribution = []
        for status, count in status_counts:
            percentage = (count / total * 100) if total > 0 else 0
            status_distribution.append(
                CaseStatusDistribution(
                    status=status.value,
                    count=count,
                    percentage=round(percentage, 1),
                )
            )

        # Monthly stats for last 6 months
        monthly_stats = []
        for i in range(5, -1, -1):
            month_start = (datetime.now() - timedelta(days=30 * i)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            month_end = (month_start + timedelta(days=32)).replace(day=1)

            new_cases = (
                self.session.query(func.count(Case.id))
                .filter(Case.id.in_(case_ids))
                .filter(Case.created_at >= month_start)
                .filter(Case.created_at < month_end)
                .scalar()
                or 0
            )

            completed_cases = (
                self.session.query(func.count(Case.id))
                .filter(Case.id.in_(case_ids))
                .filter(Case.status == CaseStatus.CLOSED)
                .filter(Case.updated_at >= month_start)
                .filter(Case.updated_at < month_end)
                .scalar()
                or 0
            )

            monthly_stats.append(
                MonthlyStats(
                    month=month_start.strftime("%Y-%m"),
                    new_cases=new_cases,
                    completed_cases=completed_cases,
                    evidence_uploaded=0,  # TODO: Get from DynamoDB
                )
            )

        return LawyerAnalyticsResponse(
            status_distribution=status_distribution,
            monthly_stats=monthly_stats,
            total_evidence=0,  # TODO: Get from DynamoDB
            avg_case_duration_days=0.0,  # TODO: Calculate
        )
