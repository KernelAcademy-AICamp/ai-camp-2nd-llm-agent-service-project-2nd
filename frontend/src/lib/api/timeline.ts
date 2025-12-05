/**
 * Timeline API Client
 * 타임라인 관련 API 호출
 */

import { apiRequest, ApiResponse } from './client';
import { TimelineResult, TimelineEvent } from '@/types/timeline';

// =============================================================================
// API 응답 타입
// =============================================================================

interface TimelineApiResponse {
  status: string;
  case_id: string;
  result: TimelineResult;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * 사건 타임라인 조회
 *
 * @param caseId - 사건 ID
 * @returns 타임라인 결과
 */
export async function getTimeline(caseId: string): Promise<ApiResponse<TimelineResult>> {
  const response = await apiRequest<TimelineApiResponse>(
    `/cases/${caseId}/timeline`,
    { method: 'GET' }
  );

  if (response.data) {
    return { ...response, data: response.data.result };
  }
  return { error: response.error, status: response.status };
}

/**
 * 타임라인 이벤트 상세 조회
 *
 * @param caseId - 사건 ID
 * @param eventId - 이벤트 ID
 * @returns 타임라인 이벤트
 */
export async function getTimelineEvent(
  caseId: string,
  eventId: string
): Promise<ApiResponse<TimelineEvent>> {
  const response = await apiRequest<{ status: string; result: TimelineEvent }>(
    `/cases/${caseId}/timeline/${eventId}`,
    { method: 'GET' }
  );

  if (response.data) {
    return { ...response, data: response.data.result };
  }
  return { error: response.error, status: response.status };
}

/**
 * 타임라인 필터링 조회
 *
 * @param caseId - 사건 ID
 * @param filters - 필터 옵션
 * @returns 필터링된 타임라인
 */
export async function getFilteredTimeline(
  caseId: string,
  filters: {
    startDate?: string;
    endDate?: string;
    labels?: string[];
    speaker?: string;
    keyEventsOnly?: boolean;
  }
): Promise<ApiResponse<TimelineResult>> {
  const params = new URLSearchParams();

  if (filters.startDate) params.append('start_date', filters.startDate);
  if (filters.endDate) params.append('end_date', filters.endDate);
  if (filters.labels?.length) params.append('labels', filters.labels.join(','));
  if (filters.speaker) params.append('speaker', filters.speaker);
  if (filters.keyEventsOnly) params.append('key_events_only', 'true');

  const queryString = params.toString();
  const url = `/cases/${caseId}/timeline${queryString ? `?${queryString}` : ''}`;

  const response = await apiRequest<TimelineApiResponse>(url, { method: 'GET' });

  if (response.data) {
    return { ...response, data: response.data.result };
  }
  return { error: response.error, status: response.status };
}

/**
 * 이벤트 핀 고정/해제
 *
 * @param caseId - 사건 ID
 * @param eventId - 이벤트 ID
 * @param pinned - 핀 고정 여부
 * @returns 업데이트된 이벤트
 */
export async function toggleEventPin(
  caseId: string,
  eventId: string,
  pinned: boolean
): Promise<ApiResponse<TimelineEvent>> {
  const response = await apiRequest<{ status: string; result: TimelineEvent }>(
    `/cases/${caseId}/timeline/${eventId}/pin`,
    {
      method: 'PATCH',
      body: JSON.stringify({ is_pinned: pinned }),
    }
  );

  if (response.data) {
    return { ...response, data: response.data.result };
  }
  return { error: response.error, status: response.status };
}

// =============================================================================
// Demo API (L-Demo 연동)
// =============================================================================

/**
 * 텍스트 날짜 추출 (Demo)
 *
 * @param text - 분석할 텍스트
 * @returns 추출된 날짜 목록
 */
export async function extractDates(text: string): Promise<ApiResponse<{
  dates: Array<{
    original: string;
    datetime: string | null;
    confidence: number;
  }>;
}>> {
  const response = await apiRequest<{
    status: string;
    result: {
      dates: Array<{
        original: string;
        datetime: string | null;
        confidence: number;
      }>;
    };
  }>('/l-demo/analyze/dates', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });

  if (response.data) {
    return { ...response, data: response.data.result };
  }
  return { error: response.error, status: response.status };
}

/**
 * 이벤트 요약 생성 (Demo)
 *
 * @param text - 요약할 텍스트
 * @param faultTypes - 유책사유 라벨 (선택)
 * @returns 요약 결과
 */
export async function summarizeEvent(
  text: string,
  faultTypes?: string[]
): Promise<ApiResponse<{
  summary: string;
  keywords: string[];
  fault_label?: string;
}>> {
  const params = new URLSearchParams();
  if (faultTypes?.length) {
    params.append('fault_types', faultTypes.join(','));
  }

  const response = await apiRequest<{
    status: string;
    result: {
      summary: string;
      keywords: string[];
      fault_label?: string;
    };
  }>(`/l-demo/analyze/summarize?${params.toString()}`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  });

  if (response.data) {
    return { ...response, data: response.data.result };
  }
  return { error: response.error, status: response.status };
}
