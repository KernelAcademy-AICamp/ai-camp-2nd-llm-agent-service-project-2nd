/**
 * ConversationList Component
 * 003-role-based-ui Feature - US6
 *
 * Displays list of conversations with preview and unread count.
 */

'use client';

import { useMemo } from 'react';
import type { ConversationSummary } from '@/types/message';

interface ConversationListProps {
  conversations: ConversationSummary[];
  selectedId?: string;
  onSelect: (conversation: ConversationSummary) => void;
}

export function ConversationList({
  conversations,
  selectedId,
  onSelect,
}: ConversationListProps) {
  const roleLabels: Record<string, string> = {
    lawyer: '변호사',
    client: '의뢰인',
    detective: '탐정',
    admin: '관리자',
    staff: '스태프',
  };

  const roleColors: Record<string, string> = {
    lawyer: 'bg-blue-100 text-blue-700',
    client: 'bg-green-100 text-green-700',
    detective: 'bg-purple-100 text-purple-700',
    admin: 'bg-red-100 text-red-700',
    staff: 'bg-gray-100 text-gray-700',
  };

  const formatTime = useMemo(
    () => (dateString: string) => {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return '방금';
      if (diffMins < 60) return `${diffMins}분 전`;
      if (diffHours < 24) return `${diffHours}시간 전`;
      if (diffDays < 7) return `${diffDays}일 전`;

      return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
    },
    []
  );

  if (conversations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-gray-500">
        <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <p className="text-sm font-medium">대화가 없습니다</p>
        <p className="text-xs text-gray-400 mt-1">케이스에서 메시지를 보내보세요</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-100">
      {conversations.map((conv) => {
        const convId = `${conv.case_id}-${conv.other_user.id}`;
        const isSelected = selectedId === convId;

        return (
          <button
            key={convId}
            type="button"
            onClick={() => onSelect(conv)}
            className={`w-full text-left p-4 hover:bg-gray-50 transition-colors ${
              isSelected ? 'bg-blue-50' : ''
            }`}
          >
            <div className="flex items-start gap-3">
              {/* Avatar */}
              <div className="relative flex-shrink-0">
                <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                  <span className="text-gray-600 font-medium text-sm">
                    {conv.other_user.name.charAt(0)}
                  </span>
                </div>
                {/* Unread badge */}
                {conv.unread_count > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-medium rounded-full flex items-center justify-center">
                    {conv.unread_count > 9 ? '9+' : conv.unread_count}
                  </span>
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 truncate">
                      {conv.other_user.name}
                    </span>
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded ${
                        roleColors[conv.other_user.role] || 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {roleLabels[conv.other_user.role] || conv.other_user.role}
                    </span>
                  </div>
                  <span className="text-xs text-gray-400 flex-shrink-0">
                    {formatTime(conv.last_message_at)}
                  </span>
                </div>

                <p className="text-xs text-gray-500 mb-1 truncate">{conv.case_title}</p>

                <p
                  className={`text-sm truncate ${
                    conv.unread_count > 0 ? 'text-gray-900 font-medium' : 'text-gray-500'
                  }`}
                >
                  {conv.last_message}
                </p>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

export default ConversationList;
