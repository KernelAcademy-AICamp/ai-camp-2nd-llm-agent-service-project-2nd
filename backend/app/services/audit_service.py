"""
Audit Service
Task T148 - US8 Implementation

Service for audit logging operations.
"""

import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import AuditLog


class AuditService:
    """Service for audit logging operations"""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        user_id: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            user_id: ID of the user performing the action
            action: Action being performed
            resource_type: Type of resource (e.g., 'invoice', 'case')
            resource_id: ID of the resource
            details: Additional details as dictionary

        Returns:
            Created AuditLog entry
        """
        # Combine resource_type, resource_id, and details into object_id
        object_info = {}
        if resource_type:
            object_info["type"] = resource_type
        if resource_id:
            object_info["id"] = resource_id
        if details:
            object_info["details"] = details

        object_id = json.dumps(object_info) if object_info else None

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            object_id=object_id,
        )

        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)

        return audit_log
