"""
Job Service - Business logic for async job management
"""

import json
import logging
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.models import Job, JobStatus, JobType
from app.repositories.job_repository import JobRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.case_member_repository import CaseMemberRepository
from app.middleware import NotFoundError, PermissionError, ValidationError

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing async processing jobs"""

    def __init__(self, db: Session):
        self.db = db
        self.job_repo = JobRepository(db)
        self.case_repo = CaseRepository(db)
        self.case_member_repo = CaseMemberRepository(db)

    def create_job(
        self,
        case_id: str,
        user_id: str,
        job_type: JobType,
        evidence_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Job:
        """
        Create a new async job

        Args:
            case_id: Case ID
            user_id: User who initiated the job
            job_type: Type of job (OCR, STT, DRAFT_GENERATION, etc.)
            evidence_id: Optional evidence ID for evidence-related jobs
            parameters: Optional job parameters

        Returns:
            Created Job instance

        Raises:
            NotFoundError: If case not found
            PermissionError: If user doesn't have access to case
        """
        # Verify case exists and user has access
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        if not self.case_member_repo.is_member(case_id, user_id):
            raise PermissionError("User does not have access to this case")

        # Serialize parameters to JSON
        input_data = json.dumps(parameters) if parameters else None

        job = self.job_repo.create(
            case_id=case_id,
            user_id=user_id,
            job_type=job_type,
            evidence_id=evidence_id,
            input_data=input_data
        )

        logger.info(f"Created job {job.id} of type {job_type} for case {case_id}")
        return job

    def get_job(self, job_id: str, user_id: str) -> Job:
        """
        Get job by ID with access check

        Args:
            job_id: Job ID
            user_id: User requesting the job

        Returns:
            Job instance

        Raises:
            NotFoundError: If job not found
            PermissionError: If user doesn't have access
        """
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job {job_id} not found")

        # Check user has access to the case
        if not self.case_member_repo.is_member(job.case_id, user_id):
            raise PermissionError("User does not have access to this job")

        return job

    def get_case_jobs(
        self,
        case_id: str,
        user_id: str,
        status: Optional[str] = None,
        job_type: Optional[str] = None
    ) -> List[Job]:
        """
        Get all jobs for a case

        Args:
            case_id: Case ID
            user_id: User requesting jobs
            status: Optional status filter
            job_type: Optional job type filter

        Returns:
            List of jobs

        Raises:
            NotFoundError: If case not found
            PermissionError: If user doesn't have access
        """
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        if not self.case_member_repo.is_member(case_id, user_id):
            raise PermissionError("User does not have access to this case")

        # Convert string filters to enums
        status_enum = JobStatus(status) if status else None
        type_enum = JobType(job_type) if job_type else None

        return self.job_repo.get_by_case(
            case_id=case_id,
            status=status_enum,
            job_type=type_enum
        )

    def get_user_jobs(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> List[Job]:
        """
        Get all jobs initiated by a user

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            List of jobs
        """
        status_enum = JobStatus(status) if status else None
        return self.job_repo.get_by_user(user_id=user_id, status=status_enum)

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_details: Optional[Dict[str, Any]] = None,
        lambda_request_id: Optional[str] = None
    ) -> Job:
        """
        Update job status (typically called by worker/callback)

        Args:
            job_id: Job ID
            status: New status
            output_data: Optional output data (for completed jobs)
            error_details: Optional error details (for failed jobs)
            lambda_request_id: Optional Lambda request ID for correlation

        Returns:
            Updated Job instance

        Raises:
            NotFoundError: If job not found
        """
        output_json = json.dumps(output_data) if output_data else None
        error_json = json.dumps(error_details) if error_details else None

        job = self.job_repo.update_status(
            job_id=job_id,
            status=status,
            output_data=output_json,
            error_details=error_json,
            lambda_request_id=lambda_request_id
        )

        if not job:
            raise NotFoundError(f"Job {job_id} not found")

        logger.info(f"Updated job {job_id} status to {status}")
        return job

    def update_job_progress(self, job_id: str, progress: int) -> Job:
        """
        Update job progress (0-100)

        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)

        Returns:
            Updated Job instance

        Raises:
            NotFoundError: If job not found
        """
        job = self.job_repo.update_progress(job_id, progress)
        if not job:
            raise NotFoundError(f"Job {job_id} not found")

        return job

    def cancel_job(self, job_id: str, user_id: str) -> Job:
        """
        Cancel a job (only if queued or in retry)

        Args:
            job_id: Job ID
            user_id: User cancelling the job

        Returns:
            Cancelled Job instance

        Raises:
            NotFoundError: If job not found
            PermissionError: If user doesn't have access
            ValidationError: If job cannot be cancelled
        """
        job = self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job {job_id} not found")

        if not self.case_member_repo.is_member(job.case_id, user_id):
            raise PermissionError("User does not have access to this job")

        if job.status not in [JobStatus.QUEUED, JobStatus.RETRY]:
            raise ValidationError(
                f"Cannot cancel job in {job.status} status. "
                f"Only QUEUED or RETRY jobs can be cancelled."
            )

        cancelled_job = self.job_repo.cancel(job_id)
        logger.info(f"Cancelled job {job_id}")
        return cancelled_job

    def retry_job(self, job_id: str) -> Job:
        """
        Retry a failed job

        Args:
            job_id: Job ID

        Returns:
            Job with updated retry status

        Raises:
            NotFoundError: If job not found
        """
        job = self.job_repo.increment_retry(job_id)
        if not job:
            raise NotFoundError(f"Job {job_id} not found")

        logger.info(f"Retrying job {job_id}, attempt {job.retry_count}")
        return job

    def get_job_output(self, job_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job output data (for completed jobs)

        Args:
            job_id: Job ID
            user_id: User requesting output

        Returns:
            Output data dict or None

        Raises:
            NotFoundError: If job not found
            PermissionError: If user doesn't have access
        """
        job = self.get_job(job_id, user_id)

        if job.output_data:
            return json.loads(job.output_data)
        return None
