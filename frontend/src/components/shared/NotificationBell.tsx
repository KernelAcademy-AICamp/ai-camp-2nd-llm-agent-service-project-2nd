/**
 * Notification Bell Component
 * 003-role-based-ui Feature - T157
 *
 * A notification bell component with dropdown and real-time updates.
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { EmptyNotifications } from './EmptyStates';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  created_at: string;
  link?: string;
}

export interface NotificationBellProps {
  notifications: Notification[];
  unreadCount?: number;
  onNotificationClick?: (notification: Notification) => void;
  onMarkAllRead?: () => void;
  onClearAll?: () => void;
  isLoading?: boolean;
}

// Format relative time in Korean
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / (1000 * 60));
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (minutes < 1) return '방금 전';
  if (minutes < 60) return `${minutes}분 전`;
  if (hours < 24) return `${hours}시간 전`;
  if (days < 7) return `${days}일 전`;
  return date.toLocaleDateString('ko-KR');
}

// Notification type icon
function NotificationIcon({ type }: { type: Notification['type'] }) {
  const iconStyles = {
    info: 'bg-blue-100 text-blue-600',
    success: 'bg-green-100 text-green-600',
    warning: 'bg-yellow-100 text-yellow-600',
    error: 'bg-red-100 text-red-600',
  };

  const icons = {
    info: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    success: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    warning: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    error: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  };

  return (
    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${iconStyles[type]}`}>
      {icons[type]}
    </div>
  );
}

// Single notification item
function NotificationItem({
  notification,
  onClick,
}: {
  notification: Notification;
  onClick?: () => void;
}) {
  return (
    <div
      className={`p-3 hover:bg-gray-50 cursor-pointer transition-colors ${
        !notification.read ? 'bg-blue-50/50' : ''
      }`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
    >
      <div className="flex gap-3">
        <NotificationIcon type={notification.type} />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={`text-sm ${!notification.read ? 'font-semibold' : ''} text-gray-900 truncate`}>
              {notification.title}
            </p>
            {!notification.read && (
              <span className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0 mt-1.5" />
            )}
          </div>
          <p className="text-xs text-gray-500 line-clamp-2 mt-0.5">
            {notification.message}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {formatRelativeTime(notification.created_at)}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function NotificationBell({
  notifications,
  unreadCount,
  onNotificationClick,
  onMarkAllRead,
  onClearAll,
  isLoading = false,
}: NotificationBellProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const displayUnreadCount = unreadCount ?? notifications.filter((n) => !n.read).length;

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen]);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
        aria-label={`알림 ${displayUnreadCount > 0 ? `(${displayUnreadCount}개 읽지 않음)` : ''}`}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>

        {/* Unread Badge */}
        {displayUnreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {displayUnreadCount > 9 ? '9+' : displayUnreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden z-50">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">알림</h3>
            {displayUnreadCount > 0 && onMarkAllRead && (
              <button
                onClick={onMarkAllRead}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                모두 읽음
              </button>
            )}
          </div>

          {/* Notification List */}
          <div className="max-h-[400px] overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center text-gray-500">
                <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto" />
                <p className="mt-2 text-sm">불러오는 중...</p>
              </div>
            ) : notifications.length > 0 ? (
              <div className="divide-y divide-gray-100">
                {notifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onClick={() => {
                      onNotificationClick?.(notification);
                      if (notification.link) {
                        window.location.href = notification.link;
                      }
                    }}
                  />
                ))}
              </div>
            ) : (
              <EmptyNotifications />
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-3 border-t border-gray-200 flex justify-between">
              <button
                onClick={() => {
                  setIsOpen(false);
                  window.location.href = '/notifications';
                }}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                전체 보기
              </button>
              {onClearAll && (
                <button
                  onClick={onClearAll}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  모두 삭제
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
