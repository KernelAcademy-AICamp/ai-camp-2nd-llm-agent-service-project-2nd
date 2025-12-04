/**
 * Integration tests for MessageThread Component
 * Task T110 - US6 Tests
 *
 * Tests for frontend/src/components/shared/MessageThread.tsx:
 * - Message list rendering
 * - Real-time message updates
 * - Sending messages
 * - Typing indicators
 * - Read receipts
 * - Scroll behavior
 * - Error handling
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { Message, MessageSender } from '@/types/message';

// Mock scrollIntoView for JSDOM
beforeAll(() => {
  window.HTMLElement.prototype.scrollIntoView = jest.fn();
});

// Mock the messaging API
const mockGetMessages = jest.fn();
const mockSendMessage = jest.fn();
const mockMarkAsRead = jest.fn();

jest.mock('@/lib/api/messaging', () => ({
  getMessages: (...args: unknown[]) => mockGetMessages(...args),
  sendMessage: (...args: unknown[]) => mockSendMessage(...args),
  markAsRead: (...args: unknown[]) => mockMarkAsRead(...args),
}));

// Mock the useMessages hook
const mockUseMessages = jest.fn();
jest.mock('@/hooks/useMessages', () => ({
  useMessages: (...args: unknown[]) => mockUseMessages(...args),
}));

// Import component after mocks
import MessageThread from '@/components/shared/MessageThread';

describe('MessageThread Component', () => {
  const mockCaseId = 'case-123';
  const mockRecipientId = 'user-456';
  const mockCurrentUserId = 'user-789';

  const mockSender: MessageSender = {
    id: 'user-789',
    name: '김변호사',
    role: 'lawyer',
  };

  const mockRecipient: MessageSender = {
    id: 'user-456',
    name: '이의뢰인',
    role: 'client',
  };

  const mockMessages: Message[] = [
    {
      id: 'msg-1',
      case_id: mockCaseId,
      sender: mockRecipient,
      recipient_id: mockCurrentUserId,
      content: '안녕하세요, 사건 진행 상황이 궁금합니다.',
      attachments: null,
      read_at: '2024-12-05T10:00:00Z',
      created_at: '2024-12-05T09:00:00Z',
      is_mine: false,
    },
    {
      id: 'msg-2',
      case_id: mockCaseId,
      sender: mockSender,
      recipient_id: mockRecipientId,
      content: '네, 현재 증거 분석 중입니다. 내일까지 결과 알려드리겠습니다.',
      attachments: null,
      read_at: '2024-12-05T10:00:00Z',
      created_at: '2024-12-05T09:30:00Z',
      is_mine: true,
    },
  ];

  const defaultHookReturn = {
    messages: mockMessages,
    isLoading: false,
    error: null,
    sendMessage: jest.fn(),
    markAsRead: jest.fn(),
    isTyping: false,
    sendTypingIndicator: jest.fn(),
    hasMore: false,
    loadMore: jest.fn(),
    isConnected: true,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseMessages.mockReturnValue(defaultHookReturn);
  });

  describe('Initial Rendering', () => {
    test('should render message thread container', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByTestId('message-thread')).toBeInTheDocument();
    });

    test('should render message list', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByTestId('message-list')).toBeInTheDocument();
    });

    test('should render message input area', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByPlaceholderText('메시지를 입력하세요...')).toBeInTheDocument();
    });

    test('should render send button', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByRole('button', { name: /전송|보내기/i })).toBeInTheDocument();
    });
  });

  describe('Message Display', () => {
    test('should display all messages', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByText('안녕하세요, 사건 진행 상황이 궁금합니다.')).toBeInTheDocument();
      expect(screen.getByText(/현재 증거 분석 중입니다/)).toBeInTheDocument();
    });

    test('should display sender name for each message', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByText('이의뢰인')).toBeInTheDocument();
    });

    test('should distinguish own messages from others', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      const ownMessage = screen.getByText(/현재 증거 분석 중입니다/).closest('[data-testid="message-item"]');
      expect(ownMessage).toHaveAttribute('data-is-mine', 'true');
    });

    test('should display message timestamp', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      // Should show time in some format (various locales/timezones)
      // The component uses toLocaleTimeString with 'ko-KR' locale
      // Match any time pattern like "오전 9:00", "오후 6:30", "09:00", "18:00"
      const timePattern = /\d{1,2}:\d{2}|오전|오후/;
      const timeElements = screen.getAllByText(timePattern);
      expect(timeElements.length).toBeGreaterThan(0);
    });

    test('should show read receipt for read messages', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      // Own message (msg-2) with read_at should show read indicator
      const readIndicator = screen.getByTestId('read-receipt-msg-2');
      expect(readIndicator).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    test('should show loading spinner when loading', () => {
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        isLoading: true,
        messages: [],
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    test('should show empty state when no messages', () => {
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        messages: [],
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByText(/메시지가 없습니다|대화를 시작하세요/)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('should display error message when error occurs', () => {
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        error: '메시지를 불러오는데 실패했습니다.',
        messages: [],
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByText('메시지를 불러오는데 실패했습니다.')).toBeInTheDocument();
    });

    test('should show retry button on error', () => {
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        error: '메시지를 불러오는데 실패했습니다.',
        messages: [],
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByRole('button', { name: /다시 시도|재시도/i })).toBeInTheDocument();
    });
  });

  describe('Sending Messages', () => {
    test('should enable send button when input has text', async () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      const input = screen.getByPlaceholderText('메시지를 입력하세요...');
      const sendButton = screen.getByRole('button', { name: /전송|보내기/i });

      expect(sendButton).toBeDisabled();

      await userEvent.type(input, '테스트 메시지');

      expect(sendButton).not.toBeDisabled();
    });

    test('should call sendMessage when send button is clicked', async () => {
      const mockSendFn = jest.fn().mockResolvedValue({ success: true });
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        sendMessage: mockSendFn,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      const input = screen.getByPlaceholderText('메시지를 입력하세요...');
      await userEvent.type(input, '테스트 메시지');

      const sendButton = screen.getByRole('button', { name: /전송|보내기/i });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(mockSendFn).toHaveBeenCalledWith({
          case_id: mockCaseId,
          recipient_id: mockRecipientId,
          content: '테스트 메시지',
        });
      });
    });

    test('should clear input after sending message', async () => {
      const mockSendFn = jest.fn().mockResolvedValue({ success: true });
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        sendMessage: mockSendFn,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      const input = screen.getByPlaceholderText('메시지를 입력하세요...');
      await userEvent.type(input, '테스트 메시지');

      const sendButton = screen.getByRole('button', { name: /전송|보내기/i });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(input).toHaveValue('');
      });
    });

    test('should send message on Enter key press', async () => {
      const mockSendFn = jest.fn().mockResolvedValue({ success: true });
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        sendMessage: mockSendFn,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      const input = screen.getByPlaceholderText('메시지를 입력하세요...');
      await userEvent.type(input, '테스트 메시지{Enter}');

      await waitFor(() => {
        expect(mockSendFn).toHaveBeenCalled();
      });
    });

    test('should not send on Shift+Enter (allows newline)', async () => {
      const mockSendFn = jest.fn().mockResolvedValue({ success: true });
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        sendMessage: mockSendFn,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      const input = screen.getByPlaceholderText('메시지를 입력하세요...');
      await userEvent.type(input, '테스트 메시지{Shift>}{Enter}{/Shift}');

      expect(mockSendFn).not.toHaveBeenCalled();
    });
  });

  describe('Typing Indicators', () => {
    test('should show typing indicator when other user is typing', () => {
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        isTyping: true,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByTestId('typing-indicator')).toBeInTheDocument();
    });

    test('should send typing indicator when user starts typing', async () => {
      const mockTypingFn = jest.fn();
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        sendTypingIndicator: mockTypingFn,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      const input = screen.getByPlaceholderText('메시지를 입력하세요...');
      await userEvent.type(input, '입');

      await waitFor(() => {
        expect(mockTypingFn).toHaveBeenCalledWith(true);
      });
    });
  });

  describe('Pagination / Load More', () => {
    test('should show load more button when hasMore is true', () => {
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        hasMore: true,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByRole('button', { name: /이전 메시지|더 보기/i })).toBeInTheDocument();
    });

    test('should call loadMore when load more button is clicked', async () => {
      const mockLoadMoreFn = jest.fn();
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        hasMore: true,
        loadMore: mockLoadMoreFn,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      const loadMoreButton = screen.getByRole('button', { name: /이전 메시지|더 보기/i });
      fireEvent.click(loadMoreButton);

      expect(mockLoadMoreFn).toHaveBeenCalled();
    });

    test('should not show load more button when hasMore is false', () => {
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        hasMore: false,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.queryByRole('button', { name: /이전 메시지|더 보기/i })).not.toBeInTheDocument();
    });
  });

  describe('Connection Status', () => {
    test('should show connection indicator when connected', () => {
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        isConnected: true,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByTestId('connection-status')).toHaveAttribute('data-connected', 'true');
    });

    test('should show disconnected state when not connected', () => {
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        isConnected: false,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByTestId('connection-status')).toHaveAttribute('data-connected', 'false');
    });

    test('should show reconnecting message when disconnected', () => {
      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        isConnected: false,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByText(/연결 중|재연결/)).toBeInTheDocument();
    });
  });

  describe('Attachments', () => {
    test('should show attachment preview when message has attachments', () => {
      const messagesWithAttachment: Message[] = [
        {
          id: 'msg-3',
          case_id: mockCaseId,
          sender: mockSender,
          recipient_id: mockRecipientId,
          content: '증거 파일입니다.',
          attachments: ['https://s3.amazonaws.com/bucket/file.pdf'],
          read_at: null,
          created_at: '2024-12-05T10:00:00Z',
          is_mine: true,
        },
      ];

      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        messages: messagesWithAttachment,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByTestId('attachment-preview')).toBeInTheDocument();
    });

    test('should render attachment icon for file attachment', () => {
      const messagesWithAttachment: Message[] = [
        {
          id: 'msg-3',
          case_id: mockCaseId,
          sender: mockSender,
          recipient_id: mockRecipientId,
          content: '증거 파일입니다.',
          attachments: ['https://s3.amazonaws.com/bucket/file.pdf'],
          read_at: null,
          created_at: '2024-12-05T10:00:00Z',
          is_mine: true,
        },
      ];

      mockUseMessages.mockReturnValue({
        ...defaultHookReturn,
        messages: messagesWithAttachment,
      });

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      expect(screen.getByLabelText(/첨부파일|attachment/i)).toBeInTheDocument();
    });
  });

  describe('Scroll Behavior', () => {
    test('should scroll to bottom on new message', async () => {
      const scrollIntoViewMock = jest.fn();
      window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      // Verify scrollIntoView was called (for auto-scroll to latest message)
      expect(scrollIntoViewMock).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    test('should have aria-label on message input', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      const input = screen.getByPlaceholderText('메시지를 입력하세요...');
      expect(input).toHaveAttribute('aria-label', expect.stringMatching(/메시지|message/i));
    });

    test('should have role="log" on message list', () => {
      render(
        <MessageThread
          caseId={mockCaseId}
          recipientId={mockRecipientId}
          currentUserId={mockCurrentUserId}
        />
      );

      const messageList = screen.getByTestId('message-list');
      expect(messageList).toHaveAttribute('role', 'log');
    });
  });
});
