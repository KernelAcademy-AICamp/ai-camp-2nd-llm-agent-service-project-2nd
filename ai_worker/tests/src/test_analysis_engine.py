"""
Test suite for AnalysisEngine
Following TDD approach: RED-GREEN-REFACTOR
"""

from datetime import datetime
from src.analysis.analysis_engine import AnalysisEngine, AnalysisResult
from src.analysis.evidence_scorer import ScoringResult
from src.analysis.risk_analyzer import RiskAssessment, RiskLevel
from src.parsers.base import Message


class TestAnalysisEngineInitialization:
    """Test AnalysisEngine initialization"""

    def test_engine_creation(self):
        """AnalysisEngine 생성 테스트"""
        engine = AnalysisEngine()

        assert engine is not None

    def test_engine_has_components(self):
        """내부 컴포넌트 초기화 테스트"""
        engine = AnalysisEngine()

        assert hasattr(engine, 'scorer')
        assert hasattr(engine, 'risk_analyzer')


class TestBasicAnalysis:
    """Test basic case analysis"""

    def test_analyze_simple_case(self):
        """간단한 케이스 분석 테스트"""
        engine = AnalysisEngine()
        messages = [
            Message(
                content="이혼 상담을 받고 싶습니다.",
                sender="상담자",
                timestamp=datetime.now()
            ),
            Message(
                content="재산 분할에 대해 알고 싶습니다.",
                sender="상담자",
                timestamp=datetime.now()
            )
        ]

        result = engine.analyze_case(messages, case_id="case_001")

        assert isinstance(result, AnalysisResult)
        assert result.case_id == "case_001"
        assert result.total_messages == 2

    def test_analyze_high_risk_case(self):
        """높은 리스크 케이스 분석 테스트"""
        engine = AnalysisEngine()
        messages = [
            Message(
                content="협박 문자를 받았습니다. 죽이겠다고 합니다.",
                sender="피해자",
                timestamp=datetime.now()
            ),
            Message(
                content="폭행을 당했고 병원 진단서가 있습니다.",
                sender="피해자",
                timestamp=datetime.now()
            )
        ]

        result = engine.analyze_case(messages, case_id="case_002")

        assert result.risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert len(result.risk_assessment.warnings) > 0


class TestHighValueMessages:
    """Test high-value message identification"""

    def test_identify_high_value_messages(self):
        """증거 가치 높은 메시지 식별 테스트"""
        engine = AnalysisEngine()
        messages = [
            Message(
                content="안녕하세요",
                sender="A",
                timestamp=datetime.now()
            ),
            Message(
                content="폭행 증거 사진이 있습니다. 이혼 소송 준비 중입니다.",
                sender="B",
                timestamp=datetime.now()
            ),
            Message(
                content="날씨 좋네요",
                sender="C",
                timestamp=datetime.now()
            )
        ]

        result = engine.analyze_case(messages, case_id="case_003")

        # 높은 점수 메시지만 포함
        assert len(result.high_value_messages) > 0
        assert all(msg.score >= 6.0 for msg in result.high_value_messages)

    def test_high_value_threshold(self):
        """증거 가치 임계값 테스트"""
        engine = AnalysisEngine()
        messages = [
            Message(
                content="이혼 소송 관련 증거 자료입니다.",
                sender="변호사",
                timestamp=datetime.now()
            )
        ]

        result = engine.analyze_case(messages, case_id="case_004")

        # 기본 임계값 6.0 이상
        for msg in result.high_value_messages:
            assert msg.score >= 6.0


class TestStatisticalSummary:
    """Test statistical summaries"""

    def test_average_score_calculation(self):
        """평균 점수 계산 테스트"""
        engine = AnalysisEngine()
        messages = [
            Message(content="안녕하세요", sender="A", timestamp=datetime.now()),
            Message(content="이혼 소송", sender="B", timestamp=datetime.now()),
            Message(content="폭행 증거", sender="C", timestamp=datetime.now())
        ]

        result = engine.analyze_case(messages, case_id="case_005")

        assert result.average_score > 0
        assert result.average_score <= 10.0

    def test_summary_contains_statistics(self):
        """요약 통계 포함 테스트"""
        engine = AnalysisEngine()
        messages = [
            Message(content="이혼 상담", sender="A", timestamp=datetime.now())
        ]

        result = engine.analyze_case(messages, case_id="case_006")

        assert "total_messages" in result.summary
        assert "average_score" in result.summary
        assert "high_value_count" in result.summary
        assert "risk_level" in result.summary


class TestResultStructure:
    """Test AnalysisResult data model"""

    def test_analysis_result_creation(self):
        """AnalysisResult 생성 테스트"""
        from src.analysis.risk_analyzer import RiskLevel

        result = AnalysisResult(
            case_id="test_case",
            total_messages=5,
            average_score=6.5,
            high_value_messages=[
                ScoringResult(score=8.0, matched_keywords=["이혼"], reasoning="test")
            ],
            risk_assessment=RiskAssessment(
                risk_level=RiskLevel.MEDIUM,
                risk_factors=["financial_dispute"],
                warnings=["Warning"],
                recommendations=["Recommendation"]
            ),
            summary={
                "total_messages": 5,
                "average_score": 6.5,
                "high_value_count": 1,
                "risk_level": "medium"
            }
        )

        assert result.case_id == "test_case"
        assert result.total_messages == 5
        assert result.average_score == 6.5
        assert len(result.high_value_messages) == 1
        assert result.risk_assessment.risk_level == RiskLevel.MEDIUM


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_message_list(self):
        """빈 메시지 리스트 테스트"""
        engine = AnalysisEngine()
        messages = []

        result = engine.analyze_case(messages, case_id="case_empty")

        assert result.total_messages == 0
        assert result.average_score == 0.0
        assert len(result.high_value_messages) == 0
        assert result.risk_assessment.risk_level == RiskLevel.LOW

    def test_single_message(self):
        """단일 메시지 테스트"""
        engine = AnalysisEngine()
        messages = [
            Message(
                content="이혼 상담 요청",
                sender="상담자",
                timestamp=datetime.now()
            )
        ]

        result = engine.analyze_case(messages, case_id="case_single")

        assert result.total_messages == 1
        assert result.average_score > 0

    def test_all_neutral_messages(self):
        """모든 중립 메시지 테스트"""
        engine = AnalysisEngine()
        messages = [
            Message(content="안녕하세요", sender="A", timestamp=datetime.now()),
            Message(content="날씨 좋네요", sender="B", timestamp=datetime.now()),
            Message(content="감사합니다", sender="C", timestamp=datetime.now())
        ]

        result = engine.analyze_case(messages, case_id="case_neutral")

        assert len(result.high_value_messages) == 0
        assert result.risk_assessment.risk_level == RiskLevel.LOW


class TestIntegration:
    """Test integration between components"""

    def test_scorer_and_risk_analyzer_coordination(self):
        """EvidenceScorer와 RiskAnalyzer 통합 테스트"""
        engine = AnalysisEngine()
        messages = [
            Message(
                content="협박을 받았고, 폭행 증거가 있습니다.",
                sender="피해자",
                timestamp=datetime.now()
            )
        ]

        result = engine.analyze_case(messages, case_id="case_integration")

        # 높은 증거 점수
        assert len(result.high_value_messages) > 0
        assert result.high_value_messages[0].score >= 7.0

        # 높은 리스크 레벨
        assert result.risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        # 요약에 모든 정보 포함
        assert result.summary["risk_level"] in ["high", "critical"]
        assert result.summary["high_value_count"] > 0

    def test_comprehensive_case_analysis(self):
        """종합 케이스 분석 테스트"""
        engine = AnalysisEngine()
        messages = [
            Message(content="상담 신청합니다", sender="상담자", timestamp=datetime.now()),
            Message(content="이혼 소송 준비 중입니다", sender="상담자", timestamp=datetime.now()),
            Message(content="폭행을 당했습니다", sender="피해자", timestamp=datetime.now()),
            Message(content="병원 진단서가 있습니다", sender="피해자", timestamp=datetime.now()),
            Message(content="재산 분할 관련 자료", sender="변호사", timestamp=datetime.now()),
            Message(content="협박 문자 증거", sender="피해자", timestamp=datetime.now())
        ]

        result = engine.analyze_case(messages, case_id="case_comprehensive")

        # 기본 검증
        assert result.total_messages == 6
        assert result.average_score > 4.0

        # 높은 가치 메시지 존재
        assert len(result.high_value_messages) >= 3

        # 리스크 요인 탐지
        assert len(result.risk_assessment.risk_factors) > 0
        assert result.risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        # 경고 및 권장사항
        assert len(result.risk_assessment.warnings) > 0
        assert len(result.risk_assessment.recommendations) > 0
