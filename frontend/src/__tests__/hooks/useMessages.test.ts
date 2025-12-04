/**
 * Integration tests for useMessages Hook
 * Task T111 - US6 Tests
 *
 * Tests for frontend/src/hooks/useMessages.ts:
 * - WebSocket connection management
 * - Message fetching and caching
 * - Sending messages (optimistic updates)
 * - Typing indicators
 * - Read receipts
 * - Offline message handling
 * - Reconnection logic
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import type { Message, MessageListResponse, WebSocketMessage } from '@/types/message';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  readyState: number = WebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  url: string;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    // Simulate connection
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send = jest.fn();
  close = jest.fn(() => {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  });

  // Test helper to simulate receiving a message
  simulateMessage(data: WebSocketMessage) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }

  // Test helper to simulate disconnection
  simulateDisconnect() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  static clearInstances() {
    MockWebSocket.instances = [];
  }
}

// Replace global WebSocket
const originalWebSocket = global.WebSocket;
beforeAll(() => {
  (global as unknown as { WebSocket: typeof MockWebSocket }).WebSocket = MockWebSocket as unknown as typeof WebSocket;
});
afterAll(() => {
  global.WebSocket = originalWebSocket;
});

// Mock the messaging API
const mockGetMessages = jest.fn();
const mockSendMessageApi = jest.fn();
const mockMarkAsReadApi = jest.fn();
const mockBuildWebSocketUrl = jest.fn().mockReturnValue('ws://localhost:8000/messages/ws?token=mock-jwt-token');

jest.mock('@/lib/api/messaging', () => ({
  getMessages: (...args: unknown[]) => mockGetMessages(...args),
  sendMessage: (...args: unknown[]) => mockSendMessageApi(...args),
  markAsRead: (...args: unknown[]) => mockMarkAsReadApi(...args),
  buildWebSocketUrl: (token: string) => mockBuildWebSocketUrl(token),
}));

// Mock fetch for WebSocket token
const mockFetch = jest.fn().mockResolvedValue({
  ok: true,
  json: () => Promise.resolve({ token: 'mock-jwt-token' }),
});
global.fetch = mockFetch;

// Mock auth context to get token
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    token: 'mock-jwt-token',
    user: { id: 'user-789', role: 'lawyer' },
  }),
}));

// Import hook after mocks
import { useMessages } from '@/hooks/useMessages';

describe('useMessages Hook', () => {
  const mockCaseId = 'case-123';
  const mockRecipientId = 'user-456';

  const mockMessageListResponse: MessageListResponse = {
    messages: [
      {
        id: 'msg-1',
        case_id: mockCaseId,
        sender: { id: 'user-456', name: '이의뢰인', role: 'client' },
        recipient_id: 'user-789',
        content: '안녕하세요',
        attachments: null,
        read_at: null,
        created_at: '2024-12-05T09:00:00Z',
        is_mine: false,
      },
    ],
    total: 1,
    has_more: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    MockWebSocket.clearInstances();

    // Reset fetch mock for WebSocket token
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ token: 'mock-jwt-token' }),
    });

    mockGetMessages.mockResolvedValue({
      data: mockMessageListResponse,
      error: null,
    });

    mockSendMessageApi.mockResolvedValue({
      data: {
        id: 'msg-new',
        case_id: mockCaseId,
        sender: { id: 'user-789', name: '김변호사', role: 'lawyer' },
        recipient_id: mockRecipientId,
        content: '테스트 메시지',
        attachments: null,
        read_at: null,
        created_at: new Date().toISOString(),
        is_mine: true,
      },
      error: null,
    });

    mockMarkAsReadApi.mockResolvedValue({
      data: { marked_count: 1 },
      error: null,
    });
  });

  describe('Initialization', () => {
    test('should return initial state', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      expect(result.current.messages).toEqual([]);
      expect(result.current.isLoading).toBe(true);
      expect(result.current.error).toBeNull();
      expect(result.current.isConnected).toBe(false);
    });

    test('should fetch messages on mount', async () => {
      renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(mockGetMessages).toHaveBeenCalledWith(mockCaseId, {
          other_user_id: mockRecipientId,
        });
      });
    });

    test('should update messages after fetch', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.messages).toHaveLength(1);
        expect(result.current.messages[0].content).toBe('안녕하세요');
      });
    });

    test('should set isLoading to false after fetch', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });
  });

  describe('WebSocket Connection', () => {
    test('should establish WebSocket connection', async () => {
      renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(MockWebSocket.instances.length).toBeGreaterThan(0);
      });

      const wsInstance = MockWebSocket.instances[0];
      expect(wsInstance.url).toContain('/messages/ws');
      expect(wsInstance.url).toContain('token=mock-jwt-token');
    });

    test('should set isConnected to true when WebSocket opens', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });
    });

    test('should set isConnected to false when WebSocket closes', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      // Simulate disconnect
      act(() => {
        MockWebSocket.instances[0].simulateDisconnect();
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(false);
      });
    });

    test('should attempt reconnection on disconnect', async () => {
      jest.useFakeTimers();

      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const initialInstanceCount = MockWebSocket.instances.length;

      // Simulate disconnect
      act(() => {
        MockWebSocket.instances[0].simulateDisconnect();
      });

      // Fast-forward reconnection timer
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(MockWebSocket.instances.length).toBeGreaterThan(initialInstanceCount);
      });

      jest.useRealTimers();
    });
  });

  describe('Receiving Messages', () => {
    test('should add new message when received via WebSocket', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const newMessage: Message = {
        id: 'msg-2',
        case_id: mockCaseId,
        sender: { id: 'user-456', name: '이의뢰인', role: 'client' },
        recipient_id: 'user-789',
        content: '새 메시지입니다',
        attachments: null,
        read_at: null,
        created_at: new Date().toISOString(),
        is_mine: false,
      };

      // Simulate receiving new message via WebSocket
      act(() => {
        MockWebSocket.instances[0].simulateMessage({
          type: 'new_message',
          payload: newMessage,
        });
      });

      await waitFor(() => {
        expect(result.current.messages).toContainEqual(
          expect.objectContaining({ id: 'msg-2', content: '새 메시지입니다' })
        );
      });
    });

    test('should handle offline_messages on connect', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const offlineMessages: Message[] = [
        {
          id: 'msg-offline-1',
          case_id: mockCaseId,
          sender: { id: 'user-456', name: '이의뢰인', role: 'client' },
          recipient_id: 'user-789',
          content: '오프라인 메시지',
          attachments: null,
          read_at: null,
          created_at: new Date().toISOString(),
          is_mine: false,
        },
      ];

      // Simulate receiving offline messages
      act(() => {
        MockWebSocket.instances[0].simulateMessage({
          type: 'offline_messages',
          payload: { messages: offlineMessages },
        });
      });

      await waitFor(() => {
        expect(result.current.messages).toContainEqual(
          expect.objectContaining({ id: 'msg-offline-1' })
        );
      });
    });
  });

  describe('Sending Messages', () => {
    test('should call sendMessage function', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.sendMessage({
          case_id: mockCaseId,
          recipient_id: mockRecipientId,
          content: '테스트 메시지',
        });
      });

      expect(mockSendMessageApi).toHaveBeenCalledWith({
        case_id: mockCaseId,
        recipient_id: mockRecipientId,
        content: '테스트 메시지',
      });
    });

    test('should add message optimistically before API response', async () => {
      // Delay API response
      mockSendMessageApi.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  data: {
                    id: 'msg-new',
                    case_id: mockCaseId,
                    sender: { id: 'user-789', name: '김변호사', role: 'lawyer' },
                    recipient_id: mockRecipientId,
                    content: '테스트 메시지',
                    attachments: null,
                    read_at: null,
                    created_at: new Date().toISOString(),
                    is_mine: true,
                  },
                  error: null,
                }),
              100
            )
          )
      );

      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Don't await - check optimistic update
      act(() => {
        result.current.sendMessage({
          case_id: mockCaseId,
          recipient_id: mockRecipientId,
          content: '테스트 메시지',
        });
      });

      // Message should appear immediately (optimistic)
      expect(result.current.messages).toContainEqual(
        expect.objectContaining({ content: '테스트 메시지' })
      );
    });

    test('should rollback on send failure', async () => {
      mockSendMessageApi.mockResolvedValue({
        data: null,
        error: '전송 실패',
      });

      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        try {
          await result.current.sendMessage({
            case_id: mockCaseId,
            recipient_id: mockRecipientId,
            content: '실패할 메시지',
          });
        } catch {
          // Expected to fail
        }
      });

      // Optimistically added message should be removed
      await waitFor(() => {
        expect(result.current.messages).not.toContainEqual(
          expect.objectContaining({ content: '실패할 메시지' })
        );
      });
    });
  });

  describe('Typing Indicators', () => {
    test('should send typing indicator via WebSocket', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      act(() => {
        result.current.sendTypingIndicator(true);
      });

      expect(MockWebSocket.instances[0].send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"typing"')
      );
    });

    test('should set isTyping when typing indicator received', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      expect(result.current.isTyping).toBe(false);

      // Simulate receiving typing indicator
      act(() => {
        MockWebSocket.instances[0].simulateMessage({
          type: 'typing',
          payload: {
            user_id: mockRecipientId,
            case_id: mockCaseId,
            is_typing: true,
          },
        });
      });

      await waitFor(() => {
        expect(result.current.isTyping).toBe(true);
      });
    });

    test('should clear isTyping when typing stops', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      // Start typing
      act(() => {
        MockWebSocket.instances[0].simulateMessage({
          type: 'typing',
          payload: {
            user_id: mockRecipientId,
            case_id: mockCaseId,
            is_typing: true,
          },
        });
      });

      await waitFor(() => {
        expect(result.current.isTyping).toBe(true);
      });

      // Stop typing
      act(() => {
        MockWebSocket.instances[0].simulateMessage({
          type: 'typing',
          payload: {
            user_id: mockRecipientId,
            case_id: mockCaseId,
            is_typing: false,
          },
        });
      });

      await waitFor(() => {
        expect(result.current.isTyping).toBe(false);
      });
    });
  });

  describe('Read Receipts', () => {
    test('should call markAsRead function', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.markAsRead(['msg-1']);
      });

      expect(mockMarkAsReadApi).toHaveBeenCalledWith(['msg-1']);
    });

    test('should update message read_at when read receipt received', async () => {
      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.messages).toHaveLength(1);
      });

      expect(result.current.messages[0].read_at).toBeNull();

      // Simulate receiving read receipt
      act(() => {
        MockWebSocket.instances[0].simulateMessage({
          type: 'read_receipt',
          payload: {
            message_ids: ['msg-1'],
            read_at: '2024-12-05T10:00:00Z',
          },
        });
      });

      await waitFor(() => {
        expect(result.current.messages[0].read_at).toBe('2024-12-05T10:00:00Z');
      });
    });
  });

  describe('Pagination', () => {
    test('should return hasMore from API response', async () => {
      mockGetMessages.mockResolvedValue({
        data: {
          ...mockMessageListResponse,
          has_more: true,
        },
        error: null,
      });

      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.hasMore).toBe(true);
      });
    });

    test('should call loadMore with correct parameters', async () => {
      mockGetMessages.mockResolvedValue({
        data: {
          ...mockMessageListResponse,
          has_more: true,
        },
        error: null,
      });

      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.loadMore();
      });

      // Should call with before_id of oldest message
      expect(mockGetMessages).toHaveBeenLastCalledWith(
        mockCaseId,
        expect.objectContaining({
          before_id: 'msg-1',
        })
      );
    });

    test('should append older messages to list', async () => {
      const olderMessages: Message[] = [
        {
          id: 'msg-0',
          case_id: mockCaseId,
          sender: { id: 'user-456', name: '이의뢰인', role: 'client' },
          recipient_id: 'user-789',
          content: '이전 메시지',
          attachments: null,
          read_at: null,
          created_at: '2024-12-05T08:00:00Z',
          is_mine: false,
        },
      ];

      mockGetMessages
        .mockResolvedValueOnce({
          data: { ...mockMessageListResponse, has_more: true },
          error: null,
        })
        .mockResolvedValueOnce({
          data: { messages: olderMessages, total: 2, has_more: false },
          error: null,
        });

      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.messages).toHaveLength(1);
      });

      await act(async () => {
        await result.current.loadMore();
      });

      await waitFor(() => {
        expect(result.current.messages).toHaveLength(2);
        // Older messages should be prepended
        expect(result.current.messages[0].id).toBe('msg-0');
      });
    });
  });

  describe('Error Handling', () => {
    test('should set error when fetch fails', async () => {
      mockGetMessages.mockResolvedValue({
        data: null,
        error: '메시지를 불러오는데 실패했습니다.',
      });

      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.error).toBe('메시지를 불러오는데 실패했습니다.');
      });
    });

    test('should clear error on retry', async () => {
      mockGetMessages
        .mockResolvedValueOnce({
          data: null,
          error: '에러',
        })
        .mockResolvedValueOnce({
          data: mockMessageListResponse,
          error: null,
        });

      const { result } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.error).toBe('에러');
      });

      // Trigger refetch
      await act(async () => {
        await result.current.refetch();
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });
    });
  });

  describe('Cleanup', () => {
    test('should close WebSocket on unmount', async () => {
      const { result, unmount } = renderHook(() =>
        useMessages({ caseId: mockCaseId, recipientId: mockRecipientId })
      );

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });

      const wsInstance = MockWebSocket.instances[0];

      unmount();

      expect(wsInstance.close).toHaveBeenCalled();
    });
  });
});
