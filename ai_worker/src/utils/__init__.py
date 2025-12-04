"""Utility modules for AI Worker."""

from .logging_filter import SensitiveDataFilter
from .hash import (
    calculate_file_hash,
    calculate_s3_object_hash,
    calculate_content_hash,
    get_s3_etag,
    is_duplicate_by_hash
)
from .observability import (
    ProcessingStage,
    ErrorType,
    StageMetrics,
    JobContext,
    StageTracker,
    JobTracker,
    log_job_event,
    classify_exception
)
from .cost_guard import (
    FileType,
    FileLimits,
    FILE_LIMITS,
    MODEL_COSTS,
    CostLimitExceeded,
    FileSizeExceeded,
    UsageRecord,
    CostLimits,
    CostGuard,
    get_file_type_from_extension
)

__all__ = [
    # Logging filter
    'SensitiveDataFilter',
    # Hash utilities
    'calculate_file_hash',
    'calculate_s3_object_hash',
    'calculate_content_hash',
    'get_s3_etag',
    'is_duplicate_by_hash',
    # Observability
    'ProcessingStage',
    'ErrorType',
    'StageMetrics',
    'JobContext',
    'StageTracker',
    'JobTracker',
    'log_job_event',
    'classify_exception',
    # Cost control
    'FileType',
    'FileLimits',
    'FILE_LIMITS',
    'MODEL_COSTS',
    'CostLimitExceeded',
    'FileSizeExceeded',
    'UsageRecord',
    'CostLimits',
    'CostGuard',
    'get_file_type_from_extension'
]
