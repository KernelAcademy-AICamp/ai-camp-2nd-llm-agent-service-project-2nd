/**
 * Lawyer Billing Page
 * 003-role-based-ui Feature - US8 (T151)
 *
 * Page for managing invoices and billing.
 */

'use client';

import { useState, useCallback } from 'react';
import { useBilling } from '@/hooks/useBilling';
import InvoiceList from '@/components/lawyer/InvoiceList';
import InvoiceForm from '@/components/lawyer/InvoiceForm';
import type { Invoice, InvoiceStatus, InvoiceCreateRequest, InvoiceUpdateRequest } from '@/types/billing';

type ViewMode = 'list' | 'create' | 'edit';

export default function LawyerBillingPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [editingInvoice, setEditingInvoice] = useState<Invoice | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    invoices,
    total,
    totalPending,
    totalPaid,
    loading,
    error,
    filters,
    setFilters,
    create,
    update,
    remove,
  } = useBilling();

  // Mock cases for demo (in real app, fetch from API)
  const mockCases = [
    { id: 'case_001', title: '김○○ 이혼 소송', client_id: 'client_001', client_name: '김철수' },
    { id: 'case_002', title: '이○○ 재산분할', client_id: 'client_002', client_name: '이영희' },
    { id: 'case_003', title: '박○○ 양육권 분쟁', client_id: 'client_003', client_name: '박민수' },
  ];

  const handleFilterChange = useCallback(
    (status: InvoiceStatus | null) => {
      setFilters({ ...filters, status: status || undefined, page: 1 });
    },
    [filters, setFilters]
  );

  const handlePageChange = useCallback(
    (page: number) => {
      setFilters({ ...filters, page });
    },
    [filters, setFilters]
  );

  const handleCreate = useCallback(async (data: InvoiceCreateRequest) => {
    setFormLoading(true);
    try {
      const invoice = await create(data);
      if (invoice) {
        setSuccessMessage('청구서가 성공적으로 발행되었습니다.');
        setViewMode('list');
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } finally {
      setFormLoading(false);
    }
  }, [create]);

  const handleEdit = useCallback((invoice: Invoice) => {
    setEditingInvoice(invoice);
    setViewMode('edit');
  }, []);

  const handleUpdate = useCallback(
    async (data: InvoiceUpdateRequest) => {
      if (!editingInvoice) return;

      setFormLoading(true);
      try {
        const invoice = await update(editingInvoice.id, data);
        if (invoice) {
          setSuccessMessage('청구서가 성공적으로 수정되었습니다.');
          setViewMode('list');
          setEditingInvoice(null);
          setTimeout(() => setSuccessMessage(null), 3000);
        }
      } finally {
        setFormLoading(false);
      }
    },
    [editingInvoice, update]
  );

  const handleDelete = useCallback(
    async (invoice: Invoice) => {
      if (!confirm('이 청구서를 삭제하시겠습니까?')) return;

      const success = await remove(invoice.id);
      if (success) {
        setSuccessMessage('청구서가 삭제되었습니다.');
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    },
    [remove]
  );

  const handleCancel = useCallback(() => {
    setViewMode('list');
    setEditingInvoice(null);
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">청구/결제 관리</h1>
          <p className="text-[var(--color-text-secondary)] mt-1">
            청구서를 발행하고 결제 상태를 관리하세요.
          </p>
        </div>
        {viewMode === 'list' && (
          <button
            type="button"
            onClick={() => setViewMode('create')}
            className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg
              font-medium hover:bg-[var(--color-primary-hover)]
              min-h-[44px] flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
            청구서 발행
          </button>
        )}
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

      {/* Content */}
      {viewMode === 'list' && (
        <InvoiceList
          invoices={invoices}
          total={total}
          totalPending={totalPending}
          totalPaid={totalPaid}
          loading={loading}
          onFilterChange={handleFilterChange}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onPageChange={handlePageChange}
          currentPage={filters.page || 1}
          pageSize={filters.limit || 20}
        />
      )}

      {viewMode === 'create' && (
        <div className="bg-white rounded-lg border border-[var(--color-border)]">
          <div className="p-6 border-b border-[var(--color-border)]">
            <h2 className="text-xl font-semibold">새 청구서 발행</h2>
          </div>
          <InvoiceForm
            cases={mockCases}
            onSubmit={handleCreate as (data: InvoiceCreateRequest | InvoiceUpdateRequest) => Promise<void>}
            onCancel={handleCancel}
            loading={formLoading}
          />
        </div>
      )}

      {viewMode === 'edit' && editingInvoice && (
        <div className="bg-white rounded-lg border border-[var(--color-border)]">
          <div className="p-6 border-b border-[var(--color-border)]">
            <h2 className="text-xl font-semibold">청구서 수정</h2>
          </div>
          <InvoiceForm
            invoice={editingInvoice}
            onSubmit={handleUpdate as (data: InvoiceCreateRequest | InvoiceUpdateRequest) => Promise<void>}
            onCancel={handleCancel}
            loading={formLoading}
          />
        </div>
      )}
    </div>
  );
}
