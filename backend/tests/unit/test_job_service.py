"""
Unit tests for Job Service
TDD - Improving test coverage for job_service.py
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import json

from app.services.job_service import JobService
from app.db.models import Job, JobStatus, JobType, Case, CaseMember
from app.middleware.error_handler import ValidationError, NotFoundError, PermissionError


class TestCreateJob:
    """Unit tests for create_job method"""

    def test_create_job_success(self):
        """Successfully create a new job"""
        mock_db = MagicMock()

        # Mock case
        mock_case = MagicMock(spec=Case)
        mock_case.id = "case-123"

        # Mock job
        mock_job = MagicMock(spec=Job)
        mock_job.id = "job-123"
        mock_job.case_id = "case-123"
        mock_job.job_type = JobType.OCR
        mock_job.status = JobStatus.QUEUED

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.case_member_repo = MagicMock()
            service.job_repo = MagicMock()

            service.case_repo.get_by_id.return_value = mock_case
            service.case_member_repo.has_access.return_value = True
            service.job_repo.create.return_value = mock_job

            result = service.create_job(
                case_id="case-123",
                user_id="user-123",
                job_type=JobType.OCR
            )

            assert result.id == "job-123"
            service.job_repo.create.assert_called_once()

    def test_create_job_case_not_found(self):
        """Raises NotFoundError when case not found"""
        mock_db = MagicMock()

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.case_member_repo = MagicMock()
            service.job_repo = MagicMock()

            service.case_repo.get_by_id.return_value = None

            with pytest.raises(NotFoundError):
                service.create_job(
                    case_id="nonexistent",
                    user_id="user-123",
                    job_type=JobType.OCR
                )

    def test_create_job_no_access(self):
        """Raises PermissionError when user has no access"""
        mock_db = MagicMock()
        mock_case = MagicMock(spec=Case)

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.case_member_repo = MagicMock()
            service.job_repo = MagicMock()

            service.case_repo.get_by_id.return_value = mock_case
            service.case_member_repo.has_access.return_value = False

            with pytest.raises(PermissionError):
                service.create_job(
                    case_id="case-123",
                    user_id="user-123",
                    job_type=JobType.OCR
                )


class TestGetJob:
    """Unit tests for get_job method"""

    def test_get_job_success(self):
        """Successfully get job by ID"""
        mock_db = MagicMock()
        mock_job = MagicMock(spec=Job)
        mock_job.id = "job-123"
        mock_job.case_id = "case-123"

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()
            service.case_member_repo = MagicMock()

            service.job_repo.get_by_id.return_value = mock_job
            service.case_member_repo.is_member.return_value = True

            result = service.get_job("job-123", "user-123")

            assert result.id == "job-123"

    def test_get_job_not_found(self):
        """Raises NotFoundError when job not found"""
        mock_db = MagicMock()

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.get_by_id.return_value = None

            with pytest.raises(NotFoundError):
                service.get_job("nonexistent", "user-123")

    def test_get_job_no_access(self):
        """Raises PermissionError when user has no access"""
        mock_db = MagicMock()
        mock_job = MagicMock(spec=Job)
        mock_job.case_id = "case-123"

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()
            service.case_member_repo = MagicMock()

            service.job_repo.get_by_id.return_value = mock_job
            service.case_member_repo.is_member.return_value = False

            with pytest.raises(PermissionError):
                service.get_job("job-123", "user-123")


class TestGetCaseJobs:
    """Unit tests for get_case_jobs method"""

    def test_get_case_jobs_success(self):
        """Successfully get jobs for a case"""
        mock_db = MagicMock()
        mock_case = MagicMock(spec=Case)
        mock_jobs = [MagicMock(spec=Job) for _ in range(3)]

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.case_member_repo = MagicMock()
            service.job_repo = MagicMock()

            service.case_repo.get_by_id.return_value = mock_case
            service.case_member_repo.has_access.return_value = True
            service.job_repo.get_by_case.return_value = mock_jobs

            result = service.get_case_jobs("case-123", "user-123")

            assert len(result) == 3

    def test_get_case_jobs_with_filters(self):
        """Get jobs with status and type filters"""
        mock_db = MagicMock()
        mock_case = MagicMock(spec=Case)
        mock_jobs = [MagicMock(spec=Job)]

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.case_member_repo = MagicMock()
            service.job_repo = MagicMock()

            service.case_repo.get_by_id.return_value = mock_case
            service.case_member_repo.has_access.return_value = True
            service.job_repo.get_by_case.return_value = mock_jobs

            result = service.get_case_jobs(
                "case-123", "user-123",
                status="completed",
                job_type="ocr"
            )

            assert len(result) == 1
            service.job_repo.get_by_case.assert_called_once_with(
                case_id="case-123",
                status=JobStatus.COMPLETED,
                job_type=JobType.OCR
            )

    def test_get_case_jobs_case_not_found(self):
        """Raises NotFoundError when case not found"""
        mock_db = MagicMock()

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()

            service.case_repo.get_by_id.return_value = None

            with pytest.raises(NotFoundError):
                service.get_case_jobs("nonexistent", "user-123")


class TestGetUserJobs:
    """Unit tests for get_user_jobs method"""

    def test_get_user_jobs_success(self):
        """Successfully get jobs for a user"""
        mock_db = MagicMock()
        mock_jobs = [MagicMock(spec=Job) for _ in range(2)]

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.get_by_user.return_value = mock_jobs

            result = service.get_user_jobs("user-123")

            assert len(result) == 2

    def test_get_user_jobs_with_status(self):
        """Get user jobs with status filter"""
        mock_db = MagicMock()
        mock_jobs = [MagicMock(spec=Job)]

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.get_by_user.return_value = mock_jobs

            result = service.get_user_jobs("user-123", status="processing")

            service.job_repo.get_by_user.assert_called_once_with(
                user_id="user-123",
                status=JobStatus.PROCESSING
            )


class TestUpdateJobStatus:
    """Unit tests for update_job_status method"""

    def test_update_job_status_success(self):
        """Successfully update job status"""
        mock_db = MagicMock()
        mock_job = MagicMock(spec=Job)
        mock_job.id = "job-123"
        mock_job.status = JobStatus.COMPLETED

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.update_status.return_value = mock_job

            result = service.update_job_status("job-123", JobStatus.COMPLETED)

            assert result.status == JobStatus.COMPLETED

    def test_update_job_status_with_output(self):
        """Update job status with output data"""
        mock_db = MagicMock()
        mock_job = MagicMock(spec=Job)

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.update_status.return_value = mock_job

            output_data = {"result": "success"}
            service.update_job_status(
                "job-123",
                JobStatus.COMPLETED,
                output_data=output_data
            )

            call_args = service.job_repo.update_status.call_args
            assert call_args.kwargs["output_data"] == json.dumps(output_data)

    def test_update_job_status_not_found(self):
        """Raises NotFoundError when job not found"""
        mock_db = MagicMock()

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.update_status.return_value = None

            with pytest.raises(NotFoundError):
                service.update_job_status("nonexistent", JobStatus.COMPLETED)


class TestUpdateJobProgress:
    """Unit tests for update_job_progress method"""

    def test_update_job_progress_success(self):
        """Successfully update job progress"""
        mock_db = MagicMock()
        mock_job = MagicMock(spec=Job)
        mock_job.progress = "50"

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.update_progress.return_value = mock_job

            result = service.update_job_progress("job-123", 50)

            assert result.progress == "50"

    def test_update_job_progress_not_found(self):
        """Raises NotFoundError when job not found"""
        mock_db = MagicMock()

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.update_progress.return_value = None

            with pytest.raises(NotFoundError):
                service.update_job_progress("nonexistent", 50)


class TestCancelJob:
    """Unit tests for cancel_job method"""

    def test_cancel_job_success(self):
        """Successfully cancel a queued job"""
        mock_db = MagicMock()
        mock_job = MagicMock(spec=Job)
        mock_job.id = "job-123"
        mock_job.case_id = "case-123"
        mock_job.status = JobStatus.QUEUED

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()
            service.case_member_repo = MagicMock()

            service.job_repo.get_by_id.return_value = mock_job
            service.case_member_repo.is_member.return_value = True
            service.job_repo.cancel.return_value = mock_job

            result = service.cancel_job("job-123", "user-123")

            service.job_repo.cancel.assert_called_once()

    def test_cancel_job_not_found(self):
        """Raises NotFoundError when job not found"""
        mock_db = MagicMock()

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.get_by_id.return_value = None

            with pytest.raises(NotFoundError):
                service.cancel_job("nonexistent", "user-123")

    def test_cancel_job_no_access(self):
        """Raises PermissionError when user has no access"""
        mock_db = MagicMock()
        mock_job = MagicMock(spec=Job)
        mock_job.case_id = "case-123"

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()
            service.case_member_repo = MagicMock()

            service.job_repo.get_by_id.return_value = mock_job
            service.case_member_repo.is_member.return_value = False

            with pytest.raises(PermissionError):
                service.cancel_job("job-123", "user-123")

    def test_cancel_job_invalid_status(self):
        """Raises ValidationError when job cannot be cancelled"""
        mock_db = MagicMock()
        mock_job = MagicMock(spec=Job)
        mock_job.case_id = "case-123"
        mock_job.status = JobStatus.PROCESSING

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()
            service.case_member_repo = MagicMock()

            service.job_repo.get_by_id.return_value = mock_job
            service.case_member_repo.is_member.return_value = True

            with pytest.raises(ValidationError, match="Cannot cancel job"):
                service.cancel_job("job-123", "user-123")


class TestRetryJob:
    """Unit tests for retry_job method"""

    def test_retry_job_success(self):
        """Successfully retry a failed job"""
        mock_db = MagicMock()
        mock_job = MagicMock(spec=Job)
        mock_job.retry_count = "1"

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.increment_retry.return_value = mock_job

            result = service.retry_job("job-123")

            assert result.retry_count == "1"

    def test_retry_job_not_found(self):
        """Raises NotFoundError when job not found"""
        mock_db = MagicMock()

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()

            service.job_repo.increment_retry.return_value = None

            with pytest.raises(NotFoundError):
                service.retry_job("nonexistent")


class TestGetJobOutput:
    """Unit tests for get_job_output method"""

    def test_get_job_output_success(self):
        """Successfully get job output"""
        mock_db = MagicMock()
        output_data = {"result": "success", "data": [1, 2, 3]}

        mock_job = MagicMock(spec=Job)
        mock_job.case_id = "case-123"
        mock_job.output_data = json.dumps(output_data)

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()
            service.case_member_repo = MagicMock()

            service.job_repo.get_by_id.return_value = mock_job
            service.case_member_repo.is_member.return_value = True

            result = service.get_job_output("job-123", "user-123")

            assert result == output_data

    def test_get_job_output_none(self):
        """Returns None when job has no output"""
        mock_db = MagicMock()
        mock_job = MagicMock(spec=Job)
        mock_job.case_id = "case-123"
        mock_job.output_data = None

        with patch.object(JobService, '__init__', lambda x, y: None):
            service = JobService(mock_db)
            service.db = mock_db
            service.job_repo = MagicMock()
            service.case_member_repo = MagicMock()

            service.job_repo.get_by_id.return_value = mock_job
            service.case_member_repo.is_member.return_value = True

            result = service.get_job_output("job-123", "user-123")

            assert result is None
