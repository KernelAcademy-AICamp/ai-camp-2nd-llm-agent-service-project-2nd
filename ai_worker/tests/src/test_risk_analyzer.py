"""
Test suite for RiskAnalyzer
Following TDD approach: RED-GREEN-REFACTOR
"""

from datetime import datetime
from src.analysis.risk_analyzer import RiskAnalyzer, RiskAssessment, RiskLevel
from src.parsers.base import Message


class TestRiskAnalyzerInitialization:
    """Test RiskAnalyzer initialization"""

    def test_analyzer_creation(self):
        """RiskAnalyzer 생성 테스트"""
        analyzer = RiskAnalyzer()

        assert analyzer is not None

    def test_analyzer_has_risk_patterns(self):
        """리스크 패턴이 초기화되는지 테스트"""
        analyzer = RiskAnalyzer()

        assert hasattr(analyzer, 'risk_patterns')
        assert len(analyzer.risk_patterns) > 0


class TestThreatDetection:
    """Test threat pattern detection"""

    def test_detect_explicit_threat(self):
        """명시적 위협 탐지 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="죽이겠다고 협박했습니다.",
                sender="피해자",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert result.risk_level == RiskLevel.CRITICAL
        assert "threat" in result.risk_factors
        assert len(result.warnings) > 0

    def test_detect_violence_pattern(self):
        """폭력 패턴 탐지 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="어제 폭행을 당했습니다. 병원에 갔습니다.",
                sender="피해자",
                timestamp=datetime.now()
            ),
            Message(
                content="진단서를 받았습니다. 전치 2주입니다.",
                sender="피해자",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert "violence" in result.risk_factors


class TestFinancialRisk:
    """Test financial dispute detection"""

    def test_detect_financial_dispute(self):
        """금전 분쟁 탐지 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="통장에서 몰래 돈을 빼갔습니다.",
                sender="A",
                timestamp=datetime.now()
            ),
            Message(
                content="재산을 숨기고 있습니다.",
                sender="A",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert "financial_dispute" in result.risk_factors
        assert result.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]

    def test_detect_property_concealment(self):
        """재산 은닉 탐지 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="재산을 다른 사람 명의로 옮겼습니다.",
                sender="증인",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert "property_concealment" in result.risk_factors


class TestChildSafetyRisk:
    """Test child-related risk detection"""

    def test_detect_child_safety_risk(self):
        """아동 안전 리스크 탐지 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="아이 앞에서 폭력을 행사했습니다.",
                sender="목격자",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert "child_safety" in result.risk_factors
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    def test_detect_custody_violation(self):
        """양육권 위반 탐지 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="약속된 면접교섭을 거부했습니다.",
                sender="배우자",
                timestamp=datetime.now()
            ),
            Message(
                content="아이를 만나지 못하게 합니다.",
                sender="배우자",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert "custody_violation" in result.risk_factors


class TestRiskLevel:
    """Test risk level classification"""

    def test_no_risk(self):
        """리스크 없는 케이스 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="안녕하세요. 상담 일정을 잡고 싶습니다.",
                sender="상담자",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert result.risk_level == RiskLevel.LOW
        assert len(result.risk_factors) == 0

    def test_medium_risk(self):
        """중간 리스크 케이스 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="재산 분할에 대해 협의가 필요합니다.",
                sender="A",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]

    def test_multiple_risk_factors(self):
        """복합 리스크 케이스 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="폭행을 당했고, 재산도 몰래 빼돌렸습니다.",
                sender="피해자",
                timestamp=datetime.now()
            ),
            Message(
                content="아이에게도 위협을 가했습니다.",
                sender="피해자",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert len(result.risk_factors) >= 2
        assert result.risk_level == RiskLevel.CRITICAL


class TestRiskAssessment:
    """Test RiskAssessment data model"""

    def test_risk_assessment_creation(self):
        """RiskAssessment 생성 테스트"""
        assessment = RiskAssessment(
            risk_level=RiskLevel.HIGH,
            risk_factors=["violence", "threat"],
            warnings=["Immediate safety concern"],
            recommendations=["Contact authorities", "Seek protective order"]
        )

        assert assessment.risk_level == RiskLevel.HIGH
        assert len(assessment.risk_factors) == 2
        assert len(assessment.warnings) == 1
        assert len(assessment.recommendations) == 2

    def test_risk_level_enum(self):
        """RiskLevel enum 테스트"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


class TestWarningsAndRecommendations:
    """Test warnings and recommendations generation"""

    def test_warnings_for_threat(self):
        """위협 상황 경고 생성 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="협박 문자를 받았습니다.",
                sender="피해자",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert len(result.warnings) > 0
        # 경고 메시지에 "안전" 또는 "경찰" 키워드 포함
        warning_text = " ".join(result.warnings).lower()
        assert any(kw in warning_text for kw in ["안전", "경찰", "신고", "보호"])

    def test_recommendations_generated(self):
        """권장 사항 생성 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="폭행 증거가 있습니다.",
                sender="피해자",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert len(result.recommendations) > 0
        # 권장 사항이 구체적이어야 함
        assert all(len(rec) > 10 for rec in result.recommendations)


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_message_list(self):
        """빈 메시지 리스트 테스트"""
        analyzer = RiskAnalyzer()
        messages = []

        result = analyzer.analyze(messages)

        assert result.risk_level == RiskLevel.LOW
        assert len(result.risk_factors) == 0
        assert len(result.warnings) == 0

    def test_single_neutral_message(self):
        """단일 중립 메시지 테스트"""
        analyzer = RiskAnalyzer()
        messages = [
            Message(
                content="안녕하세요",
                sender="A",
                timestamp=datetime.now()
            )
        ]

        result = analyzer.analyze(messages)

        assert result.risk_level == RiskLevel.LOW
