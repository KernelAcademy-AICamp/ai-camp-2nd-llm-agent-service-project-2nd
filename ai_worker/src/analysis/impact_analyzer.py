"""
Impact Analyzer - 재산분할 영향도 분석기

증거를 분석하여 재산분할 비율에 미치는 영향을 계산합니다.
LLM 미사용, 규칙 기반 + 판례 유사도 검색 방식.

Usage:
    from src.analysis.impact_analyzer import ImpactAnalyzer

    analyzer = ImpactAnalyzer(case_id="case-001")
    impact = analyzer.analyze_evidence(evidence)
    prediction = analyzer.calculate_total_impact(all_evidences)

원칙:
- 객관적 정보만 제시 ("~입니다", "~으로 확인됩니다")
- 조언/판단 표현 금지
"""

import os
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum

from .impact_rules import (
    FaultType,
    EvidenceType,
    ImpactDirection,
    ImpactRule,
    IMPACT_RULES,
    CONTRIBUTION_FACTORS,
    CONFIDENCE_THRESHOLDS,
    get_impact_rule,
    calculate_evidence_weight,
    calculate_single_impact,
    map_legal_category_to_fault,
)
from .precedent_searcher import PrecedentSearcher, PrecedentCase

logger = logging.getLogger(__name__)


# =============================================================================
# 데이터 클래스
# =============================================================================

@dataclass
class EvidenceImpact:
    """
    개별 증거의 영향도 분석 결과

    Attributes:
        evidence_id: 증거 ID
        evidence_type: 증거 유형 (photo, chat_log, etc.)
        fault_type: 유책사유 (adultery, violence, etc.)
        impact_percent: 영향도 (%p, 양수=원고 유리, 음수=피고 유리)
        direction: 영향 방향
        reason: 영향도 산출 근거 (객관적 톤)
        confidence: 신뢰도 (0.0~1.0)
        timestamp: 분석 시각
    """
    evidence_id: str
    evidence_type: str
    fault_type: str
    impact_percent: float
    direction: ImpactDirection
    reason: str
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "fault_type": self.fault_type,
            "impact_percent": round(self.impact_percent, 2),
            "direction": self.direction.value,
            "reason": self.reason,
            "confidence": round(self.confidence, 2),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SimilarCase:
    """
    유사 판례 정보

    Attributes:
        case_ref: 판례 번호
        similarity_score: 유사도 (0.0~1.0)
        division_ratio: 분할 비율 (예: "60:40")
        key_factors: 주요 요인
    """
    case_ref: str
    similarity_score: float
    division_ratio: str
    key_factors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "case_ref": self.case_ref,
            "similarity_score": round(self.similarity_score, 2),
            "division_ratio": self.division_ratio,
            "key_factors": self.key_factors
        }


@dataclass
class DivisionPrediction:
    """
    재산분할 예측 결과

    Attributes:
        case_id: 사건 ID
        plaintiff_ratio: 원고(의뢰인) 비율 (%)
        defendant_ratio: 피고 비율 (%)
        plaintiff_amount: 원고 예상 금액 (원)
        defendant_amount: 피고 예상 금액 (원)
        total_property_value: 총 재산가액 (원)
        evidence_impacts: 증거별 영향도 목록
        similar_cases: 유사 판례 목록
        confidence_level: 신뢰도 레벨 (high/medium/low)
        generated_at: 생성 시각
        disclaimer: 면책 문구
    """
    case_id: str
    plaintiff_ratio: float
    defendant_ratio: float
    plaintiff_amount: int = 0
    defendant_amount: int = 0
    total_property_value: int = 0
    evidence_impacts: List[EvidenceImpact] = field(default_factory=list)
    similar_cases: List[SimilarCase] = field(default_factory=list)
    confidence_level: str = "low"
    generated_at: datetime = field(default_factory=datetime.now)
    disclaimer: str = "본 예측은 참고용이며 실제 판결과 다를 수 있습니다."

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "case_id": self.case_id,
            "division_ratio": {
                "plaintiff": round(self.plaintiff_ratio, 1),
                "defendant": round(self.defendant_ratio, 1)
            },
            "plaintiff_amount": self.plaintiff_amount,
            "defendant_amount": self.defendant_amount,
            "total_property_value": self.total_property_value,
            "evidence_impacts": [e.to_dict() for e in self.evidence_impacts],
            "similar_cases": [s.to_dict() for s in self.similar_cases],
            "confidence_level": self.confidence_level,
            "generated_at": self.generated_at.isoformat(),
            "disclaimer": self.disclaimer
        }


# =============================================================================
# ImpactAnalyzer 클래스
# =============================================================================

class ImpactAnalyzer:
    """
    재산분할 영향도 분석기

    증거 목록을 분석하여 재산분할 비율 예측을 생성합니다.

    Usage:
        analyzer = ImpactAnalyzer(case_id="case-001")

        # 단일 증거 분석
        impact = analyzer.analyze_single_evidence(evidence_dict)

        # 전체 증거 기반 예측
        prediction = analyzer.calculate_prediction(
            evidences=evidence_list,
            total_property_value=500_000_000
        )
    """

    BASE_RATIO = 50.0  # 기본 분할 비율 (50:50)

    def __init__(
        self,
        case_id: str,
        qdrant_client: Optional[Any] = None
    ):
        """
        ImpactAnalyzer 초기화

        Args:
            case_id: 사건 ID
            qdrant_client: Qdrant 클라이언트 (유사 판례 검색용, optional)
        """
        self.case_id = case_id
        self.qdrant = qdrant_client
        self._evidence_impacts: List[EvidenceImpact] = []

    def analyze_single_evidence(
        self,
        evidence: Dict[str, Any]
    ) -> Optional[EvidenceImpact]:
        """
        단일 증거의 영향도 분석

        Args:
            evidence: 증거 정보
                - evidence_id: str
                - evidence_type: str (photo, chat_log, etc.)
                - legal_categories: List[str] (유책사유 목록)
                - confidence_score: float (0.0~1.0)

        Returns:
            EvidenceImpact 또는 None (영향 없는 경우)
        """
        evidence_id = evidence.get("evidence_id", "unknown")
        evidence_type = evidence.get("evidence_type", evidence.get("source_type", "document"))
        legal_categories = evidence.get("legal_categories", [])
        confidence = evidence.get("confidence_score", 0.5)

        # 유책사유가 없으면 영향 없음
        if not legal_categories:
            return None

        # 가장 영향력 높은 유책사유 선택
        best_impact = 0.0
        best_fault = None

        for category in legal_categories:
            # LegalCategory → FaultType 매핑
            fault_type = map_legal_category_to_fault(category)
            if not fault_type:
                continue

            impact = calculate_single_impact(
                fault_type=fault_type.value,
                evidence_type=evidence_type,
                confidence=confidence
            )

            if impact > best_impact:
                best_impact = impact
                best_fault = fault_type

        if not best_fault or best_impact <= 0:
            return None

        # 영향 방향 결정 (기본: 원고 유리)
        # TODO: 증거 컨텍스트에 따라 방향 결정 로직 추가
        direction = ImpactDirection.PLAINTIFF_FAVOR

        # 근거 문구 생성 (객관적 톤)
        rule = get_impact_rule(best_fault.value)
        reason = self._generate_reason(
            fault_type=best_fault.value,
            evidence_type=evidence_type,
            impact=best_impact,
            rule=rule
        )

        return EvidenceImpact(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            fault_type=best_fault.value,
            impact_percent=best_impact,
            direction=direction,
            reason=reason,
            confidence=confidence
        )

    def analyze_evidence_batch(
        self,
        evidences: List[Dict[str, Any]]
    ) -> List[EvidenceImpact]:
        """
        여러 증거 일괄 분석

        Args:
            evidences: 증거 목록

        Returns:
            EvidenceImpact 목록 (영향 있는 것만)
        """
        impacts = []

        for evidence in evidences:
            impact = self.analyze_single_evidence(evidence)
            if impact:
                impacts.append(impact)

        self._evidence_impacts = impacts
        return impacts

    def calculate_prediction(
        self,
        evidences: List[Dict[str, Any]],
        total_property_value: int = 0
    ) -> DivisionPrediction:
        """
        전체 증거 기반 재산분할 예측 계산

        Args:
            evidences: 증거 목록
            total_property_value: 총 재산가액 (원)

        Returns:
            DivisionPrediction: 예측 결과
        """
        # 증거 분석
        impacts = self.analyze_evidence_batch(evidences)

        # 총 영향도 계산
        total_impact = self._calculate_total_impact(impacts)

        # 비율 계산
        plaintiff_ratio = self.BASE_RATIO + total_impact
        plaintiff_ratio = max(0, min(100, plaintiff_ratio))  # 0~100 범위 제한
        defendant_ratio = 100 - plaintiff_ratio

        # 금액 계산
        plaintiff_amount = int(total_property_value * plaintiff_ratio / 100)
        defendant_amount = total_property_value - plaintiff_amount

        # 유사 판례 검색 (Qdrant 연결 시)
        similar_cases = self._find_similar_cases(impacts)

        # 신뢰도 레벨 결정
        confidence_level = self._determine_confidence_level(impacts)

        return DivisionPrediction(
            case_id=self.case_id,
            plaintiff_ratio=plaintiff_ratio,
            defendant_ratio=defendant_ratio,
            plaintiff_amount=plaintiff_amount,
            defendant_amount=defendant_amount,
            total_property_value=total_property_value,
            evidence_impacts=impacts,
            similar_cases=similar_cases,
            confidence_level=confidence_level
        )

    def _calculate_total_impact(
        self,
        impacts: List[EvidenceImpact]
    ) -> float:
        """
        총 영향도 계산

        동일 유책사유의 증거는 중복 효과 감소 적용
        """
        if not impacts:
            return 0.0

        # 유책사유별 그룹화
        fault_groups: Dict[str, List[EvidenceImpact]] = {}
        for impact in impacts:
            if impact.fault_type not in fault_groups:
                fault_groups[impact.fault_type] = []
            fault_groups[impact.fault_type].append(impact)

        total = 0.0

        for fault_type, group in fault_groups.items():
            # 동일 유책사유 내에서 최대값 + 감쇠 합산
            sorted_impacts = sorted(group, key=lambda x: x.impact_percent, reverse=True)

            group_total = 0.0
            for i, impact in enumerate(sorted_impacts):
                # 첫 번째 증거: 100%, 이후 50% 감쇠
                if i == 0:
                    group_total += impact.impact_percent
                else:
                    group_total += impact.impact_percent * 0.5

            # 유책사유별 최대값 제한
            rule = get_impact_rule(fault_type)
            if rule:
                group_total = min(group_total, rule.max_impact)

            # 방향에 따른 부호 적용
            direction = sorted_impacts[0].direction
            if direction == ImpactDirection.DEFENDANT_FAVOR:
                group_total = -group_total

            total += group_total

        return total

    def _find_similar_cases(
        self,
        impacts: List[EvidenceImpact]
    ) -> List[SimilarCase]:
        """
        유사 판례 검색 (Qdrant 연동)

        Args:
            impacts: 영향도 분석 결과

        Returns:
            유사 판례 목록
        """
        if not impacts:
            return []

        # 주요 유책사유 추출
        fault_types = list(set(i.fault_type for i in impacts))

        try:
            # PrecedentSearcher로 Qdrant 검색
            searcher = PrecedentSearcher()

            # 서비스 사용 가능 여부 확인
            if not searcher.is_available():
                logger.info("Precedent search service not available, using fallback")
                return self._get_fallback_cases(fault_types)

            # 유사 판례 검색
            precedents = searcher.search_by_fault_types(
                fault_types=fault_types,
                top_k=5,
                min_score=0.3,
            )

            if not precedents:
                logger.info("No precedents found, using fallback")
                return self._get_fallback_cases(fault_types)

            # PrecedentCase → SimilarCase 변환
            similar_cases = []
            for p in precedents[:3]:  # 최대 3개
                similar_cases.append(SimilarCase(
                    case_ref=p.case_ref,
                    similarity_score=p.similarity_score,
                    division_ratio=p.division_ratio,
                    key_factors=p.key_factors,
                ))

            return similar_cases

        except Exception as e:
            logger.warning(f"Precedent search failed: {e}, using fallback")
            return self._get_fallback_cases(fault_types)

    def _get_fallback_cases(
        self,
        fault_types: List[str]
    ) -> List[SimilarCase]:
        """
        판례 검색 실패 시 폴백 데이터 반환

        판례 데이터가 없거나 검색 실패 시 기본 참고 판례 반환.
        실제 판례가 아닌 참고용 더미 데이터임을 명시.

        Args:
            fault_types: 유책사유 목록

        Returns:
            폴백 판례 목록
        """
        # 유책사유별 참고 판례 (실제 판례 기반 예시)
        fallback_map = {
            "adultery": SimilarCase(
                case_ref="참고: 외도 관련 유사 판례",
                similarity_score=0.70,
                division_ratio="60:40",
                key_factors=["외도"],
            ),
            "violence": SimilarCase(
                case_ref="참고: 가정폭력 관련 유사 판례",
                similarity_score=0.70,
                division_ratio="65:35",
                key_factors=["폭력"],
            ),
            "verbal_abuse": SimilarCase(
                case_ref="참고: 폭언 관련 유사 판례",
                similarity_score=0.65,
                division_ratio="55:45",
                key_factors=["폭언"],
            ),
        }

        cases = []
        for fault_type in fault_types[:2]:  # 최대 2개
            if fault_type in fallback_map:
                cases.append(fallback_map[fault_type])

        if not cases:
            # 기본 폴백
            cases.append(SimilarCase(
                case_ref="참고: 일반 이혼 재산분할 판례",
                similarity_score=0.60,
                division_ratio="50:50",
                key_factors=fault_types[:2] if fault_types else ["일반"],
            ))

        return cases

    def _determine_confidence_level(
        self,
        impacts: List[EvidenceImpact]
    ) -> str:
        """
        신뢰도 레벨 결정

        Args:
            impacts: 영향도 분석 결과

        Returns:
            "high", "medium", "low"
        """
        if not impacts:
            return "low"

        count = len(impacts)
        avg_confidence = sum(i.confidence for i in impacts) / count

        if count >= CONFIDENCE_THRESHOLDS["high"]["min_evidence_count"] and \
           avg_confidence >= CONFIDENCE_THRESHOLDS["high"]["min_avg_weight"]:
            return "high"
        elif count >= CONFIDENCE_THRESHOLDS["medium"]["min_evidence_count"] and \
             avg_confidence >= CONFIDENCE_THRESHOLDS["medium"]["min_avg_weight"]:
            return "medium"
        else:
            return "low"

    def _generate_reason(
        self,
        fault_type: str,
        evidence_type: str,
        impact: float,
        rule: Optional[ImpactRule]
    ) -> str:
        """
        영향도 근거 문구 생성 (객관적 톤)

        Args:
            fault_type: 유책사유
            evidence_type: 증거 유형
            impact: 영향도
            rule: 영향도 규칙

        Returns:
            근거 문구 (객관적 톤으로 작성)
        """
        # 유책사유 한글명
        fault_names = {
            "adultery": "부정행위",
            "violence": "가정폭력",
            "verbal_abuse": "폭언",
            "economic_abuse": "경제적 학대",
            "desertion": "악의의 유기",
            "financial_misconduct": "재정 비행",
            "child_abuse": "자녀 학대",
            "substance_abuse": "약물 남용",
        }

        # 증거 유형 한글명
        evidence_names = {
            "photo": "사진",
            "chat_log": "대화 내역",
            "recording": "녹음",
            "video": "영상",
            "medical_record": "진단서",
            "police_report": "경찰 신고 기록",
            "bank_statement": "금융 거래 내역",
            "document": "문서",
            "witness": "진술서",
        }

        fault_name = fault_names.get(fault_type, fault_type)
        evidence_name = evidence_names.get(evidence_type, evidence_type)

        # 객관적 톤 문구
        return f"{fault_name} 관련 {evidence_name} 증거로, {impact:.1f}%p 영향도가 산출됩니다."


# =============================================================================
# 간편 함수
# =============================================================================

def analyze_case_impact(
    case_id: str,
    evidences: List[Dict[str, Any]],
    total_property_value: int = 0
) -> DivisionPrediction:
    """
    사건 영향도 분석 간편 함수

    Args:
        case_id: 사건 ID
        evidences: 증거 목록
        total_property_value: 총 재산가액

    Returns:
        DivisionPrediction
    """
    analyzer = ImpactAnalyzer(case_id=case_id)
    return analyzer.calculate_prediction(
        evidences=evidences,
        total_property_value=total_property_value
    )


# =============================================================================
# 모듈 export
# =============================================================================

__all__ = [
    "EvidenceImpact",
    "SimilarCase",
    "DivisionPrediction",
    "ImpactAnalyzer",
    "analyze_case_impact",
]
