"""
Observability & Job Tracking Module for AI Worker (Issue #86)

Provides:
- Job context tracking (job_id, case_id, evidence_id)
- Processing stage tracking (PARSE, ANALYZE, EMBED, STORE)
- Error classification (TIMEOUT, API_ERROR, PARSE_ERROR, etc.)
- Duration measurement and metrics
- Structured logging with CloudWatch/Lambda compatibility

Usage:
    from src.utils.observability import JobTracker, ProcessingStage, ErrorType

    tracker = JobTracker(
        job_id="job_123",
        case_id="case_456",
        evidence_id="ev_789"
    )

    with tracker.stage(ProcessingStage.PARSE) as stage:
        # Do parsing work
        stage.log("Parsing file", extra={"lines": 100})

    # On error
    tracker.record_error(ErrorType.API_ERROR, "OpenAI rate limit exceeded")
"""

import logging
import json
import uuid
import time
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager


class ProcessingStage(str, Enum):
    """AI Worker processing stages"""
    DOWNLOAD = "DOWNLOAD"      # S3 file download
    HASH = "HASH"              # Hash calculation for idempotency
    PARSE = "PARSE"            # File parsing (text/image/audio/video/pdf)
    ANALYZE = "ANALYZE"        # Article 840 tagging, summarization
    EMBED = "EMBED"            # OpenAI embedding generation
    STORE = "STORE"            # DynamoDB + Qdrant storage
    COMPLETE = "COMPLETE"      # Processing complete


class ErrorType(str, Enum):
    """Error classification for observability"""
    TIMEOUT = "TIMEOUT"                    # Lambda/API timeout
    API_ERROR = "API_ERROR"                # External API error (OpenAI, Qdrant)
    PARSE_ERROR = "PARSE_ERROR"            # File parsing error
    STORAGE_ERROR = "STORAGE_ERROR"        # DynamoDB/Qdrant storage error
    VALIDATION_ERROR = "VALIDATION_ERROR"  # Invalid input/file format
    RATE_LIMIT = "RATE_LIMIT"              # API rate limit exceeded
    DUPLICATE = "DUPLICATE"                # Duplicate file (idempotency)
    PERMISSION_ERROR = "PERMISSION_ERROR"  # Access denied (S3, etc.)
    UNKNOWN = "UNKNOWN"                    # Uncategorized error


@dataclass
class StageMetrics:
    """Metrics for a single processing stage"""
    stage: ProcessingStage
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self, success: bool = True):
        """Mark stage as complete and calculate duration"""
        self.completed_at = datetime.now(timezone.utc)
        self.success = success
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = delta.total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "stage": self.stage.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": round(self.duration_ms, 2) if self.duration_ms else None,
            "success": self.success,
        }
        if self.error_type:
            result["error_type"] = self.error_type.value
        if self.error_message:
            result["error_message"] = self.error_message
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class JobContext:
    """
    Context for a single processing job.

    All fields are logged with every log message for traceability.
    """
    job_id: str
    case_id: Optional[str] = None
    evidence_id: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_key: Optional[str] = None
    file_type: Optional[str] = None
    file_hash: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    current_stage: Optional[ProcessingStage] = None
    stages: List[StageMetrics] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_log_context(self) -> Dict[str, Any]:
        """Get minimal context for log messages"""
        return {
            "job_id": self.job_id,
            "case_id": self.case_id,
            "evidence_id": self.evidence_id,
            "stage": self.current_stage.value if self.current_stage else None,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Get full context for final summary"""
        total_duration = (datetime.now(timezone.utc) - self.started_at).total_seconds() * 1000
        return {
            "job_id": self.job_id,
            "case_id": self.case_id,
            "evidence_id": self.evidence_id,
            "s3_bucket": self.s3_bucket,
            "s3_key": self.s3_key,
            "file_type": self.file_type,
            "file_hash": self.file_hash[:16] + "..." if self.file_hash else None,
            "started_at": self.started_at.isoformat(),
            "total_duration_ms": round(total_duration, 2),
            "current_stage": self.current_stage.value if self.current_stage else None,
            "stages": [s.to_dict() for s in self.stages],
            "errors": self.errors,
            "success": len(self.errors) == 0,
            "metadata": self.metadata,
        }


class StageTracker:
    """
    Context manager for tracking a single processing stage.

    Usage:
        with tracker.stage(ProcessingStage.PARSE) as stage:
            stage.log("Parsing file", lines=100)
            result = parse_file(...)
            stage.add_metadata(parsed_lines=len(result))
    """

    def __init__(
        self,
        job_tracker: 'JobTracker',
        stage: ProcessingStage,
        logger: logging.Logger
    ):
        self.job_tracker = job_tracker
        self.stage = stage
        self.logger = logger
        self.metrics = StageMetrics(stage=stage)

    def __enter__(self) -> 'StageTracker':
        self.job_tracker.context.current_stage = self.stage
        self.job_tracker.context.stages.append(self.metrics)
        self.log("Stage started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.metrics.complete(success=False)
            error_type = self._classify_error(exc_type, exc_val)
            self.metrics.error_type = error_type
            self.metrics.error_message = str(exc_val)
            self.log(
                f"Stage failed: {exc_val}",
                level="error",
                error_type=error_type.value,
                error_message=str(exc_val)
            )
        else:
            self.metrics.complete(success=True)
            self.log(
                "Stage completed",
                duration_ms=round(self.metrics.duration_ms or 0, 2)
            )
        return False  # Don't suppress exceptions

    def log(self, message: str, level: str = "info", **extra):
        """Log a message with job context"""
        log_data = self.job_tracker.context.to_log_context()
        log_data.update(extra)
        log_data["duration_ms"] = round(
            (datetime.now(timezone.utc) - self.metrics.started_at).total_seconds() * 1000,
            2
        )

        log_func = getattr(self.logger, level)
        log_func(message, extra=log_data)

    def add_metadata(self, **kwargs):
        """Add metadata to this stage's metrics"""
        self.metrics.metadata.update(kwargs)

    def _classify_error(self, exc_type, exc_val) -> ErrorType:
        """Classify exception into ErrorType"""
        error_name = exc_type.__name__.lower()
        error_msg = str(exc_val).lower()

        if "timeout" in error_name or "timeout" in error_msg:
            return ErrorType.TIMEOUT
        if "ratelimit" in error_name or "rate limit" in error_msg or "429" in error_msg:
            return ErrorType.RATE_LIMIT
        if "parse" in error_name or "decode" in error_name:
            return ErrorType.PARSE_ERROR
        if "permission" in error_name or "access denied" in error_msg:
            return ErrorType.PERMISSION_ERROR
        if "duplicate" in error_name or "already exists" in error_msg:
            return ErrorType.DUPLICATE
        if "validation" in error_name or "invalid" in error_msg:
            return ErrorType.VALIDATION_ERROR
        if any(api in error_name for api in ["openai", "qdrant", "dynamo", "s3"]):
            return ErrorType.API_ERROR
        if "storage" in error_name or "dynamo" in error_msg or "qdrant" in error_msg:
            return ErrorType.STORAGE_ERROR

        return ErrorType.UNKNOWN


class JobTracker:
    """
    Main job tracking class for observability.

    Creates a unique job_id and provides structured logging
    with automatic context injection.

    Usage:
        tracker = JobTracker.from_s3_event(bucket, key)

        with tracker.stage(ProcessingStage.PARSE) as stage:
            parsed = parser.parse(file_path)
            stage.add_metadata(message_count=len(parsed))

        with tracker.stage(ProcessingStage.ANALYZE) as stage:
            tags = tagger.tag(parsed)

        # Get final summary
        summary = tracker.get_summary()
    """

    def __init__(
        self,
        job_id: Optional[str] = None,
        case_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
        logger_name: str = "ai_worker"
    ):
        self.context = JobContext(
            job_id=job_id or f"job_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            evidence_id=evidence_id
        )
        self.logger = logging.getLogger(logger_name)

    @classmethod
    def from_s3_event(
        cls,
        bucket: str,
        key: str,
        logger_name: str = "ai_worker"
    ) -> 'JobTracker':
        """Create tracker from S3 event information"""
        tracker = cls(logger_name=logger_name)
        tracker.context.s3_bucket = bucket
        tracker.context.s3_key = key
        return tracker

    def set_case_id(self, case_id: str):
        """Set case_id after extraction from S3 key"""
        self.context.case_id = case_id

    def set_evidence_id(self, evidence_id: str):
        """Set evidence_id after extraction from S3 key"""
        self.context.evidence_id = evidence_id

    def set_file_info(self, file_type: str, file_hash: Optional[str] = None):
        """Set file information"""
        self.context.file_type = file_type
        if file_hash:
            self.context.file_hash = file_hash

    def stage(self, stage: ProcessingStage) -> StageTracker:
        """Create a stage tracking context manager"""
        return StageTracker(self, stage, self.logger)

    def record_error(
        self,
        error_type: ErrorType,
        message: str,
        exception: Optional[Exception] = None,
        **extra
    ):
        """Record an error without raising"""
        error_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type.value,
            "message": message,
            "stage": self.context.current_stage.value if self.context.current_stage else None,
            **extra
        }
        if exception:
            error_data["exception_type"] = type(exception).__name__
            error_data["exception_message"] = str(exception)

        self.context.errors.append(error_data)
        self.logger.error(
            f"[{error_type.value}] {message}",
            extra=self.context.to_log_context(),
            exc_info=exception is not None
        )

    def log(self, message: str, level: str = "info", **extra):
        """Log a message with job context"""
        log_data = self.context.to_log_context()
        log_data.update(extra)

        log_func = getattr(self.logger, level)
        log_func(message, extra=log_data)

    def add_metadata(self, **kwargs):
        """Add metadata to job context"""
        self.context.metadata.update(kwargs)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get full job summary for final logging.

        Returns structured log compatible with CloudWatch Insights:
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "INFO",
            "job_id": "job_123",
            "case_id": "case_456",
            "evidence_id": "ev_789",
            "stage": "COMPLETE",
            "total_duration_ms": 5234,
            "stages": [...],
            "errors": [...],
            "success": true,
            "metadata": {...}
        }
        """
        return self.context.to_full_dict()

    def log_summary(self):
        """Log the full job summary"""
        summary = self.get_summary()
        level = "info" if summary["success"] else "error"

        self.logger.log(
            logging.INFO if level == "info" else logging.ERROR,
            f"Job {'completed' if summary['success'] else 'failed'}: {self.context.job_id}",
            extra={"job_summary": summary}
        )


# Utility functions for quick logging without tracker

def log_job_event(
    logger: logging.Logger,
    event: str,
    job_id: str,
    case_id: Optional[str] = None,
    evidence_id: Optional[str] = None,
    stage: Optional[ProcessingStage] = None,
    duration_ms: Optional[float] = None,
    error_type: Optional[ErrorType] = None,
    **metadata
) -> None:
    """
    Quick structured log function for job events.

    Outputs CloudWatch Insights compatible JSON:
    {
        "timestamp": "2024-01-15T10:30:00Z",
        "level": "INFO",
        "job_id": "job_123",
        "case_id": "case_456",
        "evidence_id": "ev_789",
        "stage": "ANALYZE",
        "duration_ms": 1523,
        "message": "Analysis completed",
        "metadata": {...}
    }
    """
    extra = {
        "job_id": job_id,
        "case_id": case_id,
        "evidence_id": evidence_id,
        "stage": stage.value if stage else None,
    }

    if duration_ms is not None:
        extra["duration_ms"] = round(duration_ms, 2)
    if error_type is not None:
        extra["error_type"] = error_type.value
    if metadata:
        extra["metadata"] = metadata

    # Remove None values
    extra = {k: v for k, v in extra.items() if v is not None}

    level = logging.ERROR if error_type else logging.INFO
    logger.log(level, event, extra=extra)


def classify_exception(exc: Exception) -> ErrorType:
    """
    Classify an exception into an ErrorType.

    Args:
        exc: Exception to classify

    Returns:
        ErrorType classification
    """
    exc_type_name = type(exc).__name__.lower()
    exc_msg = str(exc).lower()

    # Timeout errors
    if "timeout" in exc_type_name or "timeout" in exc_msg:
        return ErrorType.TIMEOUT

    # Rate limiting
    if "ratelimit" in exc_type_name or "rate limit" in exc_msg or "429" in exc_msg:
        return ErrorType.RATE_LIMIT

    # Parse errors
    if any(x in exc_type_name for x in ["parse", "decode", "encoding", "unicode"]):
        return ErrorType.PARSE_ERROR

    # Permission errors
    if "permission" in exc_type_name or "access denied" in exc_msg or "403" in exc_msg:
        return ErrorType.PERMISSION_ERROR

    # Duplicate/idempotency errors
    if "duplicate" in exc_type_name or "already exists" in exc_msg:
        return ErrorType.DUPLICATE

    # Validation errors
    if "validation" in exc_type_name or "invalid" in exc_msg or "value error" in exc_type_name:
        return ErrorType.VALIDATION_ERROR

    # API errors (OpenAI, AWS, etc.)
    if any(api in exc_type_name for api in ["openai", "api", "client"]):
        return ErrorType.API_ERROR
    if any(api in exc_msg for api in ["openai", "anthropic", "api key"]):
        return ErrorType.API_ERROR

    # Storage errors
    if any(store in exc_type_name for store in ["dynamo", "qdrant", "s3", "storage"]):
        return ErrorType.STORAGE_ERROR
    if any(store in exc_msg for store in ["dynamodb", "qdrant", "s3"]):
        return ErrorType.STORAGE_ERROR

    return ErrorType.UNKNOWN


# Export all public classes and functions
__all__ = [
    "ProcessingStage",
    "ErrorType",
    "StageMetrics",
    "JobContext",
    "StageTracker",
    "JobTracker",
    "log_job_event",
    "classify_exception",
]
