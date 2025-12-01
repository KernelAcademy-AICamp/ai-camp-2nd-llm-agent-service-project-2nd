"""
Role Management Service - Business logic for RBAC
Per BACKEND_SERVICE_REPOSITORY_GUIDE.md pattern
"""

from typing import List, Dict
from app.db.models import UserRole
from app.db.schemas import RolePermissions, ResourcePermission


class RoleManagementService:
    """
    Service for role and permission management

    Note: This is a stateless service that returns hardcoded permission matrices.
    In a real production system, permissions would be stored in a database table.
    For the MVP, we use predefined permission sets for each role.
    """

    # Hardcoded permission matrix for LEH project
    ROLE_PERMISSIONS: Dict[UserRole, RolePermissions] = {
        UserRole.ADMIN: RolePermissions(
            role=UserRole.ADMIN,
            cases=ResourcePermission(view=True, edit=True, delete=True),
            evidence=ResourcePermission(view=True, edit=True, delete=True),
            admin=ResourcePermission(view=True, edit=True, delete=True),
            billing=ResourcePermission(view=True, edit=True, delete=True)
        ),
        UserRole.LAWYER: RolePermissions(
            role=UserRole.LAWYER,
            cases=ResourcePermission(view=True, edit=True, delete=True),
            evidence=ResourcePermission(view=True, edit=True, delete=True),
            admin=ResourcePermission(view=False, edit=False, delete=False),
            billing=ResourcePermission(view=True, edit=False, delete=False)
        ),
        UserRole.STAFF: RolePermissions(
            role=UserRole.STAFF,
            cases=ResourcePermission(view=True, edit=False, delete=False),
            evidence=ResourcePermission(view=True, edit=False, delete=False),
            admin=ResourcePermission(view=False, edit=False, delete=False),
            billing=ResourcePermission(view=False, edit=False, delete=False)
        )
    }

    def get_all_roles(self) -> List[RolePermissions]:
        """
        Get permission matrix for all roles

        Returns:
            List of RolePermissions for ADMIN, LAWYER, STAFF
        """
        return [
            self.ROLE_PERMISSIONS[UserRole.ADMIN],
            self.ROLE_PERMISSIONS[UserRole.LAWYER],
            self.ROLE_PERMISSIONS[UserRole.STAFF]
        ]

    def get_role_permissions(self, role: UserRole) -> RolePermissions:
        """
        Get permissions for a specific role

        Args:
            role: User role (ADMIN, LAWYER, STAFF)

        Returns:
            RolePermissions for the role
        """
        return self.ROLE_PERMISSIONS[role]

    def update_role_permissions(
        self,
        role: UserRole,
        cases: ResourcePermission,
        evidence: ResourcePermission,
        admin: ResourcePermission,
        billing: ResourcePermission
    ) -> RolePermissions:
        """
        Update permissions for a role (in-memory only for MVP)

        Note: In production, this would update a database table.
        For MVP, we just update the in-memory dict.

        Args:
            role: Role to update
            cases: Cases resource permissions
            evidence: Evidence resource permissions
            admin: Admin resource permissions
            billing: Billing resource permissions

        Returns:
            Updated RolePermissions
        """
        updated_permissions = RolePermissions(
            role=role,
            cases=cases,
            evidence=evidence,
            admin=admin,
            billing=billing
        )

        # Update in-memory dict
        self.ROLE_PERMISSIONS[role] = updated_permissions

        return updated_permissions
