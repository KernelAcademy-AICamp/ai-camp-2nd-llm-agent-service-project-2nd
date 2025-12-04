"""
Unit tests for Message Service
TDD - Improving test coverage for message_service.py
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.message_service import MessageService
from app.schemas.message import MessageCreate


class TestSendMessage:
    """Unit tests for send_message method"""

    def test_send_message_no_case_access(self):
        """Raises PermissionError when sender has no case access"""
        mock_db = MagicMock()

        with patch.object(MessageService, '__init__', lambda x, y: None):
            service = MessageService(mock_db)
            service.db = mock_db
            service._has_case_access = MagicMock(return_value=False)

            message_data = MessageCreate(
                case_id="case-123",
                recipient_id="recipient-123",
                content="테스트 메시지"
            )

            with pytest.raises(PermissionError, match="접근 권한이 없습니다"):
                service.send_message("sender-123", message_data)

    def test_send_message_recipient_not_found(self):
        """Raises ValueError when recipient not found"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch.object(MessageService, '__init__', lambda x, y: None):
            service = MessageService(mock_db)
            service.db = mock_db
            service._has_case_access = MagicMock(return_value=True)

            message_data = MessageCreate(
                case_id="case-123",
                recipient_id="nonexistent",
                content="테스트 메시지"
            )

            with pytest.raises(ValueError, match="수신자를 찾을 수 없습니다"):
                service.send_message("sender-123", message_data)

    def test_send_message_recipient_no_access(self):
        """Raises ValueError when recipient has no case access"""
        mock_db = MagicMock()
        mock_recipient = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recipient

        with patch.object(MessageService, '__init__', lambda x, y: None):
            service = MessageService(mock_db)
            service.db = mock_db
            # Sender has access, recipient doesn't
            service._has_case_access = MagicMock(side_effect=[True, False])

            message_data = MessageCreate(
                case_id="case-123",
                recipient_id="recipient-123",
                content="테스트 메시지"
            )

            with pytest.raises(ValueError, match="수신자가 이 케이스에 접근할 수 없습니다"):
                service.send_message("sender-123", message_data)


class TestGetMessages:
    """Unit tests for get_messages method"""

    def test_get_messages_no_access(self):
        """Raises PermissionError when user has no case access"""
        mock_db = MagicMock()

        with patch.object(MessageService, '__init__', lambda x, y: None):
            service = MessageService(mock_db)
            service.db = mock_db
            service._has_case_access = MagicMock(return_value=False)

            with pytest.raises(PermissionError, match="접근 권한이 없습니다"):
                service.get_messages("user-123", "case-123")


class TestGetConversations:
    """Unit tests for get_conversations method"""

    def test_get_conversations_returns_empty_list(self):
        """Returns empty list when no conversations"""
        mock_db = MagicMock()
        # Mock empty results from query
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(MessageService, '__init__', lambda x, y: None):
            service = MessageService(mock_db)
            service.db = mock_db

            result = service.get_conversations("user-123")

            assert result.conversations == []


class TestHasCaseAccess:
    """Unit tests for _has_case_access method"""

    def test_has_case_access_as_owner(self):
        """Returns True when user is case owner"""
        mock_db = MagicMock()
        mock_case = MagicMock()
        mock_case.created_by = "user-123"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case

        with patch.object(MessageService, '__init__', lambda x, y: None):
            service = MessageService(mock_db)
            service.db = mock_db

            result = service._has_case_access("user-123", "case-123")

            assert result is True

    def test_has_case_access_case_not_found(self):
        """Returns False when case not found"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch.object(MessageService, '__init__', lambda x, y: None):
            service = MessageService(mock_db)
            service.db = mock_db

            result = service._has_case_access("user-123", "nonexistent")

            assert result is False
