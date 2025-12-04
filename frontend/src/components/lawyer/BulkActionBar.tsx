'use client';

/**
 * BulkActionBar Component
 * 003-role-based-ui Feature - US3
 *
 * Action bar for bulk operations on selected cases.
 */

import { useState } from 'react';

interface BulkActionBarProps {
  selectedCount: number;
  onAction: (action: string, params?: Record<string, string>) => void;
  onClearSelection: () => void;
  isLoading?: boolean;
}

const bulkActions = [
  {
    id: 'request_ai_analysis',
    label: 'AI 분석 요청',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
  {
    id: 'change_status',
    label: '상태 변경',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
      </svg>
    ),
    hasSubmenu: true,
  },
  {
    id: 'export',
    label: '내보내기',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
    ),
  },
  {
    id: 'delete',
    label: '종료',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
    ),
    danger: true,
  },
];

const statusOptions = [
  { value: 'active', label: '활성' },
  { value: 'open', label: '진행 중' },
  { value: 'in_progress', label: '검토 대기' },
  { value: 'closed', label: '종료' },
];

export function BulkActionBar({
  selectedCount,
  onAction,
  onClearSelection,
  isLoading = false,
}: BulkActionBarProps) {
  const [showStatusMenu, setShowStatusMenu] = useState(false);

  if (selectedCount === 0) return null;

  const handleAction = (actionId: string) => {
    if (actionId === 'change_status') {
      setShowStatusMenu(!showStatusMenu);
    } else {
      onAction(actionId);
    }
  };

  const handleStatusChange = (newStatus: string) => {
    onAction('change_status', { new_status: newStatus });
    setShowStatusMenu(false);
  };

  return (
    <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
      <div className="bg-[var(--color-secondary)] text-white rounded-lg shadow-lg px-4 py-3 flex items-center gap-4">
        {/* Selection Count */}
        <div className="flex items-center gap-2">
          <span className="font-medium">{selectedCount}개 선택됨</span>
          <button
            type="button"
            onClick={onClearSelection}
            className="p-1 hover:bg-white/10 rounded"
            title="선택 해제"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Divider */}
        <div className="w-px h-6 bg-white/20" />

        {/* Actions */}
        <div className="flex items-center gap-1 relative">
          {bulkActions.map((action) => (
            <div key={action.id} className="relative">
              <button
                type="button"
                onClick={() => handleAction(action.id)}
                disabled={isLoading}
                className={`
                  flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors
                  ${action.danger
                    ? 'hover:bg-red-500/20 text-red-300'
                    : 'hover:bg-white/10'
                  }
                  ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                {action.icon}
                <span className="text-sm">{action.label}</span>
                {action.hasSubmenu && (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                )}
              </button>

              {/* Status Submenu */}
              {action.id === 'change_status' && showStatusMenu && (
                <div className="absolute bottom-full left-0 mb-2 bg-white rounded-lg shadow-lg py-1 min-w-[140px]">
                  {statusOptions.map((status) => (
                    <button
                      key={status.value}
                      type="button"
                      onClick={() => handleStatusChange(status.value)}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                    >
                      {status.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Loading Indicator */}
        {isLoading && (
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
        )}
      </div>
    </div>
  );
}

export default BulkActionBar;
