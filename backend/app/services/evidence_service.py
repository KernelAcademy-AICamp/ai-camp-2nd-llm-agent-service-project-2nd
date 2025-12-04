"""
Evidence Service - Business logic for evidence management
Handles presigned URL generation and evidence metadata retrieval
"""

from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.db.schemas import (
    PresignedUrlRequest,
    PresignedUrlResponse,
    UploadCompleteRequest,
    UploadCompleteResponse,
    EvidenceSummary,
    EvidenceDetail,
    Article840Tags,
    Article840Category
)
from app.repositories.case_repository import CaseRepository
from app.repositories.case_member_repository import CaseMemberRepository
from app.utils.s3 import generate_presigned_upload_url
from app.utils.dynamo import (
    get_evidence_by_case,
    get_evidence_by_id,
    put_evidence_metadata as save_evidence_metadata,
    update_evidence_status
)
from app.utils.lambda_client import invoke_ai_worker
from app.utils.evidence import generate_evidence_id, extract_filename_from_s3_key
from app.core.config import settings
from app.middleware import NotFoundError, PermissionError
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EvidenceService:
    """
    Service for evidence management business logic
    """

    def __init__(self, db: Session):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.member_repo = CaseMemberRepository(db)

    @staticmethod
    def _parse_article_840_tags(evidence_data: dict) -> Optional[Article840Tags]:
        """
        Parse Article 840 tags from DynamoDB evidence data

        Args:
            evidence_data: DynamoDB evidence item

        Returns:
            Article840Tags if available, None otherwise
        """
        tags_data = evidence_data.get("article_840_tags")
        if not tags_data:
            return None

        try:
            # Parse categories from string values to Article840Category enum
            categories = [
                Article840Category(cat)
                for cat in tags_data.get("categories", [])
            ]

            return Article840Tags(
                categories=categories,
                confidence=tags_data.get("confidence", 0.0),
                matched_keywords=tags_data.get("matched_keywords", [])
            )
        except (ValueError, KeyError):
            # Invalid category value or malformed data
            return None

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
        evidence_temp_id = generate_evidence_id()

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
            evidence_temp_id=evidence_temp_id,
            s3_key=s3_key
        )

    def handle_upload_complete(
        self,
        request: UploadCompleteRequest,
        user_id: str
    ) -> UploadCompleteResponse:
        """
        Handle evidence upload completion notification

        Args:
            request: Upload complete request with s3_key and metadata
            user_id: ID of user who uploaded the evidence

        Returns:
            UploadCompleteResponse with created evidence info

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access to case

        Process:
            1. Validate user has access to case
            2. Create evidence metadata record in DynamoDB
            3. Trigger AI Worker processing (via SNS or direct invocation)
        """
        # Check if case exists
        case = self.case_repo.get_by_id(request.case_id)
        if not case:
            raise NotFoundError("Case")

        # Check if user has access to case
        if not self.member_repo.has_access(request.case_id, user_id):
            raise PermissionError("You do not have access to this case")

        # Extract filename from s3_key
        filename = extract_filename_from_s3_key(request.s3_key)

        # Determine file type from extension
        # NOTE: Keep in sync with ai_worker/handler.py route_parser()
        extension = filename.split(".")[-1].lower() if "." in filename else ""
        type_mapping = {
            # Images
            "jpg": "image", "jpeg": "image", "png": "image", "gif": "image", "bmp": "image",
            # Audio
            "mp3": "audio", "wav": "audio", "m4a": "audio", "aac": "audio",
            # Video
            "mp4": "video", "avi": "video", "mov": "video", "mkv": "video",
            # Documents
            "pdf": "pdf",
            "txt": "text", "csv": "text", "json": "text"
        }
        evidence_type = type_mapping.get(extension, "document")

        # Use evidence_temp_id as evidence_id (matches S3 key for AI Worker)
        evidence_id = request.evidence_temp_id
        created_at = datetime.utcnow()

        # Create evidence metadata for DynamoDB
        evidence_metadata = {
            "evidence_id": evidence_id,
            "case_id": request.case_id,
            "type": evidence_type,
            "filename": filename,
            "s3_key": request.s3_key,
            "size": request.file_size,  # File size in bytes
            "content_type": self._get_content_type(extension),
            "status": "pending",  # Waiting for AI Worker processing
            "created_at": created_at.isoformat(),
            "created_by": user_id,
            "note": request.note,
            "deleted": False
        }

        # Save to DynamoDB
        save_evidence_metadata(evidence_metadata)

        # Trigger AI Worker Lambda for processing
        try:
            invoke_result = invoke_ai_worker(
                bucket=settings.S3_EVIDENCE_BUCKET,
                s3_key=request.s3_key,
                evidence_id=evidence_id,
                case_id=request.case_id
            )
            logger.info(f"AI Worker invocation result: {invoke_result}")
            # Update status to processing if invocation succeeded
            update_evidence_status(evidence_id, "processing")
        except Exception as e:
            # Mark as failed if AI Worker invocation fails
            logger.error(f"AI Worker invocation failed for evidence {evidence_id}: {e}")
            update_evidence_status(evidence_id, "failed", error_message=str(e))
            # Still return success - the evidence record exists, just needs retry
            return UploadCompleteResponse(
                evidence_id=evidence_id,
                case_id=request.case_id,
                filename=filename,
                s3_key=request.s3_key,
                status="failed",
                created_at=created_at
            )

        return UploadCompleteResponse(
            evidence_id=evidence_id,
            case_id=request.case_id,
            filename=filename,
            s3_key=request.s3_key,
            status="processing",
            created_at=created_at
        )

    @staticmethod
    def _get_content_type(extension: str) -> str:
        """Get MIME content type from file extension"""
        content_types = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif",
            "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
            "mp4": "video/mp4", "avi": "video/x-msvideo", "mov": "video/quicktime",
            "pdf": "application/pdf",
            "txt": "text/plain", "csv": "text/csv", "json": "application/json"
        }
        return content_types.get(extension, "application/octet-stream")

    def get_evidence_list(
        self,
        case_id: str,
        user_id: str,
        categories: Optional[List[Article840Category]] = None
    ) -> List[EvidenceSummary]:
        """
        Get list of evidence for a case

        Args:
            case_id: Case ID
            user_id: User ID requesting access
            categories: Filter by Article 840 categories (optional)

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
        summaries = [
            EvidenceSummary(
                id=evidence.get("evidence_id") or evidence.get("id"),
                case_id=evidence["case_id"],
                type=evidence["type"],
                filename=evidence["filename"],
                size=evidence.get("size", 0),
                created_at=datetime.fromisoformat(evidence["created_at"]),
                status=evidence.get("status", "pending"),
                ai_summary=evidence.get("ai_summary"),
                article_840_tags=self._parse_article_840_tags(evidence)
            )
            for evidence in evidence_list
        ]

        # Apply category filter if specified
        if categories:
            summaries = [
                summary for summary in summaries
                if summary.article_840_tags and any(
                    cat in summary.article_840_tags.categories
                    for cat in categories
                )
            ]

        return summaries

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

        # Parse Article 840 tags
        article_840_tags = self._parse_article_840_tags(evidence)

        # Map categories to labels (for backward compatibility)
        labels = evidence.get("labels", [])
        if article_840_tags and article_840_tags.categories:
            # Convert Article840Category enum to string values
            labels = [cat.value for cat in article_840_tags.categories]

        # Convert to EvidenceDetail schema
        return EvidenceDetail(
            id=evidence.get("evidence_id") or evidence.get("id"),
            case_id=evidence["case_id"],
            type=evidence["type"],
            filename=evidence["filename"],
            size=evidence.get("size", 0),
            s3_key=evidence["s3_key"],
            content_type=evidence.get("content_type", "application/octet-stream"),
            created_at=datetime.fromisoformat(evidence["created_at"]),
            status=evidence.get("status", "pending"),
            ai_summary=evidence.get("ai_summary"),
            labels=labels,
            insights=evidence.get("insights", []),
            content=evidence.get("content"),
            speaker=evidence.get("speaker"),
            timestamp=datetime.fromisoformat(evidence["timestamp"]) if evidence.get("timestamp") else None,
            qdrant_id=evidence.get("qdrant_id"),
            article_840_tags=article_840_tags
        )

    def retry_processing(self, evidence_id: str, user_id: str) -> dict:
        """
        Retry processing for failed evidence

        Args:
            evidence_id: Evidence ID to retry
            user_id: User ID requesting retry

        Returns:
            dict with status and message

        Raises:
            NotFoundError: Evidence not found
            PermissionError: User does not have access
            ValueError: Evidence not in failed state

        State Machine:
            FAILED → PROCESSING (on successful retry)
        """
        # Get evidence metadata from DynamoDB
        evidence = get_evidence_by_id(evidence_id)
        if not evidence:
            raise NotFoundError("Evidence")

        # Check if user has access to the case
        case_id = evidence["case_id"]
        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

        # Only allow retry for failed evidence
        current_status = evidence.get("status", "")
        if current_status not in ["failed", "pending"]:
            raise ValueError(f"Cannot retry evidence with status '{current_status}'. Only 'failed' or 'pending' evidence can be retried.")

        # Get required fields
        s3_key = evidence.get("s3_key")
        if not s3_key:
            raise ValueError("Evidence missing s3_key - cannot retry")

        # Update status to processing
        update_evidence_status(evidence_id, "processing", error_message=None)

        # Re-invoke AI Worker
        try:
            invoke_result = invoke_ai_worker(
                bucket=settings.S3_EVIDENCE_BUCKET,
                s3_key=s3_key,
                evidence_id=evidence_id,
                case_id=case_id
            )
            logger.info(f"AI Worker retry invocation result for {evidence_id}: {invoke_result}")

            return {
                "success": True,
                "message": "Evidence processing restarted",
                "evidence_id": evidence_id,
                "status": "processing"
            }
        except Exception as e:
            # Mark as failed again
            logger.error(f"AI Worker retry failed for evidence {evidence_id}: {e}")
            update_evidence_status(evidence_id, "failed", error_message=str(e))

            return {
                "success": False,
                "message": f"Retry failed: {str(e)}",
                "evidence_id": evidence_id,
                "status": "failed"
            }

    def get_evidence_status(self, evidence_id: str, user_id: str) -> dict:
        """
        Get current status of evidence

        Args:
            evidence_id: Evidence ID
            user_id: User ID requesting status

        Returns:
            dict with status information

        Raises:
            NotFoundError: Evidence not found
            PermissionError: User does not have access
        """
        evidence = get_evidence_by_id(evidence_id)
        if not evidence:
            raise NotFoundError("Evidence")

        case_id = evidence["case_id"]
        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

        return {
            "evidence_id": evidence_id,
            "status": evidence.get("status", "unknown"),
            "error_message": evidence.get("error_message"),
            "updated_at": evidence.get("updated_at")
        }
