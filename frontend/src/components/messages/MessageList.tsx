/**
 * MessageList Component
 * 003-role-based-ui Feature - US6
 *
 * Displays a scrollable list of messages with auto-scroll and load more.
 */

'use client';

import { useRef, useEffect, useCallback } from 'react';
import type { Message, TypingIndicator } from '@/types/message';
import { MessageBubble } from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  hasMore: boolean;
  typingUsers: TypingIndicator[];
  onLoadMore: () => void;
  onMessagesViewed?: (messageIds: string[]) => void;
}

export function MessageList({
  messages,
  isLoading,
  hasMore,
  typingUsers,
  onLoadMore,
  onMessagesViewed,
}: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const prevMessagesLengthRef = useRef(messages.length);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > prevMessagesLengthRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    prevMessagesLengthRef.current = messages.length;
  }, [messages.length]);

  // Mark unread messages as read when they come into view
  useEffect(() => {
    if (!onMessagesViewed) return;

    const unreadMessages = messages.filter(
      (m) => !m.is_mine && !m.read_at
    );

    if (unreadMessages.length > 0) {
      onMessagesViewed(unreadMessages.map((m) => m.id));
    }
  }, [messages, onMessagesViewed]);

  // Infinite scroll for loading more messages
  const handleScroll = useCallback(() => {
    if (!containerRef.current || isLoading || !hasMore) return;

    const { scrollTop } = containerRef.current;

    // Load more when scrolled near top
    if (scrollTop < 100) {
      onLoadMore();
    }
  }, [isLoading, hasMore, onLoadMore]);

  // Group messages by date
  const groupedMessages = messages.reduce<{ date: string; messages: Message[] }[]>(
    (groups, message) => {
      const date = new Date(message.created_at).toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });

      const lastGroup = groups[groups.length - 1];

      if (lastGroup && lastGroup.date === date) {
        lastGroup.messages.push(message);
      } else {
        groups.push({ date, messages: [message] });
      }

      return groups;
    },
    []
  );

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto p-4 space-y-4"
    >
      {/* Loading indicator at top */}
      {isLoading && hasMore && (
        <div className="flex justify-center py-2">
          <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent" />
        </div>
      )}

      {/* Load more button */}
      {!isLoading && hasMore && (
        <div className="flex justify-center">
          <button
            onClick={onLoadMore}
            className="text-sm text-blue-600 hover:text-blue-800 py-2"
          >
            이전 메시지 불러오기
          </button>
        </div>
      )}

      {/* Empty state */}
      {messages.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
          <svg
            className="w-12 h-12 mb-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <p className="text-sm">메시지가 없습니다.</p>
          <p className="text-xs text-gray-400">대화를 시작해보세요!</p>
        </div>
      )}

      {/* Messages grouped by date */}
      {groupedMessages.map((group) => (
        <div key={group.date}>
          {/* Date separator */}
          <div className="flex items-center justify-center my-4">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="px-3 text-xs text-gray-400 bg-white">{group.date}</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          {/* Messages */}
          {group.messages.map((message, index) => {
            // Show sender name only if different from previous message
            const prevMessage = group.messages[index - 1];
            const showSender =
              !message.is_mine &&
              (!prevMessage || prevMessage.sender.id !== message.sender.id);

            return (
              <MessageBubble
                key={message.id}
                message={message}
                showSender={showSender}
              />
            );
          })}
        </div>
      ))}

      {/* Typing indicator */}
      {typingUsers.length > 0 && (
        <div className="flex items-center gap-2 text-gray-500 text-sm">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span>입력 중...</span>
        </div>
      )}

      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
}

export default MessageList;
