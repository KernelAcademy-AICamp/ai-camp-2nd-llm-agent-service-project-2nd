/**
 * Detective Portal API Functions
 * 003-role-based-ui Feature - US5
 */

import { apiRequest } from './client';
import type {
  DetectiveDashboardResponse,
  DetectiveCaseListResponse,
  DetectiveCaseDetailResponse,
  FieldRecordRequest,
  FieldRecordResponse,
  ReportRequest,
  ReportResponse,
  EarningsResponse,
  AcceptRejectResponse,
  FieldRecord,
  Transaction,
} from '@/types/detective-portal';

// Re-export types for convenience
export type { FieldRecord, Transaction, ReportRequest };
export type CaseDetailData = DetectiveCaseDetailResponse;
export type EarningsData = EarningsResponse;

/**
 * Get detective dashboard data
 */
export async function getDetectiveDashboard() {
  return apiRequest<DetectiveDashboardResponse>('/detective/dashboard', {
    method: 'GET',
    credentials: 'include',
  });
}

/**
 * Get detective's case list
 */
export async function getDetectiveCases(params?: {
  status?: string;
  page?: number;
  limit?: number;
}) {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.append('status', params.status);
  if (params?.page) searchParams.append('page', params.page.toString());
  if (params?.limit) searchParams.append('limit', params.limit.toString());

  const query = searchParams.toString();
  const url = query ? `/detective/cases?${query}` : '/detective/cases';

  return apiRequest<DetectiveCaseListResponse>(url, {
    method: 'GET',
    credentials: 'include',
  });
}

/**
 * Get detective case detail
 */
export async function getDetectiveCaseDetail(caseId: string) {
  return apiRequest<DetectiveCaseDetailResponse>(`/detective/cases/${caseId}`, {
    method: 'GET',
    credentials: 'include',
  });
}

/**
 * Accept an investigation case
 */
export async function acceptCase(caseId: string) {
  return apiRequest<AcceptRejectResponse>(`/detective/cases/${caseId}/accept`, {
    method: 'POST',
    credentials: 'include',
  });
}

/**
 * Reject an investigation case
 */
export async function rejectCase(caseId: string, reason: string) {
  return apiRequest<AcceptRejectResponse>(`/detective/cases/${caseId}/reject`, {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify({ reason }),
  });
}

/**
 * Create a field record for a case
 */
export async function createFieldRecord(
  caseId: string,
  data: FieldRecordRequest
) {
  return apiRequest<FieldRecordResponse>(`/detective/cases/${caseId}/records`, {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify(data),
  });
}

/**
 * Submit investigation report
 */
export async function submitReport(caseId: string, data: ReportRequest) {
  return apiRequest<ReportResponse>(`/detective/cases/${caseId}/report`, {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify(data),
  });
}

/**
 * Get detective earnings
 */
export async function getDetectiveEarnings(period?: string) {
  const url = period
    ? `/detective/earnings?period=${period}`
    : '/detective/earnings';

  return apiRequest<EarningsResponse>(url, {
    method: 'GET',
    credentials: 'include',
  });
}

/**
 * Upload photo to S3 using presigned URL
 */
export async function uploadPhoto(
  uploadUrl: string,
  file: File,
  onProgress?: (percent: number) => void
): Promise<{ success: boolean; url?: string; error?: string }> {
  return new Promise((resolve) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    });

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        // Extract the URL without query params
        const url = uploadUrl.split('?')[0];
        resolve({ success: true, url });
      } else {
        resolve({ success: false, error: `Upload failed: ${xhr.status}` });
      }
    });

    xhr.addEventListener('error', () => {
      resolve({ success: false, error: 'Network error during upload' });
    });

    xhr.open('PUT', uploadUrl);
    xhr.setRequestHeader('Content-Type', file.type);
    xhr.send(file);
  });
}
