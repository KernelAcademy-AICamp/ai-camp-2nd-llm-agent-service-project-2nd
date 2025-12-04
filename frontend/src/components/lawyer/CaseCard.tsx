'use client';

/**
 * CaseCard Component
 * 003-role-based-ui Feature - US3
 *
 * Card view for a single case in the list.
 */

import Link from 'next/link';

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
}

const statusColors: Record<string, string> = {
  active: 'bg-blue-100 text-blue-800',
  open: 'bg-green-100 text-green-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  closed: 'bg-gray-100 text-gray-800',
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
}: CaseCardProps) {
  const statusColor = statusColors[status] || statusColors.active;
  const statusLabel = statusLabels[status] || status;

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    onSelect?.(id, e.target.checked);
  };

  return (
    <div
      className={`
        relative p-4 bg-white border rounded-lg shadow-sm transition-all
        hover:shadow-md hover:border-[var(--color-primary)]
        ${selected ? 'border-[var(--color-primary)] ring-2 ring-[var(--color-primary)]/20' : 'border-gray-200'}
      `}
    >
      {/* Selection Checkbox */}
      {onSelect && (
        <div className="absolute top-3 left-3">
          <input
            type="checkbox"
            checked={selected}
            onChange={handleCheckboxChange}
            className="w-4 h-4 rounded border-gray-300 text-[var(--color-primary)] focus:ring-[var(--color-primary)]"
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
      <Link href={`/lawyer/cases/${id}`} className="block group">
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
        <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--color-primary)] rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
        <span>증거 {evidenceCount}건</span>
        <span>{new Date(updatedAt).toLocaleDateString('ko-KR')}</span>
      </div>
    </div>
  );
}

export default CaseCard;
