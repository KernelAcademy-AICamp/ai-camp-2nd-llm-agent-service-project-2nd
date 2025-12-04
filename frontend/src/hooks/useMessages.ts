/**
 * useMessages Hook
 * 003-role-based-ui Feature - US6 (T122)
 *
 * Manages real-time messaging with WebSocket connection:
 * - Message fetching and caching
 * - Sending messages (optimistic updates)
 * - Typing indicators
 * - Read receipts
 * - Offline message handling
 * - Reconnection logic
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getMessages,
  sendMessage as sendMessageApi,
  markAsRead as markAsReadApi,
  buildWebSocketUrl,
} from '@/lib/api/messaging';
import type {
  Message,
  SendMessageRequest,
  WebSocketMessage,
  TypingPayload,
} from '@/types/message';
import { useAuth } from '@/contexts/AuthContext';

interface UseMessagesOptions {
  caseId: string;
  recipientId: string;
}

interface UseMessagesReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (request: SendMessageRequest) => Promise<void>;
  markAsRead: (messageIds: string[]) => Promise<void>;
  isTyping: boolean;
  sendTypingIndicator: (isTyping: boolean) => void;
  hasMore: boolean;
  loadMore: () => Promise<void>;
  isConnected: boolean;
  refetch: () => Promise<void>;
}

export function useMessages({ caseId, recipientId }: UseMessagesOptions): UseMessagesReturn {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch messages from API
  const fetchMessages = useCallback(async (beforeId?: string) => {
    if (!beforeId) {
      setIsLoading(true);
    }
    setError(null);

    const response = await getMessages(caseId, {
      other_user_id: recipientId,
      before_id: beforeId,
    });

    if (response.error) {
      setError(response.error);
      setIsLoading(false);
      return;
    }

    if (response.data) {
      if (beforeId) {
        // Prepend older messages
        setMessages((prev) => [...response.data!.messages, ...prev]);
      } else {
        setMessages(response.data.messages);
      }
      setHasMore(response.data.has_more);
    }
    setIsLoading(false);
  }, [caseId, recipientId]);

  // Connect to WebSocket
  const connectWebSocket = useCallback(async () => {
    if (typeof window === 'undefined') return;

    // Get token for WebSocket auth
    // Note: In production, this should call a dedicated endpoint for WS tokens
    // For now, we'll fetch from cookies or use a workaround
    try {
      const response = await fetch('/api/auth/ws-token', { credentials: 'include' });
      if (!response.ok) {
        console.warn('Could not get WebSocket token');
        return;
      }
      const { token } = await response.json();

      const wsUrl = buildWebSocketUrl(token);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected');
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');

        // Attempt reconnection
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 3000);
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('Failed to connect WebSocket:', e);
    }
  }, []);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((data: WebSocketMessage) => {
    switch (data.type) {
      case 'new_message': {
        const newMessage = data.payload as Message;
        // Only add if it's for the current conversation
        if (newMessage.case_id === caseId) {
          setMessages((prev) => {
            // Avoid duplicates
            if (prev.some((m) => m.id === newMessage.id)) {
              return prev;
            }
            return [...prev, newMessage];
          });
        }
        break;
      }

      case 'offline_messages': {
        const offlineData = data.payload as { messages: Message[] };
        const relevantMessages = offlineData.messages.filter(
          (m) => m.case_id === caseId
        );
        if (relevantMessages.length > 0) {
          setMessages((prev) => {
            const existingIds = new Set(prev.map((m) => m.id));
            const newMessages = relevantMessages.filter(
              (m) => !existingIds.has(m.id)
            );
            return [...prev, ...newMessages];
          });
        }
        break;
      }

      case 'typing': {
        const typingData = data.payload as TypingPayload;
        if (typingData.case_id === caseId && typingData.recipient_id !== user?.id) {
          setIsTyping(typingData.is_typing);
          // Clear typing indicator after 3 seconds
          if (typingData.is_typing) {
            if (typingTimeoutRef.current) {
              clearTimeout(typingTimeoutRef.current);
            }
            typingTimeoutRef.current = setTimeout(() => {
              setIsTyping(false);
            }, 3000);
          }
        }
        break;
      }

      case 'read_receipt': {
        const readData = data.payload as { message_ids: string[]; read_at: string };
        setMessages((prev) =>
          prev.map((m) =>
            readData.message_ids.includes(m.id)
              ? { ...m, read_at: readData.read_at }
              : m
          )
        );
        break;
      }

      case 'pong':
        // Keep-alive response, nothing to do
        break;

      case 'error':
        console.error('WebSocket error:', data.payload);
        break;

      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }, [caseId, user?.id]);

  // Send message
  const sendMessage = useCallback(async (request: SendMessageRequest) => {
    // Optimistic update
    const optimisticMessage: Message = {
      id: 'temp-' + Date.now(),
      case_id: request.case_id,
      sender: {
        id: user?.id || '',
        name: user?.name || '',
        role: user?.role || '',
      },
      recipient_id: request.recipient_id,
      content: request.content,
      attachments: request.attachments || null,
      read_at: null,
      created_at: new Date().toISOString(),
      is_mine: true,
    };

    setMessages((prev) => [...prev, optimisticMessage]);

    try {
      const response = await sendMessageApi(request);

      if (response.error) {
        // Rollback optimistic update
        setMessages((prev) => prev.filter((m) => m.id !== optimisticMessage.id));
        throw new Error(response.error);
      }

      if (response.data) {
        // Replace optimistic message with real one
        setMessages((prev) =>
          prev.map((m) =>
            m.id === optimisticMessage.id ? response.data! : m
          )
        );
      }
    } catch (e) {
      // Rollback optimistic update
      setMessages((prev) => prev.filter((m) => m.id !== optimisticMessage.id));
      throw e;
    }
  }, [user]);

  // Mark messages as read
  const markAsRead = useCallback(async (messageIds: string[]) => {
    await markAsReadApi(messageIds);

    // Also send via WebSocket for real-time update
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'read',
          payload: { message_ids: messageIds },
        })
      );
    }
  }, []);

  // Send typing indicator
  const sendTypingIndicator = useCallback((typing: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'typing',
          payload: {
            case_id: caseId,
            recipient_id: recipientId,
            is_typing: typing,
          },
        })
      );
    }
  }, [caseId, recipientId]);

  // Load more (older) messages
  const loadMore = useCallback(async () => {
    if (messages.length === 0) return;
    const oldestMessageId = messages[0].id;
    await fetchMessages(oldestMessageId);
  }, [messages, fetchMessages]);

  // Refetch messages
  const refetch = useCallback(async () => {
    await fetchMessages();
  }, [fetchMessages]);

  // Initialize
  useEffect(() => {
    fetchMessages();
    connectWebSocket();

    return () => {
      // Cleanup
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [fetchMessages, connectWebSocket]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    markAsRead,
    isTyping,
    sendTypingIndicator,
    hasMore,
    loadMore,
    isConnected,
    refetch,
  };
}

export default useMessages;

/**
 * useConversations Hook
 *
 * Fetches and manages conversation list.
 */
interface UseConversationsReturn {
  conversations: ConversationSummary[];
  totalUnread: number;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

interface ConversationSummary {
  id: string;
  case_id: string;
  case_title: string;
  other_user: {
    id: string;
    name: string;
    role: string;
  };
  last_message?: {
    content: string;
    created_at: string;
    is_mine: boolean;
  };
  unread_count: number;
}

export function useConversations(): UseConversationsReturn {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // For now, return mock data until API is ready
      // In production, this would call: await getConversations();
      const mockConversations: ConversationSummary[] = [];
      setConversations(mockConversations);
    } catch (e) {
      setError(e instanceof Error ? e.message : '대화 목록을 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const totalUnread = conversations.reduce((sum, c) => sum + c.unread_count, 0);

  return {
    conversations,
    totalUnread,
    isLoading,
    error,
    refresh: fetchConversations,
  };
}

// Re-export types
export type { ConversationSummary };
