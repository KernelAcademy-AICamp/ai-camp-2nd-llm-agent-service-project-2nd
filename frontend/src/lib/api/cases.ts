/**
 * Cases API Client
 * Handles case CRUD operations
 */

import { apiRequest, ApiResponse } from './client';

export interface Case {
  id: string;
  title: string;
  client_name: string;
  description?: string;
  status: 'active' | 'in_progress' | 'closed';
  evidence_count: number;
  draft_status: 'not_started' | 'in_progress' | 'completed';
  created_at: string;
  updated_at: string;
}

export interface CreateCaseRequest {
  title: string;
  client_name: string;
  description?: string;
}

export interface CaseListResponse {
  cases: Case[];
  total: number;
}

/**
 * Get list of cases for current user
 */
export async function getCases(): Promise<ApiResponse<CaseListResponse>> {
  return apiRequest<CaseListResponse>('/cases', {
    method: 'GET',
  });
}

/**
 * Get a single case by ID
 */
export async function getCase(caseId: string): Promise<ApiResponse<Case>> {
  return apiRequest<Case>(`/cases/${caseId}`, {
    method: 'GET',
  });
}

/**
 * Create a new case
 */
export async function createCase(
  data: CreateCaseRequest
): Promise<ApiResponse<Case>> {
  return apiRequest<Case>('/cases', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
}

/**
 * Update case status
 */
export async function updateCaseStatus(
  caseId: string,
  status: Case['status']
): Promise<ApiResponse<Case>> {
  return apiRequest<Case>(`/cases/${caseId}/status`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status }),
  });
}

/**
 * Delete a case (soft delete)
 */
export async function deleteCase(caseId: string): Promise<ApiResponse<void>> {
  return apiRequest<void>(`/cases/${caseId}`, {
    method: 'DELETE',
  });
}
