/**
 * Messaging API Functions
 * 003-role-based-ui Feature - US6 (T121)
 *
 * REST API client for messaging endpoints:
 * - GET /messages/conversations
 * - GET /messages/{case_id}
 * - POST /messages
 * - POST /messages/read
 * - GET /messages/unread
 */

import { apiRequest } from './client';
import type {
  Message,
  MessageListResponse,
  ConversationListResponse,
  UnreadCountResponse,
  SendMessageRequest,
} from '@/types/message';

const API_BASE = '/messages';

/**
 * Get list of conversations for the current user
 */
export async function getConversations() {
  return apiRequest<ConversationListResponse>(`${API_BASE}/conversations`, {
    method: 'GET',
    credentials: 'include',
  });
}

/**
 * Get messages for a specific case
 * @param caseId - Case ID to fetch messages for
 * @param options - Optional filters: other_user_id, limit, before_id
 */
export async function getMessages(
  caseId: string,
  options?: {
    other_user_id?: string;
    limit?: number;
    before_id?: string;
  }
) {
  const params = new URLSearchParams();
  if (options?.other_user_id) params.append('other_user_id', options.other_user_id);
  if (options?.limit) params.append('limit', options.limit.toString());
  if (options?.before_id) params.append('before_id', options.before_id);

  const query = params.toString();
  const url = query ? `${API_BASE}/${caseId}?${query}` : `${API_BASE}/${caseId}`;

  return apiRequest<MessageListResponse>(url, {
    method: 'GET',
    credentials: 'include',
  });
}

/**
 * Send a new message
 * @param data - Message data including case_id, recipient_id, content
 */
export async function sendMessage(data: SendMessageRequest) {
  return apiRequest<Message>(`${API_BASE}`, {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify(data),
  });
}

/**
 * Mark messages as read
 * @param messageIds - Array of message IDs to mark as read
 */
export async function markAsRead(messageIds: string[]) {
  return apiRequest<{ marked_count: number }>(`${API_BASE}/read`, {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify({ message_ids: messageIds }),
  });
}

/**
 * Get unread message count
 */
export async function getUnreadCount() {
  return apiRequest<UnreadCountResponse>(`${API_BASE}/unread`, {
    method: 'GET',
    credentials: 'include',
  });
}

/**
 * Build WebSocket URL for real-time messaging
 * @param token - JWT token for authentication
 */
export function buildWebSocketUrl(token: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
  const wsHost = baseUrl.replace(/^https?:\/\//, '');
  return `${wsProtocol}://${wsHost}${API_BASE}/ws?token=${token}`;
}
