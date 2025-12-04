"""
Password Reset Service
Handles password reset token generation and validation
"""

import secrets
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.db.models import User, PasswordResetToken
from app.core.security import hash_password
from app.utils.email import email_service
from app.middleware.error_handler import ValidationError

logger = logging.getLogger(__name__)

# Token expiration time (1 hour)
TOKEN_EXPIRY_HOURS = 1


class PasswordResetService:
    """Service for password reset functionality"""

    def __init__(self, db: Session):
        self.db = db

    def request_password_reset(self, email: str) -> bool:
        """
        Request password reset for email address

        Args:
            email: User's email address

        Returns:
            True if email was sent (or would be sent if user existed)
        """
        # Find user by email
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            # Don't reveal if user exists (prevent enumeration)
            logger.info(f"Password reset requested for non-existent email: {email}")
            return True

        # Invalidate any existing tokens for this user
        self._invalidate_existing_tokens(user.id)

        # Generate new token
        token = self._generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)

        # Save token to database
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(reset_token)
        self.db.commit()

        # Send email
        email_sent = email_service.send_password_reset_email(email, token)

        if email_sent:
            logger.info(f"Password reset email sent to {email}")
        else:
            logger.error(f"Failed to send password reset email to {email}")

        return email_sent

    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using token

        Args:
            token: Password reset token from email
            new_password: New password to set

        Returns:
            True if password was reset successfully

        Raises:
            ValidationError: If token is invalid or expired
        """
        # Find token
        reset_token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used_at.is_(None)
        ).first()

        if not reset_token:
            raise ValidationError("유효하지 않은 비밀번호 재설정 링크입니다.")

        # Check if expired (handle both naive and aware datetimes)
        now = datetime.now(timezone.utc)
        expires_at = reset_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise ValidationError("비밀번호 재설정 링크가 만료되었습니다. 다시 요청해주세요.")

        # Find user
        user = self.db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            raise ValidationError("사용자를 찾을 수 없습니다.")

        # Update password
        user.hashed_password = hash_password(new_password)

        # Mark token as used
        reset_token.used_at = datetime.now(timezone.utc)

        self.db.commit()

        logger.info(f"Password reset successful for user {user.email}")
        return True

    def _generate_token(self) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    def _invalidate_existing_tokens(self, user_id: str) -> None:
        """Invalidate all existing unused tokens for a user"""
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None)
        ).update({
            PasswordResetToken.used_at: datetime.now(timezone.utc)
        })
        self.db.commit()
