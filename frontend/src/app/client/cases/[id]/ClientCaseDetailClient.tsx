/**
 * Client Case Detail - Client Component
 * 003-role-based-ui Feature - US4 (T075)
 *
 * Detailed view of a specific case for clients.
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getClientCaseDetail } from '@/lib/api/client-portal';
import ProgressTracker from '@/components/client/ProgressTracker';
import type { ClientCaseDetailResponse, RecentActivity } from '@/types/client-portal';

// Activity Item Component
function ActivityItem({
  title,
  description,
  time_ago,
  activity_type,
}: RecentActivity) {
  const typeIcons = {
    evidence: (
      <div className="w-8 h-8 rounded-full bg-[var(--color-primary-light)] flex items-center justify-center text-[var(--color-primary)]">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
    ),
    message: (
      <div className="w-8 h-8 rounded-full bg-[var(--color-success-light)] flex items-center justify-center text-[var(--color-success)]">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </div>
    ),
    document: (
      <div className="w-8 h-8 rounded-full bg-[var(--color-warning-light)] flex items-center justify-center text-[var(--color-warning)]">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
    ),
    status: (
      <div className="w-8 h-8 rounded-full bg-[var(--color-secondary-light)] flex items-center justify-center text-[var(--color-secondary)]">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
    ),
  };

  return (
    <div className="flex items-start gap-3 p-3 hover:bg-[var(--color-bg-secondary)] rounded-lg transition-colors">
      {typeIcons[activity_type]}
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-[var(--color-text-primary)]">{title}</p>
        <p className="text-sm text-[var(--color-text-secondary)] truncate">{description}</p>
      </div>
      <span className="text-xs text-[var(--color-text-tertiary)] whitespace-nowrap">{time_ago}</span>
    </div>
  );
}

// Evidence type icon
function EvidenceIcon({ type }: { type: string }) {
  switch (type) {
    case 'image':
      return (
        <svg className="w-5 h-5 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      );
    case 'audio':
      return (
        <svg className="w-5 h-5 text-[var(--color-success)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
      );
    case 'video':
      return (
        <svg className="w-5 h-5 text-[var(--color-warning)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      );
    default:
      return (
        <svg className="w-5 h-5 text-[var(--color-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      );
  }
}

// Status badge colors
function getStatusColor(status: string) {
  switch (status) {
    case 'verified':
      return 'bg-[var(--color-success-light)] text-[var(--color-success)]';
    case 'processed':
      return 'bg-[var(--color-primary-light)] text-[var(--color-primary)]';
    default:
      return 'bg-[var(--color-neutral-200)] text-[var(--color-text-secondary)]';
  }
}

interface ClientCaseDetailClientProps {
  caseId: string;
}

export default function ClientCaseDetailClient({ caseId }: ClientCaseDetailClientProps) {
  const [caseData, setCaseData] = useState<ClientCaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchCase() {
      setLoading(true);
      setError(null);

      const result = await getClientCaseDetail(caseId);

      if (result.error || !result.data) {
        setError(result.error || 'Failed to load case');
      } else {
        setCaseData(result.data);
      }

      setLoading(false);
    }

    fetchCase();
  }, [caseId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]"></div>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)] p-8 text-center">
        <svg className="w-16 h-16 mx-auto text-[var(--color-error)] mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
          케이스를 불러올 수 없습니다
        </h2>
        <p className="text-[var(--color-text-secondary)] mb-4">{error}</p>
        <Link
          href="/client/cases"
          className="inline-block px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors"
        >
          케이스 목록으로 돌아가기
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/client/cases"
            className="inline-flex items-center gap-1 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] mb-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            케이스 목록
          </Link>
          <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
            {caseData.title}
          </h1>
          {caseData.description && (
            <p className="text-[var(--color-text-secondary)] mt-1">{caseData.description}</p>
          )}
        </div>

        {caseData.can_upload_evidence && (
          <Link
            href={`/client/evidence?caseId=${caseId}`}
            className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            증거 업로드
          </Link>
        )}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Progress Tracker - 2 columns */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-[var(--color-border-default)]">
          <div className="p-4 border-b border-[var(--color-border-default)]">
            <h2 className="font-semibold text-[var(--color-text-primary)]">진행 상황</h2>
          </div>
          <div className="p-6">
            <ProgressTracker steps={caseData.progress_steps} />
          </div>
        </div>

        {/* Lawyer Info - 1 column */}
        {caseData.lawyer_info && (
          <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)]">
            <div className="p-4 border-b border-[var(--color-border-default)]">
              <h2 className="font-semibold text-[var(--color-text-primary)]">담당 변호사</h2>
            </div>
            <div className="p-6">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-14 h-14 rounded-full bg-[var(--color-secondary)] flex items-center justify-center text-white text-lg font-semibold">
                  {caseData.lawyer_info.name.slice(0, 1)}
                </div>
                <div>
                  <p className="font-semibold text-[var(--color-text-primary)]">
                    {caseData.lawyer_info.name}
                  </p>
                  {caseData.lawyer_info.firm && (
                    <p className="text-sm text-[var(--color-text-secondary)]">
                      {caseData.lawyer_info.firm}
                    </p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                {caseData.lawyer_info.phone && (
                  <a
                    href={`tel:${caseData.lawyer_info.phone}`}
                    className="flex items-center gap-3 p-3 rounded-lg border border-[var(--color-border-default)] hover:bg-[var(--color-bg-secondary)] transition-colors"
                  >
                    <svg className="w-5 h-5 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    <span className="text-sm">{caseData.lawyer_info.phone}</span>
                  </a>
                )}
                <a
                  href={`mailto:${caseData.lawyer_info.email}`}
                  className="flex items-center gap-3 p-3 rounded-lg border border-[var(--color-border-default)] hover:bg-[var(--color-bg-secondary)] transition-colors"
                >
                  <svg className="w-5 h-5 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span className="text-sm truncate">{caseData.lawyer_info.email}</span>
                </a>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Evidence List */}
      <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)]">
        <div className="p-4 border-b border-[var(--color-border-default)] flex items-center justify-between">
          <h2 className="font-semibold text-[var(--color-text-primary)]">
            제출된 증거 ({caseData.evidence_count}건)
          </h2>
          {caseData.can_upload_evidence && (
            <Link
              href={`/client/evidence?caseId=${caseId}`}
              className="text-sm text-[var(--color-primary)] hover:underline"
            >
              + 증거 추가
            </Link>
          )}
        </div>

        {caseData.evidence_list.length === 0 ? (
          <div className="p-8 text-center">
            <svg className="w-12 h-12 mx-auto text-[var(--color-text-tertiary)] mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <p className="text-[var(--color-text-secondary)]">아직 제출된 증거가 없습니다</p>
            {caseData.can_upload_evidence && (
              <Link
                href={`/client/evidence?caseId=${caseId}`}
                className="inline-block mt-3 text-[var(--color-primary)] hover:underline"
              >
                첫 증거를 업로드하세요
              </Link>
            )}
          </div>
        ) : (
          <div className="divide-y divide-[var(--color-border-default)]">
            {caseData.evidence_list.map((evidence) => (
              <div key={evidence.id} className="p-4 hover:bg-[var(--color-bg-secondary)] transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[var(--color-bg-secondary)] flex items-center justify-center">
                    <EvidenceIcon type={evidence.file_type} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-[var(--color-text-primary)] truncate">
                      {evidence.file_name}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${getStatusColor(evidence.status)}`}>
                        {evidence.status === 'verified' ? '검증완료' : evidence.status === 'processed' ? '분석완료' : '처리중'}
                      </span>
                      <span className="text-xs text-[var(--color-text-tertiary)]">
                        {new Date(evidence.uploaded_at).toLocaleDateString('ko-KR')}
                      </span>
                    </div>
                  </div>
                  {evidence.ai_labels.length > 0 && (
                    <div className="hidden sm:flex gap-1">
                      {evidence.ai_labels.slice(0, 3).map((label, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 text-xs bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] rounded"
                        >
                          {label}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Activity */}
      {caseData.recent_activities.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)]">
          <div className="p-4 border-b border-[var(--color-border-default)]">
            <h2 className="font-semibold text-[var(--color-text-primary)]">최근 활동</h2>
          </div>
          <div className="divide-y divide-[var(--color-border-default)]">
            {caseData.recent_activities.map((activity) => (
              <ActivityItem key={activity.id} {...activity} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
