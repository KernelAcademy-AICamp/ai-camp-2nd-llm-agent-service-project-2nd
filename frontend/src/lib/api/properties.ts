/**
 * Properties API Client
 * 재산분할 분석 API
 */

import { apiRequest, ApiResponse } from './client';
import { DivisionPrediction } from '@/types/property';

/**
 * API 응답 형식 (Backend l-demo)
 */
interface AnalyzeImpactResponse {
  status: string;
  result: DivisionPrediction;
}

/**
 * 증거 정보 (요청용)
 */
interface EvidenceInput {
  id: string;
  type: string;
  content?: string;
}

/**
 * 분석 요청 파라미터
 */
interface AnalyzeImpactParams {
  case_id: string;
  evidences: EvidenceInput[];
}

/**
 * 증거 기반 재산분할 영향도를 분석합니다.
 *
 * @param params - 분석 요청 파라미터
 * @param params.case_id - 사건 ID
 * @param params.evidences - 분석할 증거 목록
 * @returns 재산분할 예측 결과
 *
 * @example
 * ```typescript
 * const response = await analyzeImpact({
 *   case_id: 'case-123',
 *   evidences: [{ id: 'ev-001', type: '카카오톡' }]
 * });
 * if (response.data) {
 *   console.log(`원고: ${response.data.plaintiff_ratio}%`);
 *   console.log(`피고: ${response.data.defendant_ratio}%`);
 * }
 * ```
 */
export async function analyzeImpact(
  params: AnalyzeImpactParams
): Promise<ApiResponse<DivisionPrediction>> {
  const response = await apiRequest<AnalyzeImpactResponse>(
    '/l-demo/analyze/impact',
    {
      method: 'POST',
      body: JSON.stringify({
        case_id: params.case_id,
        evidences: params.evidences,
      }),
    }
  );

  // 성공 시 result를 추출하여 반환
  if (response.data) {
    return {
      data: response.data.result,
      status: response.status,
    };
  }

  // 에러 시 에러 정보만 반환
  return {
    error: response.error,
    status: response.status,
  };
}
