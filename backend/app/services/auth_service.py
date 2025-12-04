"""
Authentication Service - Business logic for authentication
Per BACKEND_SERVICE_REPOSITORY_GUIDE.md pattern
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token, get_token_expire_seconds
from app.db.models import User
from app.db.schemas import TokenResponse, UserOut
from app.middleware.error_handler import AuthenticationError, ConflictError, ValidationError
from app.db.models import UserRole


class AuthService:
    """
    Service for authentication operations
    """

    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepository(session)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password

        Args:
            email: User's email
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.user_repo.get_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    def login(self, email: str, password: str) -> TokenResponse:
        """
        Perform login and generate JWT token

        Args:
            email: User's email
            password: Plain text password

        Returns:
            TokenResponse with access_token, token_type, expires_in, and user info

        Raises:
            AuthenticationError: If authentication fails
        """
        # Authenticate user
        user = self.authenticate_user(email, password)

        if not user:
            # SECURITY: Use generic error message to prevent user enumeration
            raise AuthenticationError("이메일 또는 비밀번호를 확인해 주세요.")

        # Create JWT token
        token_data = {
            "sub": user.id,
            "role": user.role.value,
            "email": user.email
        }

        access_token = create_access_token(data=token_data)
        expires_in = get_token_expire_seconds()

        # Build response
        user_out = UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            status=user.status,
            created_at=user.created_at
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user_out
        )

    # Roles allowed for self-signup (without invitation)
    SELF_SIGNUP_ROLES = {UserRole.LAWYER, UserRole.CLIENT, UserRole.DETECTIVE}

    def signup(
        self,
        email: str,
        password: str,
        name: str,
        accept_terms: bool,
        role: Optional[UserRole] = None
    ) -> TokenResponse:
        """
        Register a new user and generate JWT token

        Args:
            email: User's email
            password: Plain text password (will be hashed with bcrypt)
            name: User's name
            accept_terms: Terms acceptance flag
            role: Optional user role (defaults to LAWYER if not provided)

        Returns:
            TokenResponse with access_token, token_type, expires_in, and user info

        Raises:
            ValidationError: If accept_terms is not True or role is not allowed
            ConflictError: If email already exists
        """
        # Validate terms acceptance
        if not accept_terms:
            raise ValidationError("이용약관 동의가 필요합니다.")

        # Validate role for self-signup
        final_role = role if role else UserRole.LAWYER
        if final_role not in self.SELF_SIGNUP_ROLES:
            raise ValidationError(
                f"자가 등록은 CLIENT, DETECTIVE, LAWYER 역할만 가능합니다. "
                f"ADMIN/STAFF 역할은 초대를 통해서만 가능합니다."
            )

        # Check for duplicate email
        if self.user_repo.exists(email):
            raise ConflictError("이미 등록된 이메일입니다.")

        # Create user with specified role
        user = self.user_repo.create(
            email=email,
            password=password,
            name=name,
            role=final_role
        )

        # Commit transaction
        self.session.commit()
        self.session.refresh(user)

        # Create JWT token
        token_data = {
            "sub": user.id,
            "role": user.role.value,
            "email": user.email
        }

        access_token = create_access_token(data=token_data)
        expires_in = get_token_expire_seconds()

        # Build response
        user_out = UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            status=user.status,
            created_at=user.created_at
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user_out
        )
