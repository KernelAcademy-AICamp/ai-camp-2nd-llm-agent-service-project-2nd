"""
Case Repository - Data access layer for Case model
Implements Repository pattern per BACKEND_SERVICE_REPOSITORY_GUIDE.md
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models import Case, CaseMember
from datetime import datetime, timezone
import uuid


class CaseRepository:
    """
    Repository for Case database operations
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, title: str, description: Optional[str], created_by: str, client_name: Optional[str] = None) -> Case:
        """
        Create a new case in the database

        Args:
            title: Case title
            description: Case description (optional)
            created_by: User ID who created the case
            client_name: Client name (optional)

        Returns:
            Created Case instance
        """
        case = Case(
            id=f"case_{uuid.uuid4().hex[:12]}",
            title=title,
            client_name=client_name,
            description=description,
            status="active",
            created_by=created_by,
            created_at=datetime.now(timezone.utc)
        )

        self.session.add(case)
        self.session.flush()  # Get the ID without committing

        return case

    def get_by_id(self, case_id: str, include_deleted: bool = False) -> Optional[Case]:
        """
        Get case by ID

        Args:
            case_id: Case ID
            include_deleted: If True, include soft-deleted cases

        Returns:
            Case instance if found, None otherwise
        """
        query = self.session.query(Case).filter(Case.id == case_id)
        if not include_deleted:
            query = query.filter(Case.deleted_at.is_(None))
        return query.first()

    def get_all_for_user(self, user_id: str, include_deleted: bool = False) -> List[Case]:
        """
        Get all cases accessible by user (via case_members)

        Args:
            user_id: User ID
            include_deleted: If True, include soft-deleted cases

        Returns:
            List of Case instances
        """
        # Join with case_members to filter by user access
        query = (
            self.session.query(Case)
            .join(CaseMember, Case.id == CaseMember.case_id)
            .filter(CaseMember.user_id == user_id)
        )

        if not include_deleted:
            query = query.filter(Case.deleted_at.is_(None))

        return query.all()

    def update(self, case: Case) -> Case:
        """
        Update case in database

        Args:
            case: Case instance with updated fields

        Returns:
            Updated Case instance
        """
        self.session.add(case)
        self.session.flush()
        return case

    def soft_delete(self, case_id: str) -> bool:
        """
        Soft delete case (set deleted_at timestamp and status to closed)

        Args:
            case_id: Case ID

        Returns:
            True if deleted, False if not found
        """
        case = self.get_by_id(case_id)
        if not case:
            return False

        case.status = "closed"
        case.deleted_at = datetime.now(timezone.utc)
        self.session.flush()
        return True

    def hard_delete(self, case_id: str) -> bool:
        """
        Hard delete case (permanently remove from database)
        WARNING: This is irreversible. Use soft_delete for normal operations.

        Args:
            case_id: Case ID

        Returns:
            True if deleted, False if not found
        """
        case = self.get_by_id(case_id)
        if not case:
            return False

        self.session.delete(case)
        self.session.flush()
        return True

    def get_deleted_cases_older_than(self, days: int) -> List[Case]:
        """
        Get soft-deleted cases older than specified days
        Useful for scheduled cleanup jobs

        Args:
            days: Number of days since deletion

        Returns:
            List of Case instances eligible for hard deletion
        """
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        return (
            self.session.query(Case)
            .filter(Case.deleted_at.isnot(None))
            .filter(Case.deleted_at < cutoff_date)
            .all()
        )
