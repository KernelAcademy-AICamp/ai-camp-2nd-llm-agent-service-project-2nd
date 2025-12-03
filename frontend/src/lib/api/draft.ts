/**
 * Draft API Client
 * Handles draft generation and export operations
 */

import { apiRequest, ApiResponse } from './client';

export interface DraftCitation {
  evidence_id: string;
  snippet: string;
  labels: string[];
}

export interface DraftPreviewRequest {
  sections?: string[];
  language?: string;
  style?: string;
}

export interface DraftPreviewResponse {
  case_id: string;
  draft_text: string;
  citations: DraftCitation[];
  generated_at: string;
}

/**
 * Generate draft preview using RAG + GPT-4o
 */
export async function generateDraftPreview(
  caseId: string,
  request: DraftPreviewRequest = {}
): Promise<ApiResponse<DraftPreviewResponse>> {
  return apiRequest<DraftPreviewResponse>(`/cases/${caseId}/draft-preview`, {
    method: 'POST',
    body: JSON.stringify({
      sections: request.sections || ['청구취지', '청구원인'],
      language: request.language || 'ko',
      style: request.style || '법원 제출용_표준',
    }),
  });
}
