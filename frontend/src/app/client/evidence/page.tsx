/**
 * Evidence Upload Page
 * 003-role-based-ui Feature - US4 (T076)
 *
 * Page for clients to upload evidence to their case.
 * Uses query parameter for case ID: /client/evidence?caseId=xxx
 */

'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { getClientCaseDetail } from '@/lib/api/client-portal';
import EvidenceUploader from '@/components/client/EvidenceUploader';
import { ProgressBar } from '@/components/client/ProgressTracker';

function EvidencePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const caseId = searchParams?.get('caseId') ?? null;

  const [caseTitle, setCaseTitle] = useState<string>('');
  const [canUpload, setCanUpload] = useState(true);
  const [progressPercent, setProgressPercent] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  useEffect(() => {
    if (!caseId) {
      setError('케이스 ID가 필요합니다');
      setLoading(false);
      return;
    }

    async function fetchCase() {
      setLoading(true);
      const result = await getClientCaseDetail(caseId!);

      if (result.error || !result.data) {
        setError(result.error || 'Failed to load case');
      } else {
        setCaseTitle(result.data.title);
        setCanUpload(result.data.can_upload_evidence);
        setProgressPercent(result.data.progress_percent);
      }

      setLoading(false);
    }

    fetchCase();
  }, [caseId]);

  const handleUploadComplete = (evidenceId: string) => {
    setUploadSuccess(true);
    console.log('Upload complete:', evidenceId);
  };

  const handleError = (err: string) => {
    console.error('Upload error:', err);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]"></div>
      </div>
    );
  }

  if (!caseId || error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)] p-8 text-center">
        <svg className="w-16 h-16 mx-auto text-[var(--color-error)] mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
          {!caseId ? '케이스 ID가 필요합니다' : '케이스를 불러올 수 없습니다'}
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

  if (!canUpload) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)] p-8 text-center">
        <svg className="w-16 h-16 mx-auto text-[var(--color-warning)] mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
          증거 업로드가 불가능합니다
        </h2>
        <p className="text-[var(--color-text-secondary)] mb-4">
          이 케이스는 현재 증거 업로드가 제한되어 있습니다.
        </p>
        <Link
          href={`/client/cases/${caseId}`}
          className="inline-block px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors"
        >
          케이스 상세로 돌아가기
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link
          href={`/client/cases/${caseId}`}
          className="inline-flex items-center gap-1 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] mb-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          케이스 상세
        </Link>
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          증거자료 업로드
        </h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          {caseTitle}
        </p>
      </div>

      {/* Case Progress Summary */}
      <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)] p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-[var(--color-text-secondary)]">케이스 진행률</span>
          <span className="text-sm font-medium text-[var(--color-primary)]">{progressPercent}%</span>
        </div>
        <ProgressBar percent={progressPercent} showLabel={false} />
      </div>

      {/* Upload Guidelines */}
      <div className="bg-[var(--color-bg-secondary)] rounded-xl p-4">
        <h3 className="font-medium text-[var(--color-text-primary)] mb-3">업로드 안내</h3>
        <ul className="space-y-2 text-sm text-[var(--color-text-secondary)]">
          <li className="flex items-start gap-2">
            <svg className="w-5 h-5 text-[var(--color-success)] flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>지원 형식: 이미지(JPG, PNG), 오디오(MP3, WAV), 비디오(MP4), PDF, 텍스트</span>
          </li>
          <li className="flex items-start gap-2">
            <svg className="w-5 h-5 text-[var(--color-success)] flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>최대 파일 크기: 100MB</span>
          </li>
          <li className="flex items-start gap-2">
            <svg className="w-5 h-5 text-[var(--color-success)] flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>업로드된 파일은 AI가 자동으로 분석합니다</span>
          </li>
          <li className="flex items-start gap-2">
            <svg className="w-5 h-5 text-[var(--color-primary)] flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>민감한 개인정보가 포함된 경우 해당 부분을 가려주세요</span>
          </li>
        </ul>
      </div>

      {/* Evidence Uploader */}
      <EvidenceUploader
        caseId={caseId}
        onUploadComplete={handleUploadComplete}
        onError={handleError}
      />

      {/* Success message with option to upload more */}
      {uploadSuccess && (
        <div className="bg-[var(--color-success-light)] rounded-xl p-4">
          <div className="flex items-center gap-3">
            <svg className="w-6 h-6 text-[var(--color-success)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="font-medium text-[var(--color-success)]">업로드 완료!</p>
              <p className="text-sm text-[var(--color-text-secondary)]">
                추가 파일을 업로드하거나 케이스 상세로 돌아갈 수 있습니다.
              </p>
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button
              type="button"
              onClick={() => setUploadSuccess(false)}
              className="flex-1 px-4 py-2 border border-[var(--color-success)] text-[var(--color-success)] rounded-lg hover:bg-white transition-colors"
            >
              추가 업로드
            </button>
            <button
              type="button"
              onClick={() => router.push(`/client/cases/${caseId}`)}
              className="flex-1 px-4 py-2 bg-[var(--color-success)] text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              케이스 상세로
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function EvidencePage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]"></div>
        </div>
      }
    >
      <EvidencePageContent />
    </Suspense>
  );
}
