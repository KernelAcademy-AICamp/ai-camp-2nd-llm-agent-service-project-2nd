"""
Evidence Service - Business logic for evidence management
Handles presigned URL generation and evidence metadata retrieval
"""

from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import uuid
from app.db.schemas import (
    PresignedUrlRequest,
    PresignedUrlResponse,
    EvidenceSummary,
    EvidenceDetail
)
from app.repositories.case_repository import CaseRepository
from app.repositories.case_member_repository import CaseMemberRepository
from app.utils.s3 import generate_presigned_upload_url
from app.utils.dynamo import get_evidence_by_case, get_evidence_by_id
from app.core.config import settings
from app.middleware import NotFoundError, PermissionError


class EvidenceService:
    """
    Service for evidence management business logic
    """

    def __init__(self, db: Session):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.member_repo = CaseMemberRepository(db)

    def generate_upload_presigned_url(
        self,
        request: PresignedUrlRequest,
        user_id: str
    ) -> PresignedUrlResponse:
        """
        Generate S3 presigned URL for evidence upload

        Args:
            request: Presigned URL request data
            user_id: ID of user requesting upload

        Returns:
            Presigned URL response with upload_url and fields

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access to case

        Security:
            - Validates user has access to case
            - Enforces 5-minute max expiration
            - Uses unique temporary evidence ID
        """
        # Check if case exists
        case = self.case_repo.get_by_id(request.case_id)
        if not case:
            raise NotFoundError("Case")

        # Check if user has access to case
        if not self.member_repo.has_access(request.case_id, user_id):
            raise PermissionError("You do not have access to this case")

        # Generate unique temporary evidence ID
        evidence_temp_id = f"ev_{uuid.uuid4().hex[:12]}"

        # Construct S3 key with proper prefix
        s3_key = f"cases/{request.case_id}/raw/{evidence_temp_id}_{request.filename}"

        # Generate presigned URL (max 5 minutes per security policy)
        presigned_data = generate_presigned_upload_url(
            bucket=settings.S3_EVIDENCE_BUCKET,
            key=s3_key,
            content_type=request.content_type,
            expires_in=min(settings.S3_PRESIGNED_URL_EXPIRE_SECONDS, 300)
        )

        return PresignedUrlResponse(
            upload_url=presigned_data["upload_url"],
            fields=presigned_data["fields"],
            evidence_temp_id=evidence_temp_id
        )

    def get_evidence_list(self, case_id: str, user_id: str) -> List[EvidenceSummary]:
        """
        Get list of evidence for a case

        Args:
            case_id: Case ID
            user_id: User ID requesting access

        Returns:
            List of evidence summary

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access to case
        """
        # Check if case exists
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")

        # Check if user has access to case
        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

        # Get evidence metadata from DynamoDB
        evidence_list = get_evidence_by_case(case_id)

        # Convert to EvidenceSummary schema
        return [
            EvidenceSummary(
                id=evidence["id"],
                case_id=evidence["case_id"],
                type=evidence["type"],
                filename=evidence["filename"],
                created_at=datetime.fromisoformat(evidence["created_at"]),
                status=evidence.get("status", "pending")
            )
            for evidence in evidence_list
        ]

    def get_evidence_detail(self, evidence_id: str, user_id: str) -> EvidenceDetail:
        """
        Get detailed evidence metadata with AI analysis results

        Args:
            evidence_id: Evidence ID
            user_id: User ID requesting access

        Returns:
            Evidence detail with AI analysis

        Raises:
            NotFoundError: Evidence not found
            PermissionError: User does not have access to case
        """
        # Get evidence metadata from DynamoDB
        evidence = get_evidence_by_id(evidence_id)
        if not evidence:
            raise NotFoundError("Evidence")

        # Check if user has access to the case
        case_id = evidence["case_id"]
        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

        # Convert to EvidenceDetail schema
        return EvidenceDetail(
            id=evidence["id"],
            case_id=evidence["case_id"],
            type=evidence["type"],
            filename=evidence["filename"],
            s3_key=evidence["s3_key"],
            content_type=evidence.get("content_type", "application/octet-stream"),
            created_at=datetime.fromisoformat(evidence["created_at"]),
            status=evidence.get("status", "pending"),
            ai_summary=evidence.get("ai_summary"),
            labels=evidence.get("labels", []),
            insights=evidence.get("insights", []),
            content=evidence.get("content"),
            speaker=evidence.get("speaker"),
            timestamp=datetime.fromisoformat(evidence["timestamp"]) if evidence.get("timestamp") else None,
            opensearch_id=evidence.get("opensearch_id")
        )
