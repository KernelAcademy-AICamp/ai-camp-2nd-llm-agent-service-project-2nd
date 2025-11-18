"""
AnalysisEngine Module
Integrates EvidenceScorer and RiskAnalyzer for comprehensive case analysis
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from src.parsers.base import Message
from src.analysis.evidence_scorer import EvidenceScorer, ScoringResult
from src.analysis.risk_analyzer import RiskAnalyzer, RiskAssessment


class AnalysisResult(BaseModel):
    """
    종합 분석 결과

    Attributes:
        case_id: 케이스 ID
        total_messages: 전체 메시지 개수
        average_score: 평균 증거 점수
        high_value_messages: 높은 증거 가치 메시지 목록 (score >= 6.0)
        risk_assessment: 리스크 평가 결과
        summary: 요약 통계
    """
    case_id: str
    total_messages: int
    average_score: float
    high_value_messages: List[ScoringResult] = Field(default_factory=list)
    risk_assessment: RiskAssessment
    summary: Dict[str, Any] = Field(default_factory=dict)


class AnalysisEngine:
    """
    케이스 종합 분석 엔진

    Given: 케이스의 모든 메시지
    When: 증거 점수 계산 + 리스크 분석
    Then: 통합 분석 결과 반환

    통합 기능:
    - EvidenceScorer: 각 메시지 증거 가치 점수 계산
    - RiskAnalyzer: 케이스 전체 리스크 평가
    - 통계 요약: 평균 점수, 높은 가치 메시지 식별
    """

    def __init__(self):
        """초기화 - 내부 컴포넌트 생성"""
        self.scorer = EvidenceScorer()
        self.risk_analyzer = RiskAnalyzer()

    def analyze_case(
        self,
        messages: List[Message],
        case_id: str,
        high_value_threshold: float = 6.0
    ) -> AnalysisResult:
        """
        케이스 전체 분석

        Given: 케이스 메시지 리스트 + case_id
        When: 증거 점수 계산 및 리스크 분석 실행
        Then: 통합 분석 결과 반환

        Args:
            messages: 분석할 메시지 리스트
            case_id: 케이스 ID
            high_value_threshold: 높은 가치 메시지 임계값 (기본 6.0)

        Returns:
            AnalysisResult: 종합 분석 결과
        """
        # 빈 메시지 리스트 처리
        if not messages or len(messages) == 0:
            return AnalysisResult(
                case_id=case_id,
                total_messages=0,
                average_score=0.0,
                high_value_messages=[],
                risk_assessment=RiskAssessment(
                    risk_level="low",
                    risk_factors=[],
                    warnings=[],
                    recommendations=[]
                ),
                summary={
                    "total_messages": 0,
                    "average_score": 0.0,
                    "high_value_count": 0,
                    "risk_level": "low"
                }
            )

        # 1. 모든 메시지 점수 계산
        scoring_results = self.scorer.score_batch(messages)

        # 2. 리스크 분석
        risk_assessment = self.risk_analyzer.analyze(messages)

        # 3. 평균 점수 계산
        total_score = sum(result.score for result in scoring_results)
        average_score = round(total_score / len(scoring_results), 2)

        # 4. 높은 가치 메시지 식별
        high_value_messages = [
            result for result in scoring_results
            if result.score >= high_value_threshold
        ]

        # 5. 요약 통계 생성
        summary = {
            "total_messages": len(messages),
            "average_score": average_score,
            "high_value_count": len(high_value_messages),
            "risk_level": risk_assessment.risk_level.value
        }

        # 6. 결과 반환
        return AnalysisResult(
            case_id=case_id,
            total_messages=len(messages),
            average_score=average_score,
            high_value_messages=high_value_messages,
            risk_assessment=risk_assessment,
            summary=summary
        )
