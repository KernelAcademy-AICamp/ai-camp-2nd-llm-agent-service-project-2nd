"""
Jobs API endpoints
POST /jobs - Create new async job
GET /jobs - List jobs for current user
GET /jobs/{id} - Get job detail
POST /jobs/{id}/cancel - Cancel a job
GET /cases/{case_id}/jobs - List jobs for a case (in cases.py)
POST /jobs/{id}/callback - Worker callback to update status (internal)
"""

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.db.session import get_db
from app.db.models import JobStatus, JobType
from app.db.schemas import (
    JobCreate,
    JobOut,
    JobDetail,
    JobListResponse,
    JobStatusUpdate,
    JobProgressUpdate
)
from app.services.job_service import JobService
from app.core.dependencies import get_current_user_id


router = APIRouter()


def _job_to_out(job) -> JobOut:
    """Convert Job model to JobOut schema"""
    return JobOut(
        id=job.id,
        case_id=job.case_id,
        user_id=job.user_id,
        job_type=job.job_type,
        status=job.status,
        evidence_id=job.evidence_id,
        progress=int(job.progress or "0"),
        retry_count=int(job.retry_count or "0"),
        max_retries=int(job.max_retries or "3"),
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=json.loads(job.error_details).get("message") if job.error_details else None
    )


def _job_to_detail(job) -> JobDetail:
    """Convert Job model to JobDetail schema"""
    return JobDetail(
        id=job.id,
        case_id=job.case_id,
        user_id=job.user_id,
        job_type=job.job_type,
        status=job.status,
        evidence_id=job.evidence_id,
        input_data=json.loads(job.input_data) if job.input_data else None,
        output_data=json.loads(job.output_data) if job.output_data else None,
        error_details=json.loads(job.error_details) if job.error_details else None,
        progress=int(job.progress or "0"),
        retry_count=int(job.retry_count or "0"),
        max_retries=int(job.max_retries or "3"),
        lambda_request_id=job.lambda_request_id,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: JobCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new async processing job

    **Request Body:**
    - case_id: Case ID (required)
    - job_type: Type of job (ocr, stt, vision, draft, analysis, pdf_export, docx_export)
    - evidence_id: Evidence ID for evidence-related jobs (optional)
    - parameters: Additional job parameters (optional)

    **Response:**
    - 201: Job created successfully
    - Job details including id, status (queued)

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the case

    **Notes:**
    - Job is created in QUEUED status
    - Worker will process and update status via callback
    """
    job_service = JobService(db)
    job = job_service.create_job(
        case_id=job_data.case_id,
        user_id=user_id,
        job_type=job_data.job_type,
        evidence_id=job_data.evidence_id,
        parameters=job_data.parameters
    )
    return _job_to_out(job)


@router.get("", response_model=JobListResponse)
def list_user_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all jobs for current user

    **Query Parameters:**
    - status: Filter by job status (optional)

    **Response:**
    - 200: List of jobs
    - jobs: Array of job summaries
    - total: Total count

    **Authentication:**
    - Requires valid JWT token
    - Only returns jobs created by the current user
    """
    job_service = JobService(db)
    jobs = job_service.get_user_jobs(user_id=user_id, status=status)
    return JobListResponse(
        jobs=[_job_to_out(j) for j in jobs],
        total=len(jobs)
    )


@router.get("/{job_id}", response_model=JobDetail)
def get_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get job detail by ID

    **Path Parameters:**
    - job_id: Job ID

    **Response:**
    - 200: Job detail with full data
    - 403: User doesn't have access
    - 404: Job not found

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the job's case
    """
    job_service = JobService(db)
    job = job_service.get_job(job_id, user_id)
    return _job_to_detail(job)


@router.post("/{job_id}/cancel", response_model=JobOut)
def cancel_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending job

    **Path Parameters:**
    - job_id: Job ID

    **Response:**
    - 200: Job cancelled successfully
    - 400: Job cannot be cancelled (not in QUEUED or RETRY status)
    - 403: User doesn't have access
    - 404: Job not found

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the job's case

    **Notes:**
    - Only QUEUED or RETRY jobs can be cancelled
    - PROCESSING, COMPLETED, FAILED jobs cannot be cancelled
    """
    job_service = JobService(db)
    job = job_service.cancel_job(job_id, user_id)
    return _job_to_out(job)


@router.get("/{job_id}/output")
def get_job_output(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get job output data (for completed jobs)

    **Path Parameters:**
    - job_id: Job ID

    **Response:**
    - 200: Output data (JSON)
    - 404: Job not found or no output available

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the job's case
    """
    job_service = JobService(db)
    output = job_service.get_job_output(job_id, user_id)
    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No output available for this job"
        )
    return output


# ============================================
# Internal/Callback Endpoints (for AI Worker)
# ============================================
@router.post("/{job_id}/callback", response_model=JobOut, include_in_schema=False)
def job_callback(
    job_id: str,
    update: JobStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Callback endpoint for AI Worker to update job status

    **Internal use only** - not exposed in OpenAPI schema

    **Path Parameters:**
    - job_id: Job ID

    **Request Body:**
    - status: New job status
    - output_data: Output data (for completed jobs)
    - error_details: Error details (for failed jobs)
    - lambda_request_id: Lambda request ID for correlation

    **Notes:**
    - Called by AI Worker Lambda function
    - Should be protected by API key or internal auth in production
    """
    job_service = JobService(db)
    job = job_service.update_job_status(
        job_id=job_id,
        status=update.status,
        output_data=update.output_data,
        error_details=update.error_details,
        lambda_request_id=update.lambda_request_id
    )
    return _job_to_out(job)


@router.post("/{job_id}/progress", response_model=JobOut, include_in_schema=False)
def update_job_progress(
    job_id: str,
    update: JobProgressUpdate,
    db: Session = Depends(get_db)
):
    """
    Update job progress (0-100)

    **Internal use only** - not exposed in OpenAPI schema

    **Path Parameters:**
    - job_id: Job ID

    **Request Body:**
    - progress: Progress percentage (0-100)

    **Notes:**
    - Called by AI Worker Lambda function
    - Used for long-running jobs like video processing
    """
    job_service = JobService(db)
    job = job_service.update_job_progress(job_id, update.progress)
    return _job_to_out(job)


# ============================================
# Case-specific Job Endpoints
# ============================================
@router.get("/case/{case_id}", response_model=JobListResponse)
def list_case_jobs(
    case_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all jobs for a specific case

    **Path Parameters:**
    - case_id: Case ID

    **Query Parameters:**
    - status: Filter by job status (optional)
    - job_type: Filter by job type (optional)

    **Response:**
    - 200: List of jobs for the case
    - 403: User doesn't have access to case
    - 404: Case not found

    **Authentication:**
    - Requires valid JWT token
    - User must be a member of the case
    """
    job_service = JobService(db)
    jobs = job_service.get_case_jobs(
        case_id=case_id,
        user_id=user_id,
        status=status,
        job_type=job_type
    )
    return JobListResponse(
        jobs=[_job_to_out(j) for j in jobs],
        total=len(jobs)
    )
