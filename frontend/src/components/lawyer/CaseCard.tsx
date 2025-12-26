'use client';

/**
 * CaseCard Component
 * 003-role-based-ui Feature - US3
 *
 * Card view for a single case in the list.
 */

import Link from 'next/link';
import { getCaseDetailPath, getLawyerCasePath } from '@/lib/portalPaths';

interface CaseCardProps {
  id: string;
  title: string;
  clientName?: string;
  status: string;
  updatedAt: string;
  evidenceCount: number;
  progress: number;
  selected?: boolean;
  onSelect?: (id: string, selected: boolean) => void;
  onAction?: (id: string, action: 'procedure' | 'assets' | 'ai-analyze') => void;
}

const statusColors: Record<string, string> = {
  active: 'bg-info-light text-info',
  open: 'bg-success-light text-success',
  in_progress: 'bg-warning-light text-warning',
  closed: 'bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300',
};

const statusLabels: Record<string, string> = {
  active: '활성',
  open: '진행 중',
  in_progress: '검토 대기',
  closed: '종료',
};

export function CaseCard({
  id,
  title,
  clientName,
  status,
  updatedAt,
  evidenceCount,
  progress,
  selected = false,
  onSelect,
  onAction,
}: CaseCardProps) {
  // Debug: warn if id is missing (this should not happen in production)
  if (!id && process.env.NODE_ENV === 'development') {
    console.warn('[CaseCard] Missing id for case:', title);
  }

  const statusColor = statusColors[status] || statusColors.active;
  const statusLabel = statusLabels[status] || status;

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    onSelect?.(id, e.target.checked);
  };

  return (
    <div
      className={`
        relative p-4 bg-white dark:bg-neutral-800 border rounded-lg shadow-sm transition-all
        hover:shadow-md hover:border-[var(--color-primary)]
        ${selected ? 'border-[var(--color-primary)] ring-2 ring-[var(--color-primary)]/20' : 'border-neutral-200 dark:border-neutral-700'}
      `}
    >
      {/* Selection Checkbox */}
      {onSelect && (
        <div className="absolute top-3 left-3">
          <input
            type="checkbox"
            checked={selected}
            onChange={handleCheckboxChange}
            className="w-4 h-4 rounded border-neutral-300 dark:border-neutral-600 text-[var(--color-primary)] focus:ring-[var(--color-primary)]"
          />
        </div>
      )}

      {/* Status Badge */}
      <div className="flex justify-end mb-2">
        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusColor}`}>
          {statusLabel}
        </span>
      </div>

      {/* Title */}
      <Link href={getCaseDetailPath('lawyer', id)} prefetch={false} className="block group">
        <h3 className="font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-primary)] line-clamp-2">
          {title}
        </h3>
      </Link>

      {/* Client Name */}
      {clientName && (
        <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
          의뢰인: {clientName}
        </p>
      )}

      {/* Progress Bar */}
      <div className="mt-3">
        <div className="flex justify-between text-xs text-[var(--color-text-secondary)] mb-1">
          <span>진행률</span>
          <span>{progress}%</span>
        </div>
        <div className="w-full h-1.5 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--color-primary)] rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-700 flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
        <span>증거 {evidenceCount}건</span>
        <span>{new Date(updatedAt).toLocaleDateString('ko-KR')}</span>
      </div>

      {/* Quick Actions */}
      <div className="mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-700 flex items-center justify-center gap-2">
        <Link
          href={getLawyerCasePath('procedure', id)}
          prefetch={false}
          className="flex items-center gap-1 px-2 py-1 text-xs text-info hover:bg-info-light dark:hover:bg-neutral-700 rounded transition-colors"
          title="절차 진행"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          절차
        </Link>
        <Link
          href={getLawyerCasePath('assets', id)}
          prefetch={false}
          className="flex items-center gap-1 px-2 py-1 text-xs text-success hover:bg-success-light dark:hover:bg-neutral-700 rounded transition-colors"
          title="재산분할"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          재산
        </Link>
        {onAction && (
          <button
            type="button"
            onClick={() => onAction(id, 'ai-analyze')}
            className="flex items-center gap-1 px-2 py-1 text-xs text-secondary hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded transition-colors"
            title="AI 분석"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            AI
          </button>
        )}
      </div>
    </div>
  );
}

export default CaseCard;
