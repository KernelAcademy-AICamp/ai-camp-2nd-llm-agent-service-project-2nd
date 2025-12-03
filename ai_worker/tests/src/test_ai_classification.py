"""
AI Classification 스키마 테스트

Given: AI 분류 결과
When: 스키마 변환
Then: 기존 스키마와 호환
"""

import unittest

from src.schemas import (
    DivorceGround,
    EvidenceClassification,
    LegalCategory,
    ConfidenceLevel,
    LegalAnalysis,
    to_legal_category,
    to_divorce_ground,
    confidence_to_level,
    classification_to_legal_analysis,
    get_system_prompt_categories,
)
from src.schemas.ai_classification import (
    DIVORCE_GROUND_TO_LEGAL_CATEGORY,
    DIVORCE_GROUND_DESCRIPTIONS,
)


class TestDivorceGround(unittest.TestCase):
    """DivorceGround Enum 테스트"""

    def test_all_grounds_have_korean_values(self):
        """Given: DivorceGround Enum
        When: 모든 값 확인
        Then: 한국어 값"""
        for ground in DivorceGround:
            self.assertIsInstance(ground.value, str)
            # 한글 또는 한글+영어 조합
            self.assertTrue(len(ground.value) > 0)

    def test_adultery_value(self):
        """Given: UNCHASTITY
        When: 값 확인
        Then: '부정행위'"""
        self.assertEqual(DivorceGround.UNCHASTITY.value, "부정행위")

    def test_domestic_violence_value(self):
        """Given: DOMESTIC_VIOLENCE
        When: 값 확인
        Then: '가정폭력'"""
        self.assertEqual(DivorceGround.DOMESTIC_VIOLENCE.value, "가정폭력")


class TestEvidenceClassification(unittest.TestCase):
    """EvidenceClassification 모델 테스트"""

    def test_create_basic(self):
        """Given: 기본 필드
        When: EvidenceClassification 생성
        Then: 성공"""
        classification = EvidenceClassification(
            primary_ground=DivorceGround.UNCHASTITY,
            confidence=0.85,
            reasoning="외도 키워드 발견"
        )
        self.assertEqual(classification.primary_ground, DivorceGround.UNCHASTITY)
        self.assertEqual(classification.confidence, 0.85)

    def test_create_with_all_fields(self):
        """Given: 모든 필드
        When: EvidenceClassification 생성
        Then: 성공"""
        classification = EvidenceClassification(
            primary_ground=DivorceGround.DOMESTIC_VIOLENCE,
            secondary_grounds=[DivorceGround.MALTREATMENT_BY_SPOUSE],
            confidence=0.92,
            key_phrases=["때렸어", "멍이 들었어"],
            reasoning="폭력 증거",
            mentioned_entities=["남편", "병원"],
            requires_review=True,
            review_reason="심각한 폭력 사례"
        )
        self.assertEqual(len(classification.secondary_grounds), 1)
        self.assertEqual(len(classification.key_phrases), 2)
        self.assertTrue(classification.requires_review)

    def test_confidence_validation(self):
        """Given: 범위 외 신뢰도
        When: EvidenceClassification 생성
        Then: ValidationError"""
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            EvidenceClassification(
                primary_ground=DivorceGround.UNCHASTITY,
                confidence=1.5,  # 범위 초과
                reasoning="test"
            )

    def test_model_validate_from_dict(self):
        """Given: 딕셔너리 (AI 응답)
        When: model_validate() 호출
        Then: EvidenceClassification 생성"""
        ai_response = {
            "primary_ground": "부정행위",
            "confidence": 0.8,
            "key_phrases": ["호텔", "만났어"],
            "reasoning": "외도 의심"
        }
        classification = EvidenceClassification.model_validate(ai_response)
        self.assertEqual(classification.primary_ground, DivorceGround.UNCHASTITY)


class TestCategoryMapping(unittest.TestCase):
    """카테고리 매핑 테스트"""

    def test_all_divorce_grounds_mapped(self):
        """Given: 모든 DivorceGround
        When: 매핑 확인
        Then: 모두 LegalCategory로 매핑됨"""
        for ground in DivorceGround:
            self.assertIn(ground, DIVORCE_GROUND_TO_LEGAL_CATEGORY)

    def test_to_legal_category_adultery(self):
        """Given: UNCHASTITY
        When: to_legal_category() 호출
        Then: ADULTERY"""
        result = to_legal_category(DivorceGround.UNCHASTITY)
        self.assertEqual(result, LegalCategory.ADULTERY)

    def test_to_legal_category_violence(self):
        """Given: DOMESTIC_VIOLENCE
        When: to_legal_category() 호출
        Then: DOMESTIC_VIOLENCE"""
        result = to_legal_category(DivorceGround.DOMESTIC_VIOLENCE)
        self.assertEqual(result, LegalCategory.DOMESTIC_VIOLENCE)

    def test_to_divorce_ground_adultery(self):
        """Given: ADULTERY
        When: to_divorce_ground() 호출
        Then: UNCHASTITY"""
        result = to_divorce_ground(LegalCategory.ADULTERY)
        self.assertEqual(result, DivorceGround.UNCHASTITY)

    def test_bidirectional_mapping(self):
        """Given: 매핑 테이블
        When: 양방향 변환
        Then: 원래 값 복원"""
        for ground in DivorceGround:
            legal_cat = to_legal_category(ground)
            back_to_ground = to_divorce_ground(legal_cat)
            self.assertEqual(ground, back_to_ground)


class TestConfidenceConversion(unittest.TestCase):
    """신뢰도 변환 테스트"""

    def test_very_low_confidence(self):
        """Given: 0.1 신뢰도
        When: confidence_to_level() 호출
        Then: UNCERTAIN"""
        result = confidence_to_level(0.1)
        self.assertEqual(result, ConfidenceLevel.UNCERTAIN)

    def test_low_confidence(self):
        """Given: 0.3 신뢰도
        When: confidence_to_level() 호출
        Then: WEAK"""
        result = confidence_to_level(0.3)
        self.assertEqual(result, ConfidenceLevel.WEAK)

    def test_medium_confidence(self):
        """Given: 0.5 신뢰도
        When: confidence_to_level() 호출
        Then: SUSPICIOUS"""
        result = confidence_to_level(0.5)
        self.assertEqual(result, ConfidenceLevel.SUSPICIOUS)

    def test_high_confidence(self):
        """Given: 0.7 신뢰도
        When: confidence_to_level() 호출
        Then: STRONG"""
        result = confidence_to_level(0.7)
        self.assertEqual(result, ConfidenceLevel.STRONG)

    def test_very_high_confidence(self):
        """Given: 0.9 신뢰도
        When: confidence_to_level() 호출
        Then: DEFINITIVE"""
        result = confidence_to_level(0.9)
        self.assertEqual(result, ConfidenceLevel.DEFINITIVE)


class TestClassificationToLegalAnalysis(unittest.TestCase):
    """EvidenceClassification → LegalAnalysis 변환 테스트"""

    def test_basic_conversion(self):
        """Given: EvidenceClassification
        When: classification_to_legal_analysis() 호출
        Then: LegalAnalysis 반환"""
        classification = EvidenceClassification(
            primary_ground=DivorceGround.UNCHASTITY,
            confidence=0.85,
            reasoning="외도 증거"
        )
        analysis = classification_to_legal_analysis(classification)

        self.assertIsInstance(analysis, LegalAnalysis)
        self.assertIn(LegalCategory.ADULTERY, analysis.categories)
        self.assertEqual(analysis.confidence_score, 0.85)

    def test_conversion_with_secondary_grounds(self):
        """Given: 복수 카테고리
        When: classification_to_legal_analysis() 호출
        Then: 모든 카테고리 포함"""
        classification = EvidenceClassification(
            primary_ground=DivorceGround.DOMESTIC_VIOLENCE,
            secondary_grounds=[DivorceGround.MALTREATMENT_BY_SPOUSE],
            confidence=0.9,
            reasoning="폭력 및 학대"
        )
        analysis = classification_to_legal_analysis(classification)

        self.assertEqual(len(analysis.categories), 2)
        self.assertIn(LegalCategory.DOMESTIC_VIOLENCE, analysis.categories)
        self.assertIn(LegalCategory.MISTREATMENT_BY_SPOUSE, analysis.categories)

    def test_conversion_preserves_key_phrases(self):
        """Given: key_phrases가 있는 분류
        When: classification_to_legal_analysis() 호출
        Then: matched_keywords에 보존"""
        classification = EvidenceClassification(
            primary_ground=DivorceGround.UNCHASTITY,
            confidence=0.8,
            key_phrases=["호텔", "만났어"],
            reasoning="외도 의심"
        )
        analysis = classification_to_legal_analysis(classification)

        self.assertEqual(analysis.matched_keywords, ["호텔", "만났어"])

    def test_conversion_preserves_review_flag(self):
        """Given: 검토 필요 플래그
        When: classification_to_legal_analysis() 호출
        Then: 플래그 보존"""
        classification = EvidenceClassification(
            primary_ground=DivorceGround.DOMESTIC_VIOLENCE,
            confidence=0.5,
            reasoning="폭력 의심",
            requires_review=True,
            review_reason="신뢰도 낮음"
        )
        analysis = classification_to_legal_analysis(classification)

        self.assertTrue(analysis.requires_human_review)
        self.assertEqual(analysis.review_reason, "신뢰도 낮음")


class TestSystemPromptGeneration(unittest.TestCase):
    """시스템 프롬프트 생성 테스트"""

    def test_get_system_prompt_categories(self):
        """Given: get_system_prompt_categories() 호출
        When: 결과 확인
        Then: 모든 카테고리 설명 포함"""
        prompt = get_system_prompt_categories()

        self.assertIn("민법 제840조", prompt)
        self.assertIn("부정행위", prompt)
        self.assertIn("가정폭력", prompt)

    def test_all_grounds_have_descriptions(self):
        """Given: DIVORCE_GROUND_DESCRIPTIONS
        When: 확인
        Then: 모든 DivorceGround에 설명 있음"""
        for ground in DivorceGround:
            self.assertIn(ground, DIVORCE_GROUND_DESCRIPTIONS)
            self.assertTrue(len(DIVORCE_GROUND_DESCRIPTIONS[ground]) > 0)


class TestIntegration(unittest.TestCase):
    """통합 테스트"""

    def test_full_ai_response_flow(self):
        """Given: AI 응답 (딕셔너리)
        When: 파싱 및 변환
        Then: LegalAnalysis 생성"""
        # AI가 반환할 것으로 예상되는 응답
        ai_response = {
            "primary_ground": "부정행위",
            "secondary_grounds": [],
            "confidence": 0.87,
            "key_phrases": ["호텔에서 만났어", "다른 여자"],
            "reasoning": "외도를 암시하는 직접적 표현 발견",
            "mentioned_entities": ["김영희", "역삼동 호텔"],
            "requires_review": False,
            "review_reason": None
        }

        # 1. 파싱
        classification = EvidenceClassification.model_validate(ai_response)

        # 2. 변환
        analysis = classification_to_legal_analysis(classification)

        # 3. 검증
        self.assertEqual(analysis.primary_category, LegalCategory.ADULTERY)
        self.assertEqual(analysis.confidence_level, ConfidenceLevel.DEFINITIVE)  # 0.87 >= 0.8
        self.assertEqual(analysis.confidence_score, 0.87)
        self.assertIn("호텔에서 만났어", analysis.matched_keywords)


if __name__ == "__main__":
    unittest.main()
