"""
User Management Service - Business logic for user administration
Per BACKEND_SERVICE_REPOSITORY_GUIDE.md pattern
"""

import secrets
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.repositories.invite_token_repository import InviteTokenRepository
from app.db.models import UserRole, UserStatus
from app.db.schemas import InviteResponse, UserOut
from app.middleware.error_handler import ValidationError, NotFoundError
from app.core.config import settings


class UserManagementService:
    """
    Service for user management operations (Admin only)
    """

    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.invite_repo = InviteTokenRepository(session)

    def invite_user(self, email: str, role: UserRole, inviter_id: str) -> InviteResponse:
        """
        Create invitation token for new user

        Args:
            email: Invitee's email address
            role: Role to assign
            inviter_id: User ID of the admin creating invitation

        Returns:
            InviteResponse with token and invitation URL

        Raises:
            ValidationError: If user already exists
        """
        # Check if user already exists
        if self.user_repo.exists(email):
            raise ValidationError("이미 등록된 이메일입니다.")

        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Create invite token
        invite_token = self.invite_repo.create(
            email=email,
            role=role,
            token=token,
            created_by=inviter_id
        )

        self.session.commit()

        # Build invitation URL
        invite_url = f"{settings.FRONTEND_URL}/signup?token={token}"

        return InviteResponse(
            invite_token=token,
            invite_url=invite_url,
            email=email,
            role=role,
            expires_at=invite_token.expires_at
        )

    def list_users(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> List[UserOut]:
        """
        List all users with optional filters

        Args:
            email: Filter by email (partial match)
            name: Filter by name (partial match)
            role: Filter by role
            status: Filter by status

        Returns:
            List of UserOut objects
        """
        users = self.user_repo.get_all(
            email=email,
            name=name,
            role=role,
            status=status
        )

        return [
            UserOut(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                status=user.status,
                created_at=user.created_at
            )
            for user in users
        ]

    def delete_user(self, user_id: str, current_user_id: str) -> None:
        """
        Soft delete user by setting status to INACTIVE

        Args:
            user_id: User ID to delete
            current_user_id: Current admin's user ID

        Raises:
            ValidationError: If trying to delete self
            NotFoundError: If user not found
        """
        # Prevent self-deletion
        if user_id == current_user_id:
            raise ValidationError("자기 자신을 삭제할 수 없습니다.")

        # Soft delete user
        user = self.user_repo.soft_delete(user_id)

        if not user:
            raise NotFoundError("사용자를 찾을 수 없습니다.")

        self.session.commit()
