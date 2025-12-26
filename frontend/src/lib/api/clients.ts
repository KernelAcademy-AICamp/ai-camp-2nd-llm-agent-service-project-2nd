/**
 * Clients API Client
 * 005-lawyer-portal-pages Feature - US2
 *
 * API functions for lawyer's client management.
 */

import { apiClient, ApiResponse } from './client';
import {
  ClientItem,
  ClientListResponse,
  ClientFilter,
  ClientDetail,
} from '@/types/client';

/**
 * Get list of lawyer's clients with filters
 */
export async function getClients(
  filters?: ClientFilter
): Promise<ApiResponse<ClientListResponse>> {
  const params = new URLSearchParams();

  if (filters) {
    if (filters.search) params.append('search', filters.search);
    if (filters.status && filters.status !== 'all') params.append('status', filters.status);
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    if (filters.sort_order) params.append('sort_order', filters.sort_order);
    if (filters.page) params.append('page', String(filters.page));
    if (filters.page_size) params.append('page_size', String(filters.page_size));
  }

  const queryString = params.toString();
  const url = queryString ? `/clients/lawyer-portal?${queryString}` : '/clients/lawyer-portal';

  return apiClient.get<ClientListResponse>(url);
}

/**
 * Get client details by ID
 */
export async function getClientDetail(
  clientId: string
): Promise<ApiResponse<ClientDetail>> {
  return apiClient.get<ClientDetail>(`/clients/lawyer-portal/${clientId}`);
}

// Re-export types for convenience
export type { ClientItem, ClientListResponse, ClientFilter, ClientDetail };

// ============== Client Contact CRUD (US2 - Lawyer Portal) ==============

import type {
  ClientContact,
  ClientContactCreate,
  ClientContactUpdate,
  ClientContactListResponse,
  ClientContactQueryParams,
} from '@/types/client';

const CLIENT_CONTACTS_PATH = '/clients';

/**
 * Get list of client contacts
 */
export async function getClientContacts(
  params?: ClientContactQueryParams
): Promise<ApiResponse<ClientContactListResponse>> {
  const searchParams = new URLSearchParams();

  if (params?.search) {
    searchParams.append('search', params.search);
  }
  if (params?.page) {
    searchParams.append('page', String(params.page));
  }
  if (params?.limit) {
    searchParams.append('limit', String(params.limit));
  }

  const queryString = searchParams.toString();
  const url = queryString ? `${CLIENT_CONTACTS_PATH}?${queryString}` : CLIENT_CONTACTS_PATH;

  return apiClient.get<ClientContactListResponse>(url);
}

/**
 * Get a single client contact by ID
 */
export async function getClientContact(
  clientId: string
): Promise<ApiResponse<ClientContact>> {
  return apiClient.get<ClientContact>(`${CLIENT_CONTACTS_PATH}/${clientId}`);
}

/**
 * Create a new client contact
 */
export async function createClientContact(
  data: ClientContactCreate
): Promise<ApiResponse<ClientContact>> {
  return apiClient.post<ClientContact>(CLIENT_CONTACTS_PATH, data);
}

/**
 * Update an existing client contact
 */
export async function updateClientContact(
  clientId: string,
  data: ClientContactUpdate
): Promise<ApiResponse<ClientContact>> {
  return apiClient.patch<ClientContact>(`${CLIENT_CONTACTS_PATH}/${clientId}`, data);
}

/**
 * Delete a client contact
 */
export async function deleteClientContact(
  clientId: string
): Promise<ApiResponse<{ success: boolean }>> {
  return apiClient.delete<{ success: boolean }>(`${CLIENT_CONTACTS_PATH}/${clientId}`);
}

// Re-export contact types
export type {
  ClientContact,
  ClientContactCreate,
  ClientContactUpdate,
  ClientContactListResponse,
  ClientContactQueryParams,
};
