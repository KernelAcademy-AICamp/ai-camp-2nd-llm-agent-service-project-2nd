"""
Unit tests for Password Reset Service
TDD - Improving test coverage for password_reset_service.py
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import uuid

from app.services.password_reset_service import PasswordResetService
from app.db.models import User, PasswordResetToken
from app.middleware.error_handler import ValidationError


class TestRequestPasswordReset:
    """Unit tests for request_password_reset method"""

    def test_request_reset_nonexistent_user(self, test_env):
        """Returns True even for non-existent user (prevent enumeration)"""
        from app.db.session import get_db

        db = next(get_db())
        service = PasswordResetService(db)

        result = service.request_password_reset("nonexistent@test.com")

        assert result is True

        db.close()

    def test_request_reset_existing_user(self, test_env):
        """Creates token and sends email for existing user"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"reset_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Reset User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = PasswordResetService(db)

        with patch('app.services.password_reset_service.email_service') as mock_email:
            mock_email.send_password_reset_email.return_value = True

            result = service.request_password_reset(user.email)

            assert result is True
            mock_email.send_password_reset_email.assert_called_once()

        # Cleanup
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_request_reset_invalidates_existing_tokens(self, test_env):
        """Existing tokens are invalidated when new one is requested"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"inv_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Inv User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create existing token
        old_token = PasswordResetToken(
            user_id=user.id,
            token="old_token_123",
            expires_at=now + timedelta(hours=1)
        )
        db.add(old_token)
        db.commit()
        db.refresh(old_token)

        service = PasswordResetService(db)

        with patch('app.services.password_reset_service.email_service') as mock_email:
            mock_email.send_password_reset_email.return_value = True

            service.request_password_reset(user.email)

        # Check that old token is now marked as used
        db.refresh(old_token)
        assert old_token.used_at is not None

        # Cleanup
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()
        db.delete(user)
        db.commit()
        db.close()


class TestResetPassword:
    """Unit tests for reset_password method"""

    def test_reset_password_success(self, test_env):
        """Successfully reset password with valid token"""
        from app.db.session import get_db
        from app.core.security import hash_password, verify_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"rpass_{unique_id}@test.com",
            hashed_password=hash_password("old_password"),
            name="RPass User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = PasswordResetToken(
            user_id=user.id,
            token=f"valid_token_{unique_id}",
            expires_at=now + timedelta(hours=1)
        )
        db.add(token)
        db.commit()
        db.refresh(token)

        service = PasswordResetService(db)
        result = service.reset_password(token.token, "new_password_123")

        assert result is True

        # Verify password was changed
        db.refresh(user)
        assert verify_password("new_password_123", user.hashed_password)

        # Verify token was marked as used
        db.refresh(token)
        assert token.used_at is not None

        # Cleanup
        db.query(PasswordResetToken).filter(PasswordResetToken.id == token.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_reset_password_invalid_token(self, test_env):
        """Raises ValidationError for invalid token"""
        from app.db.session import get_db

        db = next(get_db())
        service = PasswordResetService(db)

        with pytest.raises(ValidationError):
            service.reset_password("invalid_token_xyz", "new_password")

        db.close()

    def test_reset_password_expired_token(self, test_env):
        """Raises ValidationError for expired token"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"exp_{unique_id}@test.com",
            hashed_password=hash_password("password"),
            name="Exp User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create expired token (1 hour ago)
        token = PasswordResetToken(
            user_id=user.id,
            token=f"expired_token_{unique_id}",
            expires_at=now - timedelta(hours=1)
        )
        db.add(token)
        db.commit()
        db.refresh(token)

        service = PasswordResetService(db)

        with pytest.raises(ValidationError, match="만료"):
            service.reset_password(token.token, "new_password")

        # Cleanup
        db.query(PasswordResetToken).filter(PasswordResetToken.id == token.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_reset_password_already_used_token(self, test_env):
        """Raises ValidationError for already used token"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"used_{unique_id}@test.com",
            hashed_password=hash_password("password"),
            name="Used User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create already-used token
        token = PasswordResetToken(
            user_id=user.id,
            token=f"used_token_{unique_id}",
            expires_at=now + timedelta(hours=1),
            used_at=now - timedelta(minutes=30)
        )
        db.add(token)
        db.commit()
        db.refresh(token)

        service = PasswordResetService(db)

        with pytest.raises(ValidationError):
            service.reset_password(token.token, "new_password")

        # Cleanup
        db.query(PasswordResetToken).filter(PasswordResetToken.id == token.id).delete()
        db.delete(user)
        db.commit()
        db.close()


class TestHelperMethods:
    """Unit tests for helper methods"""

    def test_generate_token(self, test_env):
        """Token generation creates unique tokens"""
        from app.db.session import get_db

        db = next(get_db())
        service = PasswordResetService(db)

        token1 = service._generate_token()
        token2 = service._generate_token()

        assert token1 != token2
        assert len(token1) > 20  # Should be reasonably long

        db.close()

    def test_invalidate_existing_tokens(self, test_env):
        """All unused tokens are invalidated"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"invt_{unique_id}@test.com",
            hashed_password=hash_password("password"),
            name="InvT User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create multiple unused tokens
        tokens = []
        for i in range(3):
            token = PasswordResetToken(
                user_id=user.id,
                token=f"token_{unique_id}_{i}",
                expires_at=now + timedelta(hours=1)
            )
            db.add(token)
            db.commit()
            db.refresh(token)
            tokens.append(token)

        service = PasswordResetService(db)
        service._invalidate_existing_tokens(user.id)

        # All tokens should now be marked as used
        for token in tokens:
            db.refresh(token)
            assert token.used_at is not None

        # Cleanup
        for token in tokens:
            db.query(PasswordResetToken).filter(PasswordResetToken.id == token.id).delete()
        db.delete(user)
        db.commit()
        db.close()
