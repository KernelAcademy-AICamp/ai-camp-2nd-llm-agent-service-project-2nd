/**
 * Evidence API Client
 * Handles evidence upload and retrieval operations
 */

import { apiRequest, ApiResponse } from './client';

export interface Evidence {
  id: string;
  case_id: string;
  type: 'image' | 'audio' | 'video' | 'text' | 'pdf';
  filename: string;
  s3_key: string;
  size: number;
  content_type: string;
  status: 'pending' | 'processing' | 'processed' | 'failed';
  timestamp?: string;
  speaker?: string;
  ai_summary?: string;
  labels?: string[];
  insights?: string[];
  article_840_tags?: {
    categories: string[];
    confidence: number;
    matched_keywords: string[];
  };
  created_at: string;
}

export interface EvidenceDetail extends Evidence {
  content?: string; // STT/OCR 전문 텍스트
  qdrant_id?: string;
}

export interface EvidenceListResponse {
  evidence: Evidence[];
  total: number;
}

export interface PresignedUrlResponse {
  upload_url: string;
  evidence_temp_id: string;
  s3_key: string;
  fields?: Record<string, string>;
}

export interface UploadCompleteRequest {
  case_id: string;
  evidence_temp_id: string;
  s3_key: string;
  file_size: number;
  note?: string;
}

export interface UploadCompleteResponse {
  evidence_id: string;
  case_id: string;
  filename: string;
  s3_key: string;
  status: string;
  created_at: string;
}

/**
 * Get list of evidence for a case
 */
export async function getEvidence(
  caseId: string,
  filters?: {
    categories?: string[];
    type?: Evidence['type'];
  }
): Promise<ApiResponse<EvidenceListResponse>> {
  const params = new URLSearchParams();
  if (filters?.categories) {
    params.append('categories', filters.categories.join(','));
  }
  if (filters?.type) {
    params.append('type', filters.type);
  }

  const queryString = params.toString();
  const url = `/cases/${caseId}/evidence${queryString ? `?${queryString}` : ''}`;

  return apiRequest<EvidenceListResponse>(url, {
    method: 'GET',
  });
}

/**
 * Get a single evidence item by ID (basic info)
 */
export async function getEvidenceById(
  evidenceId: string
): Promise<ApiResponse<Evidence>> {
  return apiRequest<Evidence>(`/evidence/${evidenceId}`, {
    method: 'GET',
  });
}

/**
 * Get evidence detail with full content (STT/OCR text)
 */
export async function getEvidenceDetail(
  evidenceId: string
): Promise<ApiResponse<EvidenceDetail>> {
  return apiRequest<EvidenceDetail>(`/evidence/${evidenceId}`, {
    method: 'GET',
  });
}

/**
 * Get presigned URL for uploading evidence
 */
export async function getPresignedUploadUrl(
  caseId: string,
  filename: string,
  contentType: string
): Promise<ApiResponse<PresignedUrlResponse>> {
  return apiRequest<PresignedUrlResponse>('/evidence/presigned-url', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      case_id: caseId,
      filename,
      content_type: contentType
    }),
  });
}

/**
 * Notify backend that S3 upload is complete
 */
export async function notifyUploadComplete(
  request: UploadCompleteRequest
): Promise<ApiResponse<UploadCompleteResponse>> {
  return apiRequest<UploadCompleteResponse>('/evidence/upload-complete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percent: number;
}

/**
 * Upload file directly to S3 using presigned URL with progress tracking
 */
export async function uploadToS3(
  presignedUrl: string,
  file: File,
  onProgress?: (progress: UploadProgress) => void
): Promise<boolean> {
  return new Promise((resolve) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress({
          loaded: e.loaded,
          total: e.total,
          percent: Math.round((e.loaded / e.total) * 100),
        });
      }
    });

    xhr.addEventListener('load', () => {
      resolve(xhr.status >= 200 && xhr.status < 300);
    });

    xhr.addEventListener('error', () => {
      console.error('S3 upload error');
      resolve(false);
    });

    xhr.open('PUT', presignedUrl);
    xhr.setRequestHeader('Content-Type', file.type);
    xhr.send(file);
  });
}

/**
 * Delete evidence
 */
export async function deleteEvidence(
  evidenceId: string
): Promise<ApiResponse<void>> {
  return apiRequest<void>(`/evidence/${evidenceId}`, {
    method: 'DELETE',
  });
}

export interface RetryResponse {
  evidence_id: string;
  job_id: string;
  status: string;
  message: string;
}

/**
 * Retry processing for failed evidence
 * Re-queues the evidence for AI Worker processing
 */
export async function retryEvidence(
  evidenceId: string
): Promise<ApiResponse<RetryResponse>> {
  return apiRequest<RetryResponse>(`/evidence/${evidenceId}/retry`, {
    method: 'POST',
  });
}

export interface EvidenceStatusResponse {
  evidence_id: string;
  status: Evidence['status'];
  progress?: number;
  error_message?: string;
  retry_count?: number;
  max_retries?: number;
}

/**
 * Get the current processing status of evidence
 */
export async function getEvidenceStatus(
  evidenceId: string
): Promise<ApiResponse<EvidenceStatusResponse>> {
  return apiRequest<EvidenceStatusResponse>(`/evidence/${evidenceId}/status`, {
    method: 'GET',
  });
}
