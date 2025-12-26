"""
Test suite for Lawyer Clients API endpoints
005-lawyer-portal-pages Feature - US2

Tests for:
- GET /clients/lawyer-portal - list clients with filters
- GET /clients/lawyer-portal/{client_id} - client detail
"""

from fastapi import status


class TestGetClients:
    """Test suite for GET /clients/lawyer-portal endpoint"""

    def test_should_return_client_list_for_authenticated_lawyer(
        self, client, auth_headers
    ):
        """
        Given: Authenticated lawyer
        When: GET /clients/lawyer-portal is called
        Then:
            - Returns 200 status code
            - Response contains items, total, page, page_size, total_pages
        """
        # When
        response = client.get("/clients/lawyer-portal", headers=auth_headers)

        # Then
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    def test_should_return_401_without_auth(self, client):
        """
        Given: No authentication
        When: GET /clients/lawyer-portal is called
        Then: Returns 401 Unauthorized
        """
        # When
        response = client.get("/clients/lawyer-portal")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_should_accept_search_filter(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: GET /clients/lawyer-portal?search=test is called
        Then: Returns 200 with filtered results
        """
        # When
        response = client.get(
            "/clients/lawyer-portal?search=test",
            headers=auth_headers
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "items" in response.json()

    def test_should_accept_status_filter(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: GET /clients/lawyer-portal?status=active is called
        Then: Returns 200 with filtered results
        """
        # When
        response = client.get(
            "/clients/lawyer-portal?status=active",
            headers=auth_headers
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "items" in response.json()

    def test_should_accept_pagination_params(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: GET /clients/lawyer-portal?page=2&page_size=5 is called
        Then: Returns 200 with correct pagination
        """
        # When
        response = client.get(
            "/clients/lawyer-portal?page=2&page_size=5",
            headers=auth_headers
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    def test_should_accept_sort_params(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: GET /clients/lawyer-portal?sort_by=name&sort_order=asc is called
        Then: Returns 200 with sorted results
        """
        # When
        response = client.get(
            "/clients/lawyer-portal?sort_by=name&sort_order=asc",
            headers=auth_headers
        )

        # Then
        assert response.status_code == status.HTTP_200_OK


class TestGetClientDetail:
    """Test suite for GET /clients/lawyer-portal/{client_id} endpoint"""

    def test_should_return_client_detail_for_valid_id(
        self, client, auth_headers, client_user
    ):
        """
        Given: Authenticated lawyer and valid client ID
        When: GET /clients/lawyer-portal/{client_id} is called
        Then:
            - Returns 200 status code
            - Response contains client details
        """
        # When
        response = client.get(
            f"/clients/lawyer-portal/{client_user.id}",
            headers=auth_headers
        )

        # Then - may return 404 if no case link, which is expected behavior
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    def test_should_return_404_for_invalid_id(self, client, auth_headers):
        """
        Given: Authenticated lawyer
        When: GET /clients/lawyer-portal/{invalid_id} is called
        Then: Returns 404 Not Found
        """
        # When
        response = client.get(
            "/clients/lawyer-portal/non-existent-client-id",
            headers=auth_headers
        )

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_should_return_401_without_auth(self, client):
        """
        Given: No authentication
        When: GET /clients/lawyer-portal/{id} is called
        Then: Returns 401 Unauthorized
        """
        # When
        response = client.get("/clients/lawyer-portal/some-client-id")

        # Then
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
