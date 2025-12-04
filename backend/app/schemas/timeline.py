"""
Timeline Schemas
Pydantic models for evidence timeline feature

Feature: 002-evidence-timeline
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TimelineEventType(str, Enum):
    """Evidence type enum for timeline events"""
    MESSAGE = "message"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    INCIDENT = "incident"


class TimelineEvent(BaseModel):
    """Individual timeline event representing a piece of evidence"""
    event_id: str = Field(..., description="Unique event identifier")
    evidence_id: str = Field(..., description="Reference to evidence record")
    case_id: str = Field(..., description="Parent case ID")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")
    date: str = Field(..., description="Formatted date string (YYYY-MM-DD)")
    time: str = Field(..., description="Formatted time string (HH:MM)")
    description: str = Field(..., description="Event description/summary")
    content_preview: Optional[str] = Field(None, description="Preview of content")
    event_type: TimelineEventType = Field(..., description="Type of evidence")
    labels: List[str] = Field(default_factory=list, description="Article 840 labels")
    speaker: Optional[str] = Field(None, description="Speaker/source name")
    source_file: str = Field(..., description="Original file name")
    significance: int = Field(ge=1, le=5, default=1, description="Significance score 1-5")
    is_key_evidence: bool = Field(False, description="Whether this is key evidence")
    metadata: Optional[Dict] = Field(None, description="Additional metadata")

    class Config:
        from_attributes = True


class TimelineFilter(BaseModel):
    """Filter criteria for timeline queries"""
    date_start: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_end: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    labels: Optional[List[str]] = Field(None, description="Filter by labels")
    speakers: Optional[List[str]] = Field(None, description="Filter by speakers")
    event_types: Optional[List[TimelineEventType]] = Field(None, description="Filter by event types")
    key_only: bool = Field(False, description="Show only key evidence")
    limit: int = Field(50, ge=1, le=200, description="Max results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")
    sort_order: str = Field("asc", description="Sort order: asc or desc")


class DateRange(BaseModel):
    """Date range for timeline data"""
    start: Optional[str] = None
    end: Optional[str] = None


class TimelineResult(BaseModel):
    """Timeline query result with events and statistics"""
    case_id: str = Field(..., description="Case ID")
    events: List[TimelineEvent] = Field(default_factory=list, description="Timeline events")
    total_count: int = Field(0, description="Total events count")
    filtered_count: int = Field(0, description="Filtered events count")
    has_more: bool = Field(False, description="Whether more results exist")
    date_range: DateRange = Field(default_factory=DateRange, description="Date range of events")
    events_by_type: Dict[str, int] = Field(default_factory=dict, description="Event count by type")
    events_by_label: Dict[str, int] = Field(default_factory=dict, description="Event count by label")
    key_events_count: int = Field(0, description="Number of key evidence items")
    generated_at: str = Field(..., description="Timestamp when result was generated")

    class Config:
        from_attributes = True
