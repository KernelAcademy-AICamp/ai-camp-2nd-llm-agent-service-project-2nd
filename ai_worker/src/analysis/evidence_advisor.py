"""
Evidence Advisor - 증거 현황 분석 및 어드바이스

LLM 미사용, 규칙 기반 분석
- 시간대별 공백 탐지
- 증거 유형별 현황
- 유책사유별 현황

톤앤매너 원칙:
- 조언/지시 금지: "~하세요", "~해야 합니다" 사용 안 함
- 현황 제시만: "~입니다", "~으로 확인됩니다"
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict
from collections import Counter
from enum import Enum


class AdviceType(str, Enum):
    """어드바이스 유형"""
    TIME_GAP = "time_gap"           # 시간대 공백
    TYPE_STATUS = "type_status"     # 증거 유형별 현황
    FAULT_STATUS = "fault_status"   # 유책사유별 현황
    SUMMARY = "summary"             # 전체 요약


class Severity(str, Enum):
    """심각도"""
    INFO = "info"       # 정보성
    WARNING = "warning" # 주의 필요


@dataclass
class EvidenceAdvice:
    """
    증거 어드바이스 데이터 클래스

    Attributes:
        advice_type: 어드바이스 유형
        severity: 심각도 (info/warning)
        message: 사용자에게 표시할 메시지 (객관적 톤)
        details: 상세 데이터
    """
    advice_type: AdviceType
    severity: Severity
    message: str
    details: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """딕셔너리 변환"""
        return {
            "advice_type": self.advice_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details
        }


@dataclass
class EvidenceAdviceResponse:
    """
    어드바이스 API 응답

    Attributes:
        case_id: 사건 ID
        total_evidence_count: 총 증거 수
        advices: 어드바이스 목록
        summary: 요약 통계
        generated_at: 생성 시각
        disclaimer: 면책 문구
    """
    case_id: str
    total_evidence_count: int
    advices: List[EvidenceAdvice]
    summary: Dict
    generated_at: datetime = field(default_factory=datetime.now)
    disclaimer: str = "본 정보는 참고용이며 법률 조언이 아닙니다."

    def to_dict(self) -> Dict:
        """딕셔너리 변환"""
        return {
            "case_id": self.case_id,
            "total_evidence_count": self.total_evidence_count,
            "advices": [a.to_dict() for a in self.advices],
            "summary": self.summary,
            "generated_at": self.generated_at.isoformat(),
            "disclaimer": self.disclaimer
        }


class EvidenceAdvisor:
    """
    증거 현황 분석기 (LLM 미사용)

    규칙 기반으로 증거 현황을 분석하고 객관적 정보를 제공합니다.

    톤앤매너 원칙:
    - 조언 금지: "~하세요", "~해야 합니다" 사용 안 함
    - 현황 제시: "~입니다", "~으로 확인됩니다"

    Usage:
        advisor = EvidenceAdvisor()
        advices = advisor.analyze_time_gaps(timestamps)
    """

    # 증거 유형 한글 매핑
    EVIDENCE_TYPE_NAMES = {
        "kakaotalk": "카카오톡 대화",
        "chat": "채팅 대화",
        "photo": "사진",
        "image": "이미지",
        "recording": "녹음",
        "audio": "음성",
        "document": "문서",
        "pdf": "PDF 문서",
        "video": "영상",
    }

    # 유책사유 한글 매핑 (민법 840조)
    FAULT_TYPE_NAMES = {
        "adultery": "부정행위",
        "desertion": "악의의 유기",
        "mistreatment_by_inlaws": "시댁/처가 학대",
        "harm_to_own_parents": "직계존속 해악",
        "unknown_whereabouts": "생사불명",
        "domestic_violence": "가정폭력",
        "financial_misconduct": "재정 비행",
        "irreconcilable_differences": "기타 혼인 곤란",
        "verbal_abuse": "폭언",
        "economic_abuse": "경제적 학대",
        "general": "일반",
    }

    def __init__(self, gap_threshold_days: int = 30):
        """
        Args:
            gap_threshold_days: 공백으로 간주할 최소 일수 (기본 30일)
        """
        self.gap_threshold_days = gap_threshold_days

    def analyze_time_gaps(
        self,
        timestamps: List[datetime],
    ) -> List[EvidenceAdvice]:
        """
        시간대별 공백 분석

        Args:
            timestamps: 증거 타임스탬프 목록

        Returns:
            List[EvidenceAdvice]: 30일 이상 공백 목록

        Example:
            >>> timestamps = [datetime(2024, 1, 1), datetime(2024, 4, 1)]
            >>> advices = advisor.analyze_time_gaps(timestamps)
            >>> print(advices[0].message)
            "2024년 01월~2024년 04월 기간의 증거가 없습니다"
        """
        if len(timestamps) < 2:
            return []

        sorted_dates = sorted(timestamps)
        advices = []

        for i in range(1, len(sorted_dates)):
            diff_days = (sorted_dates[i] - sorted_dates[i-1]).days

            if diff_days > self.gap_threshold_days:
                start_str = sorted_dates[i-1].strftime('%Y년 %m월')
                end_str = sorted_dates[i].strftime('%Y년 %m월')

                advices.append(EvidenceAdvice(
                    advice_type=AdviceType.TIME_GAP,
                    severity=Severity.WARNING,
                    message=f"{start_str}~{end_str} 기간의 증거가 없습니다",
                    details={
                        "gap_start": sorted_dates[i-1].isoformat(),
                        "gap_end": sorted_dates[i].isoformat(),
                        "gap_days": diff_days
                    }
                ))

        return advices

    def analyze_evidence_types(
        self,
        evidence_types: List[str],
    ) -> List[EvidenceAdvice]:
        """
        증거 유형별 현황 분석

        Args:
            evidence_types: 증거 유형 목록 (예: ["kakaotalk", "photo", "photo"])

        Returns:
            List[EvidenceAdvice]: 유형별 건수 정보
        """
        type_counts = Counter(evidence_types)
        advices = []

        for etype, name in self.EVIDENCE_TYPE_NAMES.items():
            count = type_counts.get(etype, 0)
            advices.append(EvidenceAdvice(
                advice_type=AdviceType.TYPE_STATUS,
                severity=Severity.INFO if count > 0 else Severity.WARNING,
                message=f"{name}: {count}건",
                details={"type": etype, "count": count}
            ))

        return advices

    def analyze_fault_coverage(
        self,
        fault_types: List[str],
    ) -> List[EvidenceAdvice]:
        """
        유책사유별 현황 분석

        Args:
            fault_types: 유책사유 목록 (예: ["adultery", "domestic_violence"])

        Returns:
            List[EvidenceAdvice]: 유책사유별 건수 정보
        """
        fault_counts = Counter(fault_types)
        advices = []

        # 주요 유책사유만 표시 (general 제외)
        main_faults = [
            "adultery", "desertion", "domestic_violence",
            "verbal_abuse", "economic_abuse", "financial_misconduct"
        ]

        for fault in main_faults:
            name = self.FAULT_TYPE_NAMES.get(fault, fault)
            count = fault_counts.get(fault, 0)
            advices.append(EvidenceAdvice(
                advice_type=AdviceType.FAULT_STATUS,
                severity=Severity.INFO if count > 0 else Severity.WARNING,
                message=f"{name} 관련 증거: {count}건",
                details={"fault": fault, "count": count}
            ))

        return advices

    def get_summary(
        self,
        timestamps: List[datetime],
        evidence_types: List[str],
        fault_types: List[str],
    ) -> Dict:
        """
        전체 요약 정보 반환

        Args:
            timestamps: 증거 타임스탬프 목록
            evidence_types: 증거 유형 목록
            fault_types: 유책사유 목록

        Returns:
            dict: 요약 통계
        """
        date_range = None
        if timestamps:
            sorted_dates = sorted(timestamps)
            date_range = {
                "start": sorted_dates[0].isoformat(),
                "end": sorted_dates[-1].isoformat()
            }

        return {
            "total_count": len(timestamps),
            "date_range": date_range,
            "type_counts": dict(Counter(evidence_types)),
            "fault_counts": dict(Counter(fault_types))
        }

    def get_all_advices(
        self,
        case_id: str,
        timestamps: List[datetime],
        evidence_types: List[str],
        fault_types: List[str],
    ) -> EvidenceAdviceResponse:
        """
        전체 어드바이스 생성

        Args:
            case_id: 사건 ID
            timestamps: 증거 타임스탬프 목록
            evidence_types: 증거 유형 목록
            fault_types: 유책사유 목록

        Returns:
            EvidenceAdviceResponse: 전체 어드바이스 응답
        """
        advices = []

        # 시간 공백 분석
        advices.extend(self.analyze_time_gaps(timestamps))

        # 증거 유형별 현황
        advices.extend(self.analyze_evidence_types(evidence_types))

        # 유책사유별 현황
        advices.extend(self.analyze_fault_coverage(fault_types))

        # 요약
        summary = self.get_summary(timestamps, evidence_types, fault_types)

        return EvidenceAdviceResponse(
            case_id=case_id,
            total_evidence_count=len(timestamps),
            advices=advices,
            summary=summary
        )
