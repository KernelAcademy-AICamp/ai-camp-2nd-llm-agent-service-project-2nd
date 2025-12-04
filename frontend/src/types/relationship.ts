/**
 * Relationship Visualization Types
 * Matches backend ai_worker PersonExtractor and RelationshipInferrer
 */

// Person Role enum (matches backend PersonRole)
export type PersonRole =
  | 'plaintiff'
  | 'defendant'
  | 'child'
  | 'plaintiff_parent'
  | 'defendant_parent'
  | 'relative'
  | 'friend'
  | 'colleague'
  | 'third_party'
  | 'witness'
  | 'unknown';

// Person Side enum (matches backend PersonSide)
export type PersonSide = 'plaintiff_side' | 'defendant_side' | 'neutral' | 'unknown';

// Relationship Type enum (matches backend RelationshipType)
export type RelationshipType =
  | 'spouse'
  | 'ex_spouse'
  | 'parent'
  | 'child'
  | 'sibling'
  | 'in_law'
  | 'relative'
  | 'friend'
  | 'colleague'
  | 'affair'
  | 'acquaintance'
  | 'unknown';

// Person Node from API
export interface PersonNode {
  id: string;
  name: string;
  role: PersonRole;
  side: PersonSide;
  color: string;
}

// Relationship Edge from API
export interface RelationshipEdge {
  source: string;
  target: string;
  relationship: RelationshipType;
  label: string;
  direction: 'a_to_b' | 'b_to_a' | 'bidirectional';
  confidence: number;
  color: string;
  evidence: string;
}

// Relationship Graph from API
export interface RelationshipGraph {
  nodes: PersonNode[];
  edges: RelationshipEdge[];
}

// API Response wrapper
export interface RelationshipAnalysisResponse {
  status: string;
  input_length: number;
  result: RelationshipGraph;
}

// React Flow Node Data
export interface PersonNodeData {
  label: string;
  role: PersonRole;
  side: PersonSide;
  color: string;
  originalNode: PersonNode;
}

// React Flow Edge Data
export interface RelationshipEdgeData {
  label: string;
  relationship: RelationshipType;
  direction: string;
  confidence: number;
  color: string;
  evidence: string;
  originalEdge: RelationshipEdge;
}

// Korean labels for roles
export const ROLE_LABELS: Record<PersonRole, string> = {
  plaintiff: '원고',
  defendant: '피고',
  child: '자녀',
  plaintiff_parent: '원고 부모',
  defendant_parent: '피고 부모',
  relative: '친척',
  friend: '친구',
  colleague: '동료',
  third_party: '제3자',
  witness: '증인',
  unknown: '미상',
};

// Korean labels for relationships
export const RELATIONSHIP_LABELS: Record<RelationshipType, string> = {
  spouse: '배우자',
  ex_spouse: '전 배우자',
  parent: '부모',
  child: '자녀',
  sibling: '형제자매',
  in_law: '시/처가',
  relative: '친척',
  friend: '친구',
  colleague: '직장동료',
  affair: '외도 상대',
  acquaintance: '지인',
  unknown: '미상',
};

// Node colors by role
export const ROLE_COLORS: Record<PersonRole, string> = {
  plaintiff: '#4CAF50',
  defendant: '#F44336',
  child: '#2196F3',
  plaintiff_parent: '#66BB6A',
  defendant_parent: '#EF5350',
  relative: '#FF9800',
  friend: '#03A9F4',
  colleague: '#00BCD4',
  third_party: '#E91E63',
  witness: '#9C27B0',
  unknown: '#9E9E9E',
};

// Edge colors by relationship type
export const RELATIONSHIP_COLORS: Record<RelationshipType, string> = {
  spouse: '#2196F3',
  ex_spouse: '#9E9E9E',
  parent: '#4CAF50',
  child: '#4CAF50',
  sibling: '#8BC34A',
  in_law: '#FF9800',
  relative: '#FF9800',
  friend: '#03A9F4',
  colleague: '#00BCD4',
  affair: '#E91E63',
  acquaintance: '#607D8B',
  unknown: '#9E9E9E',
};
