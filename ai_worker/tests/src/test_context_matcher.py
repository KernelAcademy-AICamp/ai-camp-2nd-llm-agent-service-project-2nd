"""
Context-Aware Keyword Matcher 테스트

Given: 텍스트와 키워드
When: ContextAwareKeywordMatcher.analyze() 호출
Then: 부정문 감지 및 조정된 신뢰도 반환
"""

import unittest
from src.analysis.context_matcher import (
    ContextAwareKeywordMatcher,
    NegationType,
    MatchResult,
    check_negation,
    get_effective_keywords,
    NEGATION_PATTERNS,
    NEGATION_MORPHEMES,
)


class TestContextMatcherInitialization(unittest.TestCase):
    """ContextAwareKeywordMatcher 초기화 테스트"""

    def test_matcher_creation(self):
        """Given: ContextAwareKeywordMatcher 생성 요청
        When: ContextAwareKeywordMatcher() 호출
        Then: 인스턴스 생성 성공"""
        matcher = ContextAwareKeywordMatcher(use_kiwi=False)
        self.assertIsNotNone(matcher)

    def test_matcher_without_kiwi(self):
        """Given: Kiwi 비활성화 옵션
        When: ContextAwareKeywordMatcher(use_kiwi=False) 호출
        Then: 정규식 기반 매칭만 사용"""
        matcher = ContextAwareKeywordMatcher(use_kiwi=False)
        self.assertFalse(matcher.use_kiwi)
        self.assertIsNone(matcher._kiwi)


class TestKeywordMatching(unittest.TestCase):
    """키워드 매칭 기본 테스트"""

    def setUp(self):
        self.matcher = ContextAwareKeywordMatcher(use_kiwi=False)

    def test_simple_keyword_match(self):
        """Given: 키워드가 포함된 텍스트
        When: analyze() 호출
        Then: 키워드 매칭 성공"""
        result = self.matcher.analyze("외도했어", ["외도"])
        self.assertEqual(len(result.matches), 1)
        self.assertTrue(result.matches[0].found)
        self.assertEqual(result.matches[0].keyword, "외도")

    def test_no_keyword_match(self):
        """Given: 키워드가 없는 텍스트
        When: analyze() 호출
        Then: 매칭 없음"""
        result = self.matcher.analyze("오늘 날씨 좋다", ["외도"])
        self.assertEqual(len(result.matches), 0)

    def test_multiple_keyword_match(self):
        """Given: 여러 키워드가 포함된 텍스트
        When: analyze() 호출
        Then: 모든 키워드 매칭"""
        result = self.matcher.analyze("외도하고 폭력까지", ["외도", "폭력"])
        self.assertEqual(len(result.matches), 2)

    def test_empty_text(self):
        """Given: 빈 텍스트
        When: analyze() 호출
        Then: 빈 결과 반환"""
        result = self.matcher.analyze("", ["외도"])
        self.assertEqual(len(result.matches), 0)

    def test_empty_keywords(self):
        """Given: 빈 키워드 목록
        When: analyze() 호출
        Then: 빈 결과 반환"""
        result = self.matcher.analyze("외도했어", [])
        self.assertEqual(len(result.matches), 0)


class TestNegationDetection(unittest.TestCase):
    """부정문 감지 테스트"""

    def setUp(self):
        self.matcher = ContextAwareKeywordMatcher(use_kiwi=False)

    def test_suffix_negation_not(self):
        """Given: ~하지 않았다 형태의 부정문
        When: analyze() 호출
        Then: is_negated=True"""
        result = self.matcher.analyze("외도하지 않았어", ["외도"])
        self.assertTrue(result.has_negation)
        self.assertTrue(result.matches[0].is_negated)

    def test_suffix_negation_cannot(self):
        """Given: ~하지 못했다 형태의 부정문
        When: analyze() 호출
        Then: is_negated=True"""
        result = self.matcher.analyze("외도하지 못했어", ["외도"])
        self.assertTrue(result.has_negation)
        self.assertTrue(result.matches[0].is_negated)

    def test_predicate_negation_not_is(self):
        """Given: ~가 아니다 형태의 부정문
        When: analyze() 호출
        Then: is_negated=True"""
        result = self.matcher.analyze("외도가 아니야", ["외도"])
        self.assertTrue(result.has_negation)

    def test_predicate_negation_never(self):
        """Given: ~한 적 없다 형태의 부정문
        When: analyze() 호출
        Then: is_negated=True"""
        result = self.matcher.analyze("외도한 적 없어", ["외도"])
        self.assertTrue(result.has_negation)

    def test_no_negation(self):
        """Given: 긍정문
        When: analyze() 호출
        Then: is_negated=False"""
        result = self.matcher.analyze("외도했어", ["외도"])
        self.assertFalse(result.has_negation)
        self.assertFalse(result.matches[0].is_negated)

    def test_positive_statement_with_keyword(self):
        """Given: 긍정적 진술
        When: analyze() 호출
        Then: 부정으로 감지되지 않음"""
        result = self.matcher.analyze("불륜이야", ["불륜"])
        self.assertFalse(result.has_negation)


class TestQuestionDetection(unittest.TestCase):
    """의문형 감지 테스트"""

    def setUp(self):
        self.matcher = ContextAwareKeywordMatcher(use_kiwi=False)

    def test_question_mark_detection(self):
        """Given: 물음표가 포함된 문장
        When: analyze() 호출
        Then: is_question=True"""
        result = self.matcher.analyze("외도한 거 아니야?", ["외도"])
        self.assertTrue(result.matches[0].is_question)

    def test_no_question_mark(self):
        """Given: 물음표 없는 문장
        When: analyze() 호출
        Then: is_question=False"""
        result = self.matcher.analyze("외도했어", ["외도"])
        self.assertFalse(result.matches[0].is_question)


class TestScoreAdjustment(unittest.TestCase):
    """점수 조정 테스트"""

    def setUp(self):
        self.matcher = ContextAwareKeywordMatcher(use_kiwi=False)

    def test_positive_score(self):
        """Given: 긍정문
        When: analyze() 호출
        Then: adjusted_score = 1.0"""
        result = self.matcher.analyze("외도했어", ["외도"])
        self.assertEqual(result.matches[0].adjusted_score, 1.0)

    def test_negated_score(self):
        """Given: 부정문
        When: analyze() 호출
        Then: adjusted_score = -0.8"""
        result = self.matcher.analyze("외도하지 않았어", ["외도"])
        self.assertEqual(result.matches[0].adjusted_score, -0.8)

    def test_question_score(self):
        """Given: 의문형 (부정 없음)
        When: analyze() 호출
        Then: adjusted_score = 0.5"""
        result = self.matcher.analyze("외도했어?", ["외도"])
        self.assertEqual(result.matches[0].adjusted_score, 0.5)

    def test_overall_score_calculation(self):
        """Given: 여러 키워드 매칭
        When: analyze() 호출
        Then: overall_score는 평균값"""
        result = self.matcher.analyze("외도하고 폭력까지", ["외도", "폭력"])
        # 둘 다 긍정이므로 평균 = 1.0
        self.assertEqual(result.overall_score, 1.0)


class TestEffectiveKeywords(unittest.TestCase):
    """유효 키워드 추출 테스트"""

    def setUp(self):
        self.matcher = ContextAwareKeywordMatcher(use_kiwi=False)

    def test_get_effective_keywords_all_positive(self):
        """Given: 모든 키워드가 긍정
        When: get_effective_keywords() 호출
        Then: 모든 키워드 반환"""
        keywords = self.matcher.get_effective_keywords(
            "외도하고 폭력도 있어",
            ["외도", "폭력"]
        )
        self.assertEqual(len(keywords), 2)

    def test_get_effective_keywords_some_negated(self):
        """Given: 일부 키워드가 부정
        When: get_effective_keywords() 호출
        Then: 부정되지 않은 키워드만 반환"""
        keywords = self.matcher.get_effective_keywords(
            "외도는 없었지만 폭력은 있었어",
            ["외도", "폭력"]
        )
        # "외도"는 "없"이 있어서 부정됨
        self.assertIn("폭력", keywords)


class TestConfidenceAdjustment(unittest.TestCase):
    """신뢰도 조정 테스트"""

    def setUp(self):
        self.matcher = ContextAwareKeywordMatcher(use_kiwi=False)

    def test_no_adjustment_for_positive(self):
        """Given: 긍정문
        When: calculate_confidence_adjustment() 호출
        Then: 기본 신뢰도 유지"""
        adjusted = self.matcher.calculate_confidence_adjustment(
            "외도했어",
            ["외도"],
            base_confidence=0.8
        )
        self.assertEqual(adjusted, 0.8)

    def test_major_reduction_for_all_negated(self):
        """Given: 모든 키워드 부정
        When: calculate_confidence_adjustment() 호출
        Then: 신뢰도 대폭 감소 (0.2배)"""
        adjusted = self.matcher.calculate_confidence_adjustment(
            "외도하지 않았어",
            ["외도"],
            base_confidence=1.0
        )
        self.assertAlmostEqual(adjusted, 0.2)


class TestConvenienceFunctions(unittest.TestCase):
    """편의 함수 테스트"""

    def test_check_negation_true(self):
        """Given: 부정문
        When: check_negation() 호출
        Then: True"""
        self.assertTrue(check_negation("외도하지 않았어", "외도"))

    def test_check_negation_false(self):
        """Given: 긍정문
        When: check_negation() 호출
        Then: False"""
        self.assertFalse(check_negation("외도했어", "외도"))

    def test_get_effective_keywords_function(self):
        """Given: 텍스트와 키워드
        When: get_effective_keywords() 호출
        Then: 유효 키워드 반환"""
        keywords = get_effective_keywords("외도했어", ["외도", "폭력"])
        self.assertIn("외도", keywords)
        self.assertNotIn("폭력", keywords)


class TestNegationPatterns(unittest.TestCase):
    """부정 패턴 상수 테스트"""

    def test_negation_patterns_exist(self):
        """Given: NEGATION_PATTERNS 상수
        When: 확인
        Then: 4가지 패턴 유형 존재"""
        self.assertIn("prefix", NEGATION_PATTERNS)
        self.assertIn("suffix", NEGATION_PATTERNS)
        self.assertIn("predicate", NEGATION_PATTERNS)
        self.assertIn("question", NEGATION_PATTERNS)

    def test_negation_morphemes_exist(self):
        """Given: NEGATION_MORPHEMES 상수
        When: 확인
        Then: 부정 형태소 목록 존재"""
        self.assertIn("않", NEGATION_MORPHEMES)
        self.assertIn("못", NEGATION_MORPHEMES)
        self.assertIn("없", NEGATION_MORPHEMES)


class TestNegationType(unittest.TestCase):
    """NegationType Enum 테스트"""

    def test_negation_types(self):
        """Given: NegationType Enum
        When: 값 확인
        Then: 5가지 유형 존재"""
        self.assertEqual(NegationType.NONE.value, "none")
        self.assertEqual(NegationType.PREFIX.value, "prefix")
        self.assertEqual(NegationType.SUFFIX.value, "suffix")
        self.assertEqual(NegationType.PREDICATE.value, "predicate")
        self.assertEqual(NegationType.QUESTION.value, "question")


class TestMatchResult(unittest.TestCase):
    """MatchResult 데이터 클래스 테스트"""

    def test_match_result_defaults(self):
        """Given: MatchResult 생성
        When: 기본값 확인
        Then: 기본값 올바름"""
        result = MatchResult(keyword="test", found=True)
        self.assertIsNone(result.position)
        self.assertEqual(result.negation_type, NegationType.NONE)
        self.assertFalse(result.is_negated)
        self.assertEqual(result.base_score, 1.0)


class TestRealWorldCases(unittest.TestCase):
    """실제 사용 케이스 테스트"""

    def setUp(self):
        self.matcher = ContextAwareKeywordMatcher(use_kiwi=False)

    def test_divorce_evidence_positive(self):
        """실제 케이스: 외도 증거 (긍정)"""
        result = self.matcher.analyze(
            "어제 호텔에서 만났어. 불륜 맞아.",
            ["호텔", "불륜"]
        )
        self.assertEqual(len(result.matches), 2)
        self.assertFalse(result.has_negation)

    def test_divorce_evidence_denial(self):
        """실제 케이스: 외도 부인"""
        result = self.matcher.analyze(
            "외도한 적 없어. 그냥 친구야.",
            ["외도"]
        )
        self.assertTrue(result.has_negation)
        self.assertLess(result.overall_score, 0)

    def test_violence_accusation(self):
        """실제 케이스: 폭력 호소"""
        result = self.matcher.analyze(
            "남편이 또 때렸어",
            ["때렸", "폭력"]
        )
        match = next((m for m in result.matches if m.found), None)
        self.assertIsNotNone(match)
        self.assertFalse(match.is_negated)

    def test_violence_denial(self):
        """실제 케이스: 폭력 부인"""
        result = self.matcher.analyze(
            "때린 적 없어",
            ["때린"]
        )
        self.assertTrue(result.has_negation)


if __name__ == "__main__":
    unittest.main()
