/**
 * Relationship Graph Types
 * 인물 관계도 시각화를 위한 타입 정의
 */

/**
 * 인물 역할 (당사자 구분)
 */
export enum PersonRole {
  PLAINTIFF = 'plaintiff',     // 원고
  DEFENDANT = 'defendant',     // 피고
  CHILD = 'child',             // 자녀
  THIRD_PARTY = 'third_party', // 제3자 (외도 상대 등)
  UNKNOWN = 'unknown',         // 미상
}

/**
 * 관계 유형
 */
export enum RelationshipType {
  SPOUSE = 'spouse',   // 배우자
  AFFAIR = 'affair',   // 외도 관계
  PARENT = 'parent',   // 부모
  CHILD = 'child',     // 자녀
  SIBLING = 'sibling', // 형제/자매
}

/**
 * 인물 노드 (React Flow 노드 데이터)
 */
export interface PersonNode {
  /** 고유 ID (예: "person-0") */
  id: string;
  /** 인물 이름 */
  name: string;
  /** 역할 (원고/피고/자녀 등) */
  role: PersonRole;
  /** 소속 측 (원고측/피고측/제3자) */
  side: 'plaintiff' | 'defendant' | 'third_party';
  /** 노드 색상 (hex) */
  color: string;
  /** 별칭 목록 (선택) */
  aliases?: string[];
}

/**
 * 관계 엣지 (React Flow 엣지 데이터)
 */
export interface RelationshipEdge {
  /** 시작 노드 ID */
  source: string;
  /** 종료 노드 ID */
  target: string;
  /** 관계 유형 */
  relationship: RelationshipType;
  /** 관계 라벨 (한글) */
  label: string;
  /** 신뢰도 (0-1) */
  confidence: number;
  /** 근거 증거 (선택) */
  evidence?: string;
}

/**
 * 관계도 그래프 (API 응답 형식)
 */
export interface RelationshipGraph {
  /** 인물 노드 목록 */
  nodes: PersonNode[];
  /** 관계 엣지 목록 */
  edges: RelationshipEdge[];
}

/**
 * 역할별 색상 매핑
 */
export const ROLE_COLORS: Record<PersonRole, string> = {
  [PersonRole.PLAINTIFF]: '#4CAF50',   // 초록
  [PersonRole.DEFENDANT]: '#F44336',   // 빨강
  [PersonRole.CHILD]: '#2196F3',       // 파랑
  [PersonRole.THIRD_PARTY]: '#E91E63', // 핑크
  [PersonRole.UNKNOWN]: '#9E9E9E',     // 회색
};

/**
 * 관계별 색상 매핑
 */
export const RELATIONSHIP_COLORS: Record<RelationshipType, string> = {
  [RelationshipType.SPOUSE]: '#2196F3',  // 파랑
  [RelationshipType.AFFAIR]: '#E91E63',  // 핑크
  [RelationshipType.PARENT]: '#4CAF50',  // 초록
  [RelationshipType.CHILD]: '#4CAF50',   // 초록
  [RelationshipType.SIBLING]: '#FF9800', // 주황
};

/**
 * 역할 한글 라벨
 */
export const ROLE_LABELS: Record<PersonRole, string> = {
  [PersonRole.PLAINTIFF]: '원고',
  [PersonRole.DEFENDANT]: '피고',
  [PersonRole.CHILD]: '자녀',
  [PersonRole.THIRD_PARTY]: '제3자',
  [PersonRole.UNKNOWN]: '미상',
};

/**
 * 관계 한글 라벨
 */
export const RELATIONSHIP_LABELS: Record<RelationshipType, string> = {
  [RelationshipType.SPOUSE]: '배우자',
  [RelationshipType.AFFAIR]: '외도 상대',
  [RelationshipType.PARENT]: '부모',
  [RelationshipType.CHILD]: '자녀',
  [RelationshipType.SIBLING]: '형제/자매',
};
