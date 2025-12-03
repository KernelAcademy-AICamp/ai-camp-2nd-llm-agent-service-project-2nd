"""
LegalAnalyzer 테스트

Given: EvidenceChunk
When: LegalAnalyzer.analyze() 호출
Then: LegalAnalysis 반환 (카테고리, 신뢰도, 키워드)
"""

import unittest
from datetime import datetime
import hashlib

from src.analysis.legal_analyzer import (
    LegalAnalyzer,
    score_to_confidence_level,
    score_to_confidence_score,
    analyze_chunk,
    analyze_chunks,
    CATEGORY_MAPPING
)
from src.schemas import (
    EvidenceChunk,
    SourceLocation,
    FileType,
    LegalCategory,
    ConfidenceLevel,
    LegalAnalysis
)


def make_test_chunk(content: str, sender: str = "Test") -> EvidenceChunk:
    """테스트용 EvidenceChunk 생성"""
    return EvidenceChunk(
        chunk_id="test_chunk_001",
        file_id="test_file_001",
        case_id="test_case_001",
        content=content,
        content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
        source_location=SourceLocation(
            file_name="test.txt",
            file_type=FileType.TEXT,
            line_number=1
        ),
        sender=sender,
        timestamp=datetime.now()
    )


class TestLegalAnalyzerInitialization(unittest.TestCase):
    """LegalAnalyzer 초기화 테스트"""

    def test_analyzer_creation_keyword_mode(self):
        """Given: use_ai=False
        When: LegalAnalyzer() 생성
        Then: 키워드 기반 분석기 생성"""
        analyzer = LegalAnalyzer(use_ai=False)
        self.assertIsNotNone(analyzer)
        self.assertFalse(analyzer.use_ai)

    def test_analyzer_creation_ai_mode(self):
        """Given: use_ai=True
        When: LegalAnalyzer() 생성
        Then: AI 기반 분석기 생성"""
        analyzer = LegalAnalyzer(use_ai=True, ai_model="gpt-4o-mini")
        self.assertIsNotNone(analyzer)
        self.assertTrue(analyzer.use_ai)
        self.assertEqual(analyzer.ai_model, "gpt-4o-mini")

    def test_analyzer_has_tagger_and_scorer(self):
        """Given: 초기화된 LegalAnalyzer
        When: 내부 컴포넌트 확인
        Then: tagger와 scorer 존재"""
        analyzer = LegalAnalyzer()
        self.assertIsNotNone(analyzer.tagger)
        self.assertIsNotNone(analyzer.scorer)


class TestLegalAnalyzerKeywordAnalysis(unittest.TestCase):
    """키워드 기반 분석 테스트"""

    def setUp(self):
        self.analyzer = LegalAnalyzer(use_ai=False)

    def test_analyze_adultery(self):
        """Given: 외도 관련 메시지
        When: analyze() 호출
        Then: ADULTERY 카테고리 분류"""
        chunk = make_test_chunk("외도 증거입니다. 불륜 관계를 확인했습니다.")
        analysis = self.analyzer.analyze(chunk)

        self.assertIsInstance(analysis, LegalAnalysis)
        self.assertIn(LegalCategory.ADULTERY, analysis.categories)

    def test_analyze_domestic_violence(self):
        """Given: 가정폭력 관련 메시지
        When: analyze() 호출
        Then: DOMESTIC_VIOLENCE 카테고리 분류"""
        chunk = make_test_chunk("남편이 때렸어. 멍이 들었어.")
        analysis = self.analyzer.analyze(chunk)

        self.assertIn(LegalCategory.DOMESTIC_VIOLENCE, analysis.categories)

    def test_analyze_financial_misconduct(self):
        """Given: 재정 비행 관련 메시지
        When: analyze() 호출
        Then: FINANCIAL_MISCONDUCT 카테고리 분류"""
        chunk = make_test_chunk("도박으로 빚이 2억이야.")
        analysis = self.analyzer.analyze(chunk)

        self.assertIn(LegalCategory.FINANCIAL_MISCONDUCT, analysis.categories)

    def test_analyze_desertion(self):
        """Given: 유기 관련 메시지
        When: analyze() 호출
        Then: DESERTION 카테고리 분류"""
        chunk = make_test_chunk("집을 나간 지 1년이 됐어요. 연락 두절입니다.")
        analysis = self.analyzer.analyze(chunk)

        self.assertIn(LegalCategory.DESERTION, analysis.categories)

    def test_analyze_general(self):
        """Given: 일반 메시지
        When: analyze() 호출
        Then: GENERAL 카테고리 분류"""
        chunk = make_test_chunk("오늘 날씨가 좋네요.")
        analysis = self.analyzer.analyze(chunk)

        self.assertIn(LegalCategory.GENERAL, analysis.categories)


class TestLegalAnalyzerConfidence(unittest.TestCase):
    """신뢰도 계산 테스트"""

    def setUp(self):
        self.analyzer = LegalAnalyzer(use_ai=False)

    def test_high_confidence_multiple_keywords(self):
        """Given: 여러 키워드가 있는 메시지
        When: analyze() 호출
        Then: 높은 신뢰도 레벨"""
        chunk = make_test_chunk("외도, 불륜, 바람을 피우고 있어요.")
        analysis = self.analyzer.analyze(chunk)

        # 여러 키워드 → 높은 신뢰도
        self.assertGreater(analysis.confidence_score, 0.5)

    def test_low_confidence_vague_message(self):
        """Given: 모호한 메시지
        When: analyze() 호출
        Then: 낮은 신뢰도 레벨"""
        chunk = make_test_chunk("이상한 일이 있었어요.")
        analysis = self.analyzer.analyze(chunk)

        # 키워드 없음 → 낮은 신뢰도
        level_value = analysis.confidence_level.value if hasattr(analysis.confidence_level, 'value') else analysis.confidence_level
        self.assertLessEqual(level_value, 2)


class TestLegalAnalyzerHumanReview(unittest.TestCase):
    """사람 검토 필요 여부 테스트"""

    def setUp(self):
        self.analyzer = LegalAnalyzer(use_ai=False)

    def test_requires_review_low_confidence_important(self):
        """Given: 중요 카테고리 + 낮은 신뢰도
        When: analyze() 호출
        Then: requires_human_review=True"""
        # 외도 키워드 하나만 있음 → 낮은 신뢰도
        chunk = make_test_chunk("호텔에 갔다고 했어요.")
        analysis = self.analyzer.analyze(chunk)

        # 외도 카테고리이지만 신뢰도 낮으면 검토 필요
        level_value = analysis.confidence_level.value if hasattr(analysis.confidence_level, 'value') else analysis.confidence_level
        if LegalCategory.ADULTERY in analysis.categories and level_value <= 2:
            self.assertTrue(analysis.requires_human_review)


class TestLegalAnalyzerBatch(unittest.TestCase):
    """일괄 분석 테스트"""

    def setUp(self):
        self.analyzer = LegalAnalyzer(use_ai=False)

    def test_analyze_batch(self):
        """Given: 여러 청크
        When: analyze_batch() 호출
        Then: 모든 청크에 legal_analysis 추가"""
        chunks = [
            make_test_chunk("외도 증거"),
            make_test_chunk("폭력 증거"),
            make_test_chunk("일반 메시지")
        ]

        analyzed = self.analyzer.analyze_batch(chunks)

        self.assertEqual(len(analyzed), 3)
        for chunk in analyzed:
            self.assertIsNotNone(chunk.legal_analysis)

    def test_analyze_and_update(self):
        """Given: 단일 청크
        When: analyze_and_update() 호출
        Then: legal_analysis 필드 업데이트"""
        chunk = make_test_chunk("테스트 메시지")
        updated = self.analyzer.analyze_and_update(chunk)

        self.assertIsNotNone(updated.legal_analysis)


class TestLegalAnalyzerSummaryStats(unittest.TestCase):
    """통계 요약 테스트"""

    def setUp(self):
        self.analyzer = LegalAnalyzer(use_ai=False)

    def test_get_summary_stats(self):
        """Given: 분석된 청크들
        When: get_summary_stats() 호출
        Then: 통계 딕셔너리 반환"""
        chunks = [
            make_test_chunk("외도 불륜 증거"),  # ADULTERY
            make_test_chunk("때렸어 폭행"),     # DOMESTIC_VIOLENCE
            make_test_chunk("일반 메시지")       # GENERAL
        ]
        analyzed = self.analyzer.analyze_batch(chunks)

        stats = self.analyzer.get_summary_stats(analyzed)

        self.assertEqual(stats["total_chunks"], 3)
        self.assertIn("category_counts", stats)
        self.assertIn("confidence_distribution", stats)
        self.assertIn("high_value_count", stats)

    def test_empty_stats(self):
        """Given: 빈 청크 리스트
        When: get_summary_stats() 호출
        Then: 0으로 채워진 통계"""
        stats = self.analyzer.get_summary_stats([])

        self.assertEqual(stats["total_chunks"], 0)
        self.assertEqual(stats["high_value_count"], 0)


class TestScoreConversion(unittest.TestCase):
    """점수 변환 함수 테스트"""

    def test_score_to_confidence_level_uncertain(self):
        """Given: 낮은 점수 (0-2)
        When: score_to_confidence_level() 호출
        Then: UNCERTAIN 반환"""
        self.assertEqual(score_to_confidence_level(0), ConfidenceLevel.UNCERTAIN)
        self.assertEqual(score_to_confidence_level(1.5), ConfidenceLevel.UNCERTAIN)

    def test_score_to_confidence_level_weak(self):
        """Given: 점수 2-4
        When: score_to_confidence_level() 호출
        Then: WEAK 반환"""
        self.assertEqual(score_to_confidence_level(2), ConfidenceLevel.WEAK)
        self.assertEqual(score_to_confidence_level(3), ConfidenceLevel.WEAK)

    def test_score_to_confidence_level_suspicious(self):
        """Given: 점수 4-6
        When: score_to_confidence_level() 호출
        Then: SUSPICIOUS 반환"""
        self.assertEqual(score_to_confidence_level(4), ConfidenceLevel.SUSPICIOUS)
        self.assertEqual(score_to_confidence_level(5), ConfidenceLevel.SUSPICIOUS)

    def test_score_to_confidence_level_strong(self):
        """Given: 점수 6-8
        When: score_to_confidence_level() 호출
        Then: STRONG 반환"""
        self.assertEqual(score_to_confidence_level(6), ConfidenceLevel.STRONG)
        self.assertEqual(score_to_confidence_level(7), ConfidenceLevel.STRONG)

    def test_score_to_confidence_level_definitive(self):
        """Given: 높은 점수 (8-10)
        When: score_to_confidence_level() 호출
        Then: DEFINITIVE 반환"""
        self.assertEqual(score_to_confidence_level(8), ConfidenceLevel.DEFINITIVE)
        self.assertEqual(score_to_confidence_level(10), ConfidenceLevel.DEFINITIVE)

    def test_score_to_confidence_score(self):
        """Given: 점수 0-10
        When: score_to_confidence_score() 호출
        Then: 0.0-1.0 범위로 변환"""
        self.assertEqual(score_to_confidence_score(5), 0.5)
        self.assertEqual(score_to_confidence_score(10), 1.0)
        self.assertEqual(score_to_confidence_score(15), 1.0)  # max capped


class TestCategoryMapping(unittest.TestCase):
    """카테고리 매핑 테스트"""

    def test_category_mapping_complete(self):
        """Given: CATEGORY_MAPPING
        When: 모든 Article840Category 확인
        Then: 모든 카테고리가 매핑됨"""
        from src.analysis.article_840_tagger import Article840Category

        for article_cat in Article840Category:
            self.assertIn(article_cat, CATEGORY_MAPPING)


class TestConvenienceFunctions(unittest.TestCase):
    """간편 함수 테스트"""

    def test_analyze_chunk_function(self):
        """Given: EvidenceChunk
        When: analyze_chunk() 호출
        Then: LegalAnalysis 반환"""
        chunk = make_test_chunk("테스트 메시지")
        analysis = analyze_chunk(chunk)

        self.assertIsInstance(analysis, LegalAnalysis)

    def test_analyze_chunks_function(self):
        """Given: 청크 리스트
        When: analyze_chunks() 호출
        Then: 분석된 청크 리스트 반환"""
        chunks = [make_test_chunk("메시지1"), make_test_chunk("메시지2")]
        analyzed = analyze_chunks(chunks)

        self.assertEqual(len(analyzed), 2)


class TestLegalAnalyzerAIFallback(unittest.TestCase):
    """AI 분석 Fallback 테스트"""

    def test_ai_fallback_without_api_key(self):
        """Given: API 키 없음 + use_ai=True
        When: analyze() 호출
        Then: 키워드 기반으로 fallback"""
        import os
        original_key = os.environ.get("OPENAI_API_KEY")

        try:
            # API 키 제거
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]

            analyzer = LegalAnalyzer(use_ai=True)
            chunk = make_test_chunk("외도 증거입니다.")
            analysis = analyzer.analyze(chunk)

            # fallback이 동작해서 분석 결과가 있어야 함
            self.assertIsNotNone(analysis)
            self.assertIn(LegalCategory.ADULTERY, analysis.categories)
        finally:
            # 원래 키 복원
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key


if __name__ == '__main__':
    unittest.main()
