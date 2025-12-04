/**
 * MessageBubble Component
 * 003-role-based-ui Feature - US6
 *
 * Displays a single message in chat bubble format.
 */

'use client';

import { useMemo } from 'react';
import type { Message } from '@/types/message';

interface MessageBubbleProps {
  message: Message;
  showSender?: boolean;
}

export function MessageBubble({ message, showSender = true }: MessageBubbleProps) {
  const formattedTime = useMemo(() => {
    const date = new Date(message.created_at);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday) {
      return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    }

    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const isYesterday = date.toDateString() === yesterday.toDateString();

    if (isYesterday) {
      return `어제 ${date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;
    }

    return date.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }, [message.created_at]);

  const roleColors: Record<string, string> = {
    lawyer: 'text-blue-600',
    client: 'text-green-600',
    detective: 'text-purple-600',
    admin: 'text-red-600',
    staff: 'text-gray-600',
  };

  return (
    <div
      className={`flex ${message.is_mine ? 'justify-end' : 'justify-start'} mb-3`}
    >
      <div
        className={`max-w-[70%] ${
          message.is_mine
            ? 'bg-blue-500 text-white rounded-tl-2xl rounded-tr-sm rounded-bl-2xl rounded-br-2xl'
            : 'bg-gray-100 text-gray-900 rounded-tl-sm rounded-tr-2xl rounded-bl-2xl rounded-br-2xl'
        } px-4 py-2 shadow-sm`}
      >
        {/* Sender name (for received messages) */}
        {!message.is_mine && showSender && (
          <p
            className={`text-xs font-medium mb-1 ${
              roleColors[message.sender.role] || 'text-gray-500'
            }`}
          >
            {message.sender.name}
          </p>
        )}

        {/* Message content */}
        <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>

        {/* Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-2 space-y-1">
            {message.attachments.map((url, index) => (
              <a
                key={index}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className={`flex items-center gap-1 text-xs ${
                  message.is_mine
                    ? 'text-blue-100 hover:text-white'
                    : 'text-blue-600 hover:text-blue-800'
                } underline`}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                  />
                </svg>
                첨부파일 {index + 1}
              </a>
            ))}
          </div>
        )}

        {/* Time and read status */}
        <div
          className={`flex items-center gap-1 mt-1 ${
            message.is_mine ? 'justify-end' : 'justify-start'
          }`}
        >
          <span
            className={`text-xs ${
              message.is_mine ? 'text-blue-100' : 'text-gray-400'
            }`}
          >
            {formattedTime}
          </span>

          {/* Read indicator (only for sent messages) */}
          {message.is_mine && (
            <span className={`text-xs ${message.read_at ? 'text-blue-100' : 'text-blue-200'}`}>
              {message.read_at ? '읽음' : ''}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;
