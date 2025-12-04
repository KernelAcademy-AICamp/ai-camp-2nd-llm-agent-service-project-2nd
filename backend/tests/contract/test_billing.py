"""
Contract tests for Billing API
Task T141 - US8 Tests

Tests for billing/invoice endpoints:
- GET /billing/invoices (list invoices)
- POST /billing/invoices (create invoice)
- GET /billing/invoices/{id} (get invoice detail)
- PUT /billing/invoices/{id} (update invoice)
- DELETE /billing/invoices/{id} (delete invoice)
- POST /client/billing/{id}/pay (client payment)
"""

import pytest
from fastapi import status
from app.core.security import create_access_token
from app.db.models import UserRole


# ============== Invoice List Tests ==============


class TestGetInvoiceList:
    """
    Contract tests for GET /billing/invoices
    """

    def test_should_return_invoice_list_for_lawyer(
        self, client, test_user, auth_headers
    ):
        """
        Given: Authenticated lawyer user
        When: GET /billing/invoices
        Then:
            - Returns 200 status code
            - Response contains invoices array
            - Response contains total count
            - Response contains total_pending amount
            - Response contains total_paid amount
        """
        response = client.get("/billing/invoices", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "invoices" in data
        assert isinstance(data["invoices"], list)
        assert "total" in data
        assert isinstance(data["total"], int)
        assert "total_pending" in data
        assert "total_paid" in data

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: GET /billing/invoices
        Then: Returns 401 Unauthorized
        """
        response = client.get("/billing/invoices")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_user, client_auth_headers):
        """
        Given: User with CLIENT role
        When: GET /billing/invoices (lawyer endpoint)
        Then: Returns 403 Forbidden
        """
        response = client.get("/billing/invoices", headers=client_auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_detective_role(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: User with DETECTIVE role
        When: GET /billing/invoices
        Then: Returns 403 Forbidden
        """
        response = client.get("/billing/invoices", headers=detective_auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_filter_by_status(self, client, test_user, auth_headers):
        """
        Given: Authenticated lawyer
        When: GET /billing/invoices?status=pending
        Then: Returns only pending invoices
        """
        response = client.get(
            "/billing/invoices?status=pending", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # All returned invoices should be pending (if any)
        for invoice in data["invoices"]:
            assert invoice["status"] == "pending"

    def test_should_filter_by_case_id(self, client, test_user, auth_headers):
        """
        Given: Authenticated lawyer
        When: GET /billing/invoices?case_id=xxx
        Then: Returns invoices for that case only
        """
        response = client.get(
            "/billing/invoices?case_id=nonexistent", headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0


# ============== Invoice Create Tests ==============


class TestCreateInvoice:
    """
    Contract tests for POST /billing/invoices
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: POST /billing/invoices
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            "/billing/invoices",
            json={
                "case_id": "case_123",
                "client_id": "client_123",
                "amount": "500000",
                "description": "법률 자문료",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_auth_headers):
        """
        Given: User with CLIENT role
        When: POST /billing/invoices
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/billing/invoices",
            headers=client_auth_headers,
            json={
                "case_id": "case_123",
                "client_id": "client_123",
                "amount": "500000",
                "description": "법률 자문료",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_detective_role(self, client, detective_auth_headers):
        """
        Given: User with DETECTIVE role
        When: POST /billing/invoices
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/billing/invoices",
            headers=detective_auth_headers,
            json={
                "case_id": "case_123",
                "client_id": "client_123",
                "amount": "500000",
                "description": "법률 자문료",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_require_case_id(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: POST /billing/invoices without case_id
        Then: Returns 422 Unprocessable Entity
        """
        response = client.post(
            "/billing/invoices",
            headers=auth_headers,
            json={
                "client_id": "client_123",
                "amount": "500000",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_should_require_amount(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: POST /billing/invoices without amount
        Then: Returns 422 Unprocessable Entity
        """
        response = client.post(
            "/billing/invoices",
            headers=auth_headers,
            json={
                "case_id": "case_123",
                "client_id": "client_123",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_should_create_invoice_with_valid_data(
        self, client, auth_headers, test_case_with_client, client_user
    ):
        """
        Given: Authenticated lawyer with valid case
        When: POST /billing/invoices with valid data
        Then:
            - Returns 201 Created
            - Response contains invoice id
            - Response contains status = pending
        """
        response = client.post(
            "/billing/invoices",
            headers=auth_headers,
            json={
                "case_id": test_case_with_client.id,
                "client_id": client_user.id,
                "amount": "500000",
                "description": "법률 자문료",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert "id" in data
        assert data["id"].startswith("inv_")
        assert data["status"] == "pending"
        assert data["amount"] == "500000"


# ============== Invoice Detail Tests ==============


class TestGetInvoiceDetail:
    """
    Contract tests for GET /billing/invoices/{id}
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: GET /billing/invoices/{id}
        Then: Returns 401 Unauthorized
        """
        response = client.get("/billing/invoices/inv_123")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_return_404_for_nonexistent_invoice(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: GET /billing/invoices/{nonexistent_id}
        Then: Returns 404 Not Found
        """
        response = client.get(
            "/billing/invoices/inv_nonexistent", headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============== Invoice Update Tests ==============


class TestUpdateInvoice:
    """
    Contract tests for PUT /billing/invoices/{id}
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: PUT /billing/invoices/{id}
        Then: Returns 401 Unauthorized
        """
        response = client.put(
            "/billing/invoices/inv_123", json={"amount": "600000"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_auth_headers):
        """
        Given: User with CLIENT role
        When: PUT /billing/invoices/{id}
        Then: Returns 403 Forbidden
        """
        response = client.put(
            "/billing/invoices/inv_123",
            headers=client_auth_headers,
            json={"amount": "600000"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_return_404_for_nonexistent_invoice(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: PUT /billing/invoices/{nonexistent_id}
        Then: Returns 404 Not Found
        """
        response = client.put(
            "/billing/invoices/inv_nonexistent",
            headers=auth_headers,
            json={"amount": "600000"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============== Invoice Delete Tests ==============


class TestDeleteInvoice:
    """
    Contract tests for DELETE /billing/invoices/{id}
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: DELETE /billing/invoices/{id}
        Then: Returns 401 Unauthorized
        """
        response = client.delete("/billing/invoices/inv_123")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_auth_headers):
        """
        Given: User with CLIENT role
        When: DELETE /billing/invoices/{id}
        Then: Returns 403 Forbidden
        """
        response = client.delete(
            "/billing/invoices/inv_123", headers=client_auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_return_404_for_nonexistent_invoice(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: DELETE /billing/invoices/{nonexistent_id}
        Then: Returns 404 Not Found
        """
        response = client.delete(
            "/billing/invoices/inv_nonexistent", headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============== Client Payment Tests ==============


class TestClientPayment:
    """
    Contract tests for POST /client/billing/{id}/pay
    """

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: POST /client/billing/{id}/pay
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            "/client/billing/inv_123/pay",
            json={"payment_method": "card"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: POST /client/billing/{id}/pay
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/client/billing/inv_123/pay",
            headers=auth_headers,
            json={"payment_method": "card"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_detective_role(self, client, detective_auth_headers):
        """
        Given: User with DETECTIVE role
        When: POST /client/billing/{id}/pay
        Then: Returns 403 Forbidden
        """
        response = client.post(
            "/client/billing/inv_123/pay",
            headers=detective_auth_headers,
            json={"payment_method": "card"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_return_404_for_nonexistent_invoice(
        self, client, client_auth_headers
    ):
        """
        Given: Authenticated client
        When: POST /client/billing/{nonexistent_id}/pay
        Then: Returns 404 Not Found
        """
        response = client.post(
            "/client/billing/inv_nonexistent/pay",
            headers=client_auth_headers,
            json={"payment_method": "card"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_should_require_payment_method(self, client, client_auth_headers):
        """
        Given: Authenticated client
        When: POST /client/billing/{id}/pay without payment_method
        Then: Returns 422 Unprocessable Entity
        """
        response = client.post(
            "/client/billing/inv_123/pay",
            headers=client_auth_headers,
            json={},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============== Client Invoice List Tests ==============


class TestClientInvoiceList:
    """
    Contract tests for GET /client/billing
    """

    def test_should_return_invoice_list_for_client(
        self, client, client_user, client_auth_headers
    ):
        """
        Given: Authenticated client user
        When: GET /client/billing
        Then:
            - Returns 200 status code
            - Response contains invoices array
            - Response contains total count
        """
        response = client.get("/client/billing", headers=client_auth_headers)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "invoices" in data
        assert isinstance(data["invoices"], list)
        assert "total" in data
        assert isinstance(data["total"], int)

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: GET /client/billing
        Then: Returns 401 Unauthorized
        """
        response = client.get("/client/billing")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: GET /client/billing
        Then: Returns 403 Forbidden
        """
        response = client.get("/client/billing", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============== Invoice Schema Validation Tests ==============


class TestInvoiceSchemaValidation:
    """
    Contract tests for invoice schema validation
    """

    def test_invoice_out_should_have_required_fields(
        self, client, auth_headers, test_case_with_client, client_user
    ):
        """
        Given: Created invoice
        When: GET invoice detail
        Then: Response has all required fields
        """
        # Create invoice first
        create_response = client.post(
            "/billing/invoices",
            headers=auth_headers,
            json={
                "case_id": test_case_with_client.id,
                "client_id": client_user.id,
                "amount": "500000",
                "description": "테스트 청구서",
            },
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        invoice_id = create_response.json()["id"]

        # Get invoice detail
        response = client.get(
            f"/billing/invoices/{invoice_id}", headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Required fields
        assert "id" in data
        assert "case_id" in data
        assert "client_id" in data
        assert "lawyer_id" in data
        assert "amount" in data
        assert "status" in data
        assert "created_at" in data

        # Optional fields should exist (may be null)
        assert "description" in data
        assert "due_date" in data
        assert "paid_at" in data

    def test_invoice_status_enum_values(
        self, client, auth_headers, test_case_with_client, client_user
    ):
        """
        Given: Created invoice
        Then: Status should be one of valid enum values
        """
        # Create invoice
        create_response = client.post(
            "/billing/invoices",
            headers=auth_headers,
            json={
                "case_id": test_case_with_client.id,
                "client_id": client_user.id,
                "amount": "500000",
            },
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        data = create_response.json()
        valid_statuses = ["pending", "paid", "overdue", "cancelled"]
        assert data["status"] in valid_statuses
