"""
Unit tests for Role Management Service
TDD - Improving test coverage for role_management_service.py
"""

import pytest
from app.services.role_management_service import RoleManagementService
from app.db.models import UserRole
from app.db.schemas import RolePermissions, ResourcePermission


class TestGetAllRoles:
    """Unit tests for get_all_roles method"""

    def test_get_all_roles_returns_three_roles(self):
        """Returns all 3 role permission sets"""
        service = RoleManagementService()
        result = service.get_all_roles()

        assert len(result) == 3
        roles = [r.role for r in result]
        assert UserRole.ADMIN in roles
        assert UserRole.LAWYER in roles
        assert UserRole.STAFF in roles

    def test_get_all_roles_returns_role_permissions(self):
        """All results are RolePermissions objects"""
        service = RoleManagementService()
        result = service.get_all_roles()

        for permissions in result:
            assert isinstance(permissions, RolePermissions)
            assert hasattr(permissions, 'cases')
            assert hasattr(permissions, 'evidence')
            assert hasattr(permissions, 'admin')
            assert hasattr(permissions, 'billing')


class TestGetRolePermissions:
    """Unit tests for get_role_permissions method"""

    def test_get_admin_permissions(self):
        """Admin has full permissions"""
        service = RoleManagementService()
        result = service.get_role_permissions(UserRole.ADMIN)

        assert result.role == UserRole.ADMIN
        assert result.cases.view is True
        assert result.cases.edit is True
        assert result.cases.delete is True
        assert result.admin.view is True
        assert result.admin.edit is True

    def test_get_lawyer_permissions(self):
        """Lawyer has case permissions but no admin"""
        service = RoleManagementService()
        result = service.get_role_permissions(UserRole.LAWYER)

        assert result.role == UserRole.LAWYER
        assert result.cases.view is True
        assert result.cases.edit is True
        assert result.admin.view is False
        assert result.admin.edit is False

    def test_get_staff_permissions(self):
        """Staff has view-only permissions"""
        service = RoleManagementService()
        result = service.get_role_permissions(UserRole.STAFF)

        assert result.role == UserRole.STAFF
        assert result.cases.view is True
        assert result.cases.edit is False
        assert result.evidence.edit is False


class TestUpdateRolePermissions:
    """Unit tests for update_role_permissions method"""

    def test_update_role_permissions_success(self):
        """Successfully update role permissions"""
        service = RoleManagementService()

        new_cases = ResourcePermission(view=True, edit=False, delete=False)
        new_evidence = ResourcePermission(view=True, edit=True, delete=False)
        new_admin = ResourcePermission(view=False, edit=False, delete=False)
        new_billing = ResourcePermission(view=True, edit=False, delete=False)

        result = service.update_role_permissions(
            role=UserRole.STAFF,
            cases=new_cases,
            evidence=new_evidence,
            admin=new_admin,
            billing=new_billing
        )

        assert result.role == UserRole.STAFF
        assert result.evidence.edit is True  # Updated
        assert result.billing.view is True  # Updated

    def test_update_role_permissions_persists(self):
        """Updated permissions are retrievable"""
        service = RoleManagementService()

        new_cases = ResourcePermission(view=True, edit=True, delete=True)
        new_evidence = ResourcePermission(view=True, edit=True, delete=True)
        new_admin = ResourcePermission(view=True, edit=False, delete=False)
        new_billing = ResourcePermission(view=True, edit=True, delete=False)

        service.update_role_permissions(
            role=UserRole.LAWYER,
            cases=new_cases,
            evidence=new_evidence,
            admin=new_admin,
            billing=new_billing
        )

        # Verify via get_role_permissions
        result = service.get_role_permissions(UserRole.LAWYER)
        assert result.admin.view is True  # Was False, now True
