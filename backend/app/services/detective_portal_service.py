"""
Detective Portal Service
Task T094 - US5 Implementation

Business logic for detective portal operations.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.models import (
    User, Case, CaseMember, InvestigationRecord, UserRole
)
from app.schemas.detective_portal import (
    DetectiveDashboardResponse, DashboardStats, InvestigationSummary,
    ScheduleItem, ScheduleEventType, InvestigationStatus,
    CaseListResponse, CaseListItem, CaseDetailResponse,
    AcceptRejectResponse, CreateRecordResponse, ReportResponse,
    EarningsResponse, EarningsSummary, Transaction, TransactionStatus,
    RecordType, FieldRecordResponse
)


class DetectivePortalService:
    """Service for detective portal operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self, detective_id: str) -> DetectiveDashboardResponse:
        """Get detective dashboard data"""
        detective = self.db.query(User).filter(User.id == detective_id).first()
        if not detective:
            raise ValueError("Detective not found")

        # Get investigation counts
        active_count = self._get_investigation_count(detective_id, "active")
        pending_count = self._get_investigation_count(detective_id, "pending")
        completed_this_month = self._get_completed_this_month(detective_id)

        # Mock earnings for now (would come from invoices table)
        monthly_earnings = 2450000.0

        stats = DashboardStats(
            active_investigations=active_count,
            pending_requests=pending_count,
            completed_this_month=completed_this_month,
            monthly_earnings=monthly_earnings
        )

        # Get active investigations
        active_investigations = self._get_active_investigations(detective_id)

        # Get today's schedule (mock data for now)
        today_schedule = self._get_today_schedule(detective_id)

        return DetectiveDashboardResponse(
            user_name=detective.name,
            stats=stats,
            active_investigations=active_investigations,
            today_schedule=today_schedule
        )

    def get_cases(
        self,
        detective_id: str,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> CaseListResponse:
        """Get detective's case list with optional filtering"""
        # Get cases where detective is a member
        query = (
            self.db.query(Case)
            .join(CaseMember, Case.id == CaseMember.case_id)
            .filter(CaseMember.user_id == detective_id)
        )

        if status:
            query = query.filter(Case.status == status)

        total = query.count()
        cases = query.offset((page - 1) * limit).limit(limit).all()

        items = []
        for case in cases:
            # Get lawyer info
            lawyer = self._get_case_lawyer(case.id)
            record_count = self._get_case_record_count(case.id, detective_id)

            items.append(CaseListItem(
                id=case.id,
                title=case.title,
                status=self._map_case_status(case.status),
                lawyer_name=lawyer.name if lawyer else None,
                record_count=record_count,
                created_at=case.created_at,
                updated_at=case.updated_at
            ))

        return CaseListResponse(items=items, total=total)

    def get_case_detail(self, detective_id: str, case_id: str) -> CaseDetailResponse:
        """Get case detail for detective"""
        # First check if case exists
        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise KeyError("Case not found")

        # Verify detective has access to this case
        member = (
            self.db.query(CaseMember)
            .filter(
                CaseMember.case_id == case_id,
                CaseMember.user_id == detective_id
            )
            .first()
        )

        if not member:
            raise PermissionError("Not authorized to view this case")

        lawyer = self._get_case_lawyer(case_id)
        records = self._get_case_records(case_id, detective_id)

        return CaseDetailResponse(
            id=case.id,
            title=case.title,
            description=case.description,
            status=self._map_case_status(case.status),
            lawyer_name=lawyer.name if lawyer else None,
            lawyer_email=lawyer.email if lawyer else None,
            records=records,
            created_at=case.created_at,
            updated_at=case.updated_at
        )

    def accept_case(self, detective_id: str, case_id: str) -> AcceptRejectResponse:
        """Accept an investigation case"""
        member = self._get_case_member(detective_id, case_id)
        if not member:
            raise KeyError("Case not found or not assigned")

        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise KeyError("Case not found")

        # Update case status to active
        case.status = "active"
        self.db.commit()

        return AcceptRejectResponse(
            success=True,
            message="Investigation accepted",
            case_id=case_id,
            new_status=InvestigationStatus.ACTIVE
        )

    def reject_case(
        self,
        detective_id: str,
        case_id: str,
        reason: str
    ) -> AcceptRejectResponse:
        """Reject an investigation case"""
        member = self._get_case_member(detective_id, case_id)
        if not member:
            raise KeyError("Case not found or not assigned")

        # Remove detective from case
        self.db.delete(member)
        self.db.commit()

        return AcceptRejectResponse(
            success=True,
            message=f"Investigation rejected: {reason}",
            case_id=case_id,
            new_status=InvestigationStatus.PENDING
        )

    def create_field_record(
        self,
        detective_id: str,
        case_id: str,
        record_type: RecordType,
        content: str,
        gps_lat: Optional[float] = None,
        gps_lng: Optional[float] = None,
        photo_url: Optional[str] = None
    ) -> CreateRecordResponse:
        """Create a new field record"""
        from app.db.models import InvestigationRecordType

        member = self._get_case_member(detective_id, case_id)
        if not member:
            raise KeyError("Case not found or not assigned")

        # Map RecordType to InvestigationRecordType
        type_map = {
            RecordType.OBSERVATION: InvestigationRecordType.MEMO,
            RecordType.PHOTO: InvestigationRecordType.PHOTO,
            RecordType.NOTE: InvestigationRecordType.MEMO,
            RecordType.VIDEO: InvestigationRecordType.VIDEO,
            RecordType.AUDIO: InvestigationRecordType.AUDIO,
        }
        db_record_type = type_map.get(record_type, InvestigationRecordType.MEMO)

        # Create investigation record
        record = InvestigationRecord(
            case_id=case_id,
            detective_id=detective_id,
            record_type=db_record_type,
            content=content,
            location_lat=str(gps_lat) if gps_lat else None,
            location_lng=str(gps_lng) if gps_lng else None,
            recorded_at=datetime.now()
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return CreateRecordResponse(
            success=True,
            record_id=record.id,
            message="Field record created successfully"
        )

    def submit_report(
        self,
        detective_id: str,
        case_id: str,
        summary: str,
        findings: str,
        conclusion: str,
        attachments: Optional[List[str]] = None
    ) -> ReportResponse:
        """Submit final investigation report"""
        from app.db.models import InvestigationRecordType

        member = self._get_case_member(detective_id, case_id)
        if not member:
            raise KeyError("Case not found or not assigned")

        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise KeyError("Case not found")

        # Create report as a special record (use MEMO type for reports)
        report_content = f"## Summary\n{summary}\n\n## Findings\n{findings}\n\n## Conclusion\n{conclusion}"
        record = InvestigationRecord(
            case_id=case_id,
            detective_id=detective_id,
            record_type=InvestigationRecordType.MEMO,
            content=report_content,
            recorded_at=datetime.now()
        )
        self.db.add(record)

        # Update case status to review (use CaseStatus enum value)
        case.status = "in_progress"  # Using in_progress as review equivalent
        self.db.commit()
        self.db.refresh(record)

        return ReportResponse(
            success=True,
            report_id=record.id,
            message="Report submitted successfully",
            case_status=InvestigationStatus.REVIEW
        )

    def get_earnings(
        self,
        detective_id: str,
        period: Optional[str] = None
    ) -> EarningsResponse:
        """Get detective earnings"""
        # Mock earnings data for now
        # In production, this would come from invoices/payments tables
        summary = EarningsSummary(
            total_earned=15000000.0,
            pending_payment=500000.0,
            this_month=2450000.0
        )

        # Mock transactions
        transactions = [
            Transaction(
                id="tx-001",
                case_id="case-001",
                case_title="김영희 건",
                amount=800000.0,
                status=TransactionStatus.COMPLETED,
                description="조사비",
                created_at=datetime.now() - timedelta(days=5)
            ),
            Transaction(
                id="tx-002",
                case_id="case-002",
                case_title="박철수 건",
                amount=500000.0,
                status=TransactionStatus.PENDING,
                description="조사비",
                created_at=datetime.now() - timedelta(days=2)
            ),
        ]

        return EarningsResponse(
            summary=summary,
            transactions=transactions
        )

    # ============== Private Helper Methods ==============

    def _get_investigation_count(self, detective_id: str, status: str) -> int:
        """Get count of investigations by status"""
        return (
            self.db.query(Case)
            .join(CaseMember, Case.id == CaseMember.case_id)
            .filter(
                CaseMember.user_id == detective_id,
                Case.status == status
            )
            .count()
        )

    def _get_completed_this_month(self, detective_id: str) -> int:
        """Get count of completed investigations this month"""
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return (
            self.db.query(Case)
            .join(CaseMember, Case.id == CaseMember.case_id)
            .filter(
                CaseMember.user_id == detective_id,
                Case.status == "completed",
                Case.updated_at >= start_of_month
            )
            .count()
        )

    def _get_active_investigations(self, detective_id: str) -> List[InvestigationSummary]:
        """Get active investigations for dashboard"""
        cases = (
            self.db.query(Case)
            .join(CaseMember, Case.id == CaseMember.case_id)
            .filter(
                CaseMember.user_id == detective_id,
                Case.status.in_(["active", "pending", "review"])
            )
            .limit(5)
            .all()
        )

        result = []
        for case in cases:
            lawyer = self._get_case_lawyer(case.id)
            record_count = self._get_case_record_count(case.id, detective_id)

            result.append(InvestigationSummary(
                id=case.id,
                title=case.title,
                lawyer_name=lawyer.name if lawyer else None,
                status=self._map_case_status(case.status),
                record_count=record_count
            ))

        return result

    def _get_today_schedule(self, detective_id: str) -> List[ScheduleItem]:
        """Get today's schedule items"""
        # Mock schedule for now
        # In production, would come from calendar_events table
        return [
            ScheduleItem(
                id="s-1",
                time="10:00",
                title="현장 조사 - 강남구",
                type=ScheduleEventType.FIELD
            ),
            ScheduleItem(
                id="s-2",
                time="14:00",
                title="변호사 미팅",
                type=ScheduleEventType.MEETING
            ),
        ]

    def _get_case_lawyer(self, case_id: str) -> Optional[User]:
        """Get lawyer for a case"""
        lawyer_member = (
            self.db.query(CaseMember)
            .filter(
                CaseMember.case_id == case_id,
                CaseMember.role == "owner"
            )
            .first()
        )
        if lawyer_member:
            return self.db.query(User).filter(User.id == lawyer_member.user_id).first()
        return None

    def _get_case_record_count(self, case_id: str, detective_id: str) -> int:
        """Get count of records for a case by detective"""
        return (
            self.db.query(InvestigationRecord)
            .filter(
                InvestigationRecord.case_id == case_id,
                InvestigationRecord.detective_id == detective_id
            )
            .count()
        )

    def _get_case_records(self, case_id: str, detective_id: str) -> List[FieldRecordResponse]:
        """Get records for a case"""
        from app.db.models import InvestigationRecordType

        records = (
            self.db.query(InvestigationRecord)
            .filter(
                InvestigationRecord.case_id == case_id,
                InvestigationRecord.detective_id == detective_id
            )
            .order_by(InvestigationRecord.created_at.desc())
            .all()
        )

        # Map InvestigationRecordType to RecordType
        type_reverse_map = {
            InvestigationRecordType.MEMO: RecordType.NOTE,
            InvestigationRecordType.PHOTO: RecordType.PHOTO,
            InvestigationRecordType.VIDEO: RecordType.VIDEO,
            InvestigationRecordType.AUDIO: RecordType.AUDIO,
            InvestigationRecordType.LOCATION: RecordType.OBSERVATION,
            InvestigationRecordType.EVIDENCE: RecordType.OBSERVATION,
        }

        return [
            FieldRecordResponse(
                id=r.id,
                record_type=type_reverse_map.get(r.record_type, RecordType.NOTE),
                content=r.content or "",
                gps_lat=float(r.location_lat) if r.location_lat else None,
                gps_lng=float(r.location_lng) if r.location_lng else None,
                created_at=r.created_at
            )
            for r in records
        ]

    def _get_case_member(self, detective_id: str, case_id: str) -> Optional[CaseMember]:
        """Get case member entry for detective"""
        return (
            self.db.query(CaseMember)
            .filter(
                CaseMember.case_id == case_id,
                CaseMember.user_id == detective_id
            )
            .first()
        )

    def _map_case_status(self, status: str) -> InvestigationStatus:
        """Map case status to investigation status"""
        status_map = {
            "pending": InvestigationStatus.PENDING,
            "active": InvestigationStatus.ACTIVE,
            "review": InvestigationStatus.REVIEW,
            "completed": InvestigationStatus.COMPLETED,
            "closed": InvestigationStatus.COMPLETED,
        }
        return status_map.get(status, InvestigationStatus.PENDING)
