"""
Admin API Router - User Management Endpoints
Requires Admin role for all endpoints
"""

from fastapi import APIRouter, Depends, status, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_admin
from app.db.models import User, UserRole, UserStatus
from app.db.schemas import UserInviteRequest, InviteResponse, UserListResponse
from app.services.user_management_service import UserManagementService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/users/invite",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 초대",
    description="관리자가 새로운 사용자를 초대하고 초대 토큰을 생성합니다."
)
def invite_user(
    request: UserInviteRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    사용자 초대 API

    Args:
        request: 초대할 사용자의 이메일과 역할
        current_user: 현재 인증된 Admin 사용자
        db: 데이터베이스 세션

    Returns:
        InviteResponse: 초대 토큰과 URL

    Raises:
        ValidationError: 이미 등록된 이메일인 경우
        PermissionError: Admin이 아닌 경우
    """
    service = UserManagementService(db)
    return service.invite_user(
        email=request.email,
        role=request.role,
        inviter_id=current_user.id
    )


@router.get(
    "/users",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="사용자 목록 조회",
    description="로펌 내 모든 사용자 목록을 조회합니다. 검색 및 필터링을 지원합니다."
)
def list_users(
    email: Optional[str] = Query(None, description="이메일 검색 (부분 일치)"),
    name: Optional[str] = Query(None, description="이름 검색 (부분 일치)"),
    role: Optional[UserRole] = Query(None, description="역할 필터"),
    status: Optional[UserStatus] = Query(None, description="상태 필터"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    사용자 목록 조회 API

    Args:
        email: 이메일 검색어 (부분 일치)
        name: 이름 검색어 (부분 일치)
        role: 역할 필터 (admin, lawyer, staff)
        status: 상태 필터 (active, inactive)
        current_user: 현재 인증된 Admin 사용자
        db: 데이터베이스 세션

    Returns:
        UserListResponse: 사용자 목록과 총 개수

    Raises:
        PermissionError: Admin이 아닌 경우
    """
    service = UserManagementService(db)
    users = service.list_users(
        email=email,
        name=name,
        role=role,
        status=status
    )

    return UserListResponse(
        users=users,
        total=len(users)
    )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="사용자 삭제",
    description="사용자를 soft delete (status를 inactive로 변경)합니다."
)
def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    사용자 삭제 API (Soft Delete)

    Args:
        user_id: 삭제할 사용자 ID
        current_user: 현재 인증된 Admin 사용자
        db: 데이터베이스 세션

    Returns:
        dict: 성공 메시지

    Raises:
        ValidationError: 자기 자신을 삭제하려는 경우
        NotFoundError: 사용자를 찾을 수 없는 경우
        PermissionError: Admin이 아닌 경우
    """
    service = UserManagementService(db)
    service.delete_user(user_id, current_user.id)

    return {"message": "사용자가 삭제되었습니다.", "user_id": user_id}
