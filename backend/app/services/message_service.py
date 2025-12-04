"""
Message Service for real-time communication
003-role-based-ui Feature - US6

Handles:
- Message CRUD operations
- Conversation management
- Unread message tracking
- Offline message queue
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import json
import uuid

from app.db.models import Message, User, Case, CaseMember
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageSender,
    MessageListResponse,
    ConversationSummary,
    ConversationListResponse,
    UnreadCountResponse,
    OtherUserInfo,
)


class MessageService:
    """Service for message operations"""

    def __init__(self, db: Session):
        self.db = db

    def send_message(
        self,
        sender_id: str,
        message_data: MessageCreate,
    ) -> MessageResponse:
        """
        Send a new message.

        Args:
            sender_id: ID of the sender
            message_data: Message creation data

        Returns:
            Created message response

        Raises:
            PermissionError: If sender doesn't have access to the case
            ValueError: If recipient is invalid
        """
        # Verify sender has access to the case
        if not self._has_case_access(sender_id, message_data.case_id):
            raise PermissionError("이 케이스에 대한 접근 권한이 없습니다.")

        # Verify recipient exists and has access to the case
        recipient = self.db.query(User).filter(User.id == message_data.recipient_id).first()
        if not recipient:
            raise ValueError("수신자를 찾을 수 없습니다.")

        if not self._has_case_access(message_data.recipient_id, message_data.case_id):
            raise ValueError("수신자가 이 케이스에 접근할 수 없습니다.")

        # Create message
        message = Message(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            case_id=message_data.case_id,
            sender_id=sender_id,
            recipient_id=message_data.recipient_id,
            content=message_data.content,
            attachments=json.dumps(message_data.attachments) if message_data.attachments else None,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return self._to_message_response(message, sender_id)

    def get_messages(
        self,
        user_id: str,
        case_id: str,
        other_user_id: Optional[str] = None,
        limit: int = 50,
        before_id: Optional[str] = None,
    ) -> MessageListResponse:
        """
        Get messages for a case/conversation.

        Args:
            user_id: Current user ID
            case_id: Case ID to get messages for
            other_user_id: If provided, filter to conversation with this user
            limit: Maximum number of messages to return
            before_id: For pagination, get messages before this ID

        Returns:
            List of messages
        """
        # Verify access
        if not self._has_case_access(user_id, case_id):
            raise PermissionError("이 케이스에 대한 접근 권한이 없습니다.")

        query = self.db.query(Message).filter(Message.case_id == case_id)

        # Filter to conversation if other_user_id provided
        if other_user_id:
            query = query.filter(
                or_(
                    and_(Message.sender_id == user_id, Message.recipient_id == other_user_id),
                    and_(Message.sender_id == other_user_id, Message.recipient_id == user_id),
                )
            )
        else:
            # Get all messages where user is sender or recipient
            query = query.filter(
                or_(Message.sender_id == user_id, Message.recipient_id == user_id)
            )

        # Pagination
        if before_id:
            before_msg = self.db.query(Message).filter(Message.id == before_id).first()
            if before_msg:
                query = query.filter(Message.created_at < before_msg.created_at)

        # Get total count before limit
        total = query.count()

        # Order by created_at desc and limit
        messages = query.order_by(desc(Message.created_at)).limit(limit + 1).all()

        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        # Reverse to get chronological order
        messages.reverse()

        return MessageListResponse(
            messages=[self._to_message_response(m, user_id) for m in messages],
            total=total,
            has_more=has_more,
        )

    def get_conversations(self, user_id: str) -> ConversationListResponse:
        """
        Get list of conversations for a user.

        Returns conversations grouped by case and other user,
        with last message and unread count.
        """
        # Get all cases the user has access to
        case_memberships = (
            self.db.query(CaseMember)
            .filter(CaseMember.user_id == user_id)
            .all()
        )
        case_ids = [m.case_id for m in case_memberships]

        if not case_ids:
            return ConversationListResponse(conversations=[], total_unread=0)

        # Get messages where user is involved
        messages = (
            self.db.query(Message)
            .filter(
                Message.case_id.in_(case_ids),
                or_(Message.sender_id == user_id, Message.recipient_id == user_id),
            )
            .order_by(desc(Message.created_at))
            .all()
        )

        # Group by (case_id, other_user_id)
        conversations_map: dict[tuple[str, str], dict] = {}
        total_unread = 0

        for msg in messages:
            other_id = msg.recipient_id if msg.sender_id == user_id else msg.sender_id
            key = (msg.case_id, other_id)

            if key not in conversations_map:
                # Get case and other user info
                case = self.db.query(Case).filter(Case.id == msg.case_id).first()
                other_user = self.db.query(User).filter(User.id == other_id).first()

                if not case or not other_user:
                    continue

                conversations_map[key] = {
                    "case_id": msg.case_id,
                    "case_title": case.title,
                    "other_user": OtherUserInfo(
                        id=other_id,
                        name=other_user.name or "Unknown",
                        role=other_user.role.value if other_user.role else "unknown",
                    ),
                    "last_message": msg.content[:100],
                    "last_message_at": msg.created_at,
                    "unread_count": 0,
                }

            # Count unread messages (received by user, not read)
            if msg.recipient_id == user_id and msg.read_at is None:
                conversations_map[key]["unread_count"] += 1
                total_unread += 1

        conversations = [
            ConversationSummary(**conv_data)
            for conv_data in sorted(
                conversations_map.values(),
                key=lambda x: x["last_message_at"],
                reverse=True,
            )
        ]

        return ConversationListResponse(
            conversations=conversations,
            total_unread=total_unread,
        )

    def mark_as_read(
        self,
        user_id: str,
        message_ids: List[str],
    ) -> int:
        """
        Mark messages as read.

        Args:
            user_id: User marking messages as read
            message_ids: List of message IDs

        Returns:
            Number of messages marked as read
        """
        # Only mark messages where user is the recipient
        result = (
            self.db.query(Message)
            .filter(
                Message.id.in_(message_ids),
                Message.recipient_id == user_id,
                Message.read_at.is_(None),
            )
            .update(
                {"read_at": datetime.now(timezone.utc)},
                synchronize_session=False,
            )
        )

        self.db.commit()
        return result

    def get_unread_count(self, user_id: str) -> UnreadCountResponse:
        """
        Get unread message count for a user.

        Returns total unread and breakdown by case.
        """
        unread_messages = (
            self.db.query(Message)
            .filter(
                Message.recipient_id == user_id,
                Message.read_at.is_(None),
            )
            .all()
        )

        by_case: dict[str, int] = {}
        for msg in unread_messages:
            by_case[msg.case_id] = by_case.get(msg.case_id, 0) + 1

        return UnreadCountResponse(
            total=len(unread_messages),
            by_case=by_case,
        )

    def get_offline_messages(self, user_id: str) -> List[MessageResponse]:
        """
        Get unread messages for a user (offline queue).

        Called when user connects to deliver missed messages.
        """
        unread_messages = (
            self.db.query(Message)
            .filter(
                Message.recipient_id == user_id,
                Message.read_at.is_(None),
            )
            .order_by(Message.created_at)
            .all()
        )

        return [self._to_message_response(m, user_id) for m in unread_messages]

    def _has_case_access(self, user_id: str, case_id: str) -> bool:
        """Check if user has access to a case."""
        membership = (
            self.db.query(CaseMember)
            .filter(
                CaseMember.user_id == user_id,
                CaseMember.case_id == case_id,
            )
            .first()
        )
        return membership is not None

    def _to_message_response(self, message: Message, current_user_id: str) -> MessageResponse:
        """Convert Message model to MessageResponse."""
        sender = self.db.query(User).filter(User.id == message.sender_id).first()

        attachments = None
        if message.attachments:
            try:
                attachments = json.loads(message.attachments)
            except json.JSONDecodeError:
                attachments = None

        return MessageResponse(
            id=message.id,
            case_id=message.case_id,
            sender=MessageSender(
                id=sender.id if sender else message.sender_id,
                name=sender.name if sender else "Unknown",
                role=sender.role.value if sender and sender.role else "unknown",
            ),
            recipient_id=message.recipient_id,
            content=message.content,
            attachments=attachments,
            read_at=message.read_at,
            created_at=message.created_at,
            is_mine=message.sender_id == current_user_id,
        )
