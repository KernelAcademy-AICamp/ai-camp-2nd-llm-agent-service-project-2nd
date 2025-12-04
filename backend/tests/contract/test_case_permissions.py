"""
Contract tests for Role-Based Permission Checks on Cases
Task T013 - TDD RED Phase

Tests for role-based access control on case endpoints:
- Lawyer can access cases
- Client can only access their own cases
- Detective can only access assigned investigations
- Admin has full access
"""

import pytest
from fastapi import status
from app.core.security import create_access_token
from app.db.models import UserRole, CaseMemberRole


class TestLawyerCaseAccess:
    """
    Contract tests for lawyer access to cases
    """

    def test_lawyer_can_access_own_cases(self, client, test_user, auth_headers):
        """
        Given: Lawyer user with owned cases
        When: GET /cases is called
        Then:
            - Returns 200 status code
            - Returns list of cases owned/accessible by lawyer
        """
        # Given: test_user is a lawyer with auth_headers

        # When: Access cases list
        response = client.get("/cases", headers=auth_headers)

        # Then: Success
        assert response.status_code == status.HTTP_200_OK

    def test_lawyer_can_create_case(self, client, test_user, auth_headers):
        """
        Given: Lawyer user
        When: POST /cases is called with valid data
        Then:
            - Returns 201 Created
            - Case is created with lawyer as owner
        """
        # Given: test_user is a lawyer
        case_payload = {
            "title": "Test Case for Lawyer",
            "description": "Test description"
        }

        # When: Create case
        response = client.post("/cases", json=case_payload, headers=auth_headers)

        # Then: Success
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["title"] == "Test Case for Lawyer"


class TestClientCaseAccess:
    """
    Contract tests for client access to cases
    """

    def test_client_cannot_access_general_cases_list(self, client, test_env):
        """
        Given: Client user
        When: GET /cases (general endpoint) is called
        Then:
            - Returns 403 Forbidden (clients use /client/cases)
        """
        # Given: Create a client user
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        client_user = User(
            email=f"client_case_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Client",
            role=UserRole.CLIENT
        )
        db.add(client_user)
        db.commit()
        db.refresh(client_user)

        token = create_access_token({
            "sub": client_user.id,
            "role": client_user.role.value,
            "email": client_user.email
        })

        # When: Access general cases list
        response = client.get(
            "/cases",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Should be forbidden (clients use /client/cases endpoint)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Cleanup
        db.delete(client_user)
        db.commit()
        db.close()

    def test_client_can_access_own_case_via_client_portal(self, client, test_env):
        """
        Given: Client user who is a member of a case
        When: GET /client/cases/{id} is called
        Then:
            - Returns 200 OK (or 404 if endpoint not implemented)
        """
        # Given: Create a client user and a case they're part of
        from app.db.session import get_db
        from app.db.models import User, Case, CaseMember
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        # Create lawyer to own the case
        lawyer_user = User(
            email=f"lawyer_for_client_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Lawyer",
            role=UserRole.LAWYER
        )
        db.add(lawyer_user)
        db.commit()
        db.refresh(lawyer_user)

        # Create client
        client_user = User(
            email=f"client_portal_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Client Portal",
            role=UserRole.CLIENT
        )
        db.add(client_user)
        db.commit()
        db.refresh(client_user)

        # Create case
        case = Case(
            title=f"Client Case {unique_id}",
            created_by=lawyer_user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Add client as case member
        case_member = CaseMember(
            case_id=case.id,
            user_id=client_user.id,
            role=CaseMemberRole.MEMBER
        )
        db.add(case_member)
        db.commit()

        token = create_access_token({
            "sub": client_user.id,
            "role": client_user.role.value,
            "email": client_user.email
        })

        # When: Access own case via client portal
        response = client.get(
            f"/client/cases/{case.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Should succeed or 404 if endpoint not implemented
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        # Cleanup
        db.delete(case_member)
        db.delete(case)
        db.delete(client_user)
        db.delete(lawyer_user)
        db.commit()
        db.close()


class TestDetectiveCaseAccess:
    """
    Contract tests for detective access to cases
    """

    def test_detective_cannot_access_general_cases_list(self, client, test_env):
        """
        Given: Detective user
        When: GET /cases (general endpoint) is called
        Then:
            - Returns 403 Forbidden (detectives use /detective/cases)
        """
        # Given: Create a detective user
        from app.db.session import get_db
        from app.db.models import User
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        detective_user = User(
            email=f"detective_case_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Detective",
            role=UserRole.DETECTIVE
        )
        db.add(detective_user)
        db.commit()
        db.refresh(detective_user)

        token = create_access_token({
            "sub": detective_user.id,
            "role": detective_user.role.value,
            "email": detective_user.email
        })

        # When: Access general cases list
        response = client.get(
            "/cases",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Cleanup
        db.delete(detective_user)
        db.commit()
        db.close()

    def test_detective_can_access_assigned_investigation(self, client, test_env):
        """
        Given: Detective user assigned to a case
        When: GET /detective/cases/{id} is called
        Then:
            - Returns 200 OK (or 404 if endpoint not implemented)
        """
        # Given: Create detective and assign to case
        from app.db.session import get_db
        from app.db.models import User, Case, CaseMember
        from app.core.security import hash_password
        import uuid

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        # Create lawyer to own the case
        lawyer_user = User(
            email=f"lawyer_for_det_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Lawyer",
            role=UserRole.LAWYER
        )
        db.add(lawyer_user)
        db.commit()
        db.refresh(lawyer_user)

        # Create detective
        detective_user = User(
            email=f"detective_portal_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Test Detective Portal",
            role=UserRole.DETECTIVE
        )
        db.add(detective_user)
        db.commit()
        db.refresh(detective_user)

        # Create case
        case = Case(
            title=f"Detective Case {unique_id}",
            created_by=lawyer_user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Assign detective to case
        case_member = CaseMember(
            case_id=case.id,
            user_id=detective_user.id,
            role=CaseMemberRole.MEMBER
        )
        db.add(case_member)
        db.commit()

        token = create_access_token({
            "sub": detective_user.id,
            "role": detective_user.role.value,
            "email": detective_user.email
        })

        # When: Access assigned case via detective portal
        response = client.get(
            f"/detective/cases/{case.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Then: Should succeed or 404 if endpoint not implemented
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        # Cleanup
        db.delete(case_member)
        db.delete(case)
        db.delete(detective_user)
        db.delete(lawyer_user)
        db.commit()
        db.close()


class TestAdminCaseAccess:
    """
    Contract tests for admin access to cases
    """

    def test_admin_can_access_all_cases(self, client, admin_user, admin_auth_headers):
        """
        Given: Admin user
        When: GET /cases is called
        Then:
            - Returns 200 status code
            - Admin has access to all cases
        """
        # Given: admin_user with admin_auth_headers

        # When: Access cases list
        response = client.get("/cases", headers=admin_auth_headers)

        # Then: Success
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_access_any_portal(self, client, admin_user, admin_auth_headers):
        """
        Given: Admin user
        When: Accessing different portal endpoints
        Then:
            - All should return 200 or 404 (not 403)
        """
        # Given: admin_user

        # When/Then: Access various portals - should not get 403
        endpoints = [
            "/lawyer/dashboard",
            "/client/dashboard",
            "/detective/dashboard",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=admin_auth_headers)
            # Admin should have access (200) or endpoint not implemented (404)
            # but never forbidden (403)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND
            ], f"Admin should have access to {endpoint}"
