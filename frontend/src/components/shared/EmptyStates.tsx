/**
 * Empty State Components
 * 003-role-based-ui Feature - T158
 *
 * Reusable empty state components for lists and data displays.
 */

'use client';

import React from 'react';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

// Base empty state component
export function EmptyState({
  icon,
  title,
  description,
  action,
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 ${className}`}>
      {icon && (
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-gray-900 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 text-center max-w-sm mb-4">{description}</p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

// Empty cases list
export function EmptyCases({ onCreateCase }: { onCreateCase?: () => void }) {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
        </svg>
      }
      title="케이스가 없습니다"
      description="새로운 케이스를 생성하여 증거 관리를 시작하세요."
      action={onCreateCase ? { label: '새 케이스 만들기', onClick: onCreateCase } : undefined}
    />
  );
}

// Empty evidence list
export function EmptyEvidence({ onUploadEvidence }: { onUploadEvidence?: () => void }) {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      }
      title="증거가 없습니다"
      description="증거 파일을 업로드하여 AI 분석을 시작하세요."
      action={onUploadEvidence ? { label: '증거 업로드', onClick: onUploadEvidence } : undefined}
    />
  );
}

// Empty calendar events
export function EmptyCalendar({ onCreateEvent }: { onCreateEvent?: () => void }) {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      }
      title="일정이 없습니다"
      description="새로운 일정을 등록하여 케이스 관련 이벤트를 관리하세요."
      action={onCreateEvent ? { label: '일정 추가', onClick: onCreateEvent } : undefined}
    />
  );
}

// Empty messages
export function EmptyMessages({ onStartConversation }: { onStartConversation?: () => void }) {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      }
      title="메시지가 없습니다"
      description="아직 주고받은 메시지가 없습니다."
      action={onStartConversation ? { label: '대화 시작', onClick: onStartConversation } : undefined}
    />
  );
}

// Empty invoices
export function EmptyInvoices({ onCreateInvoice }: { onCreateInvoice?: () => void }) {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2zM10 8.5a.5.5 0 11-1 0 .5.5 0 011 0zm5 5a.5.5 0 11-1 0 .5.5 0 011 0z" />
        </svg>
      }
      title="청구서가 없습니다"
      description="새로운 청구서를 생성하여 결제를 요청하세요."
      action={onCreateInvoice ? { label: '청구서 생성', onClick: onCreateInvoice } : undefined}
    />
  );
}

// Empty investigations
export function EmptyInvestigations({ onViewAvailable }: { onViewAvailable?: () => void }) {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      }
      title="진행 중인 조사가 없습니다"
      description="새로운 조사 의뢰를 수락하여 업무를 시작하세요."
      action={onViewAvailable ? { label: '의뢰 목록 보기', onClick: onViewAvailable } : undefined}
    />
  );
}

// Empty notifications
export function EmptyNotifications() {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      }
      title="알림이 없습니다"
      description="새로운 알림이 없습니다."
    />
  );
}

// Empty search results
export function EmptySearchResults({ searchTerm, onClearSearch }: { searchTerm: string; onClearSearch?: () => void }) {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      }
      title="검색 결과가 없습니다"
      description={`"${searchTerm}"에 대한 검색 결과가 없습니다. 다른 검색어를 시도해 보세요.`}
      action={onClearSearch ? { label: '검색 초기화', onClick: onClearSearch } : undefined}
    />
  );
}

// Generic empty list
export function EmptyList({ itemType }: { itemType: string }) {
  return (
    <EmptyState
      icon={
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
        </svg>
      }
      title={`${itemType}(이)가 없습니다`}
      description={`표시할 ${itemType}(이)가 없습니다.`}
    />
  );
}
