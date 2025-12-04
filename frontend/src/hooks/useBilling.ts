/**
 * useBilling Hook
 * 003-role-based-ui Feature - US8 (T153)
 *
 * Hook for billing and invoice management.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  getInvoices,
  createInvoice,
  updateInvoice,
  deleteInvoice,
  getClientInvoices,
  payInvoice,
} from '@/lib/api/billing';
import type {
  Invoice,
  InvoiceListResponse,
  InvoiceCreateRequest,
  InvoiceUpdateRequest,
  InvoicePaymentRequest,
  InvoiceFilters,
  InvoiceStatus,
} from '@/types/billing';

interface UseBillingOptions {
  filters?: InvoiceFilters;
  isClient?: boolean;
  autoFetch?: boolean;
}

interface UseBillingReturn {
  invoices: Invoice[];
  total: number;
  totalPending: string;
  totalPaid: string;
  loading: boolean;
  error: string | null;
  filters: InvoiceFilters;
  setFilters: (filters: InvoiceFilters) => void;
  refetch: () => Promise<void>;
  create: (data: InvoiceCreateRequest) => Promise<Invoice | null>;
  update: (id: string, data: InvoiceUpdateRequest) => Promise<Invoice | null>;
  remove: (id: string) => Promise<boolean>;
  pay: (id: string, data: InvoicePaymentRequest) => Promise<Invoice | null>;
}

export function useBilling(options: UseBillingOptions = {}): UseBillingReturn {
  const { filters: initialFilters = {}, isClient = false, autoFetch = true } = options;

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPending, setTotalPending] = useState('0');
  const [totalPaid, setTotalPaid] = useState('0');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<InvoiceFilters>(initialFilters);

  const fetchInvoices = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const { data, error: apiError } = isClient
        ? await getClientInvoices(filters.page, filters.limit)
        : await getInvoices(filters);

      if (apiError) {
        setError(apiError);
      } else if (data) {
        setInvoices(data.invoices);
        setTotal(data.total);
        setTotalPending(data.total_pending);
        setTotalPaid(data.total_paid);
      }
    } catch {
      setError('청구서 목록을 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, [filters, isClient]);

  useEffect(() => {
    if (autoFetch) {
      fetchInvoices();
    }
  }, [fetchInvoices, autoFetch]);

  const create = useCallback(
    async (data: InvoiceCreateRequest): Promise<Invoice | null> => {
      const { data: invoice, error: apiError } = await createInvoice(data);

      if (apiError) {
        setError(apiError);
        return null;
      }

      if (invoice) {
        // Refetch to update the list
        await fetchInvoices();
        return invoice;
      }

      return null;
    },
    [fetchInvoices]
  );

  const update = useCallback(
    async (id: string, data: InvoiceUpdateRequest): Promise<Invoice | null> => {
      const { data: invoice, error: apiError } = await updateInvoice(id, data);

      if (apiError) {
        setError(apiError);
        return null;
      }

      if (invoice) {
        // Update the invoice in the list
        setInvoices((prev) =>
          prev.map((inv) => (inv.id === id ? invoice : inv))
        );
        return invoice;
      }

      return null;
    },
    []
  );

  const remove = useCallback(
    async (id: string): Promise<boolean> => {
      const { error: apiError } = await deleteInvoice(id);

      if (apiError) {
        setError(apiError);
        return false;
      }

      // Remove from list
      setInvoices((prev) => prev.filter((inv) => inv.id !== id));
      setTotal((prev) => prev - 1);
      return true;
    },
    []
  );

  const pay = useCallback(
    async (id: string, data: InvoicePaymentRequest): Promise<Invoice | null> => {
      const { data: invoice, error: apiError } = await payInvoice(id, data);

      if (apiError) {
        setError(apiError);
        return null;
      }

      if (invoice) {
        // Update the invoice in the list
        setInvoices((prev) =>
          prev.map((inv) => (inv.id === id ? invoice : inv))
        );
        return invoice;
      }

      return null;
    },
    []
  );

  return {
    invoices,
    total,
    totalPending,
    totalPaid,
    loading,
    error,
    filters,
    setFilters,
    refetch: fetchInvoices,
    create,
    update,
    remove,
    pay,
  };
}

// Helper function to format currency
export function formatCurrency(amount: string | number): string {
  const numAmount = typeof amount === 'string' ? parseInt(amount, 10) : amount;
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
  }).format(numAmount);
}

// Helper function to get status badge styles
export function getStatusBadgeStyle(status: InvoiceStatus): string {
  const styles: Record<InvoiceStatus, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    paid: 'bg-green-100 text-green-700',
    overdue: 'bg-red-100 text-red-700',
    cancelled: 'bg-gray-100 text-gray-700',
  };
  return styles[status];
}

// Helper function to get status label in Korean
export function getStatusLabel(status: InvoiceStatus): string {
  const labels: Record<InvoiceStatus, string> = {
    pending: '대기중',
    paid: '결제완료',
    overdue: '연체',
    cancelled: '취소',
  };
  return labels[status];
}
