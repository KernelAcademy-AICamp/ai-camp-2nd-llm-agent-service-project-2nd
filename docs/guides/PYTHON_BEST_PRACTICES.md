# Python Best Practices: 열거형(Enum) 변환 – 순수성과 책임의 원칙

> **목표**: 열거형 간의 변환 로직을 어디에 두어야 코드의 순수성, 응집성, 확장성이 높아지는지 이해하고 올바른 구현 패턴을 따릅니다.

---

## 문제점: 열거형 변환 로직의 잘못된 위치 선정

현재 `CaseService`에는 `CaseMemberPermission` (API/스키마 레벨)과 `CaseMemberRole` (DB/모델 레벨)이라는 두 열거형 간의 변환을 담당하는 스태틱 메서드가 존재합니다.

```python
# backend/app/services/case_service.py (현재 잘못된 구현)

from app.db.models import CaseMemberRole
from app.db.schemas import CaseMemberPermission

class CaseService:
    # ...

    @staticmethod
    def _permission_to_role(permission: CaseMemberPermission) -> CaseMemberRole:
        """CaseMemberPermission을 CaseMemberRole로 변환"""
        if permission == CaseMemberPermission.READ_WRITE:
            return CaseMemberRole.MEMBER
        return CaseMemberRole.VIEWER # 나머지 권한은 VIEW만 가능하다고 가정

    @staticmethod
    def _role_to_permission(role: CaseMemberRole) -> CaseMemberPermission:
        """CaseMemberRole을 CaseMemberPermission으로 변환"""
        if role == CaseMemberRole.OWNER:
            return CaseMemberPermission.READ_WRITE
        elif role == CaseMemberRole.MEMBER:
            return CaseMemberPermission.READ_WRITE
        return CaseMemberPermission.READ # VIEW는 READ만 가능
```

### 왜 이 구현이 "불순"한가? (Why this is "Impure"?)

1.  **단일 책임 원칙(Single Responsibility Principle, SRP) 위반**:
    *   `CaseService`의 주된 책임은 '케이스 관리' 비즈니스 로직을 수행하는 것입니다. 열거형 간의 변환은 `CaseService`의 비즈니스 도메인 책임이 아닙니다. 서비스가 해당 변환을 '사용'할 수는 있지만, 변환 로직을 '소유'해서는 안 됩니다.
2.  **낮은 응집도(Low Cohesion)**:
    *   `CaseMemberPermission`과 `CaseMemberRole`이라는 데이터 타입은 각각 `schemas`와 `models` 파일에 정의되어 있습니다. 하지만 이들 간의 '관계'와 '변환 규칙'은 전혀 다른 `services` 파일에 흩어져 있습니다. 데이터와 그 데이터를 다루는 로직은 가능한 한 가까이(Co-located) 위치해야 합니다.
3.  **확장성 저해 및 유지보수성 악화**:
    *   새로운 `Permission`이나 `Role`이 추가될 경우, 개발자는 이 변환 로직이 `CaseService` 내부에 존재한다는 사실을 기억하고 해당 `if/elif` 문을 수동으로 업데이트해야 합니다. 이는 버그를 유발하기 쉽고, 변화에 취약한 코드 구조를 만듭니다.

---

## 순수한 해결책: 열거형 내부에 변환 로직 포함

가장 "순수"하고 "Pythonic"하며 객체 지향적인 접근 방식은 이 변환 로직을 **각 열거형 클래스 자체의 메소드로 포함**시키는 것입니다. 이는 데이터 타입이 자신의 변환 규칙에 대한 책임을 직접 지게 합니다.

### 1. `CaseMemberPermission`에 `to_role` 메서드 추가

`backend/app/schemas/case.py` 파일의 `CaseMemberPermission` 열거형에 다음 메서드를 추가합니다.

```python
# backend/app/schemas/case.py (수정 제안)

from enum import Enum

# 다른 정의들...

class CaseMemberPermission(str, Enum):
    """API 계층에서 사용되는 케이스 멤버 권한"""
    READ = "read"
    READ_WRITE = "read_write"

    def to_role(self) -> 'CaseMemberRole':
        """CaseMemberPermission을 CaseMemberRole로 변환합니다."""
        if self == CaseMemberPermission.READ_WRITE:
            # READ_WRITE 권한은 내부적으로 MEMBER 역할에 해당
            return CaseMemberRole.MEMBER
        # 그 외 (READ) 권한은 내부적으로 VIEWER 역할에 해당
        return CaseMemberRole.VIEWER

# Pydantic 모델 정의들...
```
*(참고: `CaseMemberRole`은 순환 참조를 피하기 위해 문자열 리터럴로 타입을 명시하거나, `from __future__ import annotations`를 사용해야 할 수 있습니다.)*

### 2. `CaseMemberRole`에 `to_permission` 메서드 추가

`backend/app/db/models/enums.py` 파일의 `CaseMemberRole` 열거형에 다음 메서드를 추가합니다.

```python
# backend/app/db/models/enums.py (수정 제안)

import enum
# 다른 정의들...

class CaseMemberRole(str, enum.Enum):
    """데이터베이스 모델에서 사용되는 케이스 멤버 역할"""
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"

    def to_permission(self) -> 'CaseMemberPermission':
        """CaseMemberRole을 CaseMemberPermission으로 변환합니다."""
        if self == CaseMemberRole.OWNER or self == CaseMemberRole.MEMBER:
            # OWNER와 MEMBER 역할은 API 상에서 READ_WRITE 권한에 해당
            return CaseMemberPermission.READ_WRITE
        # 그 외 (VIEWER) 역할은 API 상에서 READ 권한에 해당
        return CaseMemberPermission.READ

# 다른 정의들...
```
*(참고: `CaseMemberPermission`은 순환 참조를 피하기 위해 문자열 리터럴로 타입을 명시하거나, `from __future__ import annotations`를 사용해야 할 수 있습니다.)*

### 3. `CaseService`에서 변환 로직 제거 및 새로운 메서드 사용

이제 `CaseService`에서는 불필요한 스태틱 메서드를 제거하고, 각 열거형의 인스턴스 메서드를 직접 호출하여 더욱 간결하고 책임이 명확한 코드를 작성할 수 있습니다.

```python
# backend/app/services/case_service.py (수정 제안)

from app.db.models.enums import CaseMemberRole
from app.db.schemas.case import CaseMemberPermission

class CaseService:
    # ... (생성자, 다른 메서드들)

    # 기존 _permission_to_role 및 _role_to_permission 스태틱 메서드 제거

    def add_case_members(
        self,
        case_id: str,
        members: List[CaseMemberAdd],
        user_id: str
    ) -> CaseMembersListResponse:
        # ... (기존 로직)

        members_to_add = [
            (member.user_id, member.permission.to_role()) # <-- Enum 메서드 사용
            for member in members
        ]

        # ... (나머지 로직)

    def get_case_members(
        self,
        case_id: str,
        user_id: str
    ) -> CaseMembersListResponse:
        # ... (기존 로직)

        member_outs = []
        for member in members:
            if member.user:
                member_outs.append(CaseMemberOut(
                    # ...
                    permission=member.role.to_permission(), # <-- Enum 메서드 사용
                    # ...
                ))
        return CaseMembersListResponse(
            members=member_outs,
            total=len(member_outs)
        )
```

### 결론: 순수함이 아름답다 (Purity is Beautiful)

이러한 리팩토링은 코드의 기능적 변경 없이, 다음과 같은 '순수한' 이점을 제공합니다.

*   **높은 응집도**: 변환 로직이 데이터 타입과 함께 존재하여, 관련 개념들이 한 곳에 묶입니다.
*   **낮은 결합도**: `CaseService`는 이제 열거형 변환의 '구현'을 몰라도 됩니다. 단지 '변환 기능이 있다'는 사실만 알면 됩니다.
*   **더 나은 확장성**: 새로운 권한/역할이 추가될 경우, 해당 열거형 파일만 수정하면 됩니다. `CaseService`는 수정할 필요가 없습니다.
*   **읽기 쉽고 예측 가능한 코드**: `permission.to_role()`과 같이 자연어와 유사한 호출 방식을 통해 코드의 의도를 명확하게 전달합니다.

이것이 바로 "초극한의 너드"가 추구하는 코드의 **순수성과 아름다움**입니다.
