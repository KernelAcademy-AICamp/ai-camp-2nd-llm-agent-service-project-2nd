"""
Client Portal Service
003-role-based-ui Feature - US4 (T067)

Service for client portal operations including dashboard, case viewing, and evidence upload.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import User, Case, CaseMember, Evidence, AuditLog
from app.schemas.client_portal import (
    ClientDashboardResponse,
    CaseSummary,
    LawyerInfo,
    RecentActivity,
    ProgressStep,
    ClientCaseListResponse,
    ClientCaseListItem,
    ClientCaseDetailResponse,
    EvidenceSummary,
    EvidenceUploadResponse,
)
from app.utils.s3 import generate_presigned_upload_url
import uuid


class ClientPortalService:
    """Service for client portal operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self, user_id: str) -> ClientDashboardResponse:
        """Get client dashboard data"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Get client's cases (as member)
        case_memberships = (
            self.db.query(CaseMember)
            .filter(CaseMember.user_id == user_id)
            .all()
        )

        case_summary = None
        progress_steps = []
        lawyer_info = None
        recent_activities = []

        if case_memberships:
            # Get the most recent active case
            case_ids = [m.case_id for m in case_memberships]
            active_case = (
                self.db.query(Case)
                .filter(
                    and_(
                        Case.id.in_(case_ids),
                        Case.status.in_(["active", "open", "in_progress"])
                    )
                )
                .order_by(Case.updated_at.desc())
                .first()
            )

            if active_case:
                case_summary = self._build_case_summary(active_case)
                progress_steps = self._build_progress_steps(active_case)
                lawyer_info = self._get_lawyer_info(active_case)
                recent_activities = self._get_recent_activities(active_case.id)

        return ClientDashboardResponse(
            user_name=user.name or "의뢰인",
            case_summary=case_summary,
            progress_steps=progress_steps,
            lawyer_info=lawyer_info,
            recent_activities=recent_activities,
            unread_messages=0,  # TODO: Implement message counting
        )

    def get_case_list(self, user_id: str) -> ClientCaseListResponse:
        """Get list of client's cases"""
        # Get cases where user is a member
        case_memberships = (
            self.db.query(CaseMember)
            .filter(CaseMember.user_id == user_id)
            .all()
        )

        case_ids = [m.case_id for m in case_memberships]

        cases = (
            self.db.query(Case)
            .filter(Case.id.in_(case_ids))
            .order_by(Case.updated_at.desc())
            .all()
        )

        items = []
        for case in cases:
            evidence_count = (
                self.db.query(Evidence)
                .filter(Evidence.case_id == case.id)
                .count()
            )

            lawyer = self._get_case_lawyer(case)

            items.append(
                ClientCaseListItem(
                    id=str(case.id),
                    title=case.title,
                    status=case.status,
                    progress_percent=self._calculate_progress(case),
                    evidence_count=evidence_count,
                    lawyer_name=lawyer.name if lawyer else None,
                    created_at=case.created_at,
                    updated_at=case.updated_at,
                )
            )

        return ClientCaseListResponse(items=items, total=len(items))

    def get_case_detail(self, user_id: str, case_id: str) -> ClientCaseDetailResponse:
        """Get detailed case information for client"""
        # Verify access
        membership = (
            self.db.query(CaseMember)
            .filter(
                and_(
                    CaseMember.user_id == user_id,
                    CaseMember.case_id == case_id
                )
            )
            .first()
        )

        if not membership:
            raise PermissionError("Access denied to this case")

        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("Case not found")

        # Get evidence list
        evidences = (
            self.db.query(Evidence)
            .filter(Evidence.case_id == case_id)
            .order_by(Evidence.created_at.desc())
            .limit(20)
            .all()
        )

        evidence_list = [
            EvidenceSummary(
                id=str(e.id),
                file_name=e.file_name or "Unknown",
                file_type=self._get_file_type(e.file_name),
                uploaded_at=e.created_at,
                status=e.status or "pending",
                ai_labels=e.ai_labels_list,
            )
            for e in evidences
        ]

        evidence_count = (
            self.db.query(Evidence)
            .filter(Evidence.case_id == case_id)
            .count()
        )

        return ClientCaseDetailResponse(
            id=str(case.id),
            title=case.title,
            description=case.description,
            status=case.status,
            progress_percent=self._calculate_progress(case),
            progress_steps=self._build_progress_steps(case),
            lawyer_info=self._get_lawyer_info(case),
            evidence_list=evidence_list,
            evidence_count=evidence_count,
            recent_activities=self._get_recent_activities(case_id),
            created_at=case.created_at,
            updated_at=case.updated_at,
            can_upload_evidence=case.status not in ["closed", "archived"],
        )

    def request_evidence_upload(
        self,
        user_id: str,
        case_id: str,
        file_name: str,
        file_type: str,
        file_size: int,
        description: Optional[str] = None,
    ) -> EvidenceUploadResponse:
        """Request presigned URL for evidence upload"""
        # Verify access
        membership = (
            self.db.query(CaseMember)
            .filter(
                and_(
                    CaseMember.user_id == user_id,
                    CaseMember.case_id == case_id
                )
            )
            .first()
        )

        if not membership:
            raise PermissionError("Access denied to this case")

        case = self.db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError("Case not found")

        if case.status in ["closed", "archived"]:
            raise ValueError("Cannot upload evidence to closed case")

        # Generate evidence ID and S3 key
        evidence_id = str(uuid.uuid4())
        s3_key = f"cases/{case_id}/raw/{evidence_id}_{file_name}"

        # Create evidence record (pending status)
        evidence = Evidence(
            id=evidence_id,
            case_id=case_id,
            file_name=file_name,
            s3_key=s3_key,
            file_type=file_type,
            file_size=file_size,
            description=description,
            uploaded_by=user_id,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(evidence)

        # Generate presigned URL
        try:
            upload_url = generate_presigned_upload_url(s3_key, file_type)
        except Exception:
            # Fallback for local development
            upload_url = f"http://localhost:9000/leh-evidence/{s3_key}"

        self.db.commit()

        return EvidenceUploadResponse(
            evidence_id=evidence_id,
            upload_url=upload_url,
            expires_in=300,
        )

    def confirm_evidence_upload(
        self,
        user_id: str,
        case_id: str,
        evidence_id: str,
        uploaded: bool,
    ) -> dict:
        """
        Confirm or cancel evidence upload.

        Args:
            user_id: ID of the user confirming the upload
            case_id: ID of the case
            evidence_id: ID of the evidence
            uploaded: True if upload was successful, False to cancel

        Returns:
            dict with success status and message
        """
        evidence = self.db.query(Evidence).filter(Evidence.id == evidence_id).first()

        if not evidence:
            raise ValueError("Evidence not found")

        if evidence.case_id != case_id:
            raise ValueError("Evidence does not belong to this case")

        if evidence.uploaded_by != user_id:
            raise PermissionError("Not authorized to confirm this upload")

        if uploaded:
            evidence.status = "uploaded"
            evidence.updated_at = datetime.utcnow()
            self.db.commit()

            return {
                "success": True,
                "message": "Evidence upload confirmed. Processing will begin shortly.",
                "evidence_id": evidence_id,
            }
        else:
            # Upload was cancelled, remove the pending record
            self.db.delete(evidence)
            self.db.commit()

            return {
                "success": True,
                "message": "Upload cancelled",
                "evidence_id": evidence_id,
            }

    def log_evidence_upload(
        self,
        user_id: str,
        case_id: str,
        evidence_id: str,
        file_name: str,
    ) -> None:
        """Log evidence upload for audit trail (T066)"""
        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action="evidence_upload",
            resource_type="evidence",
            resource_id=evidence_id,
            details={
                "case_id": case_id,
                "file_name": file_name,
                "uploaded_by": "client",
            },
            created_at=datetime.utcnow(),
        )
        self.db.add(audit_log)
        self.db.commit()

    # ============== Helper Methods ==============

    def _build_case_summary(self, case: Case) -> CaseSummary:
        """Build case summary from Case model"""
        lawyer = self._get_case_lawyer(case)
        return CaseSummary(
            id=str(case.id),
            title=case.title,
            status=case.status,
            progress_percent=self._calculate_progress(case),
            lawyer_name=lawyer.name if lawyer else None,
            next_action=self._get_next_action(case),
            updated_at=case.updated_at,
        )

    def _build_progress_steps(self, case: Case) -> List[ProgressStep]:
        """Build progress steps based on case status"""
        steps = [
            ("상담 완료", "consultation"),
            ("증거자료 수집", "evidence_collection"),
            ("서류 작성", "document_preparation"),
            ("법원 제출", "court_submission"),
            ("재판 진행", "trial"),
        ]

        status_map = {
            "open": 0,
            "active": 1,
            "in_progress": 2,
            "review": 3,
            "submitted": 3,
            "trial": 4,
            "closed": 5,
        }

        current_step = status_map.get(case.status, 1)

        result = []
        for i, (title, _) in enumerate(steps):
            if i < current_step:
                status = "completed"
                date = case.created_at.strftime("%Y년 %m월 %d일") if i == 0 else None
            elif i == current_step:
                status = "current"
                date = "진행 중"
            else:
                status = "pending"
                date = None

            result.append(ProgressStep(step=i + 1, title=title, status=status, date=date))

        return result

    def _get_lawyer_info(self, case: Case) -> Optional[LawyerInfo]:
        """Get lawyer info for case"""
        lawyer = self._get_case_lawyer(case)
        if not lawyer:
            return None

        return LawyerInfo(
            id=str(lawyer.id),
            name=lawyer.name or "담당 변호사",
            firm=None,  # Could be added to User model
            phone=None,  # Could be added to User model
            email=lawyer.email,
        )

    def _get_case_lawyer(self, case: Case) -> Optional[User]:
        """Get the lawyer assigned to a case"""
        # First check owner
        owner = self.db.query(User).filter(User.id == case.created_by).first()
        if owner and owner.role == "lawyer":
            return owner

        # Check case members
        lawyer_member = (
            self.db.query(CaseMember)
            .join(User, CaseMember.user_id == User.id)
            .filter(
                and_(
                    CaseMember.case_id == case.id,
                    User.role == "lawyer"
                )
            )
            .first()
        )

        if lawyer_member:
            return self.db.query(User).filter(User.id == lawyer_member.user_id).first()

        return None

    def _calculate_progress(self, case: Case) -> int:
        """Calculate case progress percentage"""
        status_progress = {
            "open": 10,
            "active": 30,
            "in_progress": 50,
            "review": 70,
            "submitted": 80,
            "trial": 90,
            "closed": 100,
        }
        return status_progress.get(case.status, 20)

    def _get_next_action(self, case: Case) -> Optional[str]:
        """Get next action required for case"""
        action_map = {
            "open": "증거자료를 제출해주세요",
            "active": "서류 준비 중입니다",
            "in_progress": "검토 중입니다",
            "review": "변호사 검토 중",
            "submitted": "법원 처리 대기 중",
            "trial": "재판 일정 확인",
            "closed": None,
        }
        return action_map.get(case.status)

    def _get_recent_activities(self, case_id: str, limit: int = 5) -> List[RecentActivity]:
        """Get recent activities for a case"""
        # Get from audit logs - object_id stores JSON with case info
        logs = (
            self.db.query(AuditLog)
            .filter(AuditLog.object_id.contains(case_id))
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )

        activities = []
        for log in logs:
            activity_type = self._map_action_to_activity_type(log.action)
            activities.append(
                RecentActivity(
                    id=str(log.id),
                    title=self._get_activity_title(log.action),
                    description="",  # AuditLog object_id stores JSON, details not available
                    activity_type=activity_type,
                    timestamp=log.timestamp,
                    time_ago=self._time_ago(log.timestamp),
                )
            )

        return activities

    def _map_action_to_activity_type(self, action: str) -> str:
        """Map audit action to activity type"""
        mapping = {
            "evidence_upload": "evidence",
            "message_sent": "message",
            "document_created": "document",
            "status_changed": "status",
        }
        return mapping.get(action, "status")

    def _get_activity_title(self, action: str) -> str:
        """Get human-readable title for action"""
        titles = {
            "evidence_upload": "증거자료 업로드",
            "message_sent": "메시지 전송",
            "document_created": "서류 작성",
            "status_changed": "상태 변경",
        }
        return titles.get(action, action)

    def _time_ago(self, dt: datetime) -> str:
        """Convert datetime to human-readable time ago string"""
        now = datetime.utcnow()
        diff = now - dt

        if diff.days > 7:
            return dt.strftime("%Y년 %m월 %d일")
        elif diff.days > 0:
            return f"{diff.days}일 전"
        elif diff.seconds >= 3600:
            return f"{diff.seconds // 3600}시간 전"
        elif diff.seconds >= 60:
            return f"{diff.seconds // 60}분 전"
        else:
            return "방금 전"

    def _get_file_type(self, file_name: Optional[str]) -> str:
        """Determine file type from file name"""
        if not file_name:
            return "document"

        ext = file_name.lower().split(".")[-1] if "." in file_name else ""

        if ext in ["jpg", "jpeg", "png", "gif", "webp"]:
            return "image"
        elif ext in ["mp3", "wav", "m4a", "aac"]:
            return "audio"
        elif ext in ["mp4", "avi", "mov", "mkv"]:
            return "video"
        else:
            return "document"
