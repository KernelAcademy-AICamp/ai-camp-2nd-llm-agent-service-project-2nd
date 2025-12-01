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

    def create(self, title: str, description: Optional[str], created_by: str) -> Case:
        """
        Create a new case in the database

        Args:
            title: Case title
            description: Case description (optional)
            created_by: User ID who created the case

        Returns:
            Created Case instance
        """
        case = Case(
            id=f"case_{uuid.uuid4().hex[:12]}",
            title=title,
            description=description,
            status="active",
            created_by=created_by,
            created_at=datetime.now(timezone.utc)
        )

        self.session.add(case)
        self.session.flush()  # Get the ID without committing

        return case

    def get_by_id(self, case_id: str) -> Optional[Case]:
        """
        Get case by ID

        Args:
            case_id: Case ID

        Returns:
            Case instance if found, None otherwise
        """
        return self.session.query(Case).filter(Case.id == case_id).first()

    def get_all_for_user(self, user_id: str) -> List[Case]:
        """
        Get all cases accessible by user (via case_members)

        Args:
            user_id: User ID

        Returns:
            List of Case instances
        """
        # Join with case_members to filter by user access
        cases = (
            self.session.query(Case)
            .join(CaseMember, Case.id == CaseMember.case_id)
            .filter(CaseMember.user_id == user_id)
            .filter(Case.status != "closed")  # Exclude closed cases
            .all()
        )

        return cases

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
        Soft delete case (set status to closed)

        Args:
            case_id: Case ID

        Returns:
            True if deleted, False if not found
        """
        case = self.get_by_id(case_id)
        if not case:
            return False

        case.status = "closed"
        self.session.flush()
        return True
