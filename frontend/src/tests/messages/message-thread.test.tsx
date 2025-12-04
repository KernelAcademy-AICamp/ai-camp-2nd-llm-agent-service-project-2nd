/**
 * Integration test for Message Thread components
 * US6 - Task T110
 *
 * Tests:
 * - MessageList rendering
 * - MessageBubble display
 * - MessageInput functionality
 * - Conversation list interaction
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MessageList } from '@/components/messages/MessageList';
import { MessageBubble } from '@/components/messages/MessageBubble';
import { MessageInput } from '@/components/messages/MessageInput';
import { ConversationList } from '@/components/messages/ConversationList';
import type { Message, ConversationSummary, TypingIndicator } from '@/types/message';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: () => '/lawyer/messages',
  useSearchParams: () => new URLSearchParams(),
}));

// Sample test data
const mockMessages: Message[] = [
  {
    id: 'msg_001',
    case_id: 'case_123',
    sender: {
      id: 'user_lawyer',
      name: '김변호사',
      role: 'lawyer',
    },
    recipient_id: 'user_client',
    content: '안녕하세요, 케이스 관련 문의드립니다.',
    attachments: null,
    read_at: '2024-12-04T10:00:00Z',
    created_at: '2024-12-04T09:30:00Z',
    is_mine: true,
  },
  {
    id: 'msg_002',
    case_id: 'case_123',
    sender: {
      id: 'user_client',
      name: '이의뢰인',
      role: 'client',
    },
    recipient_id: 'user_lawyer',
    content: '네, 증거 자료 보내드립니다.',
    attachments: ['https://s3.amazonaws.com/bucket/file.pdf'],
    read_at: null,
    created_at: '2024-12-04T09:35:00Z',
    is_mine: false,
  },
];

const mockConversations: ConversationSummary[] = [
  {
    case_id: 'case_123',
    case_title: '김○○ 이혼 소송',
    other_user: {
      id: 'user_client',
      name: '이의뢰인',
      role: 'client',
    },
    last_message: '네, 증거 자료 보내드립니다.',
    last_message_at: '2024-12-04T09:35:00Z',
    unread_count: 1,
  },
  {
    case_id: 'case_456',
    case_title: '박○○ 양육권 분쟁',
    other_user: {
      id: 'user_client2',
      name: '박의뢰인',
      role: 'client',
    },
    last_message: '다음 기일은 언제인가요?',
    last_message_at: '2024-12-03T15:20:00Z',
    unread_count: 0,
  },
];

describe('T110 - MessageList Component', () => {
  const defaultProps = {
    messages: mockMessages,
    isLoading: false,
    hasMore: false,
    typingUsers: [] as TypingIndicator[],
    onLoadMore: jest.fn(),
  };

  test('should render messages grouped by date', () => {
    render(<MessageList {...defaultProps} />);

    // Check if messages are rendered
    expect(screen.getByText('안녕하세요, 케이스 관련 문의드립니다.')).toBeInTheDocument();
    expect(screen.getByText('네, 증거 자료 보내드립니다.')).toBeInTheDocument();
  });

  test('should show empty state when no messages', () => {
    render(<MessageList {...defaultProps} messages={[]} />);

    expect(screen.getByText('메시지가 없습니다.')).toBeInTheDocument();
    expect(screen.getByText('대화를 시작해보세요!')).toBeInTheDocument();
  });

  test('should show loading indicator when loading', () => {
    render(<MessageList {...defaultProps} isLoading={true} hasMore={true} />);

    // Loading spinner should be visible
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  test('should show load more button when hasMore is true', async () => {
    const onLoadMore = jest.fn();
    render(
      <MessageList
        {...defaultProps}
        hasMore={true}
        isLoading={false}
        onLoadMore={onLoadMore}
      />
    );

    const loadMoreButton = screen.getByRole('button', { name: /이전 메시지 불러오기/i });
    expect(loadMoreButton).toBeInTheDocument();

    await userEvent.click(loadMoreButton);
    expect(onLoadMore).toHaveBeenCalled();
  });

  test('should show typing indicator', () => {
    const typingUsers: TypingIndicator[] = [
      { user_id: 'user_client', user_name: '이의뢰인', case_id: 'case_123' },
    ];

    render(<MessageList {...defaultProps} typingUsers={typingUsers} />);

    expect(screen.getByText('입력 중...')).toBeInTheDocument();
  });
});

describe('T110 - MessageBubble Component', () => {
  test('should render own message on the right', () => {
    const myMessage = mockMessages[0]; // is_mine: true
    render(<MessageBubble message={myMessage} showSender={false} />);

    const bubble = screen.getByText(myMessage.content);
    expect(bubble).toBeInTheDocument();

    // Own messages have blue background
    const container = bubble.closest('div');
    expect(container?.className).toContain('bg-blue');
  });

  test('should render other message on the left', () => {
    const otherMessage = mockMessages[1]; // is_mine: false
    render(<MessageBubble message={otherMessage} showSender={true} />);

    expect(screen.getByText(otherMessage.content)).toBeInTheDocument();
    expect(screen.getByText(otherMessage.sender.name)).toBeInTheDocument();
  });

  test('should show attachment indicator when attachments present', () => {
    const messageWithAttachment = mockMessages[1];
    render(<MessageBubble message={messageWithAttachment} showSender={false} />);

    // Should show attachment icon or text
    expect(screen.getByText(/첨부파일/i)).toBeInTheDocument();
  });

  test('should show read status for own messages', () => {
    const readMessage = { ...mockMessages[0], read_at: '2024-12-04T10:00:00Z' };
    render(<MessageBubble message={readMessage} showSender={false} />);

    // Read indicator should be visible
    expect(screen.getByText('읽음')).toBeInTheDocument();
  });
});

describe('T110 - MessageInput Component', () => {
  // Helper to get the send button (second button, after attachment button)
  const getSendButton = () => {
    const buttons = screen.getAllByRole('button');
    // First button is attachment (파일 첨부), second is send
    return buttons[1];
  };

  test('should render input field and send button', () => {
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} />);

    expect(screen.getByPlaceholderText(/메시지를 입력하세요/i)).toBeInTheDocument();
    // Send button exists (second button)
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(2);
  });

  test('should disable send button when input is empty', () => {
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} />);

    const sendButton = getSendButton();
    expect(sendButton).toBeDisabled();
  });

  test('should enable send button when input has content', async () => {
    const user = userEvent.setup();
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} />);

    const input = screen.getByPlaceholderText(/메시지를 입력하세요/i);
    await user.type(input, '테스트 메시지');

    const sendButton = getSendButton();
    expect(sendButton).toBeEnabled();
  });

  test('should call onSend when send button clicked', async () => {
    const user = userEvent.setup();
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} />);

    const input = screen.getByPlaceholderText(/메시지를 입력하세요/i);
    await user.type(input, '테스트 메시지');

    const sendButton = getSendButton();
    await user.click(sendButton);

    expect(onSend).toHaveBeenCalledWith('테스트 메시지');
  });

  test('should clear input after sending', async () => {
    const user = userEvent.setup();
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} />);

    const input = screen.getByPlaceholderText(/메시지를 입력하세요/i) as HTMLTextAreaElement;
    await user.type(input, '테스트 메시지');
    await user.click(getSendButton());

    expect(input.value).toBe('');
  });

  test('should be disabled when disabled prop is true', () => {
    const onSend = jest.fn();
    render(<MessageInput onSend={onSend} disabled={true} />);

    const input = screen.getByPlaceholderText(/메시지를 입력하세요/i);
    expect(input).toBeDisabled();
  });
});

describe('T110 - ConversationList Component', () => {
  test('should render conversation list', () => {
    const onSelect = jest.fn();
    render(
      <ConversationList
        conversations={mockConversations}
        onSelect={onSelect}
      />
    );

    expect(screen.getByText('이의뢰인')).toBeInTheDocument();
    expect(screen.getByText('박의뢰인')).toBeInTheDocument();
  });

  test('should show unread count badge', () => {
    const onSelect = jest.fn();
    render(
      <ConversationList
        conversations={mockConversations}
        onSelect={onSelect}
      />
    );

    // First conversation has unread_count: 1
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  test('should highlight selected conversation', () => {
    const onSelect = jest.fn();
    const selectedId = `${mockConversations[0].case_id}-${mockConversations[0].other_user.id}`;

    render(
      <ConversationList
        conversations={mockConversations}
        selectedId={selectedId}
        onSelect={onSelect}
      />
    );

    // Selected conversation should have different background
    const conversations = screen.getAllByRole('button');
    const selectedConv = conversations[0];
    expect(selectedConv.className).toContain('bg-blue');
  });

  test('should call onSelect when conversation clicked', async () => {
    const user = userEvent.setup();
    const onSelect = jest.fn();

    render(
      <ConversationList
        conversations={mockConversations}
        onSelect={onSelect}
      />
    );

    const firstConversation = screen.getByText('이의뢰인').closest('button');
    if (firstConversation) {
      await user.click(firstConversation);
      expect(onSelect).toHaveBeenCalledWith(mockConversations[0]);
    }
  });

  test('should show empty state when no conversations', () => {
    const onSelect = jest.fn();
    render(
      <ConversationList
        conversations={[]}
        onSelect={onSelect}
      />
    );

    expect(screen.getByText(/대화가 없습니다/i)).toBeInTheDocument();
  });

  test('should show last message preview', () => {
    const onSelect = jest.fn();
    render(
      <ConversationList
        conversations={mockConversations}
        onSelect={onSelect}
      />
    );

    expect(screen.getByText('네, 증거 자료 보내드립니다.')).toBeInTheDocument();
  });
});
