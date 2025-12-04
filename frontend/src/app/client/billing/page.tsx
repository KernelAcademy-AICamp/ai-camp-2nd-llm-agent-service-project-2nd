/**
 * Client Billing Page
 * 003-role-based-ui Feature - US8 (T152)
 *
 * Page for clients to view and pay invoices.
 */

'use client';

import { useState, useCallback } from 'react';
import { useBilling, formatCurrency, getStatusBadgeStyle, getStatusLabel } from '@/hooks/useBilling';
import type { Invoice, InvoicePaymentRequest } from '@/types/billing';

export default function ClientBillingPage() {
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    invoices,
    total,
    totalPending,
    totalPaid,
    loading,
    error,
    pay,
  } = useBilling({ isClient: true });

  const handlePayClick = useCallback((invoice: Invoice) => {
    setSelectedInvoice(invoice);
  }, []);

  const handlePaymentSubmit = useCallback(
    async (paymentMethod: string) => {
      if (!selectedInvoice) return;

      setPaymentLoading(true);
      try {
        const result = await pay(selectedInvoice.id, {
          payment_method: paymentMethod,
        });

        if (result) {
          setSuccessMessage('결제가 완료되었습니다.');
          setSelectedInvoice(null);
          setTimeout(() => setSuccessMessage(null), 3000);
        }
      } finally {
        setPaymentLoading(false);
      }
    },
    [selectedInvoice, pay]
  );

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">청구서/결제</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          발행된 청구서를 확인하고 결제하세요.
        </p>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="p-4 bg-green-50 text-green-700 rounded-lg flex items-center justify-between">
          <span>{successMessage}</span>
          <button
            type="button"
            onClick={() => setSuccessMessage(null)}
            className="p-1 hover:bg-green-100 rounded"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 text-[var(--color-error)] rounded-lg">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg border border-[var(--color-border)]">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-[var(--color-primary)]/10 rounded-lg">
              <svg className="w-6 h-6 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <span className="text-[var(--color-text-secondary)]">총 청구서</span>
          </div>
          <p className="text-2xl font-bold text-[var(--color-text-primary)]">{total}건</p>
        </div>

        <div className="bg-white p-6 rounded-lg border border-[var(--color-border)]">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span className="text-[var(--color-text-secondary)]">결제 대기</span>
          </div>
          <p className="text-2xl font-bold text-yellow-600">{formatCurrency(totalPending)}</p>
        </div>

        <div className="bg-white p-6 rounded-lg border border-[var(--color-border)]">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span className="text-[var(--color-text-secondary)]">결제 완료</span>
          </div>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(totalPaid)}</p>
        </div>
      </div>

      {/* Invoice List */}
      <div className="bg-white rounded-lg border border-[var(--color-border)]">
        <div className="p-4 border-b border-[var(--color-border)]">
          <h2 className="text-lg font-semibold">청구서 목록</h2>
        </div>

        {invoices.length > 0 ? (
          <div className="divide-y divide-[var(--color-border)]">
            {invoices.map((invoice) => (
              <div key={invoice.id} className="p-4 hover:bg-[var(--color-bg-secondary)]">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-medium text-[var(--color-text-primary)]">
                        {invoice.case_title || '사건명 없음'}
                      </h3>
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeStyle(
                          invoice.status
                        )}`}
                      >
                        {getStatusLabel(invoice.status)}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-[var(--color-text-secondary)]">
                      <span>발행일: {formatDate(invoice.created_at)}</span>
                      {invoice.due_date && (
                        <span>결제 기한: {formatDate(invoice.due_date)}</span>
                      )}
                      {invoice.paid_at && (
                        <span>결제일: {formatDate(invoice.paid_at)}</span>
                      )}
                    </div>
                    {invoice.description && (
                      <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
                        {invoice.description}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-4 ml-4">
                    <div className="text-right">
                      <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                        {formatCurrency(invoice.amount)}
                      </p>
                    </div>
                    {invoice.status === 'pending' && (
                      <button
                        type="button"
                        onClick={() => handlePayClick(invoice)}
                        className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg
                          font-medium hover:bg-[var(--color-primary-hover)]
                          min-h-[44px]"
                      >
                        결제하기
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
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

      {/* Payment Modal */}
      {selectedInvoice && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-md mx-4">
            <div className="p-6 border-b border-[var(--color-border)]">
              <h2 className="text-xl font-semibold">결제하기</h2>
            </div>
            <div className="p-6">
              <div className="mb-6">
                <p className="text-[var(--color-text-secondary)] mb-1">
                  {selectedInvoice.case_title}
                </p>
                <p className="text-3xl font-bold text-[var(--color-text-primary)]">
                  {formatCurrency(selectedInvoice.amount)}
                </p>
              </div>

              <div className="space-y-3">
                <p className="text-sm font-medium text-[var(--color-text-secondary)]">
                  결제 수단 선택
                </p>
                <button
                  type="button"
                  onClick={() => handlePaymentSubmit('card')}
                  disabled={paymentLoading}
                  className="w-full p-4 border border-[var(--color-border)] rounded-lg
                    hover:bg-[var(--color-bg-secondary)] flex items-center gap-3
                    disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg className="w-6 h-6 text-[var(--color-text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                  <span className="font-medium">신용/체크카드</span>
                </button>
                <button
                  type="button"
                  onClick={() => handlePaymentSubmit('bank')}
                  disabled={paymentLoading}
                  className="w-full p-4 border border-[var(--color-border)] rounded-lg
                    hover:bg-[var(--color-bg-secondary)] flex items-center gap-3
                    disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg className="w-6 h-6 text-[var(--color-text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
                  </svg>
                  <span className="font-medium">계좌이체</span>
                </button>
              </div>
            </div>
            <div className="p-6 border-t border-[var(--color-border)]">
              <button
                type="button"
                onClick={() => setSelectedInvoice(null)}
                disabled={paymentLoading}
                className="w-full py-3 border border-[var(--color-border)] rounded-lg
                  text-[var(--color-text-primary)] hover:bg-[var(--color-bg-secondary)]
                  disabled:opacity-50 disabled:cursor-not-allowed"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
