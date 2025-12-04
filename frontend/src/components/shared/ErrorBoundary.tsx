/**
 * Error Boundary Components
 * 003-role-based-ui Feature - T155
 *
 * Reusable error UI components for error boundaries across all portals.
 */

'use client';

import React from 'react';

export interface ErrorFallbackProps {
  error: Error & { digest?: string };
  reset: () => void;
  title?: string;
  description?: string;
}

// Default error fallback component
export function ErrorFallback({
  error,
  reset,
  title = '오류가 발생했습니다',
  description = '일시적인 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.',
}: ErrorFallbackProps) {
  return (
    <div className="min-h-[400px] flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        {/* Error Icon */}
        <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <svg
            className="w-8 h-8 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>

        {/* Error Message */}
        <h2 className="text-xl font-semibold text-gray-900 mb-2">{title}</h2>
        <p className="text-gray-600 mb-6">{description}</p>

        {/* Error Details (development only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="bg-gray-100 rounded-lg p-4 mb-6 text-left">
            <p className="text-xs font-mono text-gray-600 break-all">
              {error.message}
            </p>
            {error.digest && (
              <p className="text-xs text-gray-500 mt-2">
                Error ID: {error.digest}
              </p>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            다시 시도
          </button>
          <button
            onClick={() => window.location.href = '/'}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            홈으로 이동
          </button>
        </div>
      </div>
    </div>
  );
}

// Portal-specific error components
export function LawyerPortalError({ error, reset }: ErrorFallbackProps) {
  return (
    <ErrorFallback
      error={error}
      reset={reset}
      title="변호사 포털 오류"
      description="변호사 포털에서 오류가 발생했습니다. 문제가 지속되면 관리자에게 문의해 주세요."
    />
  );
}

export function ClientPortalError({ error, reset }: ErrorFallbackProps) {
  return (
    <ErrorFallback
      error={error}
      reset={reset}
      title="의뢰인 포털 오류"
      description="의뢰인 포털에서 오류가 발생했습니다. 문제가 지속되면 담당 변호사에게 문의해 주세요."
    />
  );
}

export function DetectivePortalError({ error, reset }: ErrorFallbackProps) {
  return (
    <ErrorFallback
      error={error}
      reset={reset}
      title="탐정 포털 오류"
      description="탐정 포털에서 오류가 발생했습니다. 문제가 지속되면 관리자에게 문의해 주세요."
    />
  );
}

// Network error component
export function NetworkError({ reset }: { reset: () => void }) {
  return (
    <div className="min-h-[400px] flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="mx-auto w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mb-4">
          <svg
            className="w-8 h-8 text-yellow-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
            />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          네트워크 연결 오류
        </h2>
        <p className="text-gray-600 mb-6">
          인터넷 연결을 확인하고 다시 시도해 주세요.
        </p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          다시 시도
        </button>
      </div>
    </div>
  );
}

// 404 Not Found component
export function NotFoundError() {
  return (
    <div className="min-h-[400px] flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <svg
            className="w-8 h-8 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          페이지를 찾을 수 없습니다
        </h2>
        <p className="text-gray-600 mb-6">
          요청하신 페이지가 존재하지 않거나 이동되었습니다.
        </p>
        <button
          onClick={() => window.location.href = '/'}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          홈으로 이동
        </button>
      </div>
    </div>
  );
}
