"""
Message API endpoints with WebSocket support
003-role-based-ui Feature - US6

REST Endpoints:
- GET /messages/conversations - List conversations
- GET /messages/{case_id} - Get messages for a case
- POST /messages - Send a message
- POST /messages/read - Mark messages as read
- GET /messages/unread - Get unread count

WebSocket:
- WS /messages/ws - Real-time message channel
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import Optional
import json
import asyncio
from datetime import datetime

from app.db.session import get_db
from app.db.models import User
from app.core.dependencies import get_current_user
from app.core.security import decode_access_token
from app.services.message_service import MessageService
from app.schemas.message import (
    MessageCreate,
    MessageMarkRead,
    MessageResponse,
    MessageListResponse,
    ConversationListResponse,
    UnreadCountResponse,
)

router = APIRouter()


# ============== Connection Manager for WebSocket ==============

class ConnectionManager:
    """
    Manages WebSocket connections for real-time messaging.

    Features:
    - User connection tracking
    - Broadcast to specific users
    - Presence updates
    """

    def __init__(self):
        # user_id -> list of WebSocket connections (user can have multiple tabs)
        self.active_connections: dict[str, list[WebSocket]] = {}
        # user_id -> last seen timestamp
        self.presence: dict[str, datetime] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept connection and register user."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.presence[user_id] = datetime.utcnow()

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove connection on disconnect."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                del self.presence[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a specific user."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Connection might be stale, will be cleaned up on next disconnect
                    pass

    async def broadcast_to_users(self, user_ids: list[str], message: dict):
        """Send message to multiple users."""
        for user_id in user_ids:
            await self.send_to_user(user_id, message)

    def is_online(self, user_id: str) -> bool:
        """Check if user is currently online."""
        return user_id in self.active_connections

    def get_online_users(self) -> list[str]:
        """Get list of online user IDs."""
        return list(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()


# ============== REST Endpoints ==============

@router.get("/conversations", response_model=ConversationListResponse)
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get list of conversations for the current user.

    Returns conversations grouped by case and other user,
    with last message preview and unread count.
    """
    service = MessageService(db)
    return service.get_conversations(current_user.id)


@router.get("/unread", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get unread message count.

    Returns total unread and breakdown by case.
    """
    service = MessageService(db)
    return service.get_unread_count(current_user.id)


@router.get("/{case_id}", response_model=MessageListResponse)
def get_messages(
    case_id: str,
    other_user_id: Optional[str] = Query(None, description="Filter to conversation with this user"),
    limit: int = Query(50, ge=1, le=100, description="Maximum messages to return"),
    before_id: Optional[str] = Query(None, description="Get messages before this ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get messages for a case.

    Optionally filter to a specific conversation with another user.
    Supports pagination with before_id.
    """
    service = MessageService(db)
    try:
        return service.get_messages(
            user_id=current_user.id,
            case_id=case_id,
            other_user_id=other_user_id,
            limit=limit,
            before_id=before_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a new message.

    Also broadcasts to recipient via WebSocket if online.
    """
    service = MessageService(db)
    try:
        message = service.send_message(
            sender_id=current_user.id,
            message_data=message_data,
        )

        # Broadcast via WebSocket to recipient
        await manager.send_to_user(
            message_data.recipient_id,
            {
                "type": "new_message",
                "payload": message.model_dump(mode="json"),
            },
        )

        return message
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/read")
def mark_messages_read(
    data: MessageMarkRead,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark messages as read.

    Only marks messages where the current user is the recipient.
    """
    service = MessageService(db)
    count = service.mark_as_read(current_user.id, data.message_ids)
    return {"marked_count": count}


# ============== WebSocket Endpoint ==============

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time messaging.

    Connection:
        ws://host/api/messages/ws?token=<jwt_token>

    Message Types (client -> server):
        - message: Send a new message
        - read: Mark messages as read
        - typing: Typing indicator
        - ping: Keep-alive

    Message Types (server -> client):
        - new_message: New message received
        - read_receipt: Message was read
        - typing: Someone is typing
        - presence: User online/offline
        - offline_messages: Unread messages on connect
        - pong: Keep-alive response
    """
    # Authenticate via token
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    # Connect
    await manager.connect(websocket, user_id)

    try:
        # Send offline messages on connect
        service = MessageService(db)
        offline_messages = service.get_offline_messages(user_id)
        if offline_messages:
            await websocket.send_json({
                "type": "offline_messages",
                "payload": {
                    "messages": [m.model_dump(mode="json") for m in offline_messages],
                },
            })

        # Main message loop
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60.0,  # Timeout for keep-alive
                )
            except asyncio.TimeoutError:
                # Send ping to check connection
                await websocket.send_json({"type": "ping"})
                continue

            msg_type = data.get("type")
            payload_data = data.get("payload", {})

            if msg_type == "message":
                # Handle new message
                try:
                    message_data = MessageCreate(**payload_data)
                    message = service.send_message(user_id, message_data)

                    # Send to recipient
                    await manager.send_to_user(
                        message_data.recipient_id,
                        {
                            "type": "new_message",
                            "payload": message.model_dump(mode="json"),
                        },
                    )

                    # Confirm to sender
                    await websocket.send_json({
                        "type": "message_sent",
                        "payload": message.model_dump(mode="json"),
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": str(e)},
                    })

            elif msg_type == "read":
                # Handle read receipt
                message_ids = payload_data.get("message_ids", [])
                service.mark_as_read(user_id, message_ids)

                # Notify senders
                # (For simplicity, broadcast to all involved - could optimize)
                await websocket.send_json({
                    "type": "read_confirmed",
                    "payload": {"message_ids": message_ids},
                })

            elif msg_type == "typing":
                # Forward typing indicator to recipient
                recipient_id = payload_data.get("recipient_id")
                if recipient_id:
                    await manager.send_to_user(
                        recipient_id,
                        {
                            "type": "typing",
                            "payload": {
                                "user_id": user_id,
                                "case_id": payload_data.get("case_id"),
                                "is_typing": payload_data.get("is_typing", True),
                            },
                        },
                    )

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception:
        manager.disconnect(websocket, user_id)
