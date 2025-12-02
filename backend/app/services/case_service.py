"""
Case Service - Business logic for case management
Implements Service pattern per BACKEND_SERVICE_REPOSITORY_GUIDE.md
"""

from sqlalchemy.orm import Session
from typing import List
from app.db.models import CaseMemberRole
from app.db.schemas import (
    CaseCreate,
    CaseUpdate,
    CaseOut,
    CaseMemberAdd,
    CaseMemberOut,
    CaseMemberPermission,
    CaseMembersListResponse
)
from app.repositories.case_repository import CaseRepository
from app.repositories.case_member_repository import CaseMemberRepository
from app.repositories.user_repository import UserRepository
from app.middleware import NotFoundError, PermissionError
from app.utils.qdrant import delete_case_collection
from app.utils.dynamo import clear_case_evidence
import logging

logger = logging.getLogger(__name__)


class CaseService:
    """
    Service for case management business logic
    """

    def __init__(self, db: Session):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.member_repo = CaseMemberRepository(db)
        self.user_repo = UserRepository(db)

    @staticmethod
    def _permission_to_role(permission: CaseMemberPermission) -> CaseMemberRole:
        """Convert CaseMemberPermission to CaseMemberRole"""
        if permission == CaseMemberPermission.READ_WRITE:
            return CaseMemberRole.MEMBER
        return CaseMemberRole.VIEWER

    @staticmethod
    def _role_to_permission(role: CaseMemberRole) -> CaseMemberPermission:
        """Convert CaseMemberRole to CaseMemberPermission"""
        if role == CaseMemberRole.OWNER:
            return CaseMemberPermission.READ_WRITE
        elif role == CaseMemberRole.MEMBER:
            return CaseMemberPermission.READ_WRITE
        return CaseMemberPermission.READ

    def create_case(self, case_data: CaseCreate, user_id: str) -> CaseOut:
        """
        Create a new case and add creator as owner

        Args:
            case_data: Case creation data
            user_id: ID of user creating the case

        Returns:
            Created case data
        """
        # Create case in database
        case = self.case_repo.create(
            title=case_data.title,
            client_name=case_data.client_name,
            description=case_data.description,
            created_by=user_id
        )

        # Add creator as owner in case_members
        self.member_repo.add_member(
            case_id=case.id,
            user_id=user_id,
            role="owner"
        )

        # Commit transaction
        self.db.commit()
        self.db.refresh(case)

        return CaseOut.model_validate(case)

    def get_cases_for_user(self, user_id: str) -> List[CaseOut]:
        """
        Get all cases accessible by user

        Args:
            user_id: User ID

        Returns:
            List of cases user has access to
        """
        cases = self.case_repo.get_all_for_user(user_id)
        return [CaseOut.model_validate(case) for case in cases]

    def get_case_by_id(self, case_id: str, user_id: str) -> CaseOut:
        """
        Get case by ID with permission check

        Args:
            case_id: Case ID
            user_id: User ID requesting access

        Returns:
            Case data

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access
        """
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")

        # Check if user has access
        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

        return CaseOut.model_validate(case)

    def update_case(self, case_id: str, update_data: CaseUpdate, user_id: str) -> CaseOut:
        """
        Update case title and/or description

        Args:
            case_id: Case ID
            update_data: Update data (title, description)
            user_id: User ID requesting update

        Returns:
            Updated case data

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have write access
        """
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")

        # Check if user has write access (owner or member with read_write)
        member = self.member_repo.get_member(case_id, user_id)
        if not member:
            raise PermissionError("You do not have access to this case")

        # Only owner and member (not viewer) can update
        if member.role not in [CaseMemberRole.OWNER, CaseMemberRole.MEMBER]:
            raise PermissionError("You do not have permission to update this case")

        # Update case fields
        if update_data.title is not None:
            case.title = update_data.title
        if update_data.description is not None:
            case.description = update_data.description

        self.db.commit()
        self.db.refresh(case)

        return CaseOut.model_validate(case)

    def delete_case(self, case_id: str, user_id: str):
        """
        Soft delete a case (set status to closed)

        Args:
            case_id: Case ID
            user_id: User ID requesting deletion

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have owner access
        """
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")

        # Check if user is owner
        member = self.member_repo.get_member(case_id, user_id)
        if not member or member.role != CaseMemberRole.OWNER:
            raise PermissionError("Only case owner can delete the case")

        # Soft delete case in RDS
        self.case_repo.soft_delete(case_id)

        # Delete Qdrant RAG collection for this case
        try:
            deleted = delete_case_collection(case_id)
            if deleted:
                logger.info(f"Deleted Qdrant collection for case {case_id}")
            else:
                logger.warning(f"Qdrant collection for case {case_id} not found or already deleted")
        except Exception as e:
            logger.error(f"Failed to delete Qdrant collection for case {case_id}: {e}")
            # Continue with deletion even if Qdrant fails

        # Clear DynamoDB evidence metadata for this case
        try:
            cleared_count = clear_case_evidence(case_id)
            logger.info(f"Cleared {cleared_count} evidence items from DynamoDB for case {case_id}")
        except Exception as e:
            logger.error(f"Failed to clear DynamoDB evidence for case {case_id}: {e}")
            # Continue with deletion even if DynamoDB fails

        self.db.commit()

    def add_case_members(
        self,
        case_id: str,
        members: List[CaseMemberAdd],
        user_id: str
    ) -> CaseMembersListResponse:
        """
        Add multiple members to a case

        Args:
            case_id: Case ID
            members: List of members to add
            user_id: User ID requesting the operation

        Returns:
            Updated list of all case members

        Raises:
            NotFoundError: Case not found or user not found
            PermissionError: User is not owner or admin
            ValidationError: Invalid member data
        """
        # Check if case exists
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")

        # Check if requester is owner or admin
        is_owner = self.member_repo.is_owner(case_id, user_id)
        requester = self.user_repo.get_by_id(user_id)

        if not is_owner and (not requester or requester.role.value != "admin"):
            raise PermissionError("Only case owner or admin can add members")

        # Validate all users exist
        for member in members:
            user = self.user_repo.get_by_id(member.user_id)
            if not user:
                raise NotFoundError(f"User {member.user_id}")

        # Convert permissions to roles and add members
        members_to_add = [
            (member.user_id, self._permission_to_role(member.permission))
            for member in members
        ]

        self.member_repo.add_members_batch(case_id, members_to_add)
        self.db.commit()

        # Return updated member list
        return self.get_case_members(case_id, user_id)

    def get_case_members(
        self,
        case_id: str,
        user_id: str
    ) -> CaseMembersListResponse:
        """
        Get all members of a case

        Args:
            case_id: Case ID
            user_id: User ID requesting the list

        Returns:
            List of case members with user information

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access to case
        """
        # Check if case exists
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")

        # Check if user has access
        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

        # Get all members
        members = self.member_repo.get_all_members(case_id)

        # Convert to response schema
        member_outs = []
        for member in members:
            user = self.user_repo.get_by_id(member.user_id)
            if user:
                member_outs.append(CaseMemberOut(
                    user_id=user.id,
                    name=user.name,
                    email=user.email,
                    permission=self._role_to_permission(member.role),
                    role=member.role
                ))

        return CaseMembersListResponse(
            members=member_outs,
            total=len(member_outs)
        )
