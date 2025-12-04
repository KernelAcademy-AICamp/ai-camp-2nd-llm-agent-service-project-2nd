'use client';

/**
 * Lawyer Case Detail Client Component
 * 003-role-based-ui Feature - US3
 *
 * Client-side component for case detail view with evidence list and AI summary.
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface CaseDetail {
  id: string;
  title: string;
  clientName?: string;
  description?: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  ownerId: string;
  ownerName?: string;
  ownerEmail?: string;
  evidenceCount: number;
  evidenceSummary: { type: string; count: number }[];
  aiSummary?: string;
  aiLabels: string[];
  recentActivities: { action: string; timestamp: string; user: string }[];
  members: { userId: string; userName?: string; role: string }[];
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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

interface LawyerCaseDetailClientProps {
  id: string;
}

export default function LawyerCaseDetailClient({ id }: LawyerCaseDetailClientProps) {
  const router = useRouter();
  const caseId = id;

  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'evidence' | 'timeline' | 'members'>('evidence');

  useEffect(() => {
    const fetchCaseDetail = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('authToken');
        if (!token) {
          router.push('/login');
          return;
        }

        const response = await fetch(`${API_BASE_URL}/lawyer/cases/${caseId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('케이스를 찾을 수 없습니다.');
          }
          throw new Error('케이스 정보를 불러오는데 실패했습니다.');
        }

        const data = await response.json();
        setCaseDetail({
          id: data.id,
          title: data.title,
          clientName: data.client_name,
          description: data.description,
          status: data.status,
          createdAt: data.created_at,
          updatedAt: data.updated_at,
          ownerId: data.owner_id,
          ownerName: data.owner_name,
          ownerEmail: data.owner_email,
          evidenceCount: data.evidence_count || 0,
          evidenceSummary: data.evidence_summary || [],
          aiSummary: data.ai_summary,
          aiLabels: data.ai_labels || [],
          recentActivities: data.recent_activities || [],
          members: data.members || [],
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : '오류가 발생했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    if (caseId) {
      fetchCaseDetail();
    }
  }, [caseId, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
      </div>
    );
  }

  if (error || !caseDetail) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
          {error || '케이스를 찾을 수 없습니다'}
        </h2>
        <Link
          href="/lawyer/cases"
          className="text-[var(--color-primary)] hover:underline"
        >
          케이스 목록으로 돌아가기
        </Link>
      </div>
    );
  }

  const statusColor = statusColors[caseDetail.status] || statusColors.active;
  const statusLabel = statusLabels[caseDetail.status] || caseDetail.status;

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-[var(--color-text-secondary)]">
        <Link href="/lawyer/cases" className="hover:text-[var(--color-primary)]">
          케이스 관리
        </Link>
        <span className="mx-2">/</span>
        <span className="text-[var(--color-text-primary)]">{caseDetail.title}</span>
      </nav>

      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
                {caseDetail.title}
              </h1>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${statusColor}`}>
                {statusLabel}
              </span>
            </div>
            {caseDetail.clientName && (
              <p className="text-[var(--color-text-secondary)]">
                의뢰인: {caseDetail.clientName}
              </p>
            )}
            {caseDetail.description && (
              <p className="mt-2 text-[var(--color-text-secondary)]">
                {caseDetail.description}
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
            >
              수정
            </button>
            <button
              type="button"
              className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm hover:bg-[var(--color-primary-hover)]"
            >
              AI 분석 요청
            </button>
          </div>
        </div>

        {/* Meta Info */}
        <div className="mt-4 pt-4 border-t border-gray-200 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-[var(--color-text-secondary)]">담당자</span>
            <p className="font-medium">{caseDetail.ownerName || '-'}</p>
          </div>
          <div>
            <span className="text-[var(--color-text-secondary)]">생성일</span>
            <p className="font-medium">
              {new Date(caseDetail.createdAt).toLocaleDateString('ko-KR')}
            </p>
          </div>
          <div>
            <span className="text-[var(--color-text-secondary)]">최근 업데이트</span>
            <p className="font-medium">
              {new Date(caseDetail.updatedAt).toLocaleDateString('ko-KR')}
            </p>
          </div>
          <div>
            <span className="text-[var(--color-text-secondary)]">증거 자료</span>
            <p className="font-medium">{caseDetail.evidenceCount}건</p>
          </div>
        </div>

        {/* AI Labels */}
        {caseDetail.aiLabels.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <span className="text-sm text-[var(--color-text-secondary)]">AI 분석 태그</span>
            <div className="flex flex-wrap gap-2 mt-2">
              {caseDetail.aiLabels.map((label, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-purple-100 text-purple-800 text-sm rounded-full"
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* AI Summary */}
      {caseDetail.aiSummary && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <h3 className="font-semibold text-purple-800">AI 분석 요약</h3>
            <span className="text-xs text-purple-600 bg-purple-100 px-2 py-0.5 rounded-full">
              Preview Only
            </span>
          </div>
          <p className="text-purple-900">{caseDetail.aiSummary}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {[
            { id: 'evidence', label: '증거 자료', count: caseDetail.evidenceCount },
            { id: 'timeline', label: '타임라인', count: caseDetail.recentActivities.length },
            { id: 'members', label: '팀원', count: caseDetail.members.length },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`
                pb-3 text-sm font-medium border-b-2 transition-colors
                ${activeTab === tab.id
                  ? 'border-[var(--color-primary)] text-[var(--color-primary)]'
                  : 'border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                }
              `}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-gray-100 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        {activeTab === 'evidence' && (
          <div>
            {caseDetail.evidenceCount > 0 ? (
              <div className="space-y-4">
                {caseDetail.evidenceSummary.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <span className="font-medium">{item.type}</span>
                    <span className="text-[var(--color-text-secondary)]">{item.count}건</span>
                  </div>
                ))}
                <Link
                  href={`/cases/${caseId}`}
                  className="inline-flex items-center gap-2 text-[var(--color-primary)] hover:underline"
                >
                  전체 증거 자료 보기
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>
            ) : (
              <p className="text-center text-[var(--color-text-secondary)] py-8">
                등록된 증거 자료가 없습니다.
              </p>
            )}
          </div>
        )}

        {activeTab === 'timeline' && (
          <div>
            {caseDetail.recentActivities.length > 0 ? (
              <div className="space-y-4">
                {caseDetail.recentActivities.map((activity, index) => (
                  <div key={index} className="flex gap-3">
                    <div className="w-2 h-2 mt-2 rounded-full bg-[var(--color-primary)]" />
                    <div>
                      <p className="text-[var(--color-text-primary)]">{activity.action}</p>
                      <p className="text-sm text-[var(--color-text-secondary)]">
                        {activity.user} - {new Date(activity.timestamp).toLocaleString('ko-KR')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-[var(--color-text-secondary)] py-8">
                활동 기록이 없습니다.
              </p>
            )}
          </div>
        )}

        {activeTab === 'members' && (
          <div>
            {caseDetail.members.length > 0 ? (
              <div className="space-y-3">
                {caseDetail.members.map((member, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-[var(--color-primary)] flex items-center justify-center text-white text-sm font-medium">
                        {member.userName?.slice(0, 1) || '?'}
                      </div>
                      <span className="font-medium">{member.userName || member.userId}</span>
                    </div>
                    <span className="text-sm text-[var(--color-text-secondary)] capitalize">
                      {member.role}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-[var(--color-text-secondary)] py-8">
                팀원이 없습니다.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
