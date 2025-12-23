/**
 * SimilarPrecedentList Component
 * Always-expanded similar precedent list for DataPanel
 * LDS2 Compact density applied
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { Scale, ExternalLink, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { searchSimilarPrecedents } from '@/lib/api/precedent';
import type { PrecedentCase } from '@/types/precedent';

interface SimilarPrecedentListProps {
  caseId: string;
  maxItems?: number;
  onViewDetail?: (precedent: PrecedentCase) => void;
}

// Helper to format similarity score as percentage
function formatSimilarity(score: number): string {
  return `${Math.round(score * 100)}%`;
}

// Helper to get color based on similarity score
function getSimilarityColor(score: number): string {
  if (score >= 0.9) return 'text-green-600 bg-green-100 dark:bg-green-900/30';
  if (score >= 0.8) return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30';
  if (score >= 0.7) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30';
  return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30';
}

export function SimilarPrecedentList({
  caseId,
  maxItems = 5,
  onViewDetail,
}: SimilarPrecedentListProps) {
  const [precedents, setPrecedents] = useState<PrecedentCase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPrecedents = useCallback(async () => {
    if (!caseId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await searchSimilarPrecedents(caseId, {
        limit: maxItems,
        min_score: 0.3,
      });
      setPrecedents(response.precedents || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '판례를 불러오는데 실패했습니다.');
      setPrecedents([]);
    } finally {
      setIsLoading(false);
    }
  }, [caseId, maxItems]);

  useEffect(() => {
    fetchPrecedents();
  }, [fetchPrecedents]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 className="w-4 h-4 animate-spin text-[var(--color-primary)]" />
        <span className="ml-2 text-xs text-[var(--color-text-secondary)]">판례 검색 중...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="text-center py-3">
        <AlertCircle className="w-4 h-4 text-amber-500 mx-auto mb-1" />
        <p className="text-xs text-[var(--color-text-secondary)]">{error}</p>
        <button
          onClick={fetchPrecedents}
          className="mt-2 inline-flex items-center text-xs text-[var(--color-primary)] hover:underline"
        >
          <RefreshCw className="w-3 h-3 mr-1" />
          다시 시도
        </button>
      </div>
    );
  }

  // Empty state
  if (precedents.length === 0) {
    return (
      <div className="text-center py-3">
        <Scale className="w-5 h-5 text-gray-400 mx-auto mb-1" />
        <p className="text-xs text-[var(--color-text-secondary)]">
          유사 판례가 없습니다.
        </p>
        <p className="text-[10px] text-[var(--color-text-secondary)] mt-0.5">
          증거 자료를 추가하면 유사 판례를 검색합니다.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {/* Summary info */}
      <div className="flex items-center justify-between px-2 py-1 bg-blue-50 dark:bg-blue-900/20 rounded text-[10px]">
        <span className="text-blue-600 dark:text-blue-400 font-medium">
          유사도 기준 상위 {precedents.length}건
        </span>
        <button
          onClick={fetchPrecedents}
          className="text-blue-500 hover:text-blue-600 transition-colors"
          title="새로고침"
        >
          <RefreshCw className="w-3 h-3" />
        </button>
      </div>

      {/* Precedent items */}
      {precedents.map((precedent, index) => (
        <div
          key={`${precedent.case_ref}-${index}`}
          onClick={() => onViewDetail?.(precedent)}
          className="group px-2 py-2 rounded hover:bg-gray-100 dark:hover:bg-neutral-700 cursor-pointer transition-colors border border-transparent hover:border-gray-200 dark:hover:border-neutral-600"
        >
          {/* Header row */}
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <Scale className="w-3 h-3 flex-shrink-0 text-[var(--color-primary)]" />
                <span className="text-xs font-medium text-[var(--color-text-primary)] truncate">
                  {precedent.case_ref}
                </span>
              </div>
              <p className="text-[10px] text-[var(--color-text-secondary)] mt-0.5">
                {precedent.court} · {precedent.decision_date}
              </p>
            </div>
            <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${getSimilarityColor(precedent.similarity_score)}`}>
              {formatSimilarity(precedent.similarity_score)}
            </span>
          </div>

          {/* Summary */}
          <p className="text-[11px] text-[var(--color-text-secondary)] mt-1 line-clamp-2">
            {precedent.summary}
          </p>

          {/* Key factors */}
          {precedent.key_factors && precedent.key_factors.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {precedent.key_factors.slice(0, 3).map((factor, idx) => (
                <span
                  key={idx}
                  className="px-1.5 py-0.5 text-[9px] bg-gray-100 dark:bg-neutral-700 text-[var(--color-text-secondary)] rounded"
                >
                  {factor}
                </span>
              ))}
              {precedent.key_factors.length > 3 && (
                <span className="text-[9px] text-[var(--color-text-secondary)]">
                  +{precedent.key_factors.length - 3}
                </span>
              )}
            </div>
          )}

          {/* Division ratio if available */}
          {precedent.division_ratio && (
            <div className="flex items-center gap-2 mt-1.5 text-[10px]">
              <span className="text-teal-600 dark:text-teal-400">
                원고 {precedent.division_ratio.plaintiff}%
              </span>
              <span className="text-gray-400">:</span>
              <span className="text-slate-600 dark:text-slate-400">
                피고 {precedent.division_ratio.defendant}%
              </span>
            </div>
          )}

          {/* View detail link on hover */}
          <div className="hidden group-hover:flex items-center gap-1 mt-1.5 text-[10px] text-[var(--color-primary)]">
            <ExternalLink className="w-3 h-3" />
            <span>상세보기</span>
          </div>
        </div>
      ))}

      {/* Footer note */}
      <p className="text-[9px] text-[var(--color-text-secondary)] text-center pt-1 border-t border-gray-100 dark:border-neutral-700">
        AI 분석 기반 유사도 점수
      </p>
    </div>
  );
}

export default SimilarPrecedentList;
