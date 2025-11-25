"""
InviteToken Repository - Data access layer for InviteToken model
Per BACKEND_SERVICE_REPOSITORY_GUIDE.md pattern
"""

from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.db.models import InviteToken, UserRole


class InviteTokenRepository:
    """
    Repository for InviteToken model database operations
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        email: str,
        role: UserRole,
        token: str,
        created_by: str,
        expires_in_hours: int = 72
    ) -> InviteToken:
        """
        Create a new invite token

        Args:
            email: Invitee's email address
            role: Role to assign to the invitee
            token: Unique token string
            created_by: User ID of the admin creating the invite
            expires_in_hours: Token expiration time in hours (default: 72)

        Returns:
            Created InviteToken object
        """
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        invite_token = InviteToken(
            email=email,
            role=role,
            token=token,
            created_by=created_by,
            expires_at=expires_at
        )

        self.session.add(invite_token)
        self.session.flush()

        return invite_token

    def get_by_token(self, token: str) -> Optional[InviteToken]:
        """
        Get invite token by token string

        Args:
            token: Token string

        Returns:
            InviteToken object if found, None otherwise
        """
        return self.session.query(InviteToken).filter(InviteToken.token == token).first()

    def get_by_email(self, email: str) -> Optional[InviteToken]:
        """
        Get the most recent unused invite token for an email

        Args:
            email: Invitee's email

        Returns:
            InviteToken object if found, None otherwise
        """
        return (
            self.session.query(InviteToken)
            .filter(
                InviteToken.email == email,
                InviteToken.used_at.is_(None)
            )
            .order_by(InviteToken.created_at.desc())
            .first()
        )

    def mark_as_used(self, token: str) -> Optional[InviteToken]:
        """
        Mark invite token as used

        Args:
            token: Token string

        Returns:
            Updated InviteToken object if found, None otherwise
        """
        invite_token = self.get_by_token(token)
        if invite_token:
            invite_token.used_at = datetime.now(timezone.utc)
            self.session.flush()
        return invite_token

    def is_valid(self, token: str) -> bool:
        """
        Check if token is valid (exists, not used, not expired)

        Args:
            token: Token string

        Returns:
            True if valid, False otherwise
        """
        invite_token = self.get_by_token(token)
        if not invite_token:
            return False

        # Check if already used
        if invite_token.used_at is not None:
            return False

        # Check if expired
        if invite_token.expires_at < datetime.now(timezone.utc):
            return False

        return True
