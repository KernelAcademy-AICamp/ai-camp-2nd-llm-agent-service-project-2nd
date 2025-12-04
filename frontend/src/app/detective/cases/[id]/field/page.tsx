/**
 * Detective Field Investigation Page
 * 003-role-based-ui Feature - US5 (T104)
 *
 * Page for field investigation activities.
 * Includes GPS tracking, field record creation, and report submission.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { getDetectiveCaseDetail, type CaseDetailData } from '@/lib/api/detective-portal';
import FieldRecorder from '@/components/detective/FieldRecorder';
import ReportEditor from '@/components/detective/ReportEditor';

type ViewMode = 'record' | 'report';

export default function DetectiveFieldPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const caseId = params.id as string;
  const mode = (searchParams.get('mode') as ViewMode) || 'record';

  const [caseDetail, setCaseDetail] = useState<CaseDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ViewMode>(mode);

  useEffect(() => {
    const fetchCaseDetail = async () => {
      setLoading(true);
      setError(null);

      const { data, error: apiError } = await getDetectiveCaseDetail(caseId);

      if (apiError) {
        setError(apiError);
      } else {
        setCaseDetail(data);
      }

      setLoading(false);
    };

    if (caseId) {
      fetchCaseDetail();
    }
  }, [caseId]);

  useEffect(() => {
    setActiveTab(mode);
  }, [mode]);

  const handleRecordSaved = useCallback((recordId: string) => {
    // Refresh case detail to show new record
    getDetectiveCaseDetail(caseId).then(({ data }) => {
      if (data) {
        setCaseDetail(data);
      }
    });
    console.log('Record saved:', recordId);
  }, [caseId]);

  const handleReportSubmitted = useCallback((reportId: string) => {
    console.log('Report submitted:', reportId);
    router.push(`/detective/cases/${caseId}`);
  }, [caseId, router]);

  const handleError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    setTimeout(() => setError(null), 5000);
  }, []);

  const switchTab = (tab: ViewMode) => {
    setActiveTab(tab);
    router.push(`/detective/cases/${caseId}/field?mode=${tab}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
      </div>
    );
  }

  if (error && !caseDetail) {
    return (
      <div className="space-y-4">
        <div className="p-6 bg-red-50 text-[var(--color-error)] rounded-lg">
          {error}
        </div>
        <Link
          href="/detective/cases"
          className="text-[var(--color-primary)] hover:underline"
        >
          &larr; 목록으로 돌아가기
        </Link>
      </div>
    );
  }

  if (!caseDetail) {
    return (
      <div className="text-center py-12 text-[var(--color-text-secondary)]">
        사건을 찾을 수 없습니다.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
        <Link href="/detective/cases" className="hover:text-[var(--color-primary)]">
          의뢰 관리
        </Link>
        <span>/</span>
        <Link
          href={`/detective/cases/${caseId}`}
          className="hover:text-[var(--color-primary)]"
        >
          {caseDetail.title}
        </Link>
        <span>/</span>
        <span className="text-[var(--color-text-primary)]">현장 조사</span>
      </nav>

      {/* Error Toast */}
      {error && (
        <div className="p-4 bg-red-50 text-[var(--color-error)] rounded-lg flex items-center justify-between">
          <span>{error}</span>
          <button
            type="button"
            onClick={() => setError(null)}
            className="p-1 hover:bg-red-100 rounded"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Header */}
      <div className="bg-white p-6 rounded-lg border border-[var(--color-border)]">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
              현장 조사
            </h1>
            <p className="text-[var(--color-text-secondary)] mt-1">
              {caseDetail.title}
            </p>
          </div>
          <Link
            href={`/detective/cases/${caseId}`}
            className="px-4 py-2 border border-[var(--color-border)] rounded-lg
              text-[var(--color-text-primary)] hover:bg-[var(--color-bg-secondary)]
              min-h-[44px] flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            사건 정보
          </Link>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mt-6 border-t border-[var(--color-border)] pt-4">
          <button
            type="button"
            onClick={() => switchTab('record')}
            className={`px-4 py-2 rounded-lg min-h-[44px] ${
              activeTab === 'record'
                ? 'bg-[var(--color-primary)] text-white'
                : 'bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] hover:bg-gray-200'
            }`}
          >
            현장 기록
          </button>
          <button
            type="button"
            onClick={() => switchTab('report')}
            className={`px-4 py-2 rounded-lg min-h-[44px] ${
              activeTab === 'report'
                ? 'bg-[var(--color-primary)] text-white'
                : 'bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] hover:bg-gray-200'
            }`}
          >
            보고서 작성
          </button>
        </div>
      </div>

      {/* Content */}
      {activeTab === 'record' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Field Recorder */}
          <FieldRecorder
            caseId={caseId}
            onRecordSaved={handleRecordSaved}
            onError={handleError}
          />

          {/* Recent Records */}
          <div className="bg-white rounded-lg border border-[var(--color-border)]">
            <div className="p-4 border-b border-[var(--color-border)]">
              <h2 className="text-lg font-semibold">최근 기록</h2>
            </div>
            {caseDetail.records.length > 0 ? (
              <div className="divide-y divide-[var(--color-border)] max-h-[600px] overflow-y-auto">
                {caseDetail.records.slice(0, 10).map((record) => (
                  <div key={record.id} className="p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="px-2 py-0.5 text-xs font-medium bg-[var(--color-bg-secondary)] rounded">
                        {record.record_type === 'observation'
                          ? '관찰'
                          : record.record_type === 'photo'
                          ? '사진'
                          : record.record_type === 'note'
                          ? '메모'
                          : record.record_type}
                      </span>
                      <span className="text-xs text-[var(--color-text-secondary)]">
                        {new Date(record.created_at).toLocaleString('ko-KR')}
                      </span>
                    </div>
                    <p className="text-sm text-[var(--color-text-primary)] line-clamp-2">
                      {record.content}
                    </p>
                    {record.gps_lat && record.gps_lng && (
                      <div className="flex items-center gap-1 mt-1 text-xs text-[var(--color-text-secondary)]">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        </svg>
                        <span>
                          {record.gps_lat.toFixed(4)}, {record.gps_lng.toFixed(4)}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-[var(--color-text-secondary)]">
                아직 기록이 없습니다.
              </div>
            )}
          </div>
        </div>
      ) : (
        <ReportEditor
          caseId={caseId}
          caseTitle={caseDetail.title}
          onReportSubmitted={handleReportSubmitted}
          onError={handleError}
        />
      )}

      {/* Quick Actions */}
      <div className="fixed bottom-6 right-6 flex flex-col gap-2">
        <button
          type="button"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="p-3 bg-white rounded-full shadow-lg border border-[var(--color-border)]
            hover:bg-[var(--color-bg-secondary)] min-h-[48px] min-w-[48px]"
          aria-label="맨 위로"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}
