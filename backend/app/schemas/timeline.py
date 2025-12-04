"""
Timeline Pydantic schemas for API request/response validation

Evidence Timeline feature - 002-evidence-timeline
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field


class TimelineEventType(str, Enum):
    """Evidence type classification for timeline display"""
    MESSAGE = "message"      # KakaoTalk/SMS/Chat
    DOCUMENT = "document"    # PDF/Documents
    IMAGE = "image"          # Images
    AUDIO = "audio"          # Audio recordings
    VIDEO = "video"          # Video recordings
    INCIDENT = "incident"    # AI-extracted events/issues


class TimelineEvent(BaseModel):
    """Single event on the timeline"""
    event_id: str
    evidence_id: str
    case_id: str

    # Time
    timestamp: Optional[datetime] = None  # Event occurrence time (nullable for unknown dates)
    date: str  # YYYY-MM-DD or "날짜 미상"
    time: str  # HH:MM or ""

    # Content
    description: str  # Brief description (max 100 chars)
    content_preview: Optional[str] = None  # Original content preview

    # Classification
    event_type: TimelineEventType
    labels: List[str] = Field(default_factory=list)  # Article 840 labels
    speaker: Optional[str] = None  # 원고/피고/제3자/unknown
    source_file: str  # Original filename

    # Significance
    significance: int = Field(ge=1, le=5, default=1)  # 1-5 scale
    is_key_evidence: bool = False  # High importance flag (significance >= 4)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class TimelineFilter(BaseModel):
    """Filter criteria for timeline queries"""
    date_start: Optional[str] = None  # YYYY-MM-DD
    date_end: Optional[str] = None  # YYYY-MM-DD
    labels: Optional[List[str]] = None  # Filter by Article 840 labels
    speakers: Optional[List[str]] = None  # Filter by speakers
    event_types: Optional[List[TimelineEventType]] = None
    key_only: bool = False  # Show key evidence only

    # Pagination
    limit: int = Field(ge=1, le=100, default=50)  # Max items per page
    offset: int = Field(ge=0, default=0)  # Skip items

    # Sort
    sort_order: Literal["asc", "desc"] = "asc"  # Chronological order


class TimelineResult(BaseModel):
    """API response container for timeline data"""
    case_id: str
    events: List[TimelineEvent]

    # Pagination
    total_count: int  # Total evidence count (before filters)
    filtered_count: int  # Count after filters applied
    has_more: bool  # More pages available

    # Statistics
    date_range: Dict[str, Optional[str]]  # {start, end}
    events_by_type: Dict[str, int]
    events_by_label: Dict[str, int]
    key_events_count: int

    # Meta
    generated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
