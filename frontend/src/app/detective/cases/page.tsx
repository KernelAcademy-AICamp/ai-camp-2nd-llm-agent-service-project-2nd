/**
 * Detective Cases List Page
 * 003-role-based-ui Feature - US5
 *
 * Page displaying list of detective's assigned cases.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getDetectiveCases } from '@/lib/api/detective-portal';
import type { CaseListItem, InvestigationStatus } from '@/types/detective-portal';

type FilterStatus = InvestigationStatus | 'all';

export default function DetectiveCasesPage() {
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [page, setPage] = useState(1);
  const limit = 20;

  useEffect(() => {
    const fetchCases = async () => {
      setLoading(true);
      setError(null);

      const { data, error: apiError } = await getDetectiveCases({
        status: filterStatus === 'all' ? undefined : filterStatus,
        page,
        limit,
      });

      if (apiError) {
        setError(apiError);
      } else if (data) {
        setCases(data.items);
        setTotal(data.total);
      }

      setLoading(false);
    };

    fetchCases();
  }, [filterStatus, page]);

  const getStatusBadge = (status: InvestigationStatus) => {
    const badges: Record<InvestigationStatus, string> = {
      pending: 'bg-yellow-100 text-yellow-700',
      active: 'bg-blue-100 text-blue-700',
      review: 'bg-purple-100 text-purple-700',
      completed: 'bg-green-100 text-green-700',
      rejected: 'bg-red-100 text-red-700',
    };
    const labels: Record<InvestigationStatus, string> = {
      pending: '대기중',
      active: '진행중',
      review: '검토중',
      completed: '완료',
      rejected: '거절됨',
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${badges[status]}`}>
        {labels[status]}
      </span>
    );
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">의뢰 관리</h1>
          <p className="text-[var(--color-text-secondary)] mt-1">
            배정된 조사 의뢰를 관리하세요.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-[var(--color-border)]">
        <div className="flex flex-wrap gap-2">
          {(['all', 'pending', 'active', 'review', 'completed'] as const).map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => {
                setFilterStatus(status);
                setPage(1);
              }}
              className={`px-4 py-2 rounded-lg min-h-[40px] transition-colors ${
                filterStatus === status
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] hover:bg-gray-200'
              }`}
            >
              {status === 'all'
                ? '전체'
                : status === 'pending'
                ? '대기중'
                : status === 'active'
                ? '진행중'
                : status === 'review'
                ? '검토중'
                : '완료'}
            </button>
          ))}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-6 bg-red-50 text-[var(--color-error)] rounded-lg">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
        </div>
      )}

      {/* Cases List */}
      {!loading && !error && (
        <div className="bg-white rounded-lg border border-[var(--color-border)]">
          {cases.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-[var(--color-bg-secondary)]">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-secondary)]">
                        사건명
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-secondary)]">
                        담당 변호사
                      </th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-[var(--color-text-secondary)]">
                        상태
                      </th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-[var(--color-text-secondary)]">
                        기록
                      </th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-secondary)]">
                        등록일
                      </th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-secondary)]">
                        액션
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-border)]">
                    {cases.map((caseItem) => (
                      <tr key={caseItem.id} className="hover:bg-[var(--color-bg-secondary)]">
                        <td className="px-4 py-4">
                          <Link
                            href={`/detective/cases/${caseItem.id}`}
                            className="font-medium text-[var(--color-text-primary)] hover:text-[var(--color-primary)]"
                          >
                            {caseItem.title}
                          </Link>
                        </td>
                        <td className="px-4 py-4 text-[var(--color-text-secondary)]">
                          {caseItem.lawyer_name || '-'}
                        </td>
                        <td className="px-4 py-4 text-center">
                          {getStatusBadge(caseItem.status)}
                        </td>
                        <td className="px-4 py-4 text-center text-[var(--color-text-secondary)]">
                          {caseItem.record_count}건
                        </td>
                        <td className="px-4 py-4 text-right text-[var(--color-text-secondary)]">
                          {formatDate(caseItem.created_at)}
                        </td>
                        <td className="px-4 py-4 text-right">
                          <Link
                            href={`/detective/cases/${caseItem.id}`}
                            className="text-[var(--color-primary)] hover:underline"
                          >
                            상세보기
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="p-4 border-t border-[var(--color-border)] flex items-center justify-between">
                  <span className="text-sm text-[var(--color-text-secondary)]">
                    총 {total}건 중 {(page - 1) * limit + 1}-{Math.min(page * limit, total)}건
                  </span>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-3 py-1.5 border border-[var(--color-border)] rounded
                        disabled:opacity-50 disabled:cursor-not-allowed
                        hover:bg-[var(--color-bg-secondary)]"
                    >
                      이전
                    </button>
                    <span className="px-3 py-1.5">
                      {page} / {totalPages}
                    </span>
                    <button
                      type="button"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-3 py-1.5 border border-[var(--color-border)] rounded
                        disabled:opacity-50 disabled:cursor-not-allowed
                        hover:bg-[var(--color-bg-secondary)]"
                    >
                      다음
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="p-12 text-center text-[var(--color-text-secondary)]">
              <svg
                className="w-12 h-12 mx-auto mb-4 text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p>배정된 의뢰가 없습니다.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
