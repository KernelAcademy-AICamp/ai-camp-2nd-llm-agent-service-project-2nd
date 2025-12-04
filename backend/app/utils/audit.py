"""
Audit logging utility
Provides helper functions to log audit events to the database
"""

from sqlalchemy.orm import Session
from typing import Optional
from app.db.models import AuditLog
from app.db.schemas import AuditAction


def log_audit_event(
    db: Session,
    user_id: str,
    action: AuditAction,
    object_id: Optional[str] = None
) -> AuditLog:
    """
    Log an audit event to the database

    Args:
        db: Database session
        user_id: ID of user performing the action
        action: Type of action being performed
        object_id: Optional ID of the object being acted upon (case_id, evidence_id, etc.)

    Returns:
        Created AuditLog instance
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action.value,
        object_id=object_id
    )

    db.add(audit_log)
    db.flush()

    return audit_log
