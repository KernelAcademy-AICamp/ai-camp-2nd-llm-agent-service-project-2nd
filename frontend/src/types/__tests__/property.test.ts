/**
 * Property Types Tests
 * TDD: Red phase - 테스트 먼저 작성
 */

import {
  PropertyType,
  ImpactDirection,
  ConfidenceLevel,
  type EvidenceImpact,
  type DivisionPrediction,
  type SimilarCase,
} from '../property';

describe('Property Types', () => {
  describe('PropertyType enum', () => {
    it('should have REAL_ESTATE value', () => {
      expect(PropertyType.REAL_ESTATE).toBe('real_estate');
    });

    it('should have SAVINGS value', () => {
      expect(PropertyType.SAVINGS).toBe('savings');
    });

    it('should have STOCKS value', () => {
      expect(PropertyType.STOCKS).toBe('stocks');
    });

    it('should have VEHICLE value', () => {
      expect(PropertyType.VEHICLE).toBe('vehicle');
    });

    it('should have OTHER value', () => {
      expect(PropertyType.OTHER).toBe('other');
    });
  });

  describe('ImpactDirection enum', () => {
    it('should have PLAINTIFF_FAVOR value', () => {
      expect(ImpactDirection.PLAINTIFF_FAVOR).toBe('plaintiff_favor');
    });

    it('should have DEFENDANT_FAVOR value', () => {
      expect(ImpactDirection.DEFENDANT_FAVOR).toBe('defendant_favor');
    });

    it('should have NEUTRAL value', () => {
      expect(ImpactDirection.NEUTRAL).toBe('neutral');
    });
  });

  describe('ConfidenceLevel enum', () => {
    it('should have HIGH value', () => {
      expect(ConfidenceLevel.HIGH).toBe('high');
    });

    it('should have MEDIUM value', () => {
      expect(ConfidenceLevel.MEDIUM).toBe('medium');
    });

    it('should have LOW value', () => {
      expect(ConfidenceLevel.LOW).toBe('low');
    });
  });

  describe('EvidenceImpact interface', () => {
    it('should create valid EvidenceImpact object', () => {
      const impact: EvidenceImpact = {
        evidence_id: 'ev-001',
        evidence_type: '카카오톡 대화',
        impact_percent: 8.5,
        direction: ImpactDirection.PLAINTIFF_FAVOR,
        reason: '외도 증거로 인한 유책사유 인정',
      };

      expect(impact.evidence_id).toBe('ev-001');
      expect(impact.evidence_type).toBe('카카오톡 대화');
      expect(impact.impact_percent).toBe(8.5);
      expect(impact.direction).toBe(ImpactDirection.PLAINTIFF_FAVOR);
      expect(impact.reason).toBe('외도 증거로 인한 유책사유 인정');
    });

    it('should handle negative impact percent for defendant favor', () => {
      const impact: EvidenceImpact = {
        evidence_id: 'ev-002',
        evidence_type: '금융거래내역',
        impact_percent: -5.0,
        direction: ImpactDirection.DEFENDANT_FAVOR,
        reason: '원고의 재산 은닉 의심',
      };

      expect(impact.impact_percent).toBe(-5.0);
      expect(impact.direction).toBe(ImpactDirection.DEFENDANT_FAVOR);
    });
  });

  describe('SimilarCase interface', () => {
    it('should create valid SimilarCase object', () => {
      const similarCase: SimilarCase = {
        case_id: 'case-2020-12345',
        case_name: '서울가정법원 2020드단12345',
        similarity_score: 0.85,
        plaintiff_ratio: 55,
        defendant_ratio: 45,
        summary: '외도로 인한 이혼 사건, 재산분할 비율 55:45',
      };

      expect(similarCase.case_id).toBe('case-2020-12345');
      expect(similarCase.similarity_score).toBe(0.85);
      expect(similarCase.plaintiff_ratio).toBe(55);
      expect(similarCase.defendant_ratio).toBe(45);
    });
  });

  describe('DivisionPrediction interface', () => {
    it('should create valid DivisionPrediction object', () => {
      const prediction: DivisionPrediction = {
        plaintiff_ratio: 60.5,
        defendant_ratio: 39.5,
        evidence_impacts: [
          {
            evidence_id: 'ev-001',
            evidence_type: '카카오톡',
            impact_percent: 8.5,
            direction: ImpactDirection.PLAINTIFF_FAVOR,
            reason: '외도 증거',
          },
        ],
        confidence_level: ConfidenceLevel.HIGH,
      };

      expect(prediction.plaintiff_ratio).toBe(60.5);
      expect(prediction.defendant_ratio).toBe(39.5);
      expect(prediction.plaintiff_ratio + prediction.defendant_ratio).toBe(100);
      expect(prediction.evidence_impacts).toHaveLength(1);
      expect(prediction.confidence_level).toBe(ConfidenceLevel.HIGH);
    });

    it('should allow optional amount fields', () => {
      const prediction: DivisionPrediction = {
        plaintiff_ratio: 60,
        defendant_ratio: 40,
        plaintiff_amount: 600000000,
        defendant_amount: 400000000,
        evidence_impacts: [],
        confidence_level: ConfidenceLevel.MEDIUM,
      };

      expect(prediction.plaintiff_amount).toBe(600000000);
      expect(prediction.defendant_amount).toBe(400000000);
    });

    it('should allow optional similar_cases field', () => {
      const prediction: DivisionPrediction = {
        plaintiff_ratio: 55,
        defendant_ratio: 45,
        evidence_impacts: [],
        confidence_level: ConfidenceLevel.LOW,
        similar_cases: [
          {
            case_id: 'case-001',
            case_name: '유사 판례 1',
            similarity_score: 0.9,
            plaintiff_ratio: 55,
            defendant_ratio: 45,
            summary: '유사한 사건',
          },
        ],
      };

      expect(prediction.similar_cases).toHaveLength(1);
      expect(prediction.similar_cases?.[0].similarity_score).toBe(0.9);
    });

    it('should handle empty evidence impacts', () => {
      const prediction: DivisionPrediction = {
        plaintiff_ratio: 50,
        defendant_ratio: 50,
        evidence_impacts: [],
        confidence_level: ConfidenceLevel.LOW,
      };

      expect(prediction.evidence_impacts).toHaveLength(0);
    });
  });
});
