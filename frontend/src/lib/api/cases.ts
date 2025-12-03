/**
 * Cases API Client
 * Handles case CRUD operations
 */

import { apiRequest, ApiResponse } from './client';

/**
 * API Case type - matches backend snake_case convention
 * Use mapApiCaseToCase() from '@/lib/utils/caseMapper' to convert to frontend Case type
 */
export interface ApiCase {
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

/** Alias for ApiCase - use when frontend component needs Case type */
export type Case = ApiCase;

export interface CreateCaseRequest {
  title: string;
  client_name: string;
  description?: string;
}

export interface CaseListResponse {
  cases: ApiCase[];
  total: number;
}

/**
 * Get list of cases for current user
 */
export async function getCases(): Promise<ApiResponse<CaseListResponse>> {
  const response = await apiRequest<ApiCase[] | CaseListResponse>('/cases', {
    method: 'GET',
  });

  // Handle both array response (from backend) and object response
  if (response.data) {
    if (Array.isArray(response.data)) {
      // Backend returns array directly
      return {
        data: {
          cases: response.data,
          total: response.data.length,
        },
        status: response.status,
      };
    }
    // Already in expected format
    return response as ApiResponse<CaseListResponse>;
  }

  return response as ApiResponse<CaseListResponse>;
}

/**
 * Get a single case by ID
 */
export async function getCase(caseId: string): Promise<ApiResponse<ApiCase>> {
  return apiRequest<ApiCase>(`/cases/${caseId}`, {
    method: 'GET',
  });
}

/**
 * Create a new case
 */
export async function createCase(
  data: CreateCaseRequest
): Promise<ApiResponse<ApiCase>> {
  return apiRequest<ApiCase>('/cases', {
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
  status: ApiCase['status']
): Promise<ApiResponse<ApiCase>> {
  return apiRequest<ApiCase>(`/cases/${caseId}/status`, {
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
