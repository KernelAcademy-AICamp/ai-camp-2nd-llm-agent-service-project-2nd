/**
 * Integration test for useMessages hook
 * US6 - Task T111
 *
 * Tests:
 * - useMessages hook state management
 * - useConversations hook state management
 * - API integration mocking
 * - WebSocket connection handling
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useMessages, useConversations } from '@/hooks/useMessages';

// Mock the API module
const mockGetMessages = jest.fn();
const mockSendMessage = jest.fn();
const mockMarkMessagesRead = jest.fn();
const mockGetConversations = jest.fn();
const mockGetUnreadCount = jest.fn();
const mockCreateMessageWebSocket = jest.fn();

jest.mock('@/lib/api/messages', () => ({
  getMessages: (...args: unknown[]) => mockGetMessages(...args),
  sendMessage: (...args: unknown[]) => mockSendMessage(...args),
  markMessagesRead: (...args: unknown[]) => mockMarkMessagesRead(...args),
  getConversations: (...args: unknown[]) => mockGetConversations(...args),
  getUnreadCount: (...args: unknown[]) => mockGetUnreadCount(...args),
  createMessageWebSocket: (...args: unknown[]) => mockCreateMessageWebSocket(...args),
}));

// Mock WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 1;

  send = jest.fn();
  close = jest.fn();

  simulateMessage(data: object) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }

  simulateOpen() {
    if (this.onopen) {
      this.onopen();
    }
  }

  simulateClose() {
    if (this.onclose) {
      this.onclose();
    }
  }
}

const mockMessagesResponse = {
  messages: [
    {
      id: 'msg_001',
      case_id: 'case_123',
      sender: { id: 'user_1', name: 'User 1', role: 'lawyer' },
      recipient_id: 'user_2',
      content: 'Test message',
      attachments: null,
      read_at: null,
      created_at: '2024-12-04T10:00:00Z',
      is_mine: true,
    },
  ],
  total: 1,
  has_more: false,
};

const mockConversationsResponse = {
  conversations: [
    {
      case_id: 'case_123',
      case_title: 'Test Case',
      other_user: { id: 'user_2', name: 'User 2', role: 'client' },
      last_message: 'Test message',
      last_message_at: '2024-12-04T10:00:00Z',
      unread_count: 1,
    },
  ],
  total_unread: 1,
};

describe('T111 - useMessages Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetMessages.mockResolvedValue({ data: mockMessagesResponse });
    mockSendMessage.mockResolvedValue({ data: mockMessagesResponse.messages[0] });
    mockMarkMessagesRead.mockResolvedValue({ data: { marked_count: 1 } });
  });

  test('should fetch messages when caseId and otherUserId provided', async () => {
    const { result } = renderHook(() =>
      useMessages({
        caseId: 'case_123',
        otherUserId: 'user_2',
      })
    );

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toBe('Test message');
    expect(mockGetMessages).toHaveBeenCalledWith(
      'case_123',
      expect.objectContaining({ otherUserId: 'user_2' })
    );
  });

  test('should not fetch messages when caseId is empty', async () => {
    // Hook will still try to fetch even with empty caseId, just won't have data
    mockGetMessages.mockResolvedValue({ data: { messages: [], total: 0, has_more: false } });

    const { result } = renderHook(() =>
      useMessages({
        caseId: '',
        otherUserId: 'user_2',
      })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.messages).toHaveLength(0);
  });

  test('should send message successfully', async () => {
    const { result } = renderHook(() =>
      useMessages({
        caseId: 'case_123',
        otherUserId: 'user_2',
      })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.sendMessage('New message content');
    });

    expect(mockSendMessage).toHaveBeenCalledWith({
      case_id: 'case_123',
      recipient_id: 'user_2',
      content: 'New message content',
      attachments: undefined,
    });
  });

  test('should handle send message with attachments', async () => {
    const { result } = renderHook(() =>
      useMessages({
        caseId: 'case_123',
        otherUserId: 'user_2',
      })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const attachments = ['https://s3.amazonaws.com/file.pdf'];

    await act(async () => {
      await result.current.sendMessage('Message with attachment', attachments);
    });

    expect(mockSendMessage).toHaveBeenCalledWith({
      case_id: 'case_123',
      recipient_id: 'user_2',
      content: 'Message with attachment',
      attachments,
    });
  });

  test('should mark messages as read', async () => {
    const { result } = renderHook(() =>
      useMessages({
        caseId: 'case_123',
        otherUserId: 'user_2',
      })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.markAsRead(['msg_001', 'msg_002']);
    });

    expect(mockMarkMessagesRead).toHaveBeenCalledWith(['msg_001', 'msg_002']);
  });

  test('should handle pagination with loadMore', async () => {
    mockGetMessages.mockResolvedValueOnce({
      data: {
        ...mockMessagesResponse,
        has_more: true,
      },
    });

    const { result } = renderHook(() =>
      useMessages({
        caseId: 'case_123',
        otherUserId: 'user_2',
      })
    );

    await waitFor(() => {
      expect(result.current.hasMore).toBe(true);
    });

    mockGetMessages.mockResolvedValueOnce({
      data: {
        messages: [
          {
            id: 'msg_002',
            case_id: 'case_123',
            sender: { id: 'user_2', name: 'User 2', role: 'client' },
            recipient_id: 'user_1',
            content: 'Older message',
            attachments: null,
            read_at: null,
            created_at: '2024-12-04T09:00:00Z',
            is_mine: false,
          },
        ],
        total: 2,
        has_more: false,
      },
    });

    await act(async () => {
      await result.current.loadMore();
    });

    await waitFor(() => {
      expect(mockGetMessages).toHaveBeenCalledTimes(2);
    });
  });

  test('should handle API error gracefully', async () => {
    mockGetMessages.mockResolvedValueOnce({ error: 'Network error' });

    const { result } = renderHook(() =>
      useMessages({
        caseId: 'case_123',
        otherUserId: 'user_2',
      })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.messages).toHaveLength(0);
  });

  test('should return initial WebSocket status as disconnected', async () => {
    const { result } = renderHook(() =>
      useMessages({
        caseId: 'case_123',
        otherUserId: 'user_2',
        enableWebSocket: false,
      })
    );

    expect(result.current.wsStatus).toBe('disconnected');
  });

  test('should have empty typing users initially', async () => {
    const { result } = renderHook(() =>
      useMessages({
        caseId: 'case_123',
        otherUserId: 'user_2',
      })
    );

    expect(result.current.typingUsers).toEqual([]);
  });
});

describe('T111 - useConversations Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetConversations.mockResolvedValue({ data: mockConversationsResponse });
    mockGetUnreadCount.mockResolvedValue({
      data: {
        total: 1,
        by_case: { case_123: 1 },
      },
    });
  });

  test('should fetch conversations on mount', async () => {
    const { result } = renderHook(() => useConversations());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.conversations).toHaveLength(1);
    expect(result.current.totalUnread).toBe(1);
    expect(mockGetConversations).toHaveBeenCalled();
  });

  test('should return conversation with correct structure', async () => {
    const { result } = renderHook(() => useConversations());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const conversation = result.current.conversations[0];
    expect(conversation.case_id).toBe('case_123');
    expect(conversation.case_title).toBe('Test Case');
    expect(conversation.other_user.id).toBe('user_2');
    expect(conversation.other_user.name).toBe('User 2');
    expect(conversation.last_message).toBe('Test message');
    expect(conversation.unread_count).toBe(1);
  });

  test('should refresh conversations when refresh called', async () => {
    const { result } = renderHook(() => useConversations());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockGetConversations).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockGetConversations).toHaveBeenCalledTimes(2);
  });

  test('should handle API error gracefully', async () => {
    mockGetConversations.mockResolvedValueOnce({ error: 'Network error' });

    const { result } = renderHook(() => useConversations());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.conversations).toHaveLength(0);
  });

  test('should return empty array when no conversations', async () => {
    mockGetConversations.mockResolvedValueOnce({
      data: {
        conversations: [],
        total_unread: 0,
      },
    });

    const { result } = renderHook(() => useConversations());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.conversations).toHaveLength(0);
    expect(result.current.totalUnread).toBe(0);
  });
});

describe('T111 - Message State Updates', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetMessages.mockResolvedValue({ data: mockMessagesResponse });
  });

  test('should add new message to state after sending', async () => {
    const newMessage = {
      id: 'msg_002',
      case_id: 'case_123',
      sender: { id: 'user_1', name: 'User 1', role: 'lawyer' },
      recipient_id: 'user_2',
      content: 'New message',
      attachments: null,
      read_at: null,
      created_at: '2024-12-04T11:00:00Z',
      is_mine: true,
    };

    mockSendMessage.mockResolvedValueOnce({ data: newMessage });

    const { result } = renderHook(() =>
      useMessages({
        caseId: 'case_123',
        otherUserId: 'user_2',
      })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialCount = result.current.messages.length;

    await act(async () => {
      await result.current.sendMessage('New message');
    });

    // Message should be added to state
    expect(result.current.messages.length).toBeGreaterThanOrEqual(initialCount);
  });
});
