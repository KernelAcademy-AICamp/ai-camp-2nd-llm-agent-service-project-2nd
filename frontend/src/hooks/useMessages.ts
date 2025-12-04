/**
 * useMessages Hook
 * 003-role-based-ui Feature - US6
 *
 * Real-time messaging hook with WebSocket support.
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getMessages,
  getConversations,
  getUnreadCount,
  sendMessage as sendMessageApi,
  markMessagesRead,
  createMessageWebSocket,
  type WebSocketStatus,
} from '@/lib/api/messages';
import type {
  Message,
  ConversationSummary,
  TypingIndicator,
} from '@/types/message';

// ============== useConversations Hook ==============

export interface UseConversationsResult {
  conversations: ConversationSummary[];
  totalUnread: number;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useConversations(): UseConversationsResult {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [totalUnread, setTotalUnread] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await getConversations();

      if (response.error) {
        setError(response.error);
        return;
      }

      if (response.data) {
        setConversations(response.data.conversations);
        setTotalUnread(response.data.total_unread);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '대화 목록을 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  return {
    conversations,
    totalUnread,
    isLoading,
    error,
    refresh: fetchConversations,
  };
}

// ============== useUnreadCount Hook ==============

export interface UseUnreadCountResult {
  total: number;
  byCase: Record<string, number>;
  isLoading: boolean;
  refresh: () => Promise<void>;
}

export function useUnreadCount(): UseUnreadCountResult {
  const [total, setTotal] = useState(0);
  const [byCase, setByCase] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(true);

  const fetchUnreadCount = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await getUnreadCount();

      if (response.data) {
        setTotal(response.data.total);
        setByCase(response.data.by_case);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUnreadCount();
  }, [fetchUnreadCount]);

  return {
    total,
    byCase,
    isLoading,
    refresh: fetchUnreadCount,
  };
}

// ============== useMessages Hook (with WebSocket) ==============

export interface UseMessagesOptions {
  caseId: string;
  otherUserId?: string;
  token?: string;
  enableWebSocket?: boolean;
}

export interface UseMessagesResult {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  hasMore: boolean;
  wsStatus: WebSocketStatus;
  typingUsers: TypingIndicator[];
  sendMessage: (content: string, attachments?: string[]) => Promise<void>;
  loadMore: () => Promise<void>;
  markAsRead: (messageIds: string[]) => Promise<void>;
  sendTyping: (isTyping: boolean) => void;
}

export function useMessages({
  caseId,
  otherUserId,
  token,
  enableWebSocket = true,
}: UseMessagesOptions): UseMessagesResult {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [wsStatus, setWsStatus] = useState<WebSocketStatus>('disconnected');
  const [typingUsers, setTypingUsers] = useState<TypingIndicator[]>([]);

  const wsRef = useRef<ReturnType<typeof createMessageWebSocket> | null>(null);
  const typingTimeoutRef = useRef<Map<string, NodeJS.Timeout>>(new Map());

  // Fetch initial messages
  const fetchMessages = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await getMessages(caseId, { otherUserId, limit: 50 });

      if (response.error) {
        setError(response.error);
        return;
      }

      if (response.data) {
        setMessages(response.data.messages);
        setHasMore(response.data.has_more);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '메시지를 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [caseId, otherUserId]);

  // Load more messages (pagination)
  const loadMore = useCallback(async () => {
    if (!hasMore || isLoading || messages.length === 0) return;

    const oldestMessage = messages[0];
    const response = await getMessages(caseId, {
      otherUserId,
      limit: 50,
      beforeId: oldestMessage.id,
    });

    if (response.data) {
      setMessages((prev) => [...response.data!.messages, ...prev]);
      setHasMore(response.data.has_more);
    }
  }, [caseId, otherUserId, hasMore, isLoading, messages]);

  // Send message
  const sendMessage = useCallback(
    async (content: string, attachments?: string[]) => {
      if (!otherUserId) {
        throw new Error('Recipient ID is required');
      }

      // Use WebSocket if connected
      if (wsRef.current && wsStatus === 'connected') {
        wsRef.current.sendMessage(caseId, otherUserId, content, attachments);
      } else {
        // Fallback to REST API
        const response = await sendMessageApi({
          case_id: caseId,
          recipient_id: otherUserId,
          content,
          attachments,
        });

        if (response.error) {
          throw new Error(response.error);
        }

        if (response.data) {
          setMessages((prev) => [...prev, response.data!]);
        }
      }
    },
    [caseId, otherUserId, wsStatus]
  );

  // Mark messages as read
  const markAsRead = useCallback(
    async (messageIds: string[]) => {
      if (wsRef.current && wsStatus === 'connected') {
        wsRef.current.markRead(messageIds);
      } else {
        await markMessagesRead(messageIds);
      }

      // Update local state
      setMessages((prev) =>
        prev.map((msg) =>
          messageIds.includes(msg.id)
            ? { ...msg, read_at: new Date().toISOString() }
            : msg
        )
      );
    },
    [wsStatus]
  );

  // Send typing indicator
  const sendTyping = useCallback(
    (isTyping: boolean) => {
      if (wsRef.current && wsStatus === 'connected' && otherUserId) {
        wsRef.current.sendTyping(caseId, otherUserId, isTyping);
      }
    },
    [caseId, otherUserId, wsStatus]
  );

  // Handle typing indicator timeout
  const handleTyping = useCallback((data: { user_id: string; case_id: string; is_typing: boolean }) => {
    if (data.case_id !== caseId) return;

    const key = data.user_id;

    // Clear existing timeout
    const existingTimeout = typingTimeoutRef.current.get(key);
    if (existingTimeout) {
      clearTimeout(existingTimeout);
      typingTimeoutRef.current.delete(key);
    }

    if (data.is_typing) {
      // Add typing indicator
      setTypingUsers((prev) => {
        const existing = prev.find((t) => t.userId === data.user_id);
        if (existing) {
          return prev.map((t) =>
            t.userId === data.user_id ? { ...t, timestamp: Date.now() } : t
          );
        }
        return [...prev, { userId: data.user_id, caseId: data.case_id, timestamp: Date.now() }];
      });

      // Auto-remove after 3 seconds
      const timeout = setTimeout(() => {
        setTypingUsers((prev) => prev.filter((t) => t.userId !== data.user_id));
        typingTimeoutRef.current.delete(key);
      }, 3000);
      typingTimeoutRef.current.set(key, timeout);
    } else {
      // Remove typing indicator
      setTypingUsers((prev) => prev.filter((t) => t.userId !== data.user_id));
    }
  }, [caseId]);

  // Initialize WebSocket
  useEffect(() => {
    if (!enableWebSocket || !token) return;

    wsRef.current = createMessageWebSocket(token, {
      onMessage: (message) => {
        // Only add if it's for this conversation
        if (
          message.case_id === caseId &&
          (!otherUserId ||
            message.sender.id === otherUserId ||
            message.recipient_id === otherUserId)
        ) {
          setMessages((prev) => {
            // Avoid duplicates
            if (prev.some((m) => m.id === message.id)) {
              return prev;
            }
            return [...prev, message];
          });
        }
      },
      onTyping: handleTyping,
      onReadReceipt: (messageIds) => {
        setMessages((prev) =>
          prev.map((msg) =>
            messageIds.includes(msg.id)
              ? { ...msg, read_at: new Date().toISOString() }
              : msg
          )
        );
      },
      onOfflineMessages: (offlineMessages) => {
        // Merge offline messages
        setMessages((prev) => {
          const newMessages = offlineMessages.filter(
            (m) => m.case_id === caseId && !prev.some((pm) => pm.id === m.id)
          );
          if (newMessages.length === 0) return prev;
          return [...prev, ...newMessages].sort(
            (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          );
        });
      },
      onStatusChange: setWsStatus,
      onError: (err) => {
        console.error('WebSocket error:', err);
      },
    });

    return () => {
      wsRef.current?.close();
      wsRef.current = null;

      // Clear all typing timeouts
      typingTimeoutRef.current.forEach((timeout) => clearTimeout(timeout));
      typingTimeoutRef.current.clear();
    };
  }, [caseId, otherUserId, token, enableWebSocket, handleTyping]);

  // Fetch messages on mount
  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  return {
    messages,
    isLoading,
    error,
    hasMore,
    wsStatus,
    typingUsers,
    sendMessage,
    loadMore,
    markAsRead,
    sendTyping,
  };
}

export default useMessages;
