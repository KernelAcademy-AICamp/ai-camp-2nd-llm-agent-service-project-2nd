/**
 * Relationship API Client
 * 인물 관계도 분석 API
 */

import { apiRequest, ApiResponse } from './client';
import { RelationshipGraph } from '@/types/relationship';

/**
 * API 응답 형식 (Backend l-demo)
 */
interface AnalyzeRelationshipsResponse {
  status: string;
  result: RelationshipGraph;
}

/**
 * 텍스트에서 인물 관계를 분석합니다.
 *
 * @param text - 분석할 텍스트 (카카오톡 대화 등)
 * @returns 관계 그래프 (노드 + 엣지)
 *
 * @example
 * ```typescript
 * const response = await analyzeRelationships('김철수: 여보, 언제 와?');
 * if (response.data) {
 *   console.log(response.data.nodes); // 인물 목록
 *   console.log(response.data.edges); // 관계 목록
 * }
 * ```
 */
export async function analyzeRelationships(
  text: string
): Promise<ApiResponse<RelationshipGraph>> {
  const response = await apiRequest<AnalyzeRelationshipsResponse>(
    '/l-demo/analyze/relationships',
    {
      method: 'POST',
      body: JSON.stringify({ text }),
    }
  );

  // 성공 시 result를 추출하여 반환
  if (response.data) {
    return {
      data: response.data.result,
      status: response.status,
    };
  }

  // 에러 시 그대로 반환
  return response as ApiResponse<RelationshipGraph>;
}
