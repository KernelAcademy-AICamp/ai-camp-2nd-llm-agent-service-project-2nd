"""
AuditLog Repository - Data access layer for AuditLog model
Handles audit log storage and retrieval
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List, Tuple
from datetime import datetime
from app.db.models import AuditLog, User
from app.db.schemas import AuditAction


class AuditLogRepository:
    """
    Repository for AuditLog database operations
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        user_id: str,
        action: str,
        object_id: Optional[str] = None
    ) -> AuditLog:
        """
        Create a new audit log entry

        Args:
            user_id: User ID performing the action
            action: Action type (e.g., "VIEW_EVIDENCE", "CREATE_CASE")
            object_id: ID of the object being acted upon (optional)

        Returns:
            Created AuditLog instance
        """
        log = AuditLog(
            user_id=user_id,
            action=action,
            object_id=object_id
        )

        self.session.add(log)
        self.session.flush()

        return log

    def get_logs_with_pagination(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        actions: Optional[List[AuditAction]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """
        Get audit logs with filtering and pagination

        Args:
            start_date: Filter logs after this date (optional)
            end_date: Filter logs before this date (optional)
            user_id: Filter logs by user ID (optional)
            actions: Filter logs by action types (optional)
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (logs list, total count)
        """
        query = self.session.query(AuditLog).join(User, AuditLog.user_id == User.id)

        # Apply filters
        filters = []

        if start_date:
            filters.append(AuditLog.timestamp >= start_date)

        if end_date:
            filters.append(AuditLog.timestamp <= end_date)

        if user_id:
            filters.append(AuditLog.user_id == user_id)

        if actions:
            # Convert AuditAction enums to strings
            action_strs = [action.value for action in actions]
            filters.append(AuditLog.action.in_(action_strs))

        if filters:
            query = query.filter(and_(*filters))

        # Get total count
        total = query.count()

        # Apply pagination and ordering (newest first)
        logs = (
            query
            .order_by(AuditLog.timestamp.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return logs, total

    def get_logs_for_export(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        actions: Optional[List[AuditAction]] = None
    ) -> List[AuditLog]:
        """
        Get all audit logs for CSV export (no pagination)

        Args:
            start_date: Filter logs after this date (optional)
            end_date: Filter logs before this date (optional)
            user_id: Filter logs by user ID (optional)
            actions: Filter logs by action types (optional)

        Returns:
            List of AuditLog instances
        """
        query = self.session.query(AuditLog).join(User, AuditLog.user_id == User.id)

        # Apply filters (same as get_logs_with_pagination)
        filters = []

        if start_date:
            filters.append(AuditLog.timestamp >= start_date)

        if end_date:
            filters.append(AuditLog.timestamp <= end_date)

        if user_id:
            filters.append(AuditLog.user_id == user_id)

        if actions:
            action_strs = [action.value for action in actions]
            filters.append(AuditLog.action.in_(action_strs))

        if filters:
            query = query.filter(and_(*filters))

        # Return all logs (no pagination) ordered by timestamp
        return query.order_by(AuditLog.timestamp.desc()).all()
