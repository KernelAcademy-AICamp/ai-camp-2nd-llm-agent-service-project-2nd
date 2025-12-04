"""
Unit tests for User Management Service
TDD - Improving test coverage for user_management_service.py
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import uuid

from app.services.user_management_service import UserManagementService
from app.db.models import User, InviteToken, UserRole, UserStatus
from app.middleware.error_handler import ValidationError, NotFoundError


class TestInviteUser:
    """Unit tests for invite_user method"""

    def test_invite_user_success(self, test_env):
        """Successfully invite a new user"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        admin = User(
            email=f"admin_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Admin User",
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        service = UserManagementService(db)

        result = service.invite_user(
            email=f"new_{unique_id}@test.com",
            role=UserRole.LAWYER,
            inviter_id=admin.id
        )

        assert result is not None
        assert result.email == f"new_{unique_id}@test.com"
        assert result.role == UserRole.LAWYER
        assert result.invite_token is not None
        assert "signup?token=" in result.invite_url

        # Cleanup
        db.query(InviteToken).filter(InviteToken.email == f"new_{unique_id}@test.com").delete()
        db.delete(admin)
        db.commit()
        db.close()

    def test_invite_user_already_exists(self, test_env):
        """Raises ValidationError when user already exists"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        admin = User(
            email=f"adm2_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Admin",
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        existing = User(
            email=f"exist_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Existing User",
            role="lawyer"
        )
        db.add(existing)
        db.commit()
        db.refresh(existing)

        service = UserManagementService(db)

        with pytest.raises(ValidationError, match="이미 등록된"):
            service.invite_user(
                email=existing.email,
                role=UserRole.LAWYER,
                inviter_id=admin.id
            )

        # Cleanup
        db.delete(existing)
        db.delete(admin)
        db.commit()
        db.close()


class TestListUsers:
    """Unit tests for list_users method"""

    def test_list_users_all(self, test_env):
        """List all users without filters"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        users = []
        for i in range(3):
            user = User(
                email=f"list_{unique_id}_{i}@test.com",
                hashed_password=hash_password("pass"),
                name=f"List User {i}",
                role="lawyer"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            users.append(user)

        service = UserManagementService(db)
        result = service.list_users()

        # Should include at least our 3 users
        assert len(result) >= 3

        # Cleanup
        for user in users:
            db.delete(user)
        db.commit()
        db.close()

    def test_list_users_with_role_filter(self, test_env):
        """Filter users by role"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        lawyer = User(
            email=f"lawyer_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Lawyer",
            role="lawyer"
        )
        db.add(lawyer)
        db.commit()
        db.refresh(lawyer)

        client = User(
            email=f"client_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Client",
            role="client"
        )
        db.add(client)
        db.commit()
        db.refresh(client)

        service = UserManagementService(db)
        result = service.list_users(role=UserRole.LAWYER)

        # All results should be lawyers
        for user in result:
            assert user.role == UserRole.LAWYER

        # Cleanup
        db.delete(lawyer)
        db.delete(client)
        db.commit()
        db.close()


class TestDeleteUser:
    """Unit tests for delete_user method"""

    def test_delete_user_success(self, test_env):
        """Successfully soft delete a user"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        admin = User(
            email=f"delad_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Admin",
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        target = User(
            email=f"target_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Target",
            role="lawyer"
        )
        db.add(target)
        db.commit()
        db.refresh(target)

        service = UserManagementService(db)
        service.delete_user(target.id, admin.id)

        # Verify user was soft deleted (status changed)
        db.refresh(target)
        assert target.status == UserStatus.INACTIVE

        # Cleanup
        db.delete(target)
        db.delete(admin)
        db.commit()
        db.close()

    def test_delete_user_self_deletion(self, test_env):
        """Raises ValidationError when trying to delete self"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        admin = User(
            email=f"self_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Admin",
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        service = UserManagementService(db)

        with pytest.raises(ValidationError, match="자기 자신"):
            service.delete_user(admin.id, admin.id)

        # Cleanup
        db.delete(admin)
        db.commit()
        db.close()

    def test_delete_user_not_found(self, test_env):
        """Raises NotFoundError when user not found"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        admin = User(
            email=f"nfad_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Admin",
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        service = UserManagementService(db)

        with pytest.raises(NotFoundError):
            service.delete_user("nonexistent-user-id", admin.id)

        # Cleanup
        db.delete(admin)
        db.commit()
        db.close()
