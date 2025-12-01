"""
User Repository - Data access layer for User model
Per BACKEND_SERVICE_REPOSITORY_GUIDE.md pattern
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import User, UserRole, UserStatus
from app.core.security import hash_password


class UserRepository:
    """
    Repository for User model database operations
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise
        """
        return self.session.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User's ID

        Returns:
            User object if found, None otherwise
        """
        return self.session.query(User).filter(User.id == user_id).first()

    def create(self, email: str, password: str, name: str, role: UserRole = UserRole.LAWYER) -> User:
        """
        Create a new user

        Args:
            email: User's email
            password: Plain text password (will be hashed)
            name: User's name
            role: User's role (default: LAWYER)

        Returns:
            Created User object
        """
        hashed_password = hash_password(password)

        user = User(
            email=email,
            hashed_password=hashed_password,
            name=name,
            role=role
        )

        self.session.add(user)
        self.session.flush()  # Get ID without committing transaction

        return user

    def exists(self, email: str) -> bool:
        """
        Check if user with email exists

        Args:
            email: User's email

        Returns:
            True if user exists, False otherwise
        """
        return self.session.query(User).filter(User.email == email).count() > 0

    def get_all(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> List[User]:
        """
        Get all users with optional filters

        Args:
            email: Filter by email (partial match)
            name: Filter by name (partial match)
            role: Filter by role
            status: Filter by status

        Returns:
            List of User objects matching filters
        """
        query = self.session.query(User)

        if email:
            query = query.filter(User.email.ilike(f"%{email}%"))
        if name:
            query = query.filter(User.name.ilike(f"%{name}%"))
        if role:
            query = query.filter(User.role == role)
        if status:
            query = query.filter(User.status == status)

        return query.order_by(User.created_at.desc()).all()

    def soft_delete(self, user_id: str) -> Optional[User]:
        """
        Soft delete user by setting status to INACTIVE

        Args:
            user_id: User's ID

        Returns:
            Updated User object if found, None otherwise
        """
        user = self.get_by_id(user_id)
        if user:
            user.status = UserStatus.INACTIVE
            self.session.flush()
        return user
