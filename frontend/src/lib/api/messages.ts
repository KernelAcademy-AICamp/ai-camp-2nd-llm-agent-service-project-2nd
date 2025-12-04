/**
 * Message API client
 * 003-role-based-ui Feature - US6
 */

import { apiClient, ApiResponse } from './client';
import type {
  Message,
  MessageListResponse,
  ConversationListResponse,
  UnreadCountResponse,
  SendMessageRequest,
  MarkReadRequest,
} from '@/types/message';

const BASE_PATH = '/messages';

/**
 * Get list of conversations for the current user
 */
export async function getConversations(): Promise<ApiResponse<ConversationListResponse>> {
  return apiClient.get<ConversationListResponse>(`${BASE_PATH}/conversations`);
}

/**
 * Get unread message count
 */
export async function getUnreadCount(): Promise<ApiResponse<UnreadCountResponse>> {
  return apiClient.get<UnreadCountResponse>(`${BASE_PATH}/unread`);
}

/**
 * Get messages for a case
 */
export async function getMessages(
  caseId: string,
  options?: {
    otherUserId?: string;
    limit?: number;
    beforeId?: string;
  }
): Promise<ApiResponse<MessageListResponse>> {
  const params = new URLSearchParams();
  if (options?.otherUserId) params.set('other_user_id', options.otherUserId);
  if (options?.limit) params.set('limit', String(options.limit));
  if (options?.beforeId) params.set('before_id', options.beforeId);

  const query = params.toString();
  const url = `${BASE_PATH}/${caseId}${query ? `?${query}` : ''}`;

  return apiClient.get<MessageListResponse>(url);
}

/**
 * Send a new message
 */
export async function sendMessage(
  data: SendMessageRequest
): Promise<ApiResponse<Message>> {
  return apiClient.post<Message>(BASE_PATH, data);
}

/**
 * Mark messages as read
 */
export async function markMessagesRead(
  messageIds: string[]
): Promise<ApiResponse<{ marked_count: number }>> {
  const body: MarkReadRequest = { message_ids: messageIds };
  return apiClient.post<{ marked_count: number }>(`${BASE_PATH}/read`, body);
}

// ============== WebSocket Client ==============

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface MessageWebSocketCallbacks {
  onMessage?: (message: Message) => void;
  onTyping?: (data: { user_id: string; case_id: string; is_typing: boolean }) => void;
  onReadReceipt?: (messageIds: string[]) => void;
  onOfflineMessages?: (messages: Message[]) => void;
  onStatusChange?: (status: WebSocketStatus) => void;
  onError?: (error: string) => void;
}

/**
 * Create a WebSocket connection for real-time messaging
 */
export function createMessageWebSocket(
  token: string,
  callbacks: MessageWebSocketCallbacks
): {
  send: (type: string, payload: unknown) => void;
  sendMessage: (caseId: string, recipientId: string, content: string, attachments?: string[]) => void;
  sendTyping: (caseId: string, recipientId: string, isTyping: boolean) => void;
  markRead: (messageIds: string[]) => void;
  close: () => void;
} {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const wsBaseUrl = apiBaseUrl.replace(/^http/, 'ws');
  const wsUrl = `${wsBaseUrl}/messages/ws?token=${encodeURIComponent(token)}`;

  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 5;
  let reconnectTimeout: NodeJS.Timeout | null = null;

  const connect = () => {
    callbacks.onStatusChange?.('connecting');

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      reconnectAttempts = 0;
      callbacks.onStatusChange?.('connected');
    };

    ws.onclose = (event) => {
      callbacks.onStatusChange?.('disconnected');

      // Attempt to reconnect if not a normal closure
      if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        reconnectTimeout = setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      callbacks.onStatusChange?.('error');
      callbacks.onError?.('WebSocket connection error');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const { type, payload } = data;

        switch (type) {
          case 'new_message':
          case 'message_sent':
            callbacks.onMessage?.(payload as Message);
            break;

          case 'typing':
            callbacks.onTyping?.(payload);
            break;

          case 'read_receipt':
          case 'read_confirmed':
            callbacks.onReadReceipt?.(payload.message_ids);
            break;

          case 'offline_messages':
            callbacks.onOfflineMessages?.(payload.messages);
            break;

          case 'error':
            callbacks.onError?.(payload.message);
            break;

          case 'pong':
            // Keep-alive response, no action needed
            break;
        }
      } catch {
        console.error('Failed to parse WebSocket message');
      }
    };
  };

  connect();

  const send = (type: string, payload: unknown) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type, payload }));
    }
  };

  return {
    send,

    sendMessage: (caseId: string, recipientId: string, content: string, attachments?: string[]) => {
      send('message', {
        case_id: caseId,
        recipient_id: recipientId,
        content,
        attachments,
      });
    },

    sendTyping: (caseId: string, recipientId: string, isTyping: boolean) => {
      send('typing', {
        case_id: caseId,
        recipient_id: recipientId,
        is_typing: isTyping,
      });
    },

    markRead: (messageIds: string[]) => {
      send('read', { message_ids: messageIds });
    },

    close: () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.close(1000, 'User closed connection');
        ws = null;
      }
    },
  };
}
