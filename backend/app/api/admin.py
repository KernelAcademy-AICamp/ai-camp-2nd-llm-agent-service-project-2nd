"""
Admin API Router - User Management Endpoints
Requires Admin role for all endpoints
"""

from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.core.dependencies import require_admin
from app.db.models import User, UserRole, UserStatus
from app.db.schemas import (
    UserInviteRequest,
    InviteResponse,
    UserListResponse,
    RolePermissionsResponse,
    UpdateRolePermissionsRequest,
    RolePermissions,
    AuditAction,
    AuditLogListRequest,
    AuditLogListResponse
)
from app.services.user_management_service import UserManagementService
from app.services.role_management_service import RoleManagementService
from app.services.audit_log_service import AuditLogService

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


@router.get(
    "/roles",
    response_model=RolePermissionsResponse,
    status_code=status.HTTP_200_OK,
    summary="역할별 권한 조회",
    description="모든 역할(ADMIN, LAWYER, STAFF)의 권한 매트릭스를 조회합니다."
)
def get_roles(
    current_user: User = Depends(require_admin)
):
    """
    역할별 권한 매트릭스 조회 API

    Args:
        current_user: 현재 인증된 Admin 사용자

    Returns:
        RolePermissionsResponse: 모든 역할의 권한 정보

    Raises:
        PermissionError: Admin이 아닌 경우
    """
    service = RoleManagementService()
    roles = service.get_all_roles()

    return RolePermissionsResponse(roles=roles)


@router.put(
    "/roles/{role}/permissions",
    response_model=RolePermissions,
    status_code=status.HTTP_200_OK,
    summary="역할 권한 업데이트",
    description="특정 역할의 권한을 업데이트합니다."
)
def update_role_permissions(
    role: UserRole,
    request: UpdateRolePermissionsRequest,
    current_user: User = Depends(require_admin)
):
    """
    역할 권한 업데이트 API

    Note: MVP 버전에서는 in-memory 업데이트만 지원합니다.
    실제 프로덕션에서는 permissions 테이블에 저장되어야 합니다.

    Args:
        role: 업데이트할 역할 (ADMIN, LAWYER, STAFF)
        request: 새로운 권한 설정
        current_user: 현재 인증된 Admin 사용자

    Returns:
        RolePermissions: 업데이트된 권한 정보

    Raises:
        PermissionError: Admin이 아닌 경우
    """
    service = RoleManagementService()
    updated_permissions = service.update_role_permissions(
        role=role,
        cases=request.cases,
        evidence=request.evidence,
        admin=request.admin,
        billing=request.billing
    )

    return updated_permissions


@router.get(
    "/audit",
    response_model=AuditLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="감사 로그 조회",
    description="사용자 활동 감사 로그를 조회합니다. 날짜, 사용자, 액션별 필터링과 페이지네이션을 지원합니다."
)
def get_audit_logs(
    start_date: Optional[datetime] = Query(None, description="시작 날짜 (UTC)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜 (UTC)"),
    user_id: Optional[str] = Query(None, description="사용자 ID 필터"),
    actions: Optional[List[AuditAction]] = Query(None, description="액션 타입 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(50, ge=1, le=100, description="페이지 크기"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    감사 로그 조회 API

    **Query Parameters:**
    - start_date: 시작 날짜 (UTC, ISO 8601 형식)
    - end_date: 종료 날짜 (UTC, ISO 8601 형식)
    - user_id: 사용자 ID 필터 (특정 사용자의 로그만 조회)
    - actions: 액션 타입 필터 (여러 개 선택 가능)
      - LOGIN, LOGOUT, SIGNUP
      - CREATE_CASE, VIEW_CASE, UPDATE_CASE, DELETE_CASE
      - UPLOAD_EVIDENCE, VIEW_EVIDENCE, DELETE_EVIDENCE
      - INVITE_USER, DELETE_USER, UPDATE_PERMISSIONS
      - GENERATE_DRAFT
    - page: 페이지 번호 (1부터 시작)
    - page_size: 페이지 크기 (1-100)

    **Response:**
    - 200: 감사 로그 목록 (페이지네이션 포함)
    - logs: 로그 목록 (사용자 이름, 이메일 포함)
    - total: 전체 로그 개수
    - page: 현재 페이지
    - page_size: 페이지 크기
    - total_pages: 전체 페이지 수

    **Errors:**
    - 401: 인증되지 않은 사용자
    - 403: Admin 권한 없음

    **Authentication:**
    - Requires Admin role

    **Notes:**
    - 로그는 최신순으로 정렬됩니다 (timestamp DESC)
    - 모든 날짜는 UTC 기준입니다
    - 사용자 정보 (이름, 이메일)는 JOIN하여 포함됩니다
    """
    service = AuditLogService(db)

    request = AuditLogListRequest(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        actions=actions,
        page=page,
        page_size=page_size
    )

    return service.get_audit_logs(request)


@router.get(
    "/audit/export",
    status_code=status.HTTP_200_OK,
    summary="감사 로그 CSV 내보내기",
    description="감사 로그를 CSV 형식으로 다운로드합니다. 동일한 필터링 조건을 적용합니다."
)
def export_audit_logs(
    start_date: Optional[datetime] = Query(None, description="시작 날짜 (UTC)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜 (UTC)"),
    user_id: Optional[str] = Query(None, description="사용자 ID 필터"),
    actions: Optional[List[AuditAction]] = Query(None, description="액션 타입 필터"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    감사 로그 CSV 내보내기 API

    **Query Parameters:**
    - start_date: 시작 날짜 (UTC, ISO 8601 형식)
    - end_date: 종료 날짜 (UTC, ISO 8601 형식)
    - user_id: 사용자 ID 필터
    - actions: 액션 타입 필터 (여러 개 선택 가능)

    **Response:**
    - 200: CSV 파일 (text/csv)
    - Content-Disposition: attachment; filename="audit_logs_YYYYMMDD_HHMMSS.csv"

    **CSV Format:**
    - Header: ID,User ID,User Email,User Name,Action,Object ID,Timestamp
    - Data: One row per log entry
    - Timestamp format: YYYY-MM-DD HH:MM:SS (UTC)

    **Errors:**
    - 401: 인증되지 않은 사용자
    - 403: Admin 권한 없음

    **Authentication:**
    - Requires Admin role

    **Notes:**
    - 모든 로그를 한 번에 내보냅니다 (페이지네이션 없음)
    - 로그는 최신순으로 정렬됩니다
    - 대량의 로그를 내보낼 경우 시간이 걸릴 수 있습니다
    """
    service = AuditLogService(db)

    csv_content = service.export_audit_logs_csv(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        actions=actions
    )

    # Generate filename with current timestamp
    filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    # Return CSV as streaming response
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
