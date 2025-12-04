/**
 * Relationship Visualization API Client
 * API functions for person extraction and relationship analysis
 */

import { apiRequest, ApiResponse } from './client';
import { RelationshipAnalysisResponse, RelationshipGraph } from '@/types/relationship';

/**
 * Analyze relationships from text
 * Uses the l-demo analyze endpoint
 */
export async function analyzeRelationships(
  text: string
): Promise<ApiResponse<RelationshipAnalysisResponse>> {
  return apiRequest<RelationshipAnalysisResponse>('/l-demo/analyze/relationships', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

/**
 * Get relationships for a case
 * Analyzes all evidence in the case and builds relationship graph
 */
export async function getCaseRelationships(
  caseId: string
): Promise<ApiResponse<RelationshipGraph>> {
  return apiRequest<RelationshipGraph>(`/cases/${caseId}/relationships`, {
    method: 'GET',
  });
}

/**
 * Mock data for development/testing
 * Returns sample relationship graph when backend API is not available
 */
export function getMockRelationshipGraph(): RelationshipGraph {
  return {
    nodes: [
      {
        id: 'person-1',
        name: '의뢰인',
        role: 'plaintiff',
        side: 'plaintiff_side',
        color: '#4CAF50',
      },
      {
        id: 'person-2',
        name: '상대방',
        role: 'defendant',
        side: 'defendant_side',
        color: '#F44336',
      },
      {
        id: 'person-3',
        name: '자녀',
        role: 'child',
        side: 'neutral',
        color: '#2196F3',
      },
      {
        id: 'person-4',
        name: '제3자',
        role: 'third_party',
        side: 'defendant_side',
        color: '#E91E63',
      },
    ],
    edges: [
      {
        source: 'person-1',
        target: 'person-2',
        relationship: 'spouse',
        label: '배우자',
        direction: 'bidirectional',
        confidence: 0.95,
        color: '#2196F3',
        evidence: '혼인관계증명서 확인',
      },
      {
        source: 'person-1',
        target: 'person-3',
        relationship: 'parent',
        label: '부모',
        direction: 'a_to_b',
        confidence: 0.9,
        color: '#4CAF50',
        evidence: '가족관계증명서 확인',
      },
      {
        source: 'person-2',
        target: 'person-3',
        relationship: 'parent',
        label: '부모',
        direction: 'a_to_b',
        confidence: 0.9,
        color: '#4CAF50',
        evidence: '가족관계증명서 확인',
      },
      {
        source: 'person-2',
        target: 'person-4',
        relationship: 'affair',
        label: '외도',
        direction: 'bidirectional',
        confidence: 0.75,
        color: '#E91E63',
        evidence: '카카오톡 대화 내역에서 추정',
      },
    ],
  };
}
