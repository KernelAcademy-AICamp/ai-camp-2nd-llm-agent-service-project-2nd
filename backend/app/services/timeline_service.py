"""
Timeline Service - Business logic for evidence timeline
Converts DynamoDB evidence metadata to timeline events

Feature: 002-evidence-timeline
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.schemas.timeline import (
    TimelineEvent,
    TimelineEventType,
    TimelineFilter,
    TimelineResult,
    DateRange,
)
from app.utils.dynamo import get_evidence_by_case
from app.repositories.case_member_repository import CaseMemberRepository
from app.repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger(__name__)

# Article 840 significance weights based on legal importance
# Higher scores indicate more legally significant evidence
SIGNIFICANCE_WEIGHTS: Dict[str, int] = {
    # Critical evidence (weight 5) - Direct grounds for divorce
    "부정행위": 5,
    "폭행": 5,
    "학대": 5,
    "불륜": 5,
    # High significance (weight 4) - Strong supporting evidence
    "유기": 4,
    "협박": 4,
    "위협": 4,
    "악의의유기": 4,
    "가정폭력": 4,
    # Medium significance (weight 3) - Relevant evidence
    "폭언": 3,
    "계속적_불화": 3,
    "혼인_파탄": 3,
    "정서적_학대": 3,
    # Lower significance (weight 2) - Context/supporting
    "재산_문제": 2,
    "양육_문제": 2,
    "경제적_문제": 2,
}

# Threshold for key evidence classification
KEY_EVIDENCE_THRESHOLD = 4


class TimelineService:
    """
    Service for evidence timeline operations
    Converts raw DynamoDB evidence to timeline view format
    """

    def __init__(self, db: Session):
        self.db = db
        self.member_repo = CaseMemberRepository(db)
        self.audit_repo = AuditLogRepository(db)

    def get_timeline(
        self,
        case_id: str,
        user_id: str,
        filter_params: Optional[TimelineFilter] = None
    ) -> TimelineResult:
        """
        Get timeline for a case with optional filtering

        Args:
            case_id: Case ID to get timeline for
            user_id: User ID requesting the timeline
            filter_params: Optional filter criteria

        Returns:
            TimelineResult with events and statistics

        Raises:
            PermissionError: If user doesn't have access to case
        """
        # Validate case access
        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError(f"User {user_id} does not have access to case {case_id}")

        # Get evidence from DynamoDB
        evidence_list = get_evidence_by_case(case_id)

        # Build timeline events
        events = self._build_events(case_id, evidence_list)

        # Apply filters if provided
        if filter_params:
            events = self._apply_filters(events, filter_params)

        # Build result with statistics
        result = self._build_result(case_id, events, len(evidence_list), filter_params)

        # Log audit trail
        self._log_timeline_view(user_id, case_id)

        return result

    def _build_events(
        self,
        case_id: str,
        evidence_list: List[Dict]
    ) -> List[TimelineEvent]:
        """
        Convert DynamoDB evidence records to TimelineEvent objects

        Args:
            case_id: Case ID
            evidence_list: List of evidence metadata from DynamoDB

        Returns:
            List of TimelineEvent objects
        """
        events = []

        for ev in evidence_list:
            # Extract timestamp
            timestamp = self._parse_timestamp(ev.get("timestamp") or ev.get("created_at"))

            # Calculate significance from labels
            labels = ev.get("labels", []) or ev.get("article_840_tags", []) or []
            significance = self._calculate_significance(labels)

            # Determine event type
            event_type = self._map_event_type(ev.get("type", "document"))

            # Build formatted date/time strings
            date_str, time_str = self._format_datetime(timestamp)

            event = TimelineEvent(
                event_id=f"evt_{ev.get('evidence_id', ev.get('id', ''))}",
                evidence_id=ev.get("evidence_id", ev.get("id", "")),
                case_id=case_id,
                timestamp=timestamp,
                date=date_str,
                time=time_str,
                description=ev.get("ai_summary", ev.get("description", "증거 자료")),
                content_preview=ev.get("content_preview", ev.get("text_preview")),
                event_type=event_type,
                labels=labels,
                speaker=ev.get("speaker"),
                source_file=ev.get("original_filename", ev.get("s3_key", "").split("/")[-1]),
                significance=significance,
                is_key_evidence=significance >= KEY_EVIDENCE_THRESHOLD,
                metadata=ev.get("metadata"),
            )
            events.append(event)

        # Sort by timestamp (ascending by default)
        events.sort(key=lambda e: e.timestamp or datetime.min.replace(tzinfo=timezone.utc))

        return events

    def _calculate_significance(self, labels: List[str]) -> int:
        """
        Calculate significance score from Article 840 labels

        Args:
            labels: List of Article 840 labels

        Returns:
            Significance score from 1-5
        """
        if not labels:
            return 1

        max_weight = 1
        for label in labels:
            # Normalize label for matching
            normalized = label.replace(" ", "_").lower()
            for key, weight in SIGNIFICANCE_WEIGHTS.items():
                if key.lower() in normalized or normalized in key.lower():
                    max_weight = max(max_weight, weight)

        return min(max_weight, 5)

    def _apply_filters(
        self,
        events: List[TimelineEvent],
        filter_params: TimelineFilter
    ) -> List[TimelineEvent]:
        """
        Apply filter criteria to events

        Args:
            events: List of timeline events
            filter_params: Filter criteria

        Returns:
            Filtered list of events
        """
        filtered = events

        # Date range filter
        if filter_params.date_start:
            start_date = datetime.fromisoformat(filter_params.date_start.replace("Z", "+00:00"))
            filtered = [e for e in filtered if e.timestamp and e.timestamp >= start_date]

        if filter_params.date_end:
            end_date = datetime.fromisoformat(filter_params.date_end.replace("Z", "+00:00"))
            filtered = [e for e in filtered if e.timestamp and e.timestamp <= end_date]

        # Labels filter (OR logic - match any)
        if filter_params.labels:
            filtered = [
                e for e in filtered
                if any(label in e.labels for label in filter_params.labels)
            ]

        # Speakers filter (OR logic)
        if filter_params.speakers:
            filtered = [
                e for e in filtered
                if e.speaker and e.speaker in filter_params.speakers
            ]

        # Event types filter (OR logic)
        if filter_params.event_types:
            type_values = [t.value if hasattr(t, "value") else t for t in filter_params.event_types]
            filtered = [
                e for e in filtered
                if e.event_type.value in type_values
            ]

        # Key evidence only filter
        if filter_params.key_only:
            filtered = [e for e in filtered if e.is_key_evidence]

        # Sort order
        if filter_params.sort_order == "desc":
            filtered = sorted(
                filtered,
                key=lambda e: e.timestamp or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )

        return filtered

    def _build_result(
        self,
        case_id: str,
        events: List[TimelineEvent],
        total_count: int,
        filter_params: Optional[TimelineFilter] = None
    ) -> TimelineResult:
        """
        Build timeline result with statistics and pagination

        Args:
            case_id: Case ID
            events: Filtered events
            total_count: Total evidence count (before filtering)
            filter_params: Filter parameters for pagination

        Returns:
            TimelineResult with events and statistics
        """
        # Apply pagination
        offset = filter_params.offset if filter_params else 0
        limit = filter_params.limit if filter_params else 50

        paginated_events = events[offset:offset + limit]
        has_more = len(events) > offset + limit

        # Calculate statistics
        events_by_type: Dict[str, int] = {}
        events_by_label: Dict[str, int] = {}
        key_events_count = 0

        for event in events:
            # Count by type
            type_key = event.event_type.value
            events_by_type[type_key] = events_by_type.get(type_key, 0) + 1

            # Count by label
            for label in event.labels:
                events_by_label[label] = events_by_label.get(label, 0) + 1

            # Count key evidence
            if event.is_key_evidence:
                key_events_count += 1

        # Calculate date range
        date_range = DateRange()
        if events:
            timestamps = [e.timestamp for e in events if e.timestamp]
            if timestamps:
                date_range.start = min(timestamps).date().isoformat()
                date_range.end = max(timestamps).date().isoformat()

        return TimelineResult(
            case_id=case_id,
            events=paginated_events,
            total_count=total_count,
            filtered_count=len(events),
            has_more=has_more,
            date_range=date_range,
            events_by_type=events_by_type,
            events_by_label=events_by_label,
            key_events_count=key_events_count,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _parse_timestamp(self, value) -> Optional[datetime]:
        """Parse timestamp from various formats"""
        if not value:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                return None
        return None

    def _format_datetime(self, dt: Optional[datetime]) -> tuple:
        """Format datetime to date and time strings"""
        if not dt:
            return "날짜 미상", ""
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")

    def _map_event_type(self, evidence_type: str) -> TimelineEventType:
        """Map evidence type to TimelineEventType"""
        type_mapping = {
            "image": TimelineEventType.IMAGE,
            "audio": TimelineEventType.AUDIO,
            "video": TimelineEventType.VIDEO,
            "text": TimelineEventType.MESSAGE,
            "pdf": TimelineEventType.DOCUMENT,
            "document": TimelineEventType.DOCUMENT,
            "message": TimelineEventType.MESSAGE,
            "incident": TimelineEventType.INCIDENT,
        }
        return type_mapping.get(evidence_type.lower(), TimelineEventType.DOCUMENT)

    def _log_timeline_view(self, user_id: str, case_id: str) -> None:
        """Log timeline view action to audit log"""
        try:
            self.audit_repo.create(
                user_id=user_id,
                action="VIEW_TIMELINE",
                object_id=case_id
            )
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to log timeline view audit: {e}")
            self.db.rollback()
