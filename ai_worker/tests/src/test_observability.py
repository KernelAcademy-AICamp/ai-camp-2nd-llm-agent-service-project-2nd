"""
Test suite for Observability & Error Tracking (Issue #86)

Tests:
- ProcessingStage enum
- ErrorType enum and classification
- JobContext and StageMetrics
- JobTracker with stage tracking
- Duration measurement
- Error recording
"""

import pytest
import time
import logging
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.utils.observability import (
    ProcessingStage,
    ErrorType,
    StageMetrics,
    JobContext,
    StageTracker,
    JobTracker,
    log_job_event,
    classify_exception
)


class TestProcessingStage:
    """Test ProcessingStage enum"""

    def test_stage_values(self):
        """Test all stage values exist"""
        assert ProcessingStage.DOWNLOAD.value == "DOWNLOAD"
        assert ProcessingStage.HASH.value == "HASH"
        assert ProcessingStage.PARSE.value == "PARSE"
        assert ProcessingStage.ANALYZE.value == "ANALYZE"
        assert ProcessingStage.EMBED.value == "EMBED"
        assert ProcessingStage.STORE.value == "STORE"
        assert ProcessingStage.COMPLETE.value == "COMPLETE"

    def test_stage_string_conversion(self):
        """Test stages can be converted to string via .value"""
        assert ProcessingStage.PARSE.value == "PARSE"
        assert ProcessingStage.ANALYZE.value == "ANALYZE"


class TestErrorType:
    """Test ErrorType enum"""

    def test_error_type_values(self):
        """Test all error type values exist"""
        assert ErrorType.TIMEOUT.value == "TIMEOUT"
        assert ErrorType.API_ERROR.value == "API_ERROR"
        assert ErrorType.PARSE_ERROR.value == "PARSE_ERROR"
        assert ErrorType.STORAGE_ERROR.value == "STORAGE_ERROR"
        assert ErrorType.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert ErrorType.RATE_LIMIT.value == "RATE_LIMIT"
        assert ErrorType.DUPLICATE.value == "DUPLICATE"
        assert ErrorType.PERMISSION_ERROR.value == "PERMISSION_ERROR"
        assert ErrorType.UNKNOWN.value == "UNKNOWN"


class TestClassifyException:
    """Test exception classification"""

    def test_classify_timeout_error(self):
        """Test timeout error classification"""
        error = TimeoutError("Connection timed out")
        assert classify_exception(error) == ErrorType.TIMEOUT

    def test_classify_rate_limit_error(self):
        """Test rate limit error classification"""
        error = Exception("Rate limit exceeded (429)")
        assert classify_exception(error) == ErrorType.RATE_LIMIT

    def test_classify_parse_error(self):
        """Test parse error classification"""
        error = UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')
        assert classify_exception(error) == ErrorType.PARSE_ERROR

    def test_classify_permission_error(self):
        """Test permission error classification"""
        error = PermissionError("Access denied")
        assert classify_exception(error) == ErrorType.PERMISSION_ERROR

    def test_classify_validation_error(self):
        """Test validation error classification"""
        error = ValueError("Invalid input")
        assert classify_exception(error) == ErrorType.VALIDATION_ERROR

    def test_classify_unknown_error(self):
        """Test unknown error classification"""
        error = Exception("Some random error")
        assert classify_exception(error) == ErrorType.UNKNOWN

    def test_classify_api_error_from_message(self):
        """Test API error classification from message"""
        error = Exception("OpenAI API request failed")
        assert classify_exception(error) == ErrorType.API_ERROR

    def test_classify_storage_error(self):
        """Test storage error classification from message"""
        error = Exception("DynamoDB throughput exceeded")
        assert classify_exception(error) == ErrorType.STORAGE_ERROR


class TestStageMetrics:
    """Test StageMetrics dataclass"""

    def test_stage_metrics_creation(self):
        """Test StageMetrics creation"""
        metrics = StageMetrics(stage=ProcessingStage.PARSE)

        assert metrics.stage == ProcessingStage.PARSE
        assert metrics.started_at is not None
        assert metrics.completed_at is None
        assert metrics.duration_ms is None
        assert metrics.success is True

    def test_stage_metrics_complete(self):
        """Test StageMetrics completion"""
        metrics = StageMetrics(stage=ProcessingStage.PARSE)
        time.sleep(0.01)  # Small delay
        metrics.complete(success=True)

        assert metrics.completed_at is not None
        assert metrics.duration_ms is not None
        assert metrics.duration_ms >= 10  # At least 10ms
        assert metrics.success is True

    def test_stage_metrics_complete_failure(self):
        """Test StageMetrics failure"""
        metrics = StageMetrics(stage=ProcessingStage.PARSE)
        metrics.complete(success=False)

        assert metrics.success is False

    def test_stage_metrics_to_dict(self):
        """Test StageMetrics serialization"""
        metrics = StageMetrics(stage=ProcessingStage.PARSE)
        metrics.complete(success=True)
        metrics.error_type = ErrorType.PARSE_ERROR
        metrics.error_message = "Test error"
        metrics.metadata = {"lines": 100}

        result = metrics.to_dict()

        assert result["stage"] == "PARSE"
        assert result["success"] is True
        assert result["error_type"] == "PARSE_ERROR"
        assert result["error_message"] == "Test error"
        assert result["metadata"] == {"lines": 100}


class TestJobContext:
    """Test JobContext dataclass"""

    def test_job_context_creation(self):
        """Test JobContext creation"""
        context = JobContext(
            job_id="job_123",
            case_id="case_456",
            evidence_id="ev_789"
        )

        assert context.job_id == "job_123"
        assert context.case_id == "case_456"
        assert context.evidence_id == "ev_789"
        assert context.started_at is not None
        assert context.stages == []
        assert context.errors == []

    def test_job_context_to_log_context(self):
        """Test minimal log context extraction"""
        context = JobContext(
            job_id="job_123",
            case_id="case_456",
            evidence_id="ev_789"
        )
        context.current_stage = ProcessingStage.PARSE

        log_ctx = context.to_log_context()

        assert log_ctx["job_id"] == "job_123"
        assert log_ctx["case_id"] == "case_456"
        assert log_ctx["evidence_id"] == "ev_789"
        assert log_ctx["stage"] == "PARSE"

    def test_job_context_to_full_dict(self):
        """Test full context serialization"""
        context = JobContext(
            job_id="job_123",
            case_id="case_456"
        )
        context.file_hash = "abc123def456"

        result = context.to_full_dict()

        assert result["job_id"] == "job_123"
        assert result["case_id"] == "case_456"
        assert result["file_hash"] == "abc123def456..."  # Truncated
        assert "total_duration_ms" in result
        assert result["success"] is True  # No errors


class TestJobTracker:
    """Test JobTracker class"""

    def test_job_tracker_creation(self):
        """Test JobTracker creation"""
        tracker = JobTracker(
            job_id="job_123",
            case_id="case_456",
            evidence_id="ev_789"
        )

        assert tracker.context.job_id == "job_123"
        assert tracker.context.case_id == "case_456"
        assert tracker.context.evidence_id == "ev_789"

    def test_job_tracker_auto_job_id(self):
        """Test JobTracker auto-generates job_id"""
        tracker = JobTracker()

        assert tracker.context.job_id is not None
        assert tracker.context.job_id.startswith("job_")

    def test_job_tracker_from_s3_event(self):
        """Test JobTracker creation from S3 event"""
        tracker = JobTracker.from_s3_event(
            bucket="test-bucket",
            key="cases/case001/raw/ev_123_file.txt"
        )

        assert tracker.context.s3_bucket == "test-bucket"
        assert tracker.context.s3_key == "cases/case001/raw/ev_123_file.txt"

    def test_job_tracker_set_case_id(self):
        """Test setting case_id"""
        tracker = JobTracker()
        tracker.set_case_id("case_new")

        assert tracker.context.case_id == "case_new"

    def test_job_tracker_set_file_info(self):
        """Test setting file info"""
        tracker = JobTracker()
        tracker.set_file_info(file_type="pdf", file_hash="abc123")

        assert tracker.context.file_type == "pdf"
        assert tracker.context.file_hash == "abc123"

    def test_job_tracker_stage_success(self):
        """Test stage tracking - success"""
        tracker = JobTracker(job_id="job_123")

        with tracker.stage(ProcessingStage.PARSE) as stage:
            stage.add_metadata(lines=100)

        assert len(tracker.context.stages) == 1
        assert tracker.context.stages[0].stage == ProcessingStage.PARSE
        assert tracker.context.stages[0].success is True
        assert tracker.context.stages[0].duration_ms is not None
        assert tracker.context.stages[0].metadata == {"lines": 100}

    def test_job_tracker_stage_failure(self):
        """Test stage tracking - failure"""
        tracker = JobTracker(job_id="job_123")

        with pytest.raises(ValueError):
            with tracker.stage(ProcessingStage.PARSE):
                raise ValueError("Invalid input data")

        assert len(tracker.context.stages) == 1
        assert tracker.context.stages[0].success is False
        # ValueError with "invalid" in message classifies as VALIDATION_ERROR
        assert tracker.context.stages[0].error_type == ErrorType.VALIDATION_ERROR
        assert "Invalid input data" in tracker.context.stages[0].error_message

    def test_job_tracker_record_error(self):
        """Test error recording"""
        tracker = JobTracker(job_id="job_123")
        tracker.context.current_stage = ProcessingStage.ANALYZE

        tracker.record_error(
            ErrorType.API_ERROR,
            "OpenAI rate limit",
            extra_data="test"
        )

        assert len(tracker.context.errors) == 1
        assert tracker.context.errors[0]["error_type"] == "API_ERROR"
        assert tracker.context.errors[0]["message"] == "OpenAI rate limit"
        assert tracker.context.errors[0]["stage"] == "ANALYZE"

    def test_job_tracker_get_summary(self):
        """Test job summary generation"""
        tracker = JobTracker(job_id="job_123", case_id="case_456")
        tracker.set_file_info(file_type="txt")

        with tracker.stage(ProcessingStage.PARSE):
            pass

        with tracker.stage(ProcessingStage.ANALYZE):
            pass

        summary = tracker.get_summary()

        assert summary["job_id"] == "job_123"
        assert summary["case_id"] == "case_456"
        assert summary["file_type"] == "txt"
        assert len(summary["stages"]) == 2
        assert summary["success"] is True

    def test_job_tracker_multiple_stages(self):
        """Test multiple stage tracking"""
        tracker = JobTracker(job_id="job_123")

        with tracker.stage(ProcessingStage.DOWNLOAD):
            time.sleep(0.01)

        with tracker.stage(ProcessingStage.HASH):
            time.sleep(0.01)

        with tracker.stage(ProcessingStage.PARSE):
            time.sleep(0.01)

        assert len(tracker.context.stages) == 3
        assert tracker.context.stages[0].stage == ProcessingStage.DOWNLOAD
        assert tracker.context.stages[1].stage == ProcessingStage.HASH
        assert tracker.context.stages[2].stage == ProcessingStage.PARSE

        # Each stage should have duration
        for stage in tracker.context.stages:
            assert stage.duration_ms >= 10


class TestLogJobEvent:
    """Test log_job_event utility function"""

    def test_log_job_event_basic(self):
        """Test basic job event logging"""
        mock_logger = MagicMock()

        log_job_event(
            logger=mock_logger,
            event="Processing started",
            job_id="job_123",
            case_id="case_456",
            evidence_id="ev_789",
            stage=ProcessingStage.PARSE
        )

        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][1] == "Processing started"
        assert call_args[1]["extra"]["job_id"] == "job_123"
        assert call_args[1]["extra"]["stage"] == "PARSE"

    def test_log_job_event_with_error(self):
        """Test job event logging with error"""
        mock_logger = MagicMock()

        log_job_event(
            logger=mock_logger,
            event="Processing failed",
            job_id="job_123",
            error_type=ErrorType.API_ERROR,
            duration_ms=1500.5
        )

        call_args = mock_logger.log.call_args
        assert call_args[1]["extra"]["error_type"] == "API_ERROR"
        assert call_args[1]["extra"]["duration_ms"] == 1500.5

    def test_log_job_event_with_metadata(self):
        """Test job event logging with metadata"""
        mock_logger = MagicMock()

        log_job_event(
            logger=mock_logger,
            event="Chunks indexed",
            job_id="job_123",
            chunks=50,
            tokens_used=1500
        )

        call_args = mock_logger.log.call_args
        assert call_args[1]["extra"]["metadata"]["chunks"] == 50
        assert call_args[1]["extra"]["metadata"]["tokens_used"] == 1500


class TestStageTrackerLogging:
    """Test StageTracker logging functionality"""

    def test_stage_tracker_log(self):
        """Test stage tracker logging"""
        tracker = JobTracker(job_id="job_123")

        with patch.object(tracker.logger, 'info') as mock_info:
            with tracker.stage(ProcessingStage.PARSE) as stage:
                stage.log("Processing 100 lines", lines=100)

            # Should have been called for start, custom log, and complete
            assert mock_info.call_count >= 2

    def test_stage_tracker_log_levels(self):
        """Test stage tracker different log levels"""
        tracker = JobTracker(job_id="job_123")

        with tracker.stage(ProcessingStage.EMBED) as stage:
            with patch.object(tracker.logger, 'warning') as mock_warning:
                stage.log("Using fallback", level="warning")
                mock_warning.assert_called_once()


class TestIntegration:
    """Integration tests for observability"""

    def test_full_job_workflow(self):
        """Test complete job workflow"""
        tracker = JobTracker.from_s3_event(
            bucket="test-bucket",
            key="cases/case001/raw/ev_123_file.txt"
        )

        # Set extracted info
        tracker.set_case_id("case001")
        tracker.set_evidence_id("ev_123")

        # Download stage
        with tracker.stage(ProcessingStage.DOWNLOAD) as stage:
            stage.add_metadata(file_size=1024)

        # Hash stage
        with tracker.stage(ProcessingStage.HASH) as stage:
            tracker.set_file_info(file_type="txt", file_hash="abc123def456")

        # Parse stage
        with tracker.stage(ProcessingStage.PARSE) as stage:
            stage.add_metadata(message_count=50)

        # Analyze stage
        with tracker.stage(ProcessingStage.ANALYZE) as stage:
            stage.add_metadata(categories=["폭언", "협박"])

        # Embed stage
        with tracker.stage(ProcessingStage.EMBED) as stage:
            stage.add_metadata(embeddings=50, fallback_count=2)

        # Store stage
        with tracker.stage(ProcessingStage.STORE) as stage:
            stage.add_metadata(chunks_indexed=50)

        # Mark complete
        tracker.context.current_stage = ProcessingStage.COMPLETE

        # Get summary
        summary = tracker.get_summary()

        assert summary["job_id"].startswith("job_")
        assert summary["case_id"] == "case001"
        assert summary["evidence_id"] == "ev_123"
        assert summary["s3_bucket"] == "test-bucket"
        assert summary["file_type"] == "txt"
        assert len(summary["stages"]) == 6
        assert summary["success"] is True
        assert len(summary["errors"]) == 0

    def test_job_with_error_workflow(self):
        """Test job workflow with error"""
        tracker = JobTracker(job_id="job_error_test")

        # Download succeeds
        with tracker.stage(ProcessingStage.DOWNLOAD):
            pass

        # Parse fails
        with pytest.raises(Exception):
            with tracker.stage(ProcessingStage.PARSE):
                raise Exception("Parse failed: format error")

        summary = tracker.get_summary()

        # Note: summary["success"] is based on errors list, not stage failures
        # Stage failures are tracked in stages array
        assert len(summary["stages"]) == 2
        assert summary["stages"][0]["success"] is True
        assert summary["stages"][1]["success"] is False
        assert summary["stages"][1]["error_type"] == "UNKNOWN"
        assert "Parse failed" in summary["stages"][1]["error_message"]
