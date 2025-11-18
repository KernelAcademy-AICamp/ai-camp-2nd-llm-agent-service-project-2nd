"""
Article 840 Tagger 테스트 (TDD RED Phase)

Given: 메시지 내용
When: Article840Tagger.tag() 호출
Then: 민법 840조 이혼 사유 카테고리 자동 태깅
"""

import unittest
from datetime import datetime

from src.analysis.article_840_tagger import Article840Tagger, TaggingResult, Article840Category
from src.parsers.base import Message


class TestArticle840TaggerInitialization(unittest.TestCase):
    """Article840Tagger 초기화 테스트"""

    def test_tagger_creation(self):
        """Given: Article840Tagger 생성 요청
        When: Article840Tagger() 호출
        Then: 인스턴스 생성 성공"""
        tagger = Article840Tagger()
        self.assertIsNotNone(tagger)

    def test_tagger_has_keywords(self):
        """Given: 초기화된 Article840Tagger
        When: 내부 키워드 사전 확인
        Then: 7가지 카테고리 키워드 존재"""
        tagger = Article840Tagger()
        self.assertIsNotNone(tagger.keywords)
        self.assertGreaterEqual(len(tagger.keywords), 7)


class TestArticle840Categorization(unittest.TestCase):
    """민법 840조 카테고리 분류 테스트"""

    def setUp(self):
        """각 테스트 전 tagger 초기화"""
        self.tagger = Article840Tagger()

    def test_tag_adultery(self):
        """Given: 부정행위 관련 메시지
        When: tag() 호출
        Then: ADULTERY 카테고리로 분류"""
        message = Message(
            content="외도 증거입니다. 불륜 관계를 확인했습니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertIn(Article840Category.ADULTERY, result.categories)
        self.assertGreater(result.confidence, 0.7)

    def test_tag_desertion(self):
        """Given: 악의의 유기 관련 메시지
        When: tag() 호출
        Then: DESERTION 카테고리로 분류"""
        message = Message(
            content="배우자가 집을 나간 지 2년이 지났습니다. 연락도 두절되고 생활비도 주지 않습니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertIn(Article840Category.DESERTION, result.categories)
        self.assertGreater(len(result.matched_keywords), 0)

    def test_tag_mistreatment_by_inlaws(self):
        """Given: 배우자 직계존속의 부당대우 관련 메시지
        When: tag() 호출
        Then: MISTREATMENT_BY_INLAWS 카테고리로 분류"""
        message = Message(
            content="시어머니의 폭언과 구타가 계속되고 있습니다. 시댁 식구들이 저를 괴롭힙니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertIn(Article840Category.MISTREATMENT_BY_INLAWS, result.categories)

    def test_tag_harm_to_own_parents(self):
        """Given: 자기 직계존속 피해 관련 메시지
        When: tag() 호출
        Then: HARM_TO_OWN_PARENTS 카테고리로 분류"""
        message = Message(
            content="배우자가 제 부모님을 폭행했습니다. 친정 부모님이 상해를 입었습니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertIn(Article840Category.HARM_TO_OWN_PARENTS, result.categories)

    def test_tag_unknown_whereabouts(self):
        """Given: 생사불명 3년 관련 메시지
        When: tag() 호출
        Then: UNKNOWN_WHEREABOUTS 카테고리로 분류"""
        message = Message(
            content="배우자가 3년 전부터 행방불명 상태입니다. 생사를 알 수 없습니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertIn(Article840Category.UNKNOWN_WHEREABOUTS, result.categories)

    def test_tag_irreconcilable_differences(self):
        """Given: 혼인 지속 곤란사유 관련 메시지
        When: tag() 호출
        Then: IRRECONCILABLE_DIFFERENCES 카테고리로 분류"""
        message = Message(
            content="남편의 지속적인 폭언과 무시로 혼인 생활을 계속할 수 없습니다. 이혼하고 싶습니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertIn(Article840Category.IRRECONCILABLE_DIFFERENCES, result.categories)

    def test_tag_general_evidence(self):
        """Given: 특정 카테고리에 해당하지 않는 일반 증거
        When: tag() 호출
        Then: GENERAL 카테고리로 분류"""
        message = Message(
            content="이혼 소송 관련 서류입니다. 조정 일정을 확인해주세요.",
            sender="Lawyer",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertIn(Article840Category.GENERAL, result.categories)


class TestMultipleCategoryTagging(unittest.TestCase):
    """다중 카테고리 태깅 테스트"""

    def setUp(self):
        """각 테스트 전 tagger 초기화"""
        self.tagger = Article840Tagger()

    def test_tag_multiple_categories(self):
        """Given: 여러 카테고리에 해당하는 메시지
        When: tag() 호출
        Then: 모든 관련 카테고리로 분류"""
        message = Message(
            content="남편의 외도와 폭언 때문에 더 이상 혼인 생활을 계속할 수 없습니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        # ADULTERY와 IRRECONCILABLE_DIFFERENCES 둘 다 포함되어야 함
        self.assertGreater(len(result.categories), 1)
        self.assertIn(Article840Category.ADULTERY, result.categories)


class TestConfidenceScoring(unittest.TestCase):
    """신뢰도 점수 계산 테스트"""

    def setUp(self):
        """각 테스트 전 tagger 초기화"""
        self.tagger = Article840Tagger()

    def test_high_confidence_multiple_keywords(self):
        """Given: 많은 키워드가 매칭되는 메시지
        When: tag() 호출
        Then: 높은 신뢰도 점수 (>= 0.8)"""
        message = Message(
            content="외도 증거입니다. 불륜 관계를 확인했고 바람 피우는 사진도 있습니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertGreaterEqual(result.confidence, 0.8)

    def test_medium_confidence_single_keyword(self):
        """Given: 1-2개 키워드만 매칭되는 메시지
        When: tag() 호출
        Then: 중간 신뢰도 점수 (0.5-0.8)"""
        message = Message(
            content="외도 의심이 됩니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertGreaterEqual(result.confidence, 0.5)
        self.assertLess(result.confidence, 0.9)

    def test_low_confidence_no_match(self):
        """Given: 키워드 매칭이 없는 메시지
        When: tag() 호출
        Then: 낮은 신뢰도 점수 (<= 0.3)"""
        message = Message(
            content="안녕하세요. 일반 대화 내용입니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertLessEqual(result.confidence, 0.3)


class TestEdgeCases(unittest.TestCase):
    """엣지 케이스 테스트"""

    def setUp(self):
        """각 테스트 전 tagger 초기화"""
        self.tagger = Article840Tagger()

    def test_empty_message(self):
        """Given: 빈 메시지
        When: tag() 호출
        Then: GENERAL 카테고리, 신뢰도 0.0"""
        message = Message(
            content="",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(result.categories, [Article840Category.GENERAL])

    def test_whitespace_only_message(self):
        """Given: 공백만 있는 메시지
        When: tag() 호출
        Then: GENERAL 카테고리, 신뢰도 0.0"""
        message = Message(
            content="   \n\t  ",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertEqual(result.confidence, 0.0)

    def test_case_insensitive_matching(self):
        """Given: 대소문자 혼합 키워드
        When: tag() 호출
        Then: 대소문자 무관하게 매칭"""
        message = Message(
            content="외도 증거입니다. 不倫 관계를 확인했습니다.",
            sender="Client",
            timestamp=datetime.now()
        )
        result = self.tagger.tag(message)
        self.assertIn(Article840Category.ADULTERY, result.categories)


class TestBatchTagging(unittest.TestCase):
    """일괄 태깅 테스트"""

    def setUp(self):
        """각 테스트 전 tagger 초기화"""
        self.tagger = Article840Tagger()

    def test_tag_batch(self):
        """Given: 여러 메시지 리스트
        When: tag_batch() 호출
        Then: 모든 메시지에 대한 TaggingResult 리스트 반환"""
        messages = [
            Message(content="외도 증거입니다.", sender="Client", timestamp=datetime.now()),
            Message(content="집을 나간 지 2년입니다.", sender="Client", timestamp=datetime.now()),
            Message(content="폭언이 계속됩니다.", sender="Client", timestamp=datetime.now())
        ]
        results = self.tagger.tag_batch(messages)
        self.assertEqual(len(results), 3)
        self.assertIsInstance(results[0], TaggingResult)

    def test_tag_empty_batch(self):
        """Given: 빈 메시지 리스트
        When: tag_batch() 호출
        Then: 빈 결과 리스트 반환"""
        results = self.tagger.tag_batch([])
        self.assertEqual(len(results), 0)


if __name__ == '__main__':
    unittest.main()
