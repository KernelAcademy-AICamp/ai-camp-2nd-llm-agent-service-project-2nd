"""
Contract tests for Detective Earnings API
Task T081 - US5 Tests

Tests for detective earnings endpoint:
- GET /detective/earnings
"""

import pytest
from fastapi import status


# ============== T081: GET /detective/earnings Contract Tests ==============


class TestGetDetectiveEarnings:
    """
    Contract tests for GET /detective/earnings
    """

    def test_should_return_earnings_for_detective(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective user
        When: GET /detective/earnings
        Then:
            - Returns 200 status code
            - Response contains summary object
            - Response contains transactions array
        """
        # When: GET /detective/earnings
        response = client.get("/detective/earnings", headers=detective_auth_headers)

        # Then: Success with earnings data
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify summary object
        assert "summary" in data
        summary = data["summary"]
        assert "total_earned" in summary
        assert "pending_payment" in summary
        assert "this_month" in summary

        # Verify transactions array
        assert "transactions" in data
        assert isinstance(data["transactions"], list)

    def test_should_reject_unauthenticated_request(self, client):
        """
        Given: No authentication token
        When: GET /detective/earnings
        Then: Returns 401 Unauthorized
        """
        response = client.get("/detective/earnings")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_reject_client_role(self, client, client_user, client_auth_headers):
        """
        Given: User with CLIENT role
        When: GET /detective/earnings
        Then: Returns 403 Forbidden
        """
        response = client.get("/detective/earnings", headers=client_auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_should_reject_lawyer_role(self, client, auth_headers):
        """
        Given: User with LAWYER role
        When: GET /detective/earnings
        Then: Returns 403 Forbidden
        """
        response = client.get("/detective/earnings", headers=auth_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestEarningsSummaryStructure:
    """
    Contract tests for earnings summary structure
    """

    def test_summary_should_have_numeric_values(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: GET /detective/earnings
        Then: Summary values are numeric
        """
        response = client.get("/detective/earnings", headers=detective_auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        summary = data["summary"]

        assert isinstance(summary["total_earned"], (int, float))
        assert isinstance(summary["pending_payment"], (int, float))
        assert isinstance(summary["this_month"], (int, float))


class TestEarningsTransactions:
    """
    Contract tests for earnings transactions structure
    """

    def test_transactions_should_have_required_fields(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective with transactions
        When: GET /detective/earnings
        Then: Each transaction has id, amount, status, date
        """
        response = client.get("/detective/earnings", headers=detective_auth_headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        for transaction in data["transactions"]:
            assert "id" in transaction
            assert "amount" in transaction
            assert "status" in transaction
            assert transaction["status"] in ["pending", "completed", "cancelled"]


class TestEarningsFiltering:
    """
    Contract tests for earnings filtering
    """

    def test_should_filter_by_period(
        self, client, detective_user, detective_auth_headers
    ):
        """
        Given: Authenticated detective
        When: GET /detective/earnings?period=this_month
        Then: Returns filtered results
        """
        response = client.get(
            "/detective/earnings?period=this_month", headers=detective_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "summary" in data
        assert "transactions" in data
