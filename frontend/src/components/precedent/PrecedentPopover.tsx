'use client';

/**
 * PrecedentPopover - Similar Precedents Hover Popup
 * Task 6: 유사판례 Hover Popup
 *
 * Animation specs:
 * - Open: Fast (150ms ease-out)
 * - Close: Delayed (300ms delay + 200ms ease-in)
 * - Maintains open while hovering on trigger or popover
 */

import { useState, useRef, useCallback } from 'react';
import { BookOpen, ExternalLink, Scale } from 'lucide-react';

interface Precedent {
  id: string;
  title: string;
  caseNumber: string;
  court: string;
  date: string;
  relevance: number; // 0-100
  summary: string;
}

interface PrecedentPopoverProps {
  precedents?: Precedent[];
  isLoading?: boolean;
  onViewAll?: () => void;
}

// Mock data for demonstration
const MOCK_PRECEDENTS: Precedent[] = [
  {
    id: '1',
    title: '재산분할청구',
    caseNumber: '2023드합12345',
    court: '서울가정법원',
    date: '2023-06-15',
    relevance: 92,
    summary: '혼인기간 20년, 전업주부의 기여도를 50%로 인정한 사례',
  },
  {
    id: '2',
    title: '재산분할청구',
    caseNumber: '2022드합67890',
    court: '부산가정법원',
    date: '2022-11-20',
    relevance: 87,
    summary: '숨겨진 재산 발견 시 분할비율 조정 인정 사례',
  },
  {
    id: '3',
    title: '이혼 및 재산분할',
    caseNumber: '2023드합11111',
    court: '대전가정법원',
    date: '2023-03-10',
    relevance: 78,
    summary: '부정행위와 재산분할 비율의 관계에 대한 판시',
  },
];

export function PrecedentPopover({
  precedents = MOCK_PRECEDENTS,
  isLoading = false,
  onViewAll,
}: PrecedentPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const closeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = useCallback(() => {
    // Clear any pending close timeout
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
    setIsOpen(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    // Delay close by 300ms
    closeTimeoutRef.current = setTimeout(() => {
      setIsOpen(false);
    }, 300);
  }, []);

  const getRelevanceColor = (relevance: number) => {
    if (relevance >= 90) return 'text-green-600 bg-green-100 dark:bg-green-900/30';
    if (relevance >= 80) return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30';
    if (relevance >= 70) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30';
    return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30';
  };

  return (
    <div className="relative" onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
      {/* Trigger Button - Lightning Related Records Style */}
      <button
        className={`
          w-full flex items-center justify-between gap-2 px-3 py-2 rounded-md text-sm
          bg-[var(--color-primary)]/5 border border-[var(--color-primary)]/20
          hover:bg-[var(--color-primary)]/10 hover:border-[var(--color-primary)]/30
          active:bg-[var(--color-primary)]/15 active:scale-[0.99]
          transition-all duration-100
          ${isOpen ? 'bg-[var(--color-primary)]/10 border-[var(--color-primary)]/40 shadow-sm' : ''}
        `}
      >
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-[var(--color-primary)]" />
          <span className="font-medium text-[var(--color-text-primary)]">유사판례</span>
        </div>
        {precedents.length > 0 && (
          <span className="px-1.5 py-0.5 text-xs font-medium bg-[var(--color-primary)] text-white rounded">
            {precedents.length}
          </span>
        )}
      </button>

      {/* Popover - Lightning Modal Style */}
      <div
        className={`
          absolute left-0 bottom-full mb-2 z-50
          w-96 max-h-96 overflow-y-auto
          bg-white dark:bg-neutral-800
          border border-gray-200 dark:border-neutral-700
          rounded-md shadow-lg
          transition-all duration-100 ease-out
          ${isOpen
            ? 'opacity-100 translate-y-0 pointer-events-auto'
            : 'opacity-0 translate-y-1 pointer-events-none'
          }
        `}
        style={{
          // Delayed close animation
          transitionDelay: isOpen ? '0ms' : '200ms',
          transitionDuration: isOpen ? '100ms' : '150ms',
          transitionTimingFunction: isOpen ? 'ease-out' : 'ease-in',
        }}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200 dark:border-neutral-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Scale className="w-4 h-4 text-[var(--color-primary)]" />
              <h4 className="font-semibold text-[var(--color-text-primary)]">유사 판례</h4>
            </div>
            {onViewAll && (
              <button
                onClick={onViewAll}
                className="text-xs text-[var(--color-primary)] hover:underline flex items-center gap-1"
              >
                전체보기
                <ExternalLink className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[var(--color-primary)]" />
            </div>
          ) : precedents.length === 0 ? (
            <div className="text-center py-8 text-[var(--color-text-secondary)] text-sm">
              유사 판례가 없습니다.
            </div>
          ) : (
            <div className="space-y-2">
              {precedents.map((precedent) => (
                <div
                  key={precedent.id}
                  className="p-3 rounded-lg bg-gray-50 dark:bg-neutral-900 hover:bg-gray-100 dark:hover:bg-neutral-800 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex-1 min-w-0">
                      <h5 className="font-medium text-sm text-[var(--color-text-primary)] line-clamp-2">
                        {precedent.title}
                      </h5>
                      <p className="text-xs text-[var(--color-text-secondary)]">
                        {precedent.caseNumber} | {precedent.court}
                      </p>
                    </div>
                    <span className={`px-1.5 py-0.5 text-xs rounded ${getRelevanceColor(precedent.relevance)}`}>
                      {precedent.relevance}%
                    </span>
                  </div>
                  <p className="text-xs text-[var(--color-text-secondary)] line-clamp-2">
                    {precedent.summary}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-gray-200 dark:border-neutral-700 bg-gray-50 dark:bg-neutral-900/50 rounded-b-lg">
          <p className="text-xs text-[var(--color-text-secondary)]">
            AI가 분석한 유사도 기준 상위 판례입니다.
          </p>
        </div>
      </div>
    </div>
  );
}

export default PrecedentPopover;
