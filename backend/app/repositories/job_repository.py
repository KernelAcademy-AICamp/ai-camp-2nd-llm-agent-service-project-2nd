"""
Job Repository - Data access layer for Job model
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timezone

from app.db.models import Job, JobStatus, JobType


class JobRepository:
    """Repository for Job database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        case_id: str,
        user_id: str,
        job_type: JobType,
        evidence_id: Optional[str] = None,
        input_data: Optional[str] = None
    ) -> Job:
        """Create a new job"""
        job = Job(
            case_id=case_id,
            user_id=user_id,
            job_type=job_type,
            evidence_id=evidence_id,
            input_data=input_data,
            status=JobStatus.QUEUED
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_by_id(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.db.query(Job).filter(Job.id == job_id).first()

    def get_by_case(
        self,
        case_id: str,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 50
    ) -> List[Job]:
        """Get jobs for a case with optional filters"""
        query = self.db.query(Job).filter(Job.case_id == case_id)

        if status:
            query = query.filter(Job.status == status)
        if job_type:
            query = query.filter(Job.job_type == job_type)

        return query.order_by(desc(Job.created_at)).limit(limit).all()

    def get_by_user(
        self,
        user_id: str,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[Job]:
        """Get jobs for a user with optional status filter"""
        query = self.db.query(Job).filter(Job.user_id == user_id)

        if status:
            query = query.filter(Job.status == status)

        return query.order_by(desc(Job.created_at)).limit(limit).all()

    def get_by_evidence(self, evidence_id: str) -> List[Job]:
        """Get all jobs for an evidence item"""
        return self.db.query(Job).filter(
            Job.evidence_id == evidence_id
        ).order_by(desc(Job.created_at)).all()

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        output_data: Optional[str] = None,
        error_details: Optional[str] = None,
        lambda_request_id: Optional[str] = None
    ) -> Optional[Job]:
        """Update job status and related fields"""
        job = self.get_by_id(job_id)
        if not job:
            return None

        job.status = status

        if output_data:
            job.output_data = output_data
        if error_details:
            job.error_details = error_details
        if lambda_request_id:
            job.lambda_request_id = lambda_request_id

        # Update timestamps based on status
        now = datetime.now(timezone.utc)
        if status == JobStatus.PROCESSING and not job.started_at:
            job.started_at = now
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = now

        self.db.commit()
        self.db.refresh(job)
        return job

    def update_progress(self, job_id: str, progress: int) -> Optional[Job]:
        """Update job progress (0-100)"""
        job = self.get_by_id(job_id)
        if not job:
            return None

        job.progress = str(min(100, max(0, progress)))
        self.db.commit()
        self.db.refresh(job)
        return job

    def increment_retry(self, job_id: str) -> Optional[Job]:
        """Increment retry count and set status to RETRY"""
        job = self.get_by_id(job_id)
        if not job:
            return None

        current_retry = int(job.retry_count or "0")
        max_retries = int(job.max_retries or "3")

        if current_retry < max_retries:
            job.retry_count = str(current_retry + 1)
            job.status = JobStatus.RETRY
            job.error_details = None  # Clear previous error
        else:
            job.status = JobStatus.FAILED

        self.db.commit()
        self.db.refresh(job)
        return job

    def cancel(self, job_id: str) -> Optional[Job]:
        """Cancel a job if it's still queued or in retry"""
        job = self.get_by_id(job_id)
        if not job:
            return None

        if job.status in [JobStatus.QUEUED, JobStatus.RETRY]:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(job)

        return job

    def get_pending_jobs(self, limit: int = 100) -> List[Job]:
        """Get jobs waiting to be processed (QUEUED or RETRY)"""
        return self.db.query(Job).filter(
            Job.status.in_([JobStatus.QUEUED, JobStatus.RETRY])
        ).order_by(Job.created_at).limit(limit).all()
