/**
 * Billing API Client
 * 003-role-based-ui Feature - US8
 *
 * API functions for billing and invoice management.
 */

import { apiClient, type ApiResponse } from './client';
import type {
  Invoice,
  InvoiceListResponse,
  InvoiceCreateRequest,
  InvoiceUpdateRequest,
  InvoicePaymentRequest,
  InvoiceFilters,
} from '@/types/billing';

/**
 * Get list of invoices (lawyer endpoint)
 */
export async function getInvoices(
  filters?: InvoiceFilters
): Promise<ApiResponse<InvoiceListResponse>> {
  const params = new URLSearchParams();

  if (filters?.status) params.append('status', filters.status);
  if (filters?.case_id) params.append('case_id', filters.case_id);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.limit) params.append('limit', String(filters.limit));

  const queryString = params.toString();
  const url = queryString ? `/billing/invoices?${queryString}` : '/billing/invoices';

  return apiClient.get<InvoiceListResponse>(url);
}

/**
 * Create a new invoice (lawyer endpoint)
 */
export async function createInvoice(
  data: InvoiceCreateRequest
): Promise<ApiResponse<Invoice>> {
  return apiClient.post<Invoice>('/billing/invoices', data);
}

/**
 * Get invoice by ID
 */
export async function getInvoice(
  invoiceId: string
): Promise<ApiResponse<Invoice>> {
  return apiClient.get<Invoice>(`/billing/invoices/${invoiceId}`);
}

/**
 * Update an invoice (lawyer endpoint)
 */
export async function updateInvoice(
  invoiceId: string,
  data: InvoiceUpdateRequest
): Promise<ApiResponse<Invoice>> {
  return apiClient.put<Invoice>(`/billing/invoices/${invoiceId}`, data);
}

/**
 * Delete an invoice (lawyer endpoint)
 */
export async function deleteInvoice(
  invoiceId: string
): Promise<ApiResponse<void>> {
  return apiClient.delete<void>(`/billing/invoices/${invoiceId}`);
}

/**
 * Get invoices for client
 */
export async function getClientInvoices(
  page?: number,
  limit?: number
): Promise<ApiResponse<InvoiceListResponse>> {
  const params = new URLSearchParams();

  if (page) params.append('page', String(page));
  if (limit) params.append('limit', String(limit));

  const queryString = params.toString();
  const url = queryString ? `/client/billing?${queryString}` : '/client/billing';

  return apiClient.get<InvoiceListResponse>(url);
}

/**
 * Pay an invoice (client endpoint)
 */
export async function payInvoice(
  invoiceId: string,
  data: InvoicePaymentRequest
): Promise<ApiResponse<Invoice>> {
  return apiClient.post<Invoice>(`/client/billing/${invoiceId}/pay`, data);
}
