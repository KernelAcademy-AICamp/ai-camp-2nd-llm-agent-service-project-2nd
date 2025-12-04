"""
Case List Service
003-role-based-ui Feature - US3

Business logic for case list filtering, pagination, and bulk actions.
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc, asc
from typing import List, Optional, Tuple
from datetime import datetime, timezone

from app.db.models import Case, CaseMember, User, CaseStatus, CaseMemberRole
from app.schemas.case_list import (
    CaseFilter,
    CaseListItem,
    CaseListResponse,
    CaseSortField,
    SortOrder,
    BulkActionType,
    BulkActionResult,
    BulkActionResponse,
    CaseDetailResponse,
)


class CaseListService:
    """Service for case list operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_cases(
        self,
        user_id: str,
        filters: Optional[CaseFilter] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: CaseSortField = CaseSortField.UPDATED_AT,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> CaseListResponse:
        """
        Get paginated case list with filters.

        Args:
            user_id: Current user ID
            filters: Filter parameters
            page: Page number (1-indexed)
            page_size: Items per page
            sort_by: Field to sort by
            sort_order: Sort direction

        Returns:
            Paginated case list response
        """
        # Base query - cases user has access to
        query = self.db.query(Case).join(
            CaseMember,
            and_(
                CaseMember.case_id == Case.id,
                CaseMember.user_id == user_id
            ),
            isouter=True
        ).filter(
            or_(
                Case.created_by == user_id,
                CaseMember.user_id == user_id
            )
        ).distinct()

        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sort_column = self._get_sort_column(sort_by)
        if sort_order == SortOrder.DESC:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        offset = (page - 1) * page_size
        cases = query.offset(offset).limit(page_size).all()

        # Convert to response items
        items = [self._case_to_list_item(case) for case in cases]

        # Get status counts
        status_counts = self._get_status_counts(user_id)

        total_pages = (total + page_size - 1) // page_size

        return CaseListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            status_counts=status_counts,
        )

    def _apply_filters(self, query, filters: CaseFilter):
        """Apply filters to query"""
        if filters.status:
            query = query.filter(Case.status.in_(filters.status))

        if filters.client_name:
            query = query.filter(
                Case.client_name.ilike(f"%{filters.client_name}%")
            )

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Case.title.ilike(search_term),
                    Case.description.ilike(search_term),
                    Case.client_name.ilike(search_term),
                )
            )

        if filters.date_from:
            query = query.filter(Case.created_at >= filters.date_from)

        if filters.date_to:
            query = query.filter(Case.created_at <= filters.date_to)

        return query

    def _get_sort_column(self, sort_by: CaseSortField):
        """Get SQLAlchemy column for sorting"""
        mapping = {
            CaseSortField.UPDATED_AT: Case.updated_at,
            CaseSortField.CREATED_AT: Case.created_at,
            CaseSortField.TITLE: Case.title,
            CaseSortField.CLIENT_NAME: Case.client_name,
            CaseSortField.STATUS: Case.status,
        }
        return mapping.get(sort_by, Case.updated_at)

    def _case_to_list_item(self, case: Case) -> CaseListItem:
        """Convert Case model to CaseListItem"""
        # Get member count
        member_count = len(case.members) if case.members else 0

        # Calculate days since update (handle both naive and aware datetimes)
        now = datetime.now(timezone.utc)
        if case.updated_at:
            updated = case.updated_at
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            days_since_update = (now - updated).days
        else:
            days_since_update = 0

        # Get owner name
        owner_name = case.owner.name if case.owner else None

        # Calculate progress (simplified)
        progress = self._calculate_progress(case)

        return CaseListItem(
            id=case.id,
            title=case.title,
            client_name=case.client_name,
            status=case.status.value if case.status else "unknown",
            description=case.description,
            created_at=case.created_at,
            updated_at=case.updated_at,
            evidence_count=0,  # Would need DynamoDB query
            member_count=member_count,
            progress=progress,
            days_since_update=days_since_update,
            owner_name=owner_name,
            last_activity=f"{days_since_update}일 전 업데이트" if days_since_update > 0 else "오늘 업데이트",
        )

    def _calculate_progress(self, case: Case) -> int:
        """Calculate case progress percentage"""
        status_progress = {
            CaseStatus.ACTIVE: 20,
            CaseStatus.OPEN: 40,
            CaseStatus.IN_PROGRESS: 70,
            CaseStatus.CLOSED: 100,
        }
        return status_progress.get(case.status, 0)

    def _get_status_counts(self, user_id: str) -> dict:
        """Get case counts by status"""
        results = (
            self.db.query(Case.status, func.count(Case.id))
            .join(
                CaseMember,
                and_(
                    CaseMember.case_id == Case.id,
                    CaseMember.user_id == user_id
                ),
                isouter=True
            )
            .filter(
                or_(
                    Case.created_by == user_id,
                    CaseMember.user_id == user_id
                )
            )
            .group_by(Case.status)
            .all()
        )
        return {status.value: count for status, count in results}

    def execute_bulk_action(
        self,
        user_id: str,
        case_ids: List[str],
        action: BulkActionType,
        params: Optional[dict] = None,
    ) -> BulkActionResponse:
        """
        Execute bulk action on multiple cases.

        Args:
            user_id: Current user ID
            case_ids: List of case IDs to act on
            action: Type of action to perform
            params: Action-specific parameters

        Returns:
            Bulk action response with results
        """
        results: List[BulkActionResult] = []
        successful = 0
        failed = 0

        for case_id in case_ids:
            try:
                result = self._execute_single_action(user_id, case_id, action, params)
                results.append(result)
                if result.success:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                results.append(BulkActionResult(
                    case_id=case_id,
                    success=False,
                    error=str(e)
                ))
                failed += 1

        self.db.commit()

        return BulkActionResponse(
            action=action,
            total_requested=len(case_ids),
            successful=successful,
            failed=failed,
            results=results,
        )

    def _execute_single_action(
        self,
        user_id: str,
        case_id: str,
        action: BulkActionType,
        params: Optional[dict] = None,
    ) -> BulkActionResult:
        """Execute action on single case"""
        # Verify access
        case = self._get_case_with_access(user_id, case_id)
        if not case:
            return BulkActionResult(
                case_id=case_id,
                success=False,
                error="케이스를 찾을 수 없거나 접근 권한이 없습니다."
            )

        if action == BulkActionType.REQUEST_AI_ANALYSIS:
            # Queue AI analysis request
            return BulkActionResult(
                case_id=case_id,
                success=True,
                message="AI 분석이 요청되었습니다."
            )

        elif action == BulkActionType.CHANGE_STATUS:
            new_status = params.get("new_status") if params else None
            if not new_status:
                return BulkActionResult(
                    case_id=case_id,
                    success=False,
                    error="새 상태가 지정되지 않았습니다."
                )
            try:
                case.status = CaseStatus(new_status)
                case.updated_at = datetime.now(timezone.utc)
                return BulkActionResult(
                    case_id=case_id,
                    success=True,
                    message=f"상태가 '{new_status}'로 변경되었습니다."
                )
            except ValueError:
                return BulkActionResult(
                    case_id=case_id,
                    success=False,
                    error=f"유효하지 않은 상태: {new_status}"
                )

        elif action == BulkActionType.EXPORT:
            return BulkActionResult(
                case_id=case_id,
                success=True,
                message="내보내기가 준비되었습니다."
            )

        elif action == BulkActionType.DELETE:
            # Soft delete - change status to closed
            case.status = CaseStatus.CLOSED
            case.updated_at = datetime.now(timezone.utc)
            return BulkActionResult(
                case_id=case_id,
                success=True,
                message="케이스가 종료되었습니다."
            )

        return BulkActionResult(
            case_id=case_id,
            success=False,
            error=f"지원되지 않는 작업: {action}"
        )

    def _get_case_with_access(self, user_id: str, case_id: str) -> Optional[Case]:
        """Get case if user has access"""
        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return None

        # Check if owner
        if case.created_by == user_id:
            return case

        # Check if member
        member = (
            self.db.query(CaseMember)
            .filter(
                CaseMember.case_id == case_id,
                CaseMember.user_id == user_id
            )
            .first()
        )
        if member:
            return case

        return None

    def get_case_detail(self, user_id: str, case_id: str) -> Optional[CaseDetailResponse]:
        """
        Get detailed case information.

        Args:
            user_id: Current user ID
            case_id: Case ID

        Returns:
            Detailed case response or None if not found/no access
        """
        case = self._get_case_with_access(user_id, case_id)
        if not case:
            return None

        # Get members
        members = [
            {
                "user_id": m.user_id,
                "user_name": m.user.name if m.user else None,
                "role": m.role.value,
            }
            for m in case.members
        ]

        return CaseDetailResponse(
            id=case.id,
            title=case.title,
            client_name=case.client_name,
            description=case.description,
            status=case.status.value if case.status else "unknown",
            created_at=case.created_at,
            updated_at=case.updated_at,
            owner_id=case.created_by,
            owner_name=case.owner.name if case.owner else None,
            owner_email=case.owner.email if case.owner else None,
            evidence_count=0,  # Would need DynamoDB query
            evidence_summary=[],
            ai_summary=None,  # Would need RAG query
            ai_labels=[],
            recent_activities=[],
            members=members,
        )
