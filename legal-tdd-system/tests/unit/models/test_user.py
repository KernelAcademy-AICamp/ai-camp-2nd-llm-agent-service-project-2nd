"""
User Model Tests - TDD RED Phase
Given-When-Then 구조로 테스트 작성
"""

import pytest
from datetime import datetime, timedelta
from typing import Optional
import re


@pytest.mark.green
class TestUserModel:
    """User 모델 테스트 - RED Phase"""

    def test_create_user_with_required_fields(self):
        """Given: 필수 필드만으로 When: User 생성시 Then: 성공"""
        # Given
        from src.models.user import User

        # When
        user = User(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!"
        )

        # Then
        assert user.email == "user@example.com"
        assert user.username == "testuser"
        assert user.id is not None
        assert isinstance(user.created_at, datetime)
        # 비밀번호는 해시되어야 함
        assert user.password != "SecurePass123!"
        assert user.is_active is True

    def test_email_validation(self):
        """Given: 잘못된 이메일로 When: User 생성시 Then: 검증 실패"""
        # Given
        from src.models.user import User

        # When/Then
        with pytest.raises(ValueError, match="Invalid email format"):
            User(
                email="invalid-email",
                username="testuser",
                password="SecurePass123!"
            )

        with pytest.raises(ValueError, match="Invalid email format"):
            User(
                email="@example.com",
                username="testuser",
                password="SecurePass123!"
            )

    def test_password_strength_validation(self):
        """Given: 약한 비밀번호로 When: User 생성시 Then: 검증 실패"""
        # Given
        from src.models.user import User

        # When/Then - 너무 짧은 비밀번호
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            User(
                email="user@example.com",
                username="testuser",
                password="Pass1!"
            )

        # 숫자 없음
        with pytest.raises(ValueError, match="Password must contain at least one digit"):
            User(
                email="user@example.com",
                username="testuser",
                password="Password!"
            )

        # 특수문자 없음
        with pytest.raises(ValueError, match="Password must contain at least one special character"):
            User(
                email="user@example.com",
                username="testuser",
                password="Password123"
            )

        # 대소문자 없음
        with pytest.raises(ValueError, match="Password must contain both uppercase and lowercase"):
            User(
                email="user@example.com",
                username="testuser",
                password="password123!"
            )

    def test_username_validation(self):
        """Given: 잘못된 username으로 When: User 생성시 Then: 검증 실패"""
        # Given
        from src.models.user import User

        # When/Then - 너무 짧은 username
        with pytest.raises(ValueError, match="Username must be between 3 and 30 characters"):
            User(
                email="user@example.com",
                username="ab",
                password="SecurePass123!"
            )

        # 특수문자 포함
        with pytest.raises(ValueError, match="Username can only contain alphanumeric characters and underscores"):
            User(
                email="user@example.com",
                username="test@user",
                password="SecurePass123!"
            )

    def test_verify_password(self):
        """Given: 생성된 User를 When: 비밀번호 확인시 Then: 올바른 검증"""
        # Given
        from src.models.user import User
        user = User(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!"
        )

        # When/Then
        assert user.verify_password("SecurePass123!") is True
        assert user.verify_password("WrongPassword") is False

    def test_user_roles(self):
        """Given: 역할 정보로 When: User 생성시 Then: 역할 관리"""
        # Given
        from src.models.user import User, UserRole

        # When
        user = User(
            email="admin@example.com",
            username="admin",
            password="SecurePass123!",
            role=UserRole.ADMIN
        )

        # Then
        assert user.role == UserRole.ADMIN
        assert user.is_admin() is True
        assert user.is_lawyer() is False

        # 변호사 사용자
        lawyer = User(
            email="lawyer@example.com",
            username="lawyer",
            password="SecurePass123!",
            role=UserRole.LAWYER
        )
        assert lawyer.is_lawyer() is True
        assert lawyer.is_admin() is False

    def test_user_profile_information(self):
        """Given: 프로필 정보로 When: User 생성시 Then: 프로필 저장"""
        # Given
        from src.models.user import User

        # When
        user = User(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!",
            full_name="김철수",
            phone="010-1234-5678",
            company="법무법인 테스트"
        )

        # Then
        assert user.full_name == "김철수"
        assert user.phone == "010-1234-5678"
        assert user.company == "법무법인 테스트"

    def test_user_activation_deactivation(self):
        """Given: 활성 사용자를 When: 비활성화시 Then: 상태 변경"""
        # Given
        from src.models.user import User
        user = User(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!"
        )
        assert user.is_active is True

        # When
        user.deactivate()

        # Then
        assert user.is_active is False
        assert user.deactivated_at is not None

        # 재활성화
        user.activate()
        assert user.is_active is True

    def test_user_last_login_tracking(self):
        """Given: 사용자가 When: 로그인시 Then: 마지막 로그인 시간 기록"""
        # Given
        from src.models.user import User
        import time

        user = User(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!"
        )
        assert user.last_login is None

        # When
        time.sleep(0.001)
        user.update_last_login()

        # Then
        assert user.last_login is not None
        assert isinstance(user.last_login, datetime)
        assert user.last_login > user.created_at

    def test_user_to_dict(self):
        """Given: User 객체를 When: dict로 변환시 Then: 안전한 정보만 포함"""
        # Given
        from src.models.user import User
        user = User(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!",
            full_name="김철수"
        )

        # When
        user_dict = user.to_dict()

        # Then
        assert user_dict["email"] == "user@example.com"
        assert user_dict["username"] == "testuser"
        assert "password" not in user_dict  # 비밀번호는 포함하지 않음
        assert user_dict["full_name"] == "김철수"
        assert "id" in user_dict
        assert "created_at" in user_dict


@pytest.mark.green
class TestUserRole:
    """UserRole Enum 테스트"""

    def test_user_role_enum_values(self):
        """Given: UserRole enum When: 값 확인시 Then: 정의된 역할 존재"""
        # Given/When
        from src.models.user import UserRole

        # Then
        assert UserRole.USER == "user"
        assert UserRole.LAWYER == "lawyer"
        assert UserRole.ADMIN == "admin"
        assert UserRole.MANAGER == "manager"

    def test_role_permissions(self):
        """Given: 각 역할에 대해 When: 권한 확인시 Then: 적절한 권한 반환"""
        # Given
        from src.models.user import UserRole

        # When/Then
        # 일반 사용자
        assert UserRole.has_permission("user", "read") is True
        assert UserRole.has_permission("user", "write") is True
        assert UserRole.has_permission("user", "admin") is False

        # 변호사
        assert UserRole.has_permission("lawyer", "read") is True
        assert UserRole.has_permission("lawyer", "write") is True
        assert UserRole.has_permission("lawyer", "review") is True
        assert UserRole.has_permission("lawyer", "admin") is False

        # 관리자
        assert UserRole.has_permission("admin", "read") is True
        assert UserRole.has_permission("admin", "write") is True
        assert UserRole.has_permission("admin", "review") is True
        assert UserRole.has_permission("admin", "admin") is True


@pytest.mark.green
class TestAuthenticationService:
    """인증 서비스 테스트 - JWT 토큰 관리"""

    def test_generate_access_token(self):
        """Given: 사용자 정보로 When: 액세스 토큰 생성시 Then: 유효한 JWT 토큰"""
        # Given
        from src.services.auth import AuthService
        from src.models.user import User

        user = User(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!"
        )

        # When
        token = AuthService.generate_access_token(user)

        # Then
        assert token is not None
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT 형식

    def test_verify_access_token(self):
        """Given: 유효한 토큰으로 When: 검증시 Then: 사용자 정보 반환"""
        # Given
        from src.services.auth import AuthService
        from src.models.user import User

        user = User(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!"
        )
        token = AuthService.generate_access_token(user)

        # When
        payload = AuthService.verify_access_token(token)

        # Then
        assert payload is not None
        assert payload["user_id"] == str(user.id)
        assert payload["email"] == user.email

    def test_expired_token_verification(self):
        """Given: 만료된 토큰으로 When: 검증시 Then: 검증 실패"""
        # Given
        from src.services.auth import AuthService, TokenExpiredError
        from src.models.user import User

        user = User(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!"
        )
        # 만료 시간이 매우 짧은 토큰 생성
        token = AuthService.generate_access_token(user, expires_in=timedelta(seconds=-1))

        # When/Then
        with pytest.raises(TokenExpiredError):
            AuthService.verify_access_token(token)

    def test_refresh_token_generation(self):
        """Given: 사용자 정보로 When: 리프레시 토큰 생성시 Then: 장기 유효 토큰"""
        # Given
        from src.services.auth import AuthService
        from src.models.user import User

        user = User(
            email="user@example.com",
            username="testuser",
            password="SecurePass123!"
        )

        # When
        refresh_token = AuthService.generate_refresh_token(user)

        # Then
        assert refresh_token is not None
        assert isinstance(refresh_token, str)

        # 리프레시 토큰으로 새 액세스 토큰 생성 가능
        new_access_token = AuthService.refresh_access_token(refresh_token)
        assert new_access_token is not None

    def test_user_registration(self):
        """Given: 신규 사용자 정보로 When: 회원가입시 Then: 사용자 생성 및 토큰 발급"""
        # Given
        from src.services.auth import AuthService

        # When
        result = AuthService.register(
            email="new@example.com",
            username="newuser",
            password="NewPass123!",
            full_name="신규사용자"
        )

        # Then
        assert result["user"] is not None
        assert result["access_token"] is not None
        assert result["refresh_token"] is not None
        assert result["user"].email == "new@example.com"

    def test_user_login(self):
        """Given: 등록된 사용자로 When: 로그인시 Then: 토큰 발급"""
        # Given
        from src.services.auth import AuthService

        # 먼저 사용자 등록
        AuthService.register(
            email="login@example.com",
            username="loginuser",
            password="LoginPass123!"
        )

        # When
        result = AuthService.login(
            email="login@example.com",
            password="LoginPass123!"
        )

        # Then
        assert result["user"] is not None
        assert result["access_token"] is not None
        assert result["refresh_token"] is not None
        assert result["user"].last_login is not None

    def test_login_with_wrong_credentials(self):
        """Given: 잘못된 인증정보로 When: 로그인시 Then: 인증 실패"""
        # Given
        from src.services.auth import AuthService, AuthenticationError

        # 사용자 등록
        AuthService.register(
            email="test@example.com",
            username="testuser",
            password="TestPass123!"
        )

        # When/Then - 잘못된 비밀번호
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            AuthService.login(
                email="test@example.com",
                password="WrongPass123!"
            )

        # 존재하지 않는 이메일
        with pytest.raises(AuthenticationError, match="User not found"):
            AuthService.login(
                email="nonexistent@example.com",
                password="TestPass123!"
            )

    def test_password_reset_token(self):
        """Given: 사용자가 When: 비밀번호 재설정 요청시 Then: 재설정 토큰 생성"""
        # Given
        from src.services.auth import AuthService

        # 사용자 등록
        AuthService.register(
            email="reset@example.com",
            username="resetuser",
            password="OldPass123!"
        )

        # When
        reset_token = AuthService.generate_password_reset_token("reset@example.com")

        # Then
        assert reset_token is not None

        # 재설정 토큰으로 비밀번호 변경
        success = AuthService.reset_password(
            token=reset_token,
            new_password="NewPass123!"
        )
        assert success is True

        # 새 비밀번호로 로그인 가능
        result = AuthService.login(
            email="reset@example.com",
            password="NewPass123!"
        )
        assert result["user"] is not None