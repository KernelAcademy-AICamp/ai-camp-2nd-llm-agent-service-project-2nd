/**
 * Detective Investigation Detail Client Component
 * 003-role-based-ui Feature - US5 (T103)
 *
 * Client component for case detail page.
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  getDetectiveCaseDetail,
  acceptCase,
  rejectCase,
  type CaseDetailData,
  type FieldRecord,
} from '@/lib/api/detective-portal';

interface DetectiveCaseDetailClientProps {
  caseId: string;
}

export default function DetectiveCaseDetailClient({ caseId }: DetectiveCaseDetailClientProps) {
  const router = useRouter();

  const [caseDetail, setCaseDetail] = useState<CaseDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    const fetchCaseDetail = async () => {
      setLoading(true);
      setError(null);

      const { data, error: apiError } = await getDetectiveCaseDetail(caseId);

      if (apiError) {
        setError(apiError);
      } else if (data) {
        setCaseDetail(data);
      }

      setLoading(false);
    };

    if (caseId) {
      fetchCaseDetail();
    }
  }, [caseId]);

  const handleAccept = async () => {
    setActionLoading(true);
    const { data, error: apiError } = await acceptCase(caseId);

    if (apiError) {
      setError(apiError);
    } else if (data?.success) {
      setCaseDetail((prev) =>
        prev ? { ...prev, status: data.new_status } : null
      );
    }
    setActionLoading(false);
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) return;

    setActionLoading(true);
    const { data, error: apiError } = await rejectCase(caseId, rejectReason);

    if (apiError) {
      setError(apiError);
    } else if (data?.success) {
      router.push('/detective/cases');
    }
    setActionLoading(false);
    setShowRejectModal(false);
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-700',
      active: 'bg-blue-100 text-blue-700',
      review: 'bg-purple-100 text-purple-700',
      completed: 'bg-green-100 text-green-700',
    };
    const labels: Record<string, string> = {
      pending: '대기중',
      active: '진행중',
      review: '검토중',
      completed: '완료',
    };

    return (
      <span className={`px-3 py-1 text-sm font-medium rounded-full ${badges[status] || badges.pending}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getRecordTypeLabel = (type: FieldRecord['record_type']) => {
    const labels: Record<string, string> = {
      observation: '관찰 기록',
      photo: '사진',
      note: '메모',
      video: '영상',
      audio: '음성',
    };
    return labels[type] || type;
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
      </div>
    );
  }

  if (error) {
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
        <span className="text-[var(--color-text-primary)]">{caseDetail.title}</span>
      </nav>

      {/* Header */}
      <div className="bg-white p-6 rounded-lg border border-[var(--color-border)]">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
                {caseDetail.title}
              </h1>
              {getStatusBadge(caseDetail.status)}
            </div>
            <p className="text-[var(--color-text-secondary)]">
              {caseDetail.description || '설명 없음'}
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            {caseDetail.status === 'pending' && (
              <>
                <button
                  type="button"
                  onClick={handleAccept}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg
                    hover:bg-[var(--color-primary-hover)] disabled:opacity-50 min-h-[44px]"
                >
                  {actionLoading ? '처리중...' : '수락'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowRejectModal(true)}
                  disabled={actionLoading}
                  className="px-4 py-2 border border-[var(--color-error)] text-[var(--color-error)] rounded-lg
                    hover:bg-red-50 disabled:opacity-50 min-h-[44px]"
                >
                  거절
                </button>
              </>
            )}
            {caseDetail.status === 'active' && (
              <button
                type="button"
                className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg
                  hover:bg-[var(--color-primary-hover)] min-h-[44px] flex items-center gap-2"
                onClick={() => {/* TODO: Open evidence upload modal */}}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                증거 업로드
              </button>
            )}
          </div>
        </div>

        {/* Case Info */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-[var(--color-border)]">
          <div>
            <span className="text-sm text-[var(--color-text-secondary)]">담당 변호사</span>
            <p className="font-medium">{caseDetail.lawyer_name || '-'}</p>
          </div>
          <div>
            <span className="text-sm text-[var(--color-text-secondary)]">연락처</span>
            <p className="font-medium">{caseDetail.lawyer_email || '-'}</p>
          </div>
          <div>
            <span className="text-sm text-[var(--color-text-secondary)]">생성일</span>
            <p className="font-medium">{formatDate(caseDetail.created_at)}</p>
          </div>
          <div>
            <span className="text-sm text-[var(--color-text-secondary)]">최근 수정</span>
            <p className="font-medium">{formatDate(caseDetail.updated_at)}</p>
          </div>
        </div>
      </div>

      {/* Records Section */}
      <div className="bg-white rounded-lg border border-[var(--color-border)]">
        <div className="p-4 border-b border-[var(--color-border)] flex items-center justify-between">
          <h2 className="text-lg font-semibold">증거 목록</h2>
          <span className="text-sm text-[var(--color-text-secondary)]">
            총 {caseDetail.records.length}건
          </span>
        </div>

        {caseDetail.records.length > 0 ? (
          <div className="divide-y divide-[var(--color-border)]">
            {caseDetail.records.map((record) => (
              <div key={record.id} className="p-4 hover:bg-[var(--color-bg-secondary)]">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="px-2 py-0.5 text-xs font-medium bg-[var(--color-bg-secondary)] rounded">
                        {getRecordTypeLabel(record.record_type)}
                      </span>
                      <span className="text-sm text-[var(--color-text-secondary)]">
                        {formatDate(record.created_at)}
                      </span>
                    </div>
                    <p className="text-[var(--color-text-primary)]">{record.content}</p>
                  </div>
                  {record.photo_url && (
                    <img
                      src={record.photo_url}
                      alt="첨부 사진"
                      className="w-16 h-16 object-cover rounded-lg ml-4"
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-[var(--color-text-secondary)]">
            아직 등록된 증거가 없습니다.
          </div>
        )}
      </div>

      {/* Report Section - Only show for active cases */}
      {caseDetail.status === 'active' && (
        <div className="bg-white p-6 rounded-lg border border-[var(--color-border)]">
          <h2 className="text-lg font-semibold mb-4">보고서 제출</h2>
          <p className="text-[var(--color-text-secondary)] mb-4">
            조사가 완료되면 최종 보고서를 작성하여 제출해 주세요.
          </p>
          <button
            type="button"
            className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--color-secondary)] text-white rounded-lg
              hover:opacity-90 min-h-[44px]"
            onClick={() => {/* TODO: Open report modal */}}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            보고서 작성
          </button>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">의뢰 거절</h3>
            <p className="text-[var(--color-text-secondary)] mb-4">
              거절 사유를 입력해 주세요.
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="거절 사유..."
              rows={3}
              className="w-full px-4 py-3 border border-[var(--color-border)] rounded-lg
                focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]
                resize-none mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowRejectModal(false)}
                className="px-4 py-2 border border-[var(--color-border)] rounded-lg
                  hover:bg-[var(--color-bg-secondary)] min-h-[44px]"
              >
                취소
              </button>
              <button
                type="button"
                onClick={handleReject}
                disabled={!rejectReason.trim() || actionLoading}
                className="px-4 py-2 bg-[var(--color-error)] text-white rounded-lg
                  hover:opacity-90 disabled:opacity-50 min-h-[44px]"
              >
                {actionLoading ? '처리중...' : '거절하기'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
