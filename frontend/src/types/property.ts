/**
 * Property Division Types
 * Types for property management and division prediction
 */

// Property types matching backend enum
export type PropertyType =
  | 'real_estate'
  | 'savings'
  | 'stocks'
  | 'retirement'
  | 'vehicle'
  | 'insurance'
  | 'debt'
  | 'other';

export type PropertyOwner = 'plaintiff' | 'defendant' | 'joint';

export type ConfidenceLevel = 'low' | 'medium' | 'high';

export interface Property {
  id: string;
  case_id: string;
  property_type: PropertyType;
  description?: string;
  estimated_value: number;
  owner: PropertyOwner;
  is_premarital: boolean;
  acquisition_date?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PropertyCreate {
  property_type: PropertyType;
  estimated_value: number;
  owner: PropertyOwner;
  description?: string;
  is_premarital?: boolean;
  acquisition_date?: string;
  notes?: string;
}

export interface PropertyUpdate {
  property_type?: PropertyType;
  estimated_value?: number;
  owner?: PropertyOwner;
  description?: string;
  is_premarital?: boolean;
  acquisition_date?: string;
  notes?: string;
}

export interface PropertyListResponse {
  properties: Property[];
  total: number;
  total_assets: number;
  total_debts: number;
  net_value: number;
}

export interface PropertySummary {
  total_assets: number;
  total_debts: number;
  net_value: number;
  by_type: Record<PropertyType, number>;
  by_owner: Record<PropertyOwner, number>;
}

export interface EvidenceImpact {
  evidence_id: string;
  evidence_type: string;
  impact_type: string;
  impact_percent: number;
  direction: 'plaintiff' | 'defendant';
  reason: string;
  confidence: number;
}

export interface SimilarCase {
  case_ref: string;
  similarity_score: number;
  division_ratio: string;
  key_factors: string[];
}

export interface DivisionPrediction {
  id: string;
  case_id: string;
  total_property_value: number;
  total_debt_value: number;
  net_value: number;
  plaintiff_ratio: number;
  defendant_ratio: number;
  plaintiff_amount: number;
  defendant_amount: number;
  evidence_impacts: EvidenceImpact[];
  similar_cases: SimilarCase[];
  confidence_level: ConfidenceLevel;
  version: number;
  created_at: string;
  updated_at: string;
}

// UI display helpers
export const PROPERTY_TYPE_LABELS: Record<PropertyType, string> = {
  real_estate: '부동산',
  savings: '예금/적금',
  stocks: '주식/펀드',
  retirement: '퇴직금/연금',
  vehicle: '차량',
  insurance: '보험',
  debt: '부채',
  other: '기타',
};

export const PROPERTY_OWNER_LABELS: Record<PropertyOwner, string> = {
  plaintiff: '원고',
  defendant: '피고',
  joint: '공동',
};

export const CONFIDENCE_LEVEL_LABELS: Record<ConfidenceLevel, string> = {
  low: '낮음',
  medium: '보통',
  high: '높음',
};
