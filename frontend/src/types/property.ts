/**
 * Property Division Types
 * 재산분할 예측 관련 타입 정의
 */

/**
 * 재산 유형
 */
export enum PropertyType {
  REAL_ESTATE = 'real_estate', // 부동산
  SAVINGS = 'savings',         // 예금
  STOCKS = 'stocks',           // 주식
  VEHICLE = 'vehicle',         // 차량
  OTHER = 'other',             // 기타
}

/**
 * 영향도 방향
 */
export enum ImpactDirection {
  PLAINTIFF_FAVOR = 'plaintiff_favor',   // 원고에게 유리
  DEFENDANT_FAVOR = 'defendant_favor',   // 피고에게 유리
  NEUTRAL = 'neutral',                   // 중립
}

/**
 * 신뢰도 수준
 */
export enum ConfidenceLevel {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
}

/**
 * 증거 영향도
 */
export interface EvidenceImpact {
  /** 증거 ID */
  evidence_id: string;
  /** 증거 유형 (카카오톡, 금융거래내역 등) */
  evidence_type: string;
  /** 영향도 퍼센트 (양수: 원고 유리, 음수: 피고 유리) */
  impact_percent: number;
  /** 영향 방향 */
  direction: ImpactDirection;
  /** 영향도 근거 설명 */
  reason: string;
}

/**
 * 유사 판례
 */
export interface SimilarCase {
  /** 판례 ID */
  case_id: string;
  /** 판례명 */
  case_name: string;
  /** 유사도 점수 (0-1) */
  similarity_score: number;
  /** 원고 분할 비율 */
  plaintiff_ratio: number;
  /** 피고 분할 비율 */
  defendant_ratio: number;
  /** 판례 요약 */
  summary: string;
}

/**
 * 재산분할 예측 결과
 */
export interface DivisionPrediction {
  /** 원고 분할 비율 (%) */
  plaintiff_ratio: number;
  /** 피고 분할 비율 (%) */
  defendant_ratio: number;
  /** 원고 예상 금액 (선택) */
  plaintiff_amount?: number;
  /** 피고 예상 금액 (선택) */
  defendant_amount?: number;
  /** 증거별 영향도 목록 */
  evidence_impacts: EvidenceImpact[];
  /** 신뢰도 수준 */
  confidence_level: ConfidenceLevel;
  /** 유사 판례 목록 (선택) */
  similar_cases?: SimilarCase[];
}

/**
 * 영향도 방향별 색상
 */
export const IMPACT_COLORS: Record<ImpactDirection, string> = {
  [ImpactDirection.PLAINTIFF_FAVOR]: '#4CAF50', // 초록
  [ImpactDirection.DEFENDANT_FAVOR]: '#F44336', // 빨강
  [ImpactDirection.NEUTRAL]: '#9E9E9E',         // 회색
};

/**
 * 신뢰도 수준별 색상
 */
export const CONFIDENCE_COLORS: Record<ConfidenceLevel, string> = {
  [ConfidenceLevel.HIGH]: '#4CAF50',   // 초록
  [ConfidenceLevel.MEDIUM]: '#FF9800', // 주황
  [ConfidenceLevel.LOW]: '#F44336',    // 빨강
};

/**
 * 신뢰도 수준 한글 라벨
 */
export const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  [ConfidenceLevel.HIGH]: '높음',
  [ConfidenceLevel.MEDIUM]: '보통',
  [ConfidenceLevel.LOW]: '낮음',
};

/**
 * 재산 유형 한글 라벨
 */
export const PROPERTY_TYPE_LABELS: Record<PropertyType, string> = {
  [PropertyType.REAL_ESTATE]: '부동산',
  [PropertyType.SAVINGS]: '예금',
  [PropertyType.STOCKS]: '주식',
  [PropertyType.VEHICLE]: '차량',
  [PropertyType.OTHER]: '기타',
};

/**
 * 금액 포맷팅 (한국어)
 */
export function formatAmount(amount: number): string {
  if (amount >= 100000000) {
    const billions = Math.floor(amount / 100000000);
    const remainder = amount % 100000000;
    if (remainder >= 10000000) {
      const tenMillions = Math.floor(remainder / 10000000);
      return `${billions}억 ${tenMillions}천만원`;
    }
    return `${billions}억원`;
  }
  if (amount >= 10000000) {
    return `${Math.floor(amount / 10000000)}천만원`;
  }
  if (amount >= 10000) {
    return `${Math.floor(amount / 10000)}만원`;
  }
  return `${amount.toLocaleString()}원`;
}
