"""
RiskAnalyzer Module
Analyzes case messages for risk factors and generates warnings
"""

from typing import List
from enum import Enum
from pydantic import BaseModel, Field
from src.parsers.base import Message


class RiskLevel(str, Enum):
    """리스크 레벨 분류"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAssessment(BaseModel):
    """
    리스크 평가 결과

    Attributes:
        risk_level: 전체 리스크 레벨
        risk_factors: 탐지된 리스크 요인 목록
        warnings: 경고 메시지 목록
        recommendations: 권장 조치 사항 목록
    """
    risk_level: RiskLevel
    risk_factors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class RiskAnalyzer:
    """
    케이스 리스크 분석기

    Given: 케이스의 모든 메시지
    When: 리스크 패턴 탐지 및 분석
    Then: 리스크 평가 및 경고/권장사항 생성

    리스크 카테고리:
    - threat: 위협/협박
    - violence: 폭력/폭행
    - child_safety: 아동 안전
    - financial_dispute: 금전 분쟁
    - property_concealment: 재산 은닉
    - custody_violation: 양육권 위반
    """

    def __init__(self):
        """초기화 - 리스크 패턴 사전 구성"""
        self.risk_patterns = {
            "threat": {
                "keywords": ["협박", "죽이겠다", "해치겠다", "위협", "죽인다", "가만두지"],
                "severity": RiskLevel.CRITICAL,
                "warning": "즉각적인 안전 위협이 감지되었습니다. 경찰에 신고하고 안전조치를 취하세요.",
                "recommendation": "112 긴급신고 및 경찰 조사 요청|법원 접근금지 가처분 신청|안전한 장소로 즉시 대피"
            },
            "violence": {
                "keywords": ["폭행", "폭력", "때렸다", "맞았다", "상해", "진단서", "병원", "멍", "상처"],
                "severity": RiskLevel.HIGH,
                "warning": "폭력 증거가 발견되었습니다. 의료 기록과 증거를 확보하세요.",
                "recommendation": "병원 방문 및 진단서 발급|상처 부위 사진 촬영 및 보관|경찰서 방문 신고 및 보호조치 신청"
            },
            "child_safety": {
                "keywords": ["아이 앞에서", "자녀 앞", "아동학대", "아이에게 폭력", "아이 때렸다"],
                "severity": RiskLevel.CRITICAL,
                "warning": "아동 안전에 위협이 있습니다. 즉시 아동보호 조치가 필요합니다.",
                "recommendation": "아동보호전문기관 신고(1577-1391)|아동 임시보호 조치 신청|아동 심리상담 지원 요청"
            },
            "financial_dispute": {
                "keywords": ["몰래 돈", "통장 빼갔다", "재산 숨", "돈 빼돌", "계좌 정리", "재산 빼돌"],
                "severity": RiskLevel.MEDIUM,
                "warning": "재산 분쟁 가능성이 있습니다. 금융 기록을 확보하세요.",
                "recommendation": "금융기관 방문 통장 거래내역 확보|부동산 및 재산 목록 작성|법원 재산명시 신청 검토"
            },
            "property_concealment": {
                "keywords": ["명의 변경", "명의 이전", "재산 옮겼다", "다른 사람 명의"],
                "severity": RiskLevel.HIGH,
                "warning": "재산 은닉 의심 정황이 발견되었습니다.",
                "recommendation": "법원 재산조회 신청 제출|재산명시 신청 및 재산은닉 조사 요청|필요시 가압류 신청 검토"
            },
            "custody_violation": {
                "keywords": ["면접교섭", "아이 못 만나게", "양육권 방해", "면회 거부", "만나지 못하게"],
                "severity": RiskLevel.MEDIUM,
                "warning": "양육권 관련 분쟁이 있습니다.",
                "recommendation": "가정법원 면접교섭 조정 신청 권장|양육권 분쟁 조정 절차 검토|이행강제금 신청 검토 필요"
            },
        }

    def analyze(self, messages: List[Message]) -> RiskAssessment:
        """
        케이스 전체 리스크 분석

        Given: 케이스의 모든 메시지 리스트
        When: 각 메시지에서 리스크 패턴 탐지
        Then: 종합 리스크 평가 반환

        Args:
            messages: 분석할 메시지 리스트

        Returns:
            RiskAssessment: 리스크 평가 결과
        """
        # 빈 메시지 리스트 처리
        if not messages or len(messages) == 0:
            return RiskAssessment(
                risk_level=RiskLevel.LOW,
                risk_factors=[],
                warnings=[],
                recommendations=[]
            )

        # 전체 메시지 내용 통합
        all_content = " ".join([msg.content.lower() for msg in messages])

        detected_risks = {}
        max_severity = RiskLevel.LOW

        # 각 리스크 패턴 탐지
        for risk_type, pattern in self.risk_patterns.items():
            matched = False
            for keyword in pattern["keywords"]:
                if keyword in all_content:
                    matched = True
                    break

            if matched:
                detected_risks[risk_type] = pattern
                # 최대 심각도 업데이트
                if self._compare_severity(pattern["severity"], max_severity) > 0:
                    max_severity = pattern["severity"]

        # 리스크 평가 결과 생성
        risk_factors = list(detected_risks.keys())
        warnings = [pattern["warning"] for pattern in detected_risks.values()]
        recommendations = []

        # 권장사항 생성
        for pattern in detected_risks.values():
            # 구분자로 파싱 (", " 또는 "|")
            rec_text = pattern["recommendation"]
            if "|" in rec_text:
                rec_items = rec_text.split("|")
            else:
                rec_items = rec_text.split(", ")
            recommendations.extend(rec_items)

        # 리스크가 없으면 LOW
        if len(risk_factors) == 0:
            max_severity = RiskLevel.LOW

        return RiskAssessment(
            risk_level=max_severity,
            risk_factors=risk_factors,
            warnings=warnings,
            recommendations=recommendations
        )

    def _compare_severity(self, level1: RiskLevel, level2: RiskLevel) -> int:
        """
        리스크 레벨 비교

        Args:
            level1: 첫 번째 레벨
            level2: 두 번째 레벨

        Returns:
            int: level1이 더 심각하면 1, 같으면 0, level2가 더 심각하면 -1
        """
        severity_order = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3
        }

        level1_score = severity_order[level1]
        level2_score = severity_order[level2]

        if level1_score > level2_score:
            return 1
        elif level1_score == level2_score:
            return 0
        else:
            return -1
