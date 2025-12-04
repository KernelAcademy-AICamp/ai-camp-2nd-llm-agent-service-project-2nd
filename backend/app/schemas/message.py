"""
Message schemas for real-time communication
003-role-based-ui Feature - US6
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============== Request Schemas ==============

class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    case_id: str = Field(..., description="Case ID the message belongs to")
    recipient_id: str = Field(..., description="Recipient user ID")
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    attachments: Optional[List[str]] = Field(None, description="List of attachment URLs")


class MessageMarkRead(BaseModel):
    """Schema for marking messages as read"""
    message_ids: List[str] = Field(..., description="List of message IDs to mark as read")


# ============== Response Schemas ==============

class MessageSender(BaseModel):
    """Sender information in message"""
    id: str
    name: str
    role: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Single message response"""
    id: str
    case_id: str
    sender: MessageSender
    recipient_id: str
    content: str
    attachments: Optional[List[str]] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    is_mine: bool = False  # Whether the current user is the sender

    class Config:
        from_attributes = True


class OtherUserInfo(BaseModel):
    """Other user info in conversation"""
    id: str
    name: str
    role: str


class ConversationSummary(BaseModel):
    """Summary of a conversation thread"""
    case_id: str
    case_title: str
    other_user: OtherUserInfo
    last_message: str
    last_message_at: datetime
    unread_count: int


class MessageListResponse(BaseModel):
    """List of messages response"""
    messages: List[MessageResponse]
    total: int
    has_more: bool


class ConversationListResponse(BaseModel):
    """List of conversations response"""
    conversations: List[ConversationSummary]
    total_unread: int


class UnreadCountResponse(BaseModel):
    """Unread message count response"""
    total: int
    by_case: dict[str, int]  # case_id -> count


# ============== WebSocket Schemas ==============

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str = Field(..., description="Message type: message, read, typing, presence")
    payload: dict = Field(..., description="Message payload")


class NewMessagePayload(BaseModel):
    """Payload for new message via WebSocket"""
    case_id: str
    recipient_id: str
    content: str
    attachments: Optional[List[str]] = None


class TypingPayload(BaseModel):
    """Payload for typing indicator"""
    case_id: str
    recipient_id: str
    is_typing: bool


class PresencePayload(BaseModel):
    """Payload for presence update"""
    status: str  # online, away, offline
