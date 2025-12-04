/**
 * Detective Earnings Page
 * 003-role-based-ui Feature - US5 (T105)
 *
 * Page displaying detective's earnings, payment history, and financial summary.
 */

'use client';

import { useEffect, useState } from 'react';
import { getDetectiveEarnings, type EarningsData, type Transaction } from '@/lib/api/detective-portal';

type FilterPeriod = 'this_month' | 'last_month' | 'this_year' | null;

export default function DetectiveEarningsPage() {
  const [earnings, setEarnings] = useState<EarningsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterPeriod, setFilterPeriod] = useState<FilterPeriod>(null);

  useEffect(() => {
    const fetchEarnings = async () => {
      setLoading(true);
      setError(null);

      const { data, error: apiError } = await getDetectiveEarnings({
        period: filterPeriod || undefined,
      });

      if (apiError) {
        setError(apiError);
      } else {
        setEarnings(data);
      }

      setLoading(false);
    };

    fetchEarnings();
  }, [filterPeriod]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(amount);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getStatusBadge = (status: Transaction['status']) => {
    const badges = {
      pending: 'bg-yellow-100 text-yellow-700',
      completed: 'bg-green-100 text-green-700',
      cancelled: 'bg-gray-100 text-gray-700',
    };
    const labels = {
      pending: '대기중',
      completed: '완료',
      cancelled: '취소',
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${badges[status]}`}>
        {labels[status]}
      </span>
    );
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
      <div className="p-6 bg-red-50 text-[var(--color-error)] rounded-lg">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">정산/수익</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          수익 현황 및 거래 내역을 확인하세요.
        </p>
      </div>

      {/* Summary Cards */}
      {earnings && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Total Earned */}
          <div className="bg-white p-6 rounded-lg border border-[var(--color-border)]">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-[var(--color-primary)]/10 rounded-lg">
                <svg className="w-6 h-6 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="text-[var(--color-text-secondary)]">총 수익</span>
            </div>
            <p className="text-2xl font-bold text-[var(--color-text-primary)]">
              {formatCurrency(earnings.summary.total_earned)}
            </p>
          </div>

          {/* This Month */}
          <div className="bg-white p-6 rounded-lg border border-[var(--color-border)]">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <span className="text-[var(--color-text-secondary)]">이번 달 수익</span>
            </div>
            <p className="text-2xl font-bold text-[var(--color-text-primary)]">
              {formatCurrency(earnings.summary.this_month)}
            </p>
          </div>

          {/* Pending Payment */}
          <div className="bg-white p-6 rounded-lg border border-[var(--color-border)]">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="text-[var(--color-text-secondary)]">정산 대기</span>
            </div>
            <p className="text-2xl font-bold text-[var(--color-text-primary)]">
              {formatCurrency(earnings.summary.pending_payment)}
            </p>
          </div>
        </div>
      )}

      {/* Transaction History */}
      <div className="bg-white rounded-lg border border-[var(--color-border)]">
        {/* Header with Filter */}
        <div className="p-4 border-b border-[var(--color-border)] flex items-center justify-between">
          <h2 className="text-lg font-semibold">거래 내역</h2>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setFilterPeriod(null)}
              className={`px-3 py-1.5 text-sm rounded-lg min-h-[36px] ${
                filterPeriod === null
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] hover:bg-gray-200'
              }`}
            >
              전체
            </button>
            <button
              type="button"
              onClick={() => setFilterPeriod('this_month')}
              className={`px-3 py-1.5 text-sm rounded-lg min-h-[36px] ${
                filterPeriod === 'this_month'
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] hover:bg-gray-200'
              }`}
            >
              이번 달
            </button>
            <button
              type="button"
              onClick={() => setFilterPeriod('last_month')}
              className={`px-3 py-1.5 text-sm rounded-lg min-h-[36px] ${
                filterPeriod === 'last_month'
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] hover:bg-gray-200'
              }`}
            >
              지난 달
            </button>
            <button
              type="button"
              onClick={() => setFilterPeriod('this_year')}
              className={`px-3 py-1.5 text-sm rounded-lg min-h-[36px] ${
                filterPeriod === 'this_year'
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] hover:bg-gray-200'
              }`}
            >
              올해
            </button>
          </div>
        </div>

        {/* Transaction Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[var(--color-bg-secondary)]">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-secondary)]">
                  사건
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-secondary)]">
                  내용
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-secondary)]">
                  금액
                </th>
                <th className="px-4 py-3 text-center text-sm font-medium text-[var(--color-text-secondary)]">
                  상태
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-secondary)]">
                  날짜
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {earnings?.transactions && earnings.transactions.length > 0 ? (
                earnings.transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-[var(--color-bg-secondary)]">
                    <td className="px-4 py-4">
                      <span className="font-medium text-[var(--color-text-primary)]">
                        {tx.case_title || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-[var(--color-text-secondary)]">
                      {tx.description || '-'}
                    </td>
                    <td className="px-4 py-4 text-right font-medium text-[var(--color-text-primary)]">
                      {formatCurrency(tx.amount)}
                    </td>
                    <td className="px-4 py-4 text-center">
                      {getStatusBadge(tx.status)}
                    </td>
                    <td className="px-4 py-4 text-right text-[var(--color-text-secondary)]">
                      {formatDate(tx.created_at)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-[var(--color-text-secondary)]">
                    거래 내역이 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bank Account Section */}
      <div className="bg-white p-6 rounded-lg border border-[var(--color-border)]">
        <h2 className="text-lg font-semibold mb-4">정산 계좌</h2>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-[var(--color-bg-secondary)] rounded-lg">
              <svg className="w-6 h-6 text-[var(--color-text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <div>
              <p className="text-[var(--color-text-secondary)] text-sm">등록된 계좌</p>
              <p className="font-medium">계좌 정보를 등록해 주세요</p>
            </div>
          </div>
          <button
            type="button"
            className="px-4 py-2 border border-[var(--color-border)] rounded-lg
              text-[var(--color-text-primary)] hover:bg-[var(--color-bg-secondary)]
              min-h-[44px]"
          >
            계좌 등록
          </button>
        </div>
      </div>
    </div>
  );
}
