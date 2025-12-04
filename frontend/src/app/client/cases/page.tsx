/**
 * Client Cases List Page
 * 003-role-based-ui Feature - US4
 *
 * List of all cases for the client.
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getClientCases } from '@/lib/api/client-portal';
import { ProgressBar } from '@/components/client/ProgressTracker';
import type { ClientCaseListItem } from '@/types/client-portal';

// Status badge colors
function getStatusColor(status: string) {
  switch (status) {
    case 'active':
    case 'in_progress':
      return 'bg-[var(--color-primary-light)] text-[var(--color-primary)]';
    case 'closed':
      return 'bg-[var(--color-success-light)] text-[var(--color-success)]';
    case 'review':
    case 'submitted':
      return 'bg-[var(--color-warning-light)] text-[var(--color-warning)]';
    default:
      return 'bg-[var(--color-neutral-200)] text-[var(--color-text-secondary)]';
  }
}

// Status display text
function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    open: '접수',
    active: '진행 중',
    in_progress: '진행 중',
    review: '검토 중',
    submitted: '제출됨',
    trial: '재판',
    closed: '종결',
  };
  return statusMap[status] || status;
}

// Case card component
function CaseCard({ caseItem }: { caseItem: ClientCaseListItem }) {
  return (
    <Link
      href={`/client/cases/${caseItem.id}`}
      className="block bg-white rounded-xl shadow-sm border border-[var(--color-border-default)] hover:shadow-md hover:border-[var(--color-primary)] transition-all"
    >
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold text-[var(--color-text-primary)] line-clamp-2">
            {caseItem.title}
          </h3>
          <span className={`px-2 py-1 text-xs font-medium rounded-full flex-shrink-0 ml-2 ${getStatusColor(caseItem.status)}`}>
            {getStatusText(caseItem.status)}
          </span>
        </div>

        {/* Progress */}
        <ProgressBar percent={caseItem.progress_percent} className="mb-4" />

        {/* Meta info */}
        <div className="flex items-center justify-between text-sm text-[var(--color-text-secondary)]">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {caseItem.evidence_count}건
            </span>
            {caseItem.lawyer_name && (
              <span className="flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                {caseItem.lawyer_name}
              </span>
            )}
          </div>
          <span className="text-xs">
            {new Date(caseItem.updated_at).toLocaleDateString('ko-KR')}
          </span>
        </div>
      </div>
    </Link>
  );
}

export default function ClientCasesPage() {
  const [cases, setCases] = useState<ClientCaseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchCases() {
      setLoading(true);
      setError(null);

      const result = await getClientCases();

      if (result.error || !result.data) {
        setError(result.error || 'Failed to load cases');
      } else {
        setCases(result.data.items);
      }

      setLoading(false);
    }

    fetchCases();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">내 케이스</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          진행 중인 모든 케이스를 확인하세요
        </p>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]"></div>
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)] p-8 text-center">
          <svg className="w-16 h-16 mx-auto text-[var(--color-error)] mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
            케이스를 불러올 수 없습니다
          </h2>
          <p className="text-[var(--color-text-secondary)]">{error}</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && cases.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)] p-8 text-center">
          <svg className="w-16 h-16 mx-auto text-[var(--color-text-tertiary)] mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
            아직 케이스가 없습니다
          </h2>
          <p className="text-[var(--color-text-secondary)]">
            담당 변호사가 케이스를 등록하면 여기에 표시됩니다
          </p>
        </div>
      )}

      {/* Cases grid */}
      {!loading && !error && cases.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cases.map((caseItem) => (
            <CaseCard key={caseItem.id} caseItem={caseItem} />
          ))}
        </div>
      )}
    </div>
  );
}
