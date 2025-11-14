"""
User Model - REFACTOR Phase
Production-ready user authentication model with secure password handling
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
import bcrypt
import re


class UserRole(str, Enum):
    """사용자 역할 정의"""
    USER = "user"
    LAWYER = "lawyer"
    ADMIN = "admin"
    MANAGER = "manager"

    @classmethod
    def has_permission(cls, role: str, permission: str) -> bool:
        """역할별 권한 확인"""
        permissions = {
            "user": ["read", "write"],
            "lawyer": ["read", "write", "review"],
            "manager": ["read", "write", "review", "manage"],
            "admin": ["read", "write", "review", "manage", "admin"]
        }
        return permission in permissions.get(role, [])


@dataclass
class User:
    """사용자 모델"""

    # 필수 필드
    email: str
    username: str
    password: str

    # 선택 필드
    role: str = field(default=UserRole.USER.value)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None

    # 자동 생성 필드
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """초기화 후 유효성 검증 및 비밀번호 해싱"""
        self._validate_email()
        self._validate_username()
        self._validate_password()
        self._hash_password()

    def _validate_email(self):
        """이메일 형식 검증"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email format")

    def _validate_username(self):
        """사용자명 검증"""
        if not 3 <= len(self.username) <= 30:
            raise ValueError("Username must be between 3 and 30 characters")

        if not re.match(r'^[a-zA-Z0-9_]+$', self.username):
            raise ValueError("Username can only contain alphanumeric characters and underscores")

    def _validate_password(self):
        """비밀번호 강도 검증"""
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not re.search(r'\d', self.password):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', self.password):
            raise ValueError("Password must contain at least one special character")

        if not (re.search(r'[A-Z]', self.password) and re.search(r'[a-z]', self.password)):
            raise ValueError("Password must contain both uppercase and lowercase")

    def _hash_password(self) -> None:
        """
        비밀번호 해싱 (bcrypt 사용)

        Raises:
            ValueError: 비밀번호 해싱 실패시
        """
        if not self.password.startswith('$2b$'):  # bcrypt 해시 체크
            try:
                # bcrypt로 안전한 해싱
                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(self.password.encode('utf-8'), salt)
                self.password = hashed.decode('utf-8')
            except Exception as e:
                raise ValueError(f"Password hashing failed: {e}")

    def verify_password(self, password: str) -> bool:
        """
        비밀번호 검증

        Args:
            password: 검증할 비밀번호

        Returns:
            bool: 비밀번호가 일치하면 True
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                self.password.encode('utf-8')
            )
        except Exception:
            return False

    def is_admin(self) -> bool:
        """관리자 권한 확인"""
        return self.role == UserRole.ADMIN.value

    def is_lawyer(self) -> bool:
        """변호사 권한 확인"""
        return self.role == UserRole.LAWYER.value

    def deactivate(self) -> None:
        """사용자 비활성화"""
        self.is_active = False
        self.deactivated_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        """사용자 활성화"""
        self.is_active = True
        self.deactivated_at = None
        self.updated_at = datetime.now(timezone.utc)

    def update_last_login(self) -> None:
        """마지막 로그인 시간 업데이트"""
        self.last_login = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """사용자 정보를 딕셔너리로 변환 (비밀번호 제외)"""
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "role": self.role,
            "full_name": self.full_name,
            "phone": self.phone,
            "company": self.company,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None
        }