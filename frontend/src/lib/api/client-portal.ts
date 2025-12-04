/**
 * Client Portal API Functions
 * 003-role-based-ui Feature - US4
 */

import { apiRequest } from './client';
import type {
  ClientDashboardResponse,
  ClientCaseListResponse,
  ClientCaseDetailResponse,
  EvidenceUploadRequest,
  EvidenceUploadResponse,
  EvidenceConfirmResponse,
} from '@/types/client-portal';

/**
 * Get client dashboard data
 */
export async function getClientDashboard() {
  return apiRequest<ClientDashboardResponse>('/client/dashboard', {
    method: 'GET',
    credentials: 'include',
  });
}

/**
 * Get client's case list
 */
export async function getClientCases() {
  return apiRequest<ClientCaseListResponse>('/client/cases', {
    method: 'GET',
    credentials: 'include',
  });
}

/**
 * Get client case detail
 */
export async function getClientCaseDetail(caseId: string) {
  return apiRequest<ClientCaseDetailResponse>(`/client/cases/${caseId}`, {
    method: 'GET',
    credentials: 'include',
  });
}

/**
 * Request presigned URL for evidence upload
 */
export async function requestEvidenceUpload(caseId: string, data: EvidenceUploadRequest) {
  return apiRequest<EvidenceUploadResponse>(`/client/cases/${caseId}/evidence`, {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify(data),
  });
}

/**
 * Confirm evidence upload completion
 */
export async function confirmEvidenceUpload(caseId: string, evidenceId: string, uploaded: boolean) {
  return apiRequest<EvidenceConfirmResponse>(
    `/client/cases/${caseId}/evidence/${evidenceId}/confirm`,
    {
      method: 'POST',
      credentials: 'include',
      body: JSON.stringify({ uploaded }),
    }
  );
}

/**
 * Upload file to S3 using presigned URL
 */
export async function uploadFileToS3(
  uploadUrl: string,
  file: File,
  onProgress?: (percent: number) => void
): Promise<{ success: boolean; error?: string }> {
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
        resolve({ success: true });
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
