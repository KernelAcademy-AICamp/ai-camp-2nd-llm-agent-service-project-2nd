"""
Test suite for EvidenceScorer
Following TDD approach: RED-GREEN-REFACTOR
"""

from datetime import datetime
from src.analysis.evidence_scorer import EvidenceScorer, ScoringResult
from src.parsers.base import Message


class TestEvidenceScorerInitialization:
    """Test EvidenceScorer initialization"""

    def test_scorer_creation(self):
        """EvidenceScorer 생성 테스트"""
        scorer = EvidenceScorer()

        assert scorer is not None

    def test_scorer_has_keywords(self):
        """키워드 목록이 초기화되는지 테스트"""
        scorer = EvidenceScorer()

        assert hasattr(scorer, 'keywords')
        assert len(scorer.keywords) > 0


class TestBasicScoring:
    """Test basic scoring functionality"""

    def test_score_neutral_message(self):
        """중립적 메시지의 점수 테스트"""
        scorer = EvidenceScorer()
        message = Message(
            content="안녕하세요. 오늘 날씨가 좋네요.",
            sender="홍길동",
            timestamp=datetime.now()
        )

        result = scorer.score(message)

        assert isinstance(result, ScoringResult)
        assert 0 <= result.score <= 10
        assert result.score < 3  # 중립적 메시지는 낮은 점수

    def test_score_high_evidence_message(self):
        """증거 가치가 높은 메시지 테스트"""
        scorer = EvidenceScorer()
        message = Message(
            content="이혼 소송을 진행하려고 합니다. 불륜 증거가 있습니다.",
            sender="홍길동",
            timestamp=datetime.now()
        )

        result = scorer.score(message)

        assert result.score > 5  # 증거 키워드가 있으면 높은 점수

    def test_score_violence_message(self):
        """폭력 관련 메시지 테스트"""
        scorer = EvidenceScorer()
        message = Message(
            content="폭행을 당했습니다. 병원 진단서가 있습니다.",
            sender="김철수",
            timestamp=datetime.now()
        )

        result = scorer.score(message)

        assert result.score > 7  # 폭력 키워드는 매우 높은 점수


class TestKeywordMatching:
    """Test keyword-based scoring"""

    def test_divorce_keywords(self):
        """이혼 관련 키워드 테스트"""
        scorer = EvidenceScorer()
        message = Message(
            content="이혼 합의서를 작성했습니다.",
            sender="홍길동",
            timestamp=datetime.now()
        )

        result = scorer.score(message)

        assert "이혼" in result.matched_keywords
        assert result.score > 3

    def test_financial_keywords(self):
        """재산 관련 키워드 테스트"""
        scorer = EvidenceScorer()
        message = Message(
            content="재산 분할 협의가 필요합니다. 통장 내역을 확인해주세요.",
            sender="김철수",
            timestamp=datetime.now()
        )

        result = scorer.score(message)

        assert any(kw in result.matched_keywords for kw in ["재산", "통장"])
        assert result.score > 4

    def test_multiple_keywords(self):
        """여러 키워드가 있는 메시지 테스트"""
        scorer = EvidenceScorer()
        message = Message(
            content="이혼 소송을 위해 불륜 증거와 재산 목록이 필요합니다.",
            sender="홍길동",
            timestamp=datetime.now()
        )

        result = scorer.score(message)

        assert len(result.matched_keywords) >= 3
        assert result.score > 6  # 다중 키워드는 더 높은 점수


class TestScoringResult:
    """Test ScoringResult data model"""

    def test_scoring_result_creation(self):
        """ScoringResult 생성 테스트"""
        result = ScoringResult(
            score=7.5,
            matched_keywords=["이혼", "증거"],
            reasoning="High evidence value due to divorce and evidence keywords"
        )

        assert result.score == 7.5
        assert result.matched_keywords == ["이혼", "증거"]
        assert "divorce" in result.reasoning.lower()

    def test_score_validation(self):
        """점수 범위 검증 테스트"""
        # 유효한 점수
        result = ScoringResult(score=5.0, matched_keywords=[], reasoning="test")
        assert 0 <= result.score <= 10

        # 최소값
        result_min = ScoringResult(score=0.0, matched_keywords=[], reasoning="test")
        assert result_min.score == 0.0

        # 최대값
        result_max = ScoringResult(score=10.0, matched_keywords=[], reasoning="test")
        assert result_max.score == 10.0


class TestBatchScoring:
    """Test batch scoring functionality"""

    def test_score_multiple_messages(self):
        """여러 메시지 일괄 점수 계산 테스트"""
        scorer = EvidenceScorer()
        messages = [
            Message(content="안녕하세요", sender="A", timestamp=datetime.now()),
            Message(content="이혼 소송 관련 상담", sender="B", timestamp=datetime.now()),
            Message(content="폭행 증거 제출", sender="C", timestamp=datetime.now())
        ]

        results = scorer.score_batch(messages)

        assert len(results) == 3
        assert all(isinstance(r, ScoringResult) for r in results)
        # 순서대로 점수가 증가해야 함
        assert results[0].score < results[1].score < results[2].score


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_message(self):
        """빈 메시지 테스트"""
        scorer = EvidenceScorer()
        message = Message(
            content="",
            sender="홍길동",
            timestamp=datetime.now()
        )

        result = scorer.score(message)

        assert result.score == 0.0
        assert len(result.matched_keywords) == 0

    def test_very_long_message(self):
        """매우 긴 메시지 테스트"""
        scorer = EvidenceScorer()
        message = Message(
            content="이혼 " * 100 + "증거 " * 50,  # 긴 메시지
            sender="홍길동",
            timestamp=datetime.now()
        )

        result = scorer.score(message)

        # 점수는 10을 초과하지 않아야 함
        assert result.score <= 10.0
        # 키워드는 감지되어야 함
        assert len(result.matched_keywords) > 0

    def test_special_characters(self):
        """특수 문자 포함 메시지 테스트"""
        scorer = EvidenceScorer()
        message = Message(
            content="이혼!!! 소송@@@ 진행#$%",
            sender="홍길동",
            timestamp=datetime.now()
        )

        result = scorer.score(message)

        # 특수 문자를 무시하고 키워드 매칭
        assert "이혼" in result.matched_keywords
        assert result.score > 0
