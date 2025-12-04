/**
 * Billing Types
 * 003-role-based-ui Feature - US8
 *
 * TypeScript types for billing and invoice management.
 */

export type InvoiceStatus = 'pending' | 'paid' | 'overdue' | 'cancelled';

export interface Invoice {
  id: string;
  case_id: string;
  case_title?: string | null;
  client_id: string;
  client_name?: string | null;
  lawyer_id: string;
  lawyer_name?: string | null;
  amount: string;
  description?: string | null;
  status: InvoiceStatus;
  due_date?: string | null;
  paid_at?: string | null;
  created_at: string;
}

export interface InvoiceListResponse {
  invoices: Invoice[];
  total: number;
  total_pending: string;
  total_paid: string;
}

export interface InvoiceCreateRequest {
  case_id: string;
  client_id: string;
  amount: string;
  description?: string;
  due_date?: string;
}

export interface InvoiceUpdateRequest {
  amount?: string;
  description?: string;
  status?: InvoiceStatus;
  due_date?: string;
}

export interface InvoicePaymentRequest {
  payment_method: string;
  payment_reference?: string;
}

export interface InvoiceFilters {
  status?: InvoiceStatus;
  case_id?: string;
  page?: number;
  limit?: number;
}
