"""
Cost Control & Rate Limiting Module for AI Worker (Issue #84)

Provides:
- File type/size validation
- API call limits per case/tenant
- Token usage tracking
- Cost estimation and limits
- Rate limiting for external APIs

Usage:
    from src.utils.cost_guard import CostGuard, FileLimits, CostLimitExceeded

    guard = CostGuard()

    # Validate file before processing
    guard.validate_file(file_path, file_type="image")

    # Check rate limits
    guard.check_rate_limit(case_id, "openai")

    # Record usage
    guard.record_usage(case_id, tokens_used=1500, model="gpt-4o")
"""

import os
import logging
from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    """Supported file types"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"
    TEXT = "text"


@dataclass
class FileLimits:
    """File size and processing limits by type"""
    max_size_mb: float
    max_duration_sec: Optional[int] = None  # For audio/video
    max_pages: Optional[int] = None  # For PDF
    chunk_size_mb: Optional[float] = None  # For chunked processing


# Default file limits from Issue #84 spec
FILE_LIMITS: Dict[FileType, FileLimits] = {
    FileType.IMAGE: FileLimits(max_size_mb=10.0),
    FileType.AUDIO: FileLimits(max_size_mb=100.0, max_duration_sec=1800, chunk_size_mb=25.0),
    FileType.VIDEO: FileLimits(max_size_mb=500.0, max_duration_sec=3600, chunk_size_mb=50.0),
    FileType.PDF: FileLimits(max_size_mb=50.0, max_pages=100),
    FileType.TEXT: FileLimits(max_size_mb=10.0),
}


# Cost estimates per model (USD per 1K tokens)
MODEL_COSTS = {
    # OpenAI
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
    "whisper-1": {"input": 0.006, "output": 0.0},  # Per minute
}


class CostLimitExceeded(Exception):
    """Raised when cost or rate limit is exceeded"""

    def __init__(
        self,
        message: str,
        limit_type: str,
        current_value: float,
        limit_value: float,
        case_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ):
        super().__init__(message)
        self.limit_type = limit_type
        self.current_value = current_value
        self.limit_value = limit_value
        self.case_id = case_id
        self.tenant_id = tenant_id


class FileSizeExceeded(Exception):
    """Raised when file size exceeds limit"""

    def __init__(
        self,
        message: str,
        file_type: str,
        file_size_mb: float,
        max_size_mb: float
    ):
        super().__init__(message)
        self.file_type = file_type
        self.file_size_mb = file_size_mb
        self.max_size_mb = max_size_mb


@dataclass
class UsageRecord:
    """Record of API usage"""
    timestamp: datetime
    case_id: str
    tenant_id: Optional[str]
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    operation: str  # e.g., "embedding", "summarize", "transcribe"


@dataclass
class CostLimits:
    """Cost and rate limits configuration"""
    # Per-case limits
    max_daily_tokens_per_case: int = 100_000
    max_daily_api_calls_per_case: int = 100
    max_monthly_cost_per_case_usd: float = 50.0

    # Per-tenant limits
    max_monthly_cost_per_tenant_usd: float = 500.0
    max_daily_tokens_per_tenant: int = 1_000_000

    # Global rate limits
    max_concurrent_jobs: int = 10
    min_delay_between_api_calls_ms: int = 100


class CostGuard:
    """
    Cost control and rate limiting for AI Worker.

    Tracks usage, enforces limits, and prevents cost overruns.
    """

    def __init__(
        self,
        limits: Optional[CostLimits] = None,
        usage_store: Optional[Any] = None  # DynamoDB or in-memory
    ):
        self.limits = limits or CostLimits()
        self._usage_store = usage_store  # Future: DynamoDB table for usage tracking
        self._usage_cache: Dict[str, Dict[str, Any]] = {}  # In-memory cache

    def validate_file(
        self,
        file_path: str,
        file_type: str,
        check_duration: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate file against size and processing limits.

        Args:
            file_path: Path to the file
            file_type: Type of file (image, audio, video, pdf, text)
            check_duration: Whether to check audio/video duration

        Returns:
            Tuple of (is_valid, details)

        Raises:
            FileSizeExceeded: If file exceeds size limit
        """
        try:
            file_type_enum = FileType(file_type.lower())
        except ValueError:
            # Unknown file type - allow with default limits
            logger.warning(f"Unknown file type: {file_type}, using TEXT limits")
            file_type_enum = FileType.TEXT

        limits = FILE_LIMITS.get(file_type_enum, FILE_LIMITS[FileType.TEXT])

        # Check file size
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)

        details = {
            "file_path": file_path,
            "file_type": file_type,
            "file_size_mb": round(file_size_mb, 2),
            "max_size_mb": limits.max_size_mb,
            "within_limit": file_size_mb <= limits.max_size_mb,
        }

        if file_size_mb > limits.max_size_mb:
            raise FileSizeExceeded(
                f"File size {file_size_mb:.2f}MB exceeds limit of {limits.max_size_mb}MB for {file_type}",
                file_type=file_type,
                file_size_mb=file_size_mb,
                max_size_mb=limits.max_size_mb
            )

        # Check if chunking is needed
        if limits.chunk_size_mb and file_size_mb > limits.chunk_size_mb:
            details["requires_chunking"] = True
            details["chunk_size_mb"] = limits.chunk_size_mb
            details["estimated_chunks"] = int(file_size_mb / limits.chunk_size_mb) + 1
        else:
            details["requires_chunking"] = False

        return True, details

    def check_rate_limit(
        self,
        case_id: str,
        service: str = "openai",
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if rate limit allows another API call.

        Args:
            case_id: Case identifier
            service: Service name (openai, qdrant, etc.)
            tenant_id: Optional tenant identifier

        Returns:
            True if within limits

        Raises:
            CostLimitExceeded: If rate limit exceeded
        """
        cache_key = f"{case_id}:{service}"
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()

        # Get or initialize usage cache
        if cache_key not in self._usage_cache:
            self._usage_cache[cache_key] = {
                "date": today,
                "api_calls": 0,
                "tokens": 0,
                "cost_usd": 0.0,
            }

        usage = self._usage_cache[cache_key]

        # Reset if new day
        if usage["date"] != today:
            usage["date"] = today
            usage["api_calls"] = 0
            usage["tokens"] = 0
            usage["cost_usd"] = 0.0

        # Check daily API call limit
        if usage["api_calls"] >= self.limits.max_daily_api_calls_per_case:
            raise CostLimitExceeded(
                f"Daily API call limit ({self.limits.max_daily_api_calls_per_case}) reached for case {case_id}",
                limit_type="daily_api_calls",
                current_value=usage["api_calls"],
                limit_value=self.limits.max_daily_api_calls_per_case,
                case_id=case_id
            )

        # Check daily token limit
        if usage["tokens"] >= self.limits.max_daily_tokens_per_case:
            raise CostLimitExceeded(
                f"Daily token limit ({self.limits.max_daily_tokens_per_case}) reached for case {case_id}",
                limit_type="daily_tokens",
                current_value=usage["tokens"],
                limit_value=self.limits.max_daily_tokens_per_case,
                case_id=case_id
            )

        return True

    def record_usage(
        self,
        case_id: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        operation: str = "unknown",
        tenant_id: Optional[str] = None,
        duration_sec: Optional[float] = None  # For audio transcription
    ) -> UsageRecord:
        """
        Record API usage for tracking and billing.

        Args:
            case_id: Case identifier
            model: Model name (gpt-4o, whisper-1, etc.)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            operation: Type of operation
            tenant_id: Optional tenant identifier
            duration_sec: Audio duration for whisper (charged per minute)

        Returns:
            UsageRecord with cost estimate
        """
        now = datetime.now(timezone.utc)

        # Calculate cost
        cost_usd = self._estimate_cost(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_sec=duration_sec
        )

        record = UsageRecord(
            timestamp=now,
            case_id=case_id,
            tenant_id=tenant_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            operation=operation
        )

        # Update cache
        cache_key = f"{case_id}:openai"
        if cache_key not in self._usage_cache:
            self._usage_cache[cache_key] = {
                "date": now.date().isoformat(),
                "api_calls": 0,
                "tokens": 0,
                "cost_usd": 0.0,
            }

        self._usage_cache[cache_key]["api_calls"] += 1
        self._usage_cache[cache_key]["tokens"] += input_tokens + output_tokens
        self._usage_cache[cache_key]["cost_usd"] += cost_usd

        logger.info(
            f"Usage recorded: {operation} for {case_id}",
            extra={
                "case_id": case_id,
                "model": model,
                "tokens": input_tokens + output_tokens,
                "cost_usd": round(cost_usd, 6),
            }
        )

        return record

    def _estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_sec: Optional[float] = None
    ) -> float:
        """
        Estimate cost in USD for API usage.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_sec: Duration in seconds (for audio models)

        Returns:
            Estimated cost in USD
        """
        if model not in MODEL_COSTS:
            logger.warning(f"Unknown model {model}, using default cost estimate")
            return 0.001 * (input_tokens + output_tokens) / 1000

        costs = MODEL_COSTS[model]

        if model == "whisper-1" and duration_sec:
            # Whisper charges per minute
            minutes = duration_sec / 60
            return costs["input"] * minutes
        else:
            # Token-based pricing
            input_cost = (input_tokens / 1000) * costs["input"]
            output_cost = (output_tokens / 1000) * costs["output"]
            return input_cost + output_cost

    def get_usage_summary(
        self,
        case_id: str,
        period: str = "daily"
    ) -> Dict[str, Any]:
        """
        Get usage summary for a case.

        Args:
            case_id: Case identifier
            period: "daily" or "monthly"

        Returns:
            Usage summary dictionary
        """
        cache_key = f"{case_id}:openai"
        usage = self._usage_cache.get(cache_key, {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "api_calls": 0,
            "tokens": 0,
            "cost_usd": 0.0,
        })

        return {
            "case_id": case_id,
            "period": period,
            "date": usage.get("date"),
            "api_calls": usage.get("api_calls", 0),
            "tokens": usage.get("tokens", 0),
            "cost_usd": round(usage.get("cost_usd", 0.0), 4),
            "limits": {
                "max_daily_api_calls": self.limits.max_daily_api_calls_per_case,
                "max_daily_tokens": self.limits.max_daily_tokens_per_case,
                "max_monthly_cost_usd": self.limits.max_monthly_cost_per_case_usd,
            },
            "usage_percent": {
                "api_calls": round(
                    (usage.get("api_calls", 0) / self.limits.max_daily_api_calls_per_case) * 100, 1
                ),
                "tokens": round(
                    (usage.get("tokens", 0) / self.limits.max_daily_tokens_per_case) * 100, 1
                ),
            }
        }

    def estimate_processing_cost(
        self,
        file_path: str,
        file_type: str,
        operations: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Estimate cost before processing a file.

        Args:
            file_path: Path to file
            file_type: Type of file
            operations: List of operations (default: standard pipeline)

        Returns:
            Cost estimate dictionary
        """
        if operations is None:
            operations = ["parse", "embed", "analyze", "summarize"]

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        # Rough token estimates by file type and size
        estimated_tokens = 0
        cost_breakdown = {}

        if file_type in ["image", "pdf"]:
            # ~1000 tokens per page/image
            pages = max(1, int(file_size_mb / 0.5))
            estimated_tokens = pages * 1000
            cost_breakdown["ocr_tokens"] = pages * 500
            cost_breakdown["analysis_tokens"] = pages * 500

        elif file_type in ["audio", "video"]:
            # Estimate duration based on file size (~1MB per minute)
            estimated_duration_min = file_size_mb
            # Whisper cost
            whisper_cost = estimated_duration_min * MODEL_COSTS["whisper-1"]["input"]
            cost_breakdown["transcription_cost"] = round(whisper_cost, 4)
            # Analysis tokens
            estimated_tokens = int(estimated_duration_min * 150)  # ~150 tokens per minute
            cost_breakdown["analysis_tokens"] = estimated_tokens

        elif file_type == "text":
            # ~4 chars per token
            estimated_tokens = int((file_size_mb * 1024 * 1024) / 4)
            cost_breakdown["text_tokens"] = estimated_tokens

        # Embedding cost
        if "embed" in operations:
            embedding_cost = (estimated_tokens / 1000) * MODEL_COSTS["text-embedding-3-small"]["input"]
            cost_breakdown["embedding_cost"] = round(embedding_cost, 4)

        # Analysis cost (GPT-4o)
        if "analyze" in operations or "summarize" in operations:
            analysis_cost = (estimated_tokens / 1000) * (
                MODEL_COSTS["gpt-4o"]["input"] + MODEL_COSTS["gpt-4o"]["output"] * 0.3
            )
            cost_breakdown["analysis_cost"] = round(analysis_cost, 4)

        total_cost = sum(v for v in cost_breakdown.values() if isinstance(v, (int, float)))

        return {
            "file_path": file_path,
            "file_type": file_type,
            "file_size_mb": round(file_size_mb, 2),
            "estimated_tokens": estimated_tokens,
            "estimated_cost_usd": round(total_cost, 4),
            "cost_breakdown": cost_breakdown,
            "operations": operations,
        }


def get_file_type_from_extension(extension: str) -> str:
    """
    Map file extension to file type.

    Args:
        extension: File extension (with or without dot)

    Returns:
        File type string
    """
    ext = extension.lower().lstrip('.')

    image_exts = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
    audio_exts = {'mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac'}
    video_exts = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    pdf_exts = {'pdf'}
    text_exts = {'txt', 'csv', 'json', 'md'}

    if ext in image_exts:
        return "image"
    elif ext in audio_exts:
        return "audio"
    elif ext in video_exts:
        return "video"
    elif ext in pdf_exts:
        return "pdf"
    elif ext in text_exts:
        return "text"
    else:
        return "text"  # Default to text


# Export all public classes and functions
__all__ = [
    "FileType",
    "FileLimits",
    "FILE_LIMITS",
    "MODEL_COSTS",
    "CostLimitExceeded",
    "FileSizeExceeded",
    "UsageRecord",
    "CostLimits",
    "CostGuard",
    "get_file_type_from_extension",
]
