"""
Test suite for EvidenceAdvisor
증거 현황 분석기 테스트 (LLM 미사용, 규칙 기반)
"""

from datetime import datetime
from src.analysis.evidence_advisor import (
    EvidenceAdvisor,
    EvidenceAdvice,
    EvidenceAdviceResponse,
    AdviceType,
    Severity,
)


class TestEvidenceAdvisorInitialization:
    """EvidenceAdvisor 초기화 테스트"""

    def test_advisor_creation(self):
        """기본 생성 테스트"""
        advisor = EvidenceAdvisor()
        assert advisor is not None
        assert advisor.gap_threshold_days == 30

    def test_advisor_custom_threshold(self):
        """커스텀 임계값 테스트"""
        advisor = EvidenceAdvisor(gap_threshold_days=60)
        assert advisor.gap_threshold_days == 60

    def test_evidence_type_names_exist(self):
        """증거 유형 이름 매핑 테스트"""
        advisor = EvidenceAdvisor()
        assert "kakaotalk" in advisor.EVIDENCE_TYPE_NAMES
        assert "photo" in advisor.EVIDENCE_TYPE_NAMES
        assert advisor.EVIDENCE_TYPE_NAMES["kakaotalk"] == "카카오톡 대화"

    def test_fault_type_names_exist(self):
        """유책사유 이름 매핑 테스트"""
        advisor = EvidenceAdvisor()
        assert "adultery" in advisor.FAULT_TYPE_NAMES
        assert "domestic_violence" in advisor.FAULT_TYPE_NAMES
        assert advisor.FAULT_TYPE_NAMES["adultery"] == "부정행위"


class TestTimeGapAnalysis:
    """시간대 공백 분석 테스트"""

    def test_no_gap_with_continuous_dates(self):
        """연속된 날짜에서는 공백이 없어야 함"""
        advisor = EvidenceAdvisor()
        timestamps = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 15),
            datetime(2024, 1, 25),
        ]

        advices = advisor.analyze_time_gaps(timestamps)

        assert len(advices) == 0

    def test_detect_single_gap(self):
        """단일 공백 탐지 테스트"""
        advisor = EvidenceAdvisor()
        timestamps = [
            datetime(2024, 1, 1),
            datetime(2024, 4, 1),  # 90일 공백
        ]

        advices = advisor.analyze_time_gaps(timestamps)

        assert len(advices) == 1
        assert advices[0].advice_type == AdviceType.TIME_GAP
        assert advices[0].severity == Severity.WARNING
        assert "2024년 01월" in advices[0].message
        assert "2024년 04월" in advices[0].message

    def test_detect_multiple_gaps(self):
        """여러 공백 탐지 테스트"""
        advisor = EvidenceAdvisor()
        timestamps = [
            datetime(2024, 1, 1),
            datetime(2024, 4, 1),   # 첫 번째 공백
            datetime(2024, 4, 15),
            datetime(2024, 8, 1),   # 두 번째 공백
        ]

        advices = advisor.analyze_time_gaps(timestamps)

        assert len(advices) == 2

    def test_gap_threshold_boundary(self):
        """공백 임계값 경계 테스트"""
        advisor = EvidenceAdvisor(gap_threshold_days=30)

        # 정확히 30일 - 공백 아님
        timestamps_30 = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 31),  # 30일
        ]
        advices_30 = advisor.analyze_time_gaps(timestamps_30)
        assert len(advices_30) == 0

        # 31일 - 공백
        timestamps_31 = [
            datetime(2024, 1, 1),
            datetime(2024, 2, 1),  # 31일
        ]
        advices_31 = advisor.analyze_time_gaps(timestamps_31)
        assert len(advices_31) == 1

    def test_unsorted_timestamps(self):
        """정렬되지 않은 타임스탬프 처리 테스트"""
        advisor = EvidenceAdvisor()
        timestamps = [
            datetime(2024, 4, 1),
            datetime(2024, 1, 1),
            datetime(2024, 7, 1),
        ]

        advices = advisor.analyze_time_gaps(timestamps)

        # 자동 정렬 후 분석
        assert len(advices) == 2

    def test_empty_timestamps(self):
        """빈 타임스탬프 리스트 테스트"""
        advisor = EvidenceAdvisor()
        advices = advisor.analyze_time_gaps([])
        assert len(advices) == 0

    def test_single_timestamp(self):
        """단일 타임스탬프 테스트"""
        advisor = EvidenceAdvisor()
        advices = advisor.analyze_time_gaps([datetime(2024, 1, 1)])
        assert len(advices) == 0

    def test_gap_details_included(self):
        """공백 상세 정보 포함 테스트"""
        advisor = EvidenceAdvisor()
        timestamps = [
            datetime(2024, 1, 1),
            datetime(2024, 4, 1),
        ]

        advices = advisor.analyze_time_gaps(timestamps)

        assert "gap_start" in advices[0].details
        assert "gap_end" in advices[0].details
        assert "gap_days" in advices[0].details
        assert advices[0].details["gap_days"] == 91


class TestEvidenceTypeAnalysis:
    """증거 유형별 현황 분석 테스트"""

    def test_count_evidence_types(self):
        """증거 유형 카운트 테스트"""
        advisor = EvidenceAdvisor()
        evidence_types = ["kakaotalk", "kakaotalk", "photo", "recording"]

        advices = advisor.analyze_evidence_types(evidence_types)

        # 모든 정의된 유형에 대해 어드바이스 생성
        assert len(advices) == len(advisor.EVIDENCE_TYPE_NAMES)

        # 카카오톡 카운트 확인
        kakao_advice = next(a for a in advices if a.details.get("type") == "kakaotalk")
        assert kakao_advice.details["count"] == 2
        assert "카카오톡 대화: 2건" in kakao_advice.message

    def test_zero_count_warning(self):
        """0건 유형의 severity 테스트"""
        advisor = EvidenceAdvisor()
        evidence_types = ["kakaotalk"]

        advices = advisor.analyze_evidence_types(evidence_types)

        # 녹음 파일은 0건이므로 WARNING
        recording_advice = next(a for a in advices if a.details.get("type") == "recording")
        assert recording_advice.severity == Severity.WARNING
        assert recording_advice.details["count"] == 0

    def test_positive_count_info(self):
        """1건 이상 유형의 severity 테스트"""
        advisor = EvidenceAdvisor()
        evidence_types = ["photo", "photo", "photo"]

        advices = advisor.analyze_evidence_types(evidence_types)

        photo_advice = next(a for a in advices if a.details.get("type") == "photo")
        assert photo_advice.severity == Severity.INFO
        assert photo_advice.details["count"] == 3

    def test_empty_evidence_types(self):
        """빈 증거 유형 리스트 테스트"""
        advisor = EvidenceAdvisor()
        advices = advisor.analyze_evidence_types([])

        # 모든 유형이 0건으로 표시
        assert len(advices) == len(advisor.EVIDENCE_TYPE_NAMES)
        assert all(a.details["count"] == 0 for a in advices)


class TestFaultCoverageAnalysis:
    """유책사유별 현황 분석 테스트"""

    def test_count_fault_types(self):
        """유책사유 카운트 테스트"""
        advisor = EvidenceAdvisor()
        fault_types = ["adultery", "adultery", "domestic_violence"]

        advices = advisor.analyze_fault_coverage(fault_types)

        # 주요 유책사유에 대해 어드바이스 생성
        assert len(advices) == 6  # 6개 주요 유책사유

        adultery_advice = next(a for a in advices if a.details.get("fault") == "adultery")
        assert adultery_advice.details["count"] == 2
        assert "부정행위 관련 증거: 2건" in adultery_advice.message

    def test_zero_fault_warning(self):
        """0건 유책사유의 severity 테스트"""
        advisor = EvidenceAdvisor()
        fault_types = ["adultery"]

        advices = advisor.analyze_fault_coverage(fault_types)

        violence_advice = next(a for a in advices if a.details.get("fault") == "domestic_violence")
        assert violence_advice.severity == Severity.WARNING
        assert violence_advice.details["count"] == 0

    def test_general_excluded(self):
        """general 카테고리 제외 테스트"""
        advisor = EvidenceAdvisor()
        fault_types = ["general", "general", "adultery"]

        advices = advisor.analyze_fault_coverage(fault_types)

        # general은 주요 유책사유에 포함되지 않음
        fault_names = [a.details.get("fault") for a in advices]
        assert "general" not in fault_names


class TestSummary:
    """요약 정보 테스트"""

    def test_summary_basic(self):
        """기본 요약 정보 테스트"""
        advisor = EvidenceAdvisor()
        timestamps = [datetime(2024, 1, 1), datetime(2024, 6, 1)]
        evidence_types = ["kakaotalk", "photo"]
        fault_types = ["adultery"]

        summary = advisor.get_summary(timestamps, evidence_types, fault_types)

        assert summary["total_count"] == 2
        assert summary["date_range"]["start"] == "2024-01-01T00:00:00"
        assert summary["date_range"]["end"] == "2024-06-01T00:00:00"
        assert summary["type_counts"]["kakaotalk"] == 1
        assert summary["fault_counts"]["adultery"] == 1

    def test_summary_empty(self):
        """빈 데이터 요약 테스트"""
        advisor = EvidenceAdvisor()
        summary = advisor.get_summary([], [], [])

        assert summary["total_count"] == 0
        assert summary["date_range"] is None


class TestGetAllAdvices:
    """전체 어드바이스 생성 테스트"""

    def test_get_all_advices_structure(self):
        """전체 어드바이스 응답 구조 테스트"""
        advisor = EvidenceAdvisor()
        timestamps = [datetime(2024, 1, 1), datetime(2024, 6, 1)]
        evidence_types = ["kakaotalk", "photo"]
        fault_types = ["adultery"]

        response = advisor.get_all_advices(
            case_id="TEST-001",
            timestamps=timestamps,
            evidence_types=evidence_types,
            fault_types=fault_types
        )

        assert isinstance(response, EvidenceAdviceResponse)
        assert response.case_id == "TEST-001"
        assert response.total_evidence_count == 2
        assert len(response.advices) > 0
        assert response.disclaimer is not None

    def test_response_to_dict(self):
        """응답 딕셔너리 변환 테스트"""
        advisor = EvidenceAdvisor()
        response = advisor.get_all_advices(
            case_id="TEST-001",
            timestamps=[datetime(2024, 1, 1)],
            evidence_types=["photo"],
            fault_types=["adultery"]
        )

        result = response.to_dict()

        assert isinstance(result, dict)
        assert "case_id" in result
        assert "advices" in result
        assert "summary" in result
        assert "generated_at" in result


class TestEvidenceAdviceDataClass:
    """EvidenceAdvice 데이터 클래스 테스트"""

    def test_advice_creation(self):
        """어드바이스 생성 테스트"""
        advice = EvidenceAdvice(
            advice_type=AdviceType.TIME_GAP,
            severity=Severity.WARNING,
            message="2024년 01월~04월 기간의 증거가 없습니다",
            details={"gap_days": 90}
        )

        assert advice.advice_type == AdviceType.TIME_GAP
        assert advice.severity == Severity.WARNING
        assert "증거가 없습니다" in advice.message

    def test_advice_to_dict(self):
        """어드바이스 딕셔너리 변환 테스트"""
        advice = EvidenceAdvice(
            advice_type=AdviceType.TYPE_STATUS,
            severity=Severity.INFO,
            message="카카오톡 대화: 5건",
            details={"type": "kakaotalk", "count": 5}
        )

        result = advice.to_dict()

        assert result["advice_type"] == "type_status"
        assert result["severity"] == "info"
        assert result["message"] == "카카오톡 대화: 5건"
        assert result["details"]["count"] == 5


class TestToneCompliance:
    """톤앤매너 준수 테스트"""

    def test_messages_use_objective_tone(self):
        """메시지가 객관적 톤을 사용하는지 테스트"""
        advisor = EvidenceAdvisor()
        timestamps = [datetime(2024, 1, 1), datetime(2024, 6, 1)]

        advices = advisor.analyze_time_gaps(timestamps)

        for advice in advices:
            # "~하세요" 형태 금지
            assert "하세요" not in advice.message
            assert "해야 합니다" not in advice.message
            # "~입니다" 형태 사용
            assert "입니다" in advice.message or "없습니다" in advice.message

    def test_no_advice_expressions(self):
        """조언 표현이 없는지 테스트"""
        advisor = EvidenceAdvisor()
        response = advisor.get_all_advices(
            case_id="TEST",
            timestamps=[datetime(2024, 1, 1)],
            evidence_types=["photo"],
            fault_types=["adultery"]
        )

        forbidden_phrases = ["추천", "권장", "좋겠습니다", "유리합니다"]

        for advice in response.advices:
            for phrase in forbidden_phrases:
                assert phrase not in advice.message, f"Found forbidden phrase '{phrase}' in: {advice.message}"
