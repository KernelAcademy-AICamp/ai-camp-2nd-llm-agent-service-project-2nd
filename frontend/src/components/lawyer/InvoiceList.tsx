/**
 * InvoiceList Component
 * 003-role-based-ui Feature - US8 (T149)
 *
 * Component for displaying list of invoices with filtering and actions.
 */

'use client';

import { useState } from 'react';
import type { Invoice, InvoiceStatus } from '@/types/billing';
import { formatCurrency, getStatusBadgeStyle, getStatusLabel } from '@/hooks/useBilling';

interface InvoiceListProps {
  invoices: Invoice[];
  total: number;
  totalPending: string;
  totalPaid: string;
  loading?: boolean;
  onFilterChange?: (status: InvoiceStatus | null) => void;
  onEdit?: (invoice: Invoice) => void;
  onDelete?: (invoice: Invoice) => void;
  onPageChange?: (page: number) => void;
  currentPage?: number;
  pageSize?: number;
  className?: string;
}

export default function InvoiceList({
  invoices,
  total,
  totalPending,
  totalPaid,
  loading = false,
  onFilterChange,
  onEdit,
  onDelete,
  onPageChange,
  currentPage = 1,
  pageSize = 20,
  className = '',
}: InvoiceListProps) {
  const [activeFilter, setActiveFilter] = useState<InvoiceStatus | null>(null);

  const handleFilterClick = (status: InvoiceStatus | null) => {
    setActiveFilter(status);
    onFilterChange?.(status);
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const totalPages = Math.ceil(total / pageSize);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-[var(--color-border)]">
          <p className="text-sm text-[var(--color-text-secondary)]">총 청구서</p>
          <p className="text-2xl font-bold text-[var(--color-text-primary)]">{total}건</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-[var(--color-border)]">
          <p className="text-sm text-[var(--color-text-secondary)]">대기중 금액</p>
          <p className="text-2xl font-bold text-yellow-600">{formatCurrency(totalPending)}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-[var(--color-border)]">
          <p className="text-sm text-[var(--color-text-secondary)]">결제 완료</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(totalPaid)}</p>
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="flex flex-wrap gap-2">
        {([null, 'pending', 'paid', 'overdue', 'cancelled'] as const).map((status) => (
          <button
            key={status ?? 'all'}
            type="button"
            onClick={() => handleFilterClick(status)}
            className={`px-4 py-2 rounded-lg min-h-[40px] transition-colors ${
              activeFilter === status
                ? 'bg-[var(--color-primary)] text-white'
                : 'bg-[var(--color-bg-secondary)] text-[var(--color-text-secondary)] hover:bg-gray-200'
            }`}
          >
            {status === null ? '전체' : getStatusLabel(status)}
          </button>
        ))}
      </div>

      {/* Invoice Table */}
      <div className="bg-white rounded-lg border border-[var(--color-border)] overflow-hidden">
        {invoices.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[var(--color-bg-secondary)]">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-secondary)]">
                      사건
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-[var(--color-text-secondary)]">
                      의뢰인
                    </th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-secondary)]">
                      금액
                    </th>
                    <th className="px-4 py-3 text-center text-sm font-medium text-[var(--color-text-secondary)]">
                      상태
                    </th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-secondary)]">
                      발행일
                    </th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-[var(--color-text-secondary)]">
                      결제 기한
                    </th>
                    <th className="px-4 py-3 text-center text-sm font-medium text-[var(--color-text-secondary)]">
                      액션
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-border)]">
                  {invoices.map((invoice) => (
                    <tr key={invoice.id} className="hover:bg-[var(--color-bg-secondary)]">
                      <td className="px-4 py-4">
                        <span className="font-medium text-[var(--color-text-primary)]">
                          {invoice.case_title || '-'}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-[var(--color-text-secondary)]">
                        {invoice.client_name || '-'}
                      </td>
                      <td className="px-4 py-4 text-right font-medium text-[var(--color-text-primary)]">
                        {formatCurrency(invoice.amount)}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeStyle(
                            invoice.status
                          )}`}
                        >
                          {getStatusLabel(invoice.status)}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right text-[var(--color-text-secondary)]">
                        {formatDate(invoice.created_at)}
                      </td>
                      <td className="px-4 py-4 text-right text-[var(--color-text-secondary)]">
                        {formatDate(invoice.due_date)}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <div className="flex items-center justify-center gap-2">
                          {onEdit && (
                            <button
                              type="button"
                              onClick={() => onEdit(invoice)}
                              className="p-1 text-[var(--color-primary)] hover:bg-blue-50 rounded"
                              aria-label="수정"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                />
                              </svg>
                            </button>
                          )}
                          {onDelete && invoice.status === 'pending' && (
                            <button
                              type="button"
                              onClick={() => onDelete(invoice)}
                              className="p-1 text-[var(--color-error)] hover:bg-red-50 rounded"
                              aria-label="삭제"
                            >
                              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                />
                              </svg>
                            </button>
                          )}
                        </div>
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
                  총 {total}건 중 {(currentPage - 1) * pageSize + 1}-
                  {Math.min(currentPage * pageSize, total)}건
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => onPageChange?.(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-1.5 border border-[var(--color-border)] rounded
                      disabled:opacity-50 disabled:cursor-not-allowed
                      hover:bg-[var(--color-bg-secondary)]"
                  >
                    이전
                  </button>
                  <span className="px-3 py-1.5">
                    {currentPage} / {totalPages}
                  </span>
                  <button
                    type="button"
                    onClick={() => onPageChange?.(currentPage + 1)}
                    disabled={currentPage === totalPages}
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
            <p>청구서가 없습니다.</p>
          </div>
        )}
      </div>
    </div>
  );
}
