"""
Timeline Service - Business logic for Evidence Timeline feature

Feature: 002-evidence-timeline
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from collections import Counter

from sqlalchemy.orm import Session

from app.schemas.timeline import (
    TimelineEvent,
    TimelineEventType,
    TimelineFilter,
    TimelineResult,
)
from app.repositories.case_repository import CaseRepository
from app.repositories.case_member_repository import CaseMemberRepository
from app.utils.dynamo import get_evidence_by_case
from app.middleware import NotFoundError, PermissionError
from app.services.audit_log_service import AuditLogService
from app.db.schemas import AuditAction

logger = logging.getLogger(__name__)

# ============================================
# Significance Calculation Constants (T006)
# ============================================

# Article 840 label weights for significance calculation
SIGNIFICANCE_WEIGHTS: Dict[str, int] = {
    # Severity 5 (Critical)
    "부정행위": 5,
    "폭행": 5,
    "학대": 5,

    # Severity 4 (High)
    "유기": 4,
    "협박": 4,
    "위협": 4,
    "악의의유기": 4,

    # Severity 3 (Medium)
    "폭언": 3,
    "계속적_불화": 3,
    "혼인_파탄": 3,

    # Severity 2 (Low)
    "재산_문제": 2,
    "양육_문제": 2,
}

# Key evidence threshold (significance >= 4)
KEY_EVIDENCE_THRESHOLD = 4

# Labels that automatically mark evidence as key
KEY_EVIDENCE_LABELS = {"부정행위", "폭행", "학대", "유기", "협박", "위협", "악의의유기"}

# Evidence type mapping from DynamoDB type field
TYPE_MAPPING: Dict[str, TimelineEventType] = {
    "text": TimelineEventType.MESSAGE,
    "image": TimelineEventType.IMAGE,
    "audio": TimelineEventType.AUDIO,
    "video": TimelineEventType.VIDEO,
    "pdf": TimelineEventType.DOCUMENT,
    "document": TimelineEventType.DOCUMENT,
}


class TimelineService:
    """
    Service for timeline operations

    Provides methods to retrieve and filter evidence timeline for a case.
    """

    def __init__(self, db: Session):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.member_repo = CaseMemberRepository(db)
        self.audit_service = AuditLogService(db)

    def get_timeline(
        self,
        case_id: str,
        user_id: str,
        filter: Optional[TimelineFilter] = None
    ) -> TimelineResult:
        """
        Get evidence timeline for a case with optional filtering

        Args:
            case_id: Case ID
            user_id: Current user ID (for access control)
            filter: Optional filter criteria

        Returns:
            TimelineResult with events and statistics

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access to case
        """
        # Validate case exists
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")

        # Validate user access
        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

        # Get evidence from DynamoDB
        evidence_list = get_evidence_by_case(case_id)

        # Convert to timeline events
        all_events = self._build_events(evidence_list, case_id)

        # Apply filters
        filter = filter or TimelineFilter()
        filtered_events = self._apply_filters(all_events, filter)

        # Log audit entry
        self._log_timeline_view(case_id, user_id, filter, len(filtered_events))

        # Build and return result
        return self._build_result(case_id, all_events, filtered_events, filter)

    def _build_events(
        self,
        evidence_list: List[Dict[str, Any]],
        case_id: str
    ) -> List[TimelineEvent]:
        """
        Convert DynamoDB evidence records to TimelineEvent objects

        Args:
            evidence_list: Raw evidence data from DynamoDB
            case_id: Case ID

        Returns:
            List of TimelineEvent objects
        """
        events = []

        for evidence in evidence_list:
            try:
                event = self._evidence_to_event(evidence, case_id)
                events.append(event)
            except Exception as e:
                logger.warning(
                    f"Failed to convert evidence {evidence.get('evidence_id')}: {e}"
                )
                continue

        return events

    def _evidence_to_event(
        self,
        evidence: Dict[str, Any],
        case_id: str
    ) -> TimelineEvent:
        """
        Convert a single evidence record to TimelineEvent

        Args:
            evidence: Evidence data from DynamoDB
            case_id: Case ID

        Returns:
            TimelineEvent object
        """
        evidence_id = evidence.get("evidence_id") or evidence.get("id", "")

        # Parse timestamp
        timestamp_str = evidence.get("timestamp") or evidence.get("created_at")
        timestamp = None
        date_str = "날짜 미상"
        time_str = ""

        if timestamp_str:
            try:
                if isinstance(timestamp_str, str):
                    # Handle ISO format timestamps
                    timestamp = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                elif isinstance(timestamp_str, datetime):
                    timestamp = timestamp_str

                if timestamp:
                    date_str = timestamp.strftime("%Y-%m-%d")
                    time_str = timestamp.strftime("%H:%M")
            except (ValueError, AttributeError) as e:
                logger.debug(f"Failed to parse timestamp {timestamp_str}: {e}")

        # Get labels
        labels = evidence.get("labels", []) or []
        if not labels:
            # Try to extract from article_840_tags
            tags = evidence.get("article_840_tags", {})
            if isinstance(tags, dict):
                labels = tags.get("categories", []) or []

        # Calculate significance
        significance = self._calculate_significance(labels)
        is_key_evidence = significance >= KEY_EVIDENCE_THRESHOLD

        # Map evidence type
        raw_type = evidence.get("type", "document")
        event_type = TYPE_MAPPING.get(raw_type, TimelineEventType.DOCUMENT)

        # Build description
        description = evidence.get("ai_summary") or evidence.get("summary") or ""
        if not description:
            description = evidence.get("filename", "증거 자료")
        # Truncate to 100 chars
        if len(description) > 100:
            description = description[:97] + "..."

        # Content preview
        content_preview = evidence.get("content")
        if content_preview and len(content_preview) > 200:
            content_preview = content_preview[:197] + "..."

        return TimelineEvent(
            event_id=f"evt_{evidence_id}",
            evidence_id=evidence_id,
            case_id=case_id,
            timestamp=timestamp,
            date=date_str,
            time=time_str,
            description=description,
            content_preview=content_preview,
            event_type=event_type,
            labels=labels if isinstance(labels, list) else [],
            speaker=evidence.get("speaker"),
            source_file=evidence.get("filename", ""),
            significance=significance,
            is_key_evidence=is_key_evidence,
            metadata={
                "s3_key": evidence.get("s3_key"),
                "status": evidence.get("status"),
                "qdrant_id": evidence.get("qdrant_id"),
            }
        )

    def _calculate_significance(self, labels: List[str]) -> int:
        """
        Calculate significance score from Article 840 labels

        Args:
            labels: List of evidence labels

        Returns:
            Significance score (1-5)
        """
        if not labels:
            return 1

        max_weight = 1
        for label in labels:
            weight = SIGNIFICANCE_WEIGHTS.get(label, 1)
            max_weight = max(max_weight, weight)

        return min(max_weight, 5)

    def _apply_filters(
        self,
        events: List[TimelineEvent],
        filter: TimelineFilter
    ) -> List[TimelineEvent]:
        """
        Apply filter criteria to events

        Args:
            events: List of timeline events
            filter: Filter criteria

        Returns:
            Filtered list of events
        """
        filtered = events

        # Date range filter
        if filter.date_start:
            filtered = [
                e for e in filtered
                if e.date != "날짜 미상" and e.date >= filter.date_start
            ]

        if filter.date_end:
            filtered = [
                e for e in filtered
                if e.date != "날짜 미상" and e.date <= filter.date_end
            ]

        # Label filter
        if filter.labels:
            label_set = set(filter.labels)
            filtered = [
                e for e in filtered
                if any(label in label_set for label in e.labels)
            ]

        # Speaker filter
        if filter.speakers:
            speaker_set = set(filter.speakers)
            filtered = [
                e for e in filtered
                if e.speaker in speaker_set
            ]

        # Event type filter
        if filter.event_types:
            type_set = set(filter.event_types)
            filtered = [
                e for e in filtered
                if e.event_type in type_set
            ]

        # Key evidence only filter
        if filter.key_only:
            filtered = [e for e in filtered if e.is_key_evidence]

        # Sort by timestamp
        # Events with unknown dates go to the end
        def sort_key(event: TimelineEvent):
            if event.date == "날짜 미상":
                # Put at end with secondary sort by event_id for stability
                return ("9999-99-99", event.event_id)
            return (event.date, event.time or "00:00", event.event_id)

        reverse = filter.sort_order == "desc"
        filtered = sorted(filtered, key=sort_key, reverse=reverse)

        return filtered

    def _build_result(
        self,
        case_id: str,
        all_events: List[TimelineEvent],
        filtered_events: List[TimelineEvent],
        filter: TimelineFilter
    ) -> TimelineResult:
        """
        Build timeline result with statistics

        Args:
            case_id: Case ID
            all_events: All events (before filtering)
            filtered_events: Events after filtering
            filter: Applied filter

        Returns:
            TimelineResult object
        """
        # Apply pagination
        offset = filter.offset
        limit = filter.limit
        paginated = filtered_events[offset:offset + limit]
        has_more = len(filtered_events) > offset + limit

        # Calculate date range (from all events with valid dates)
        valid_dates = [
            e.date for e in all_events
            if e.date != "날짜 미상"
        ]
        date_range = {
            "start": min(valid_dates) if valid_dates else None,
            "end": max(valid_dates) if valid_dates else None,
        }

        # Count events by type
        events_by_type = Counter(e.event_type.value for e in all_events)

        # Count events by label
        label_counter: Counter = Counter()
        for event in all_events:
            for label in event.labels:
                label_counter[label] += 1

        # Count key events
        key_events_count = sum(1 for e in all_events if e.is_key_evidence)

        return TimelineResult(
            case_id=case_id,
            events=paginated,
            total_count=len(all_events),
            filtered_count=len(filtered_events),
            has_more=has_more,
            date_range=date_range,
            events_by_type=dict(events_by_type),
            events_by_label=dict(label_counter),
            key_events_count=key_events_count,
            generated_at=datetime.now(timezone.utc),
        )

    def _log_timeline_view(
        self,
        case_id: str,
        user_id: str,
        filter: TimelineFilter,
        events_returned: int
    ) -> None:
        """
        Log timeline view to audit log

        Args:
            case_id: Case ID
            user_id: User ID
            filter: Applied filter
            events_returned: Number of events returned
        """
        try:
            # Create custom action for timeline view
            # Using VIEW_CASE as closest existing action type
            self.audit_service.create_log(
                user_id=user_id,
                action=AuditAction.VIEW_CASE,  # Using VIEW_CASE for timeline view
                object_id=case_id,
            )
        except Exception as e:
            # Don't fail the request if audit logging fails
            logger.warning(f"Failed to log timeline view: {e}")
