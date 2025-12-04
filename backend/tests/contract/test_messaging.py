"""
Contract tests for Messaging API
US6 - Task T106, T107, T108

Tests for messaging endpoints:
- GET /messages/conversations - List conversations (T106)
- GET /messages/{case_id} - Get messages for a case (T106)
- POST /messages - Send a message (T107)
- POST /messages/read - Mark messages as read (T107)
- GET /messages/unread - Get unread count (T106)
- POST /messages with attachments (T108)

Note: These tests focus on API contract validation.
Complex integration tests are in the integration test suite.
"""

import pytest
from fastapi import status
from app.core.security import create_access_token


# ============================================
# T106: Contract tests for GET /messages endpoints
# ============================================

class TestGetMessages:
    """
    Contract tests for GET /messages/{case_id}
    Task T106
    """

    def test_should_return_messages_for_case(
        self, client, test_case_with_client, auth_headers
    ):
        """
        Given: Authenticated user with case access
        When: GET /messages/{case_id}
        Then:
            - Returns 200 status code
            - Response contains messages array
            - Response contains total count
            - Response contains has_more pagination flag
        """
        # When: GET /messages/{case_id}
        response = client.get(
            f"/messages/{test_case_with_client.id}",
            headers=auth_headers
        )

        # Then: Success with message list
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify response structure
        assert "messages" in data
        assert isinstance(data["messages"], list)
        assert "total" in data
        assert isinstance(data["total"], int)
        assert "has_more" in data
        assert isinstance(data["has_more"], bool)

    def test_should_filter_by_other_user_id(
        self, client, test_case_with_client, client_user, auth_headers
    ):
        """
        Given: Authenticated user with case access
        When: GET /messages/{case_id}?other_user_id={user_id}
        Then: Returns messages filtered to that conversation
        """
        # When: GET with other_user_id filter
        response = client.get(
            f"/messages/{test_case_with_client.id}?other_user_id={client_user.id}",
            headers=auth_headers
        )

        # Then: Success
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "messages" in data

    def test_should_support_pagination_with_limit(
        self, client, test_case_with_client, auth_headers
    ):
        """
        Given: Authenticated user
        When: GET /messages/{case_id}?limit=10
        Then: Returns limited messages
        """
        # When: GET with limit
        response = client.get(
            f"/messages/{test_case_with_client.id}?limit=10",
            headers=auth_headers
        )

        # Then: Success
        assert response.status_code == status.HTTP_200_OK

    def test_should_reject_unauthenticated_request(self, client, test_env):
        """
        Given: No authentication token
        When: GET /messages/{case_id}
        Then: Returns 401 Unauthorized
        """
        # When: GET without auth
        response = client.get("/messages/case_123")

        # Then: Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetConversations:
    """
    Contract tests for GET /messages/conversations
    Task T106
    """

    def test_should_return_conversation_list(self, client, auth_headers):
        """
        Given: Authenticated user
        When: GET /messages/conversations
        Then:
            - Returns 200 status code
            - Response contains conversations array
            - Response contains total_unread count
        """
        # When: GET /messages/conversations
        response = client.get("/messages/conversations", headers=auth_headers)

        # Then: Success with conversation list
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify response structure
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
        assert "total_unread" in data
        assert isinstance(data["total_unread"], int)

    def test_should_reject_unauthenticated_request(self, client, test_env):
        """
        Given: No authentication token
        When: GET /messages/conversations
        Then: Returns 401 Unauthorized
        """
        response = client.get("/messages/conversations")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetUnreadCount:
    """
    Contract tests for GET /messages/unread
    Task T106
    """

    def test_should_return_unread_count(self, client, auth_headers):
        """
        Given: Authenticated user
        When: GET /messages/unread
        Then:
            - Returns 200 status code
            - Response contains total count
            - Response contains by_case breakdown
        """
        # When: GET /messages/unread
        response = client.get("/messages/unread", headers=auth_headers)

        # Then: Success
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify response structure
        assert "total" in data
        assert isinstance(data["total"], int)
        assert "by_case" in data
        assert isinstance(data["by_case"], dict)

    def test_should_reject_unauthenticated_request(self, client, test_env):
        """
        Given: No authentication token
        When: GET /messages/unread
        Then: Returns 401 Unauthorized
        """
        response = client.get("/messages/unread")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# T107: Contract tests for POST /messages endpoints
# ============================================

class TestSendMessage:
    """
    Contract tests for POST /messages
    Task T107
    """

    def test_should_send_message_successfully(
        self, client, test_case_with_client, client_user, auth_headers
    ):
        """
        Given: Authenticated user with case access
        When: POST /messages with valid data
        Then:
            - Returns 200 status code
            - Response contains created message
            - Message has id, case_id, sender, content, created_at
        """
        message_data = {
            "case_id": test_case_with_client.id,
            "recipient_id": client_user.id,
            "content": "안녕하세요, 케이스 관련 문의드립니다."
        }

        # When: POST /messages
        response = client.post(
            "/messages",
            json=message_data,
            headers=auth_headers
        )

        # Then: Success with message data
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["id"].startswith("msg_")
        assert "case_id" in data
        assert data["case_id"] == test_case_with_client.id
        assert "sender" in data
        assert "id" in data["sender"]
        assert "name" in data["sender"]
        assert "role" in data["sender"]
        assert "recipient_id" in data
        assert data["recipient_id"] == client_user.id
        assert "content" in data
        assert data["content"] == message_data["content"]
        assert "created_at" in data
        assert "is_mine" in data
        assert data["is_mine"] is True

    def test_should_validate_content_not_empty(
        self, client, test_case_with_client, client_user, auth_headers
    ):
        """
        Given: Authenticated user
        When: POST /messages with empty content
        Then: Returns 422 Validation Error
        """
        message_data = {
            "case_id": test_case_with_client.id,
            "recipient_id": client_user.id,
            "content": ""  # Empty content
        }

        # When: POST /messages
        response = client.post(
            "/messages",
            json=message_data,
            headers=auth_headers
        )

        # Then: Validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_should_validate_content_max_length(
        self, client, test_case_with_client, client_user, auth_headers
    ):
        """
        Given: Authenticated user
        When: POST /messages with content > 5000 chars
        Then: Returns 422 Validation Error
        """
        message_data = {
            "case_id": test_case_with_client.id,
            "recipient_id": client_user.id,
            "content": "x" * 5001  # Exceeds max length
        }

        # When: POST /messages
        response = client.post(
            "/messages",
            json=message_data,
            headers=auth_headers
        )

        # Then: Validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_should_reject_invalid_recipient(
        self, client, test_case_with_client, auth_headers
    ):
        """
        Given: Authenticated user
        When: POST /messages with non-existent recipient
        Then: Returns 400 Bad Request
        """
        message_data = {
            "case_id": test_case_with_client.id,
            "recipient_id": "nonexistent_user_id",
            "content": "Test message"
        }

        # When: POST /messages
        response = client.post(
            "/messages",
            json=message_data,
            headers=auth_headers
        )

        # Then: Bad request
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_should_reject_unauthenticated_request(self, client, test_env):
        """
        Given: No authentication token
        When: POST /messages
        Then: Returns 401 Unauthorized
        """
        message_data = {
            "case_id": "case_123",
            "recipient_id": "user_456",
            "content": "Test message"
        }

        response = client.post("/messages", json=message_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMarkMessagesRead:
    """
    Contract tests for POST /messages/read
    Task T107
    """

    def test_should_mark_messages_as_read(self, client, auth_headers):
        """
        Given: Authenticated user
        When: POST /messages/read with message IDs
        Then:
            - Returns 200 status code
            - Response contains marked_count
        """
        # When: POST /messages/read
        response = client.post(
            "/messages/read",
            json={"message_ids": ["msg_123", "msg_456"]},
            headers=auth_headers
        )

        # Then: Success
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "marked_count" in data
        assert isinstance(data["marked_count"], int)

    def test_should_validate_message_ids_required(self, client, auth_headers):
        """
        Given: Authenticated user
        When: POST /messages/read without message_ids
        Then: Returns 422 Validation Error
        """
        response = client.post(
            "/messages/read",
            json={},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_should_reject_unauthenticated_request(self, client, test_env):
        """
        Given: No authentication token
        When: POST /messages/read
        Then: Returns 401 Unauthorized
        """
        response = client.post(
            "/messages/read",
            json={"message_ids": ["msg_123"]}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# T108: Contract tests for messages with attachments
# ============================================

class TestMessageAttachments:
    """
    Contract tests for POST /messages with attachments
    Task T108
    """

    def test_should_send_message_with_attachments(
        self, client, test_case_with_client, client_user, auth_headers
    ):
        """
        Given: Authenticated user with case access
        When: POST /messages with attachments
        Then:
            - Returns 200 status code
            - Response contains attachments array
        """
        message_data = {
            "case_id": test_case_with_client.id,
            "recipient_id": client_user.id,
            "content": "Please see attached files.",
            "attachments": [
                "https://s3.amazonaws.com/bucket/file1.pdf",
                "https://s3.amazonaws.com/bucket/file2.jpg"
            ]
        }

        # When: POST /messages
        response = client.post(
            "/messages",
            json=message_data,
            headers=auth_headers
        )

        # Then: Success with attachments
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "attachments" in data
        assert data["attachments"] == message_data["attachments"]

    def test_should_accept_message_without_attachments(
        self, client, test_case_with_client, client_user, auth_headers
    ):
        """
        Given: Authenticated user
        When: POST /messages without attachments field
        Then: Returns 200 with null attachments
        """
        message_data = {
            "case_id": test_case_with_client.id,
            "recipient_id": client_user.id,
            "content": "Message without attachments"
        }

        # When: POST /messages
        response = client.post(
            "/messages",
            json=message_data,
            headers=auth_headers
        )

        # Then: Success
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # attachments should be null or empty
        assert data.get("attachments") is None or data.get("attachments") == []


# ============================================
# T106: Message Response Structure Tests
# ============================================

class TestMessageResponseStructure:
    """
    Contract tests for message response schema
    Task T106
    """

    def test_message_response_should_have_all_fields(
        self, client, test_case_with_client, client_user, auth_headers
    ):
        """
        Given: Authenticated user
        When: POST /messages (create a message)
        Then: Response has all required fields with correct types
        """
        message_data = {
            "case_id": test_case_with_client.id,
            "recipient_id": client_user.id,
            "content": "Test message for structure validation"
        }

        response = client.post(
            "/messages",
            json=message_data,
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Verify all fields
        assert isinstance(data["id"], str)
        assert isinstance(data["case_id"], str)
        assert isinstance(data["sender"], dict)
        assert isinstance(data["sender"]["id"], str)
        assert isinstance(data["sender"]["name"], str)
        assert isinstance(data["sender"]["role"], str)
        assert isinstance(data["recipient_id"], str)
        assert isinstance(data["content"], str)
        assert isinstance(data["created_at"], str)  # ISO datetime string
        assert isinstance(data["is_mine"], bool)
        # read_at can be None or string
        assert data.get("read_at") is None or isinstance(data["read_at"], str)
        # attachments can be None or list
        assert data.get("attachments") is None or isinstance(data["attachments"], list)


class TestConversationResponseStructure:
    """
    Contract tests for conversation response schema
    Task T106
    """

    def test_conversation_should_have_required_fields(
        self, client, test_case_with_client, client_user, auth_headers
    ):
        """
        Given: User with conversations
        When: GET /messages/conversations
        Then: Each conversation has case_id, case_title, other_user,
              last_message, last_message_at, unread_count
        """
        # First send a message to create a conversation
        message_data = {
            "case_id": test_case_with_client.id,
            "recipient_id": client_user.id,
            "content": "Hello from lawyer"
        }
        send_response = client.post(
            "/messages",
            json=message_data,
            headers=auth_headers
        )

        # Skip if message sending failed
        if send_response.status_code != status.HTTP_200_OK:
            pytest.skip("Message sending not available")

        # When: GET /messages/conversations
        response = client.get("/messages/conversations", headers=auth_headers)

        # Then: Verify structure
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # If conversations exist, verify structure
        for conv in data["conversations"]:
            assert "case_id" in conv
            assert "case_title" in conv
            assert "other_user" in conv
            assert "id" in conv["other_user"]
            assert "name" in conv["other_user"]
            assert "role" in conv["other_user"]
            assert "last_message" in conv
            assert "last_message_at" in conv
            assert "unread_count" in conv
