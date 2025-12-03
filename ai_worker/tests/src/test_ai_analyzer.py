"""
AI Analyzer 테스트

Given: EvidenceChunk
When: AI 분석 수행
Then: LegalAnalysis 반환 (API 모킹)
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from src.analysis.ai_analyzer import (
    AIAnalyzer,
    AIAnalyzerConfig,
    analyze_with_ai,
    SYSTEM_PROMPT,
)
from src.schemas import (
    EvidenceChunk,
    SourceLocation,
    FileType,
    LegalAnalysis,
    LegalCategory,
)
from src.exceptions import AnalysisError


def make_test_chunk(content: str, sender: str = "테스트") -> EvidenceChunk:
    """테스트용 청크 생성"""
    return EvidenceChunk(
        chunk_id="test_chunk_001",
        file_id="test_file_001",
        case_id="test_case_001",
        content=content,
        content_hash="abc123",
        source_location=SourceLocation(
            file_name="test.txt",
            file_type=FileType.KAKAOTALK,
            line_number=1
        ),
        sender=sender,
        timestamp=datetime.now()
    )


class TestAIAnalyzerConfig(unittest.TestCase):
    """AIAnalyzerConfig 테스트"""

    def test_default_config(self):
        """Given: 기본 설정
        When: AIAnalyzerConfig 생성
        Then: 기본값 설정"""
        config = AIAnalyzerConfig()
        self.assertEqual(config.model, "gpt-4o-mini")
        self.assertEqual(config.temperature, 0.1)
        self.assertEqual(config.max_retries, 3)

    def test_custom_config(self):
        """Given: 커스텀 설정
        When: AIAnalyzerConfig 생성
        Then: 커스텀 값 적용"""
        config = AIAnalyzerConfig(
            model="gpt-4o",
            temperature=0.2,
            use_instructor=True
        )
        self.assertEqual(config.model, "gpt-4o")
        self.assertEqual(config.temperature, 0.2)
        self.assertTrue(config.use_instructor)


class TestAIAnalyzerInitialization(unittest.TestCase):
    """AIAnalyzer 초기화 테스트"""

    def test_analyzer_creation(self):
        """Given: AIAnalyzer 생성
        When: __init__ 호출
        Then: 인스턴스 생성"""
        analyzer = AIAnalyzer()
        self.assertIsNotNone(analyzer)
        self.assertIsNotNone(analyzer._system_prompt)

    def test_analyzer_with_config(self):
        """Given: 커스텀 설정
        When: AIAnalyzer 생성
        Then: 설정 적용"""
        config = AIAnalyzerConfig(model="gpt-4o")
        analyzer = AIAnalyzer(config=config)
        self.assertEqual(analyzer.config.model, "gpt-4o")


class TestSystemPrompt(unittest.TestCase):
    """시스템 프롬프트 테스트"""

    def test_system_prompt_contains_categories(self):
        """Given: SYSTEM_PROMPT
        When: 내용 확인
        Then: 민법 840조 카테고리 포함"""
        self.assertIn("민법", SYSTEM_PROMPT)
        self.assertIn("부정행위", SYSTEM_PROMPT)
        self.assertIn("가정폭력", SYSTEM_PROMPT)

    def test_system_prompt_contains_examples(self):
        """Given: SYSTEM_PROMPT
        When: 내용 확인
        Then: Few-shot 예시 포함"""
        self.assertIn("예시 1", SYSTEM_PROMPT)
        self.assertIn("호텔", SYSTEM_PROMPT)

    def test_system_prompt_length(self):
        """Given: SYSTEM_PROMPT
        When: 길이 확인
        Then: 1024자 이상 (캐싱 최적화)"""
        # 토큰이 아닌 문자 수로 대략적 확인
        self.assertGreater(len(SYSTEM_PROMPT), 1500)


class TestAIAnalyzerWithMock(unittest.TestCase):
    """AI 분석 테스트 (API 모킹)"""

    def setUp(self):
        self.analyzer = AIAnalyzer()
        self.test_chunk = make_test_chunk("호텔에서 그 사람 만났어")

    @patch('src.analysis.ai_analyzer.AIAnalyzer._get_client')
    def test_analyze_adultery(self, mock_get_client):
        """Given: 외도 관련 메시지
        When: analyze() 호출 (모킹)
        Then: ADULTERY 카테고리"""
        # Mock 응답 설정
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "primary_ground": "부정행위",
            "secondary_grounds": [],
            "confidence": 0.85,
            "key_phrases": ["호텔에서", "그 사람 만났어"],
            "reasoning": "외도 의심 표현",
            "mentioned_entities": [],
            "requires_review": False,
            "review_reason": None
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = self.analyzer.analyze(self.test_chunk)

        self.assertIsInstance(result, LegalAnalysis)
        self.assertIn(LegalCategory.ADULTERY, result.categories)

    @patch('src.analysis.ai_analyzer.AIAnalyzer._get_client')
    def test_analyze_domestic_violence(self, mock_get_client):
        """Given: 폭력 관련 메시지
        When: analyze() 호출 (모킹)
        Then: DOMESTIC_VIOLENCE 카테고리"""
        chunk = make_test_chunk("남편이 또 때렸어")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "primary_ground": "가정폭력",
            "confidence": 0.9,
            "key_phrases": ["때렸어"],
            "reasoning": "신체 폭력",
            "mentioned_entities": ["남편"],
            "requires_review": False,
            "review_reason": None
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = self.analyzer.analyze(chunk)

        self.assertIn(LegalCategory.DOMESTIC_VIOLENCE, result.categories)

    @patch('src.analysis.ai_analyzer.AIAnalyzer._get_client')
    def test_analyze_general(self, mock_get_client):
        """Given: 일반 메시지
        When: analyze() 호출 (모킹)
        Then: GENERAL 카테고리"""
        chunk = make_test_chunk("오늘 날씨 좋다")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "primary_ground": "무관",
            "confidence": 0.95,
            "key_phrases": [],
            "reasoning": "일상 대화",
            "mentioned_entities": [],
            "requires_review": False,
            "review_reason": None
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = self.analyzer.analyze(chunk)

        self.assertIn(LegalCategory.GENERAL, result.categories)

    @patch('src.analysis.ai_analyzer.AIAnalyzer._get_client')
    def test_analyze_with_review_flag(self, mock_get_client):
        """Given: 검토 필요한 메시지
        When: analyze() 호출 (모킹)
        Then: requires_human_review=True"""
        chunk = make_test_chunk("이상한 일이 있었어")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "primary_ground": "부정행위",
            "confidence": 0.3,
            "key_phrases": ["이상한 일"],
            "reasoning": "모호한 표현",
            "mentioned_entities": [],
            "requires_review": True,
            "review_reason": "신뢰도 낮음"
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = self.analyzer.analyze(chunk)

        self.assertTrue(result.requires_human_review)
        self.assertEqual(result.review_reason, "신뢰도 낮음")


class TestAIAnalyzerErrors(unittest.TestCase):
    """AI 분석 에러 처리 테스트"""

    def setUp(self):
        self.analyzer = AIAnalyzer()
        self.test_chunk = make_test_chunk("테스트 메시지")

    @patch('src.analysis.ai_analyzer.AIAnalyzer._get_client')
    def test_json_parse_error(self, mock_get_client):
        """Given: 잘못된 JSON 응답
        When: analyze() 호출
        Then: AnalysisError 발생"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "invalid json"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        with self.assertRaises(AnalysisError) as ctx:
            self.analyzer.analyze(self.test_chunk)

        self.assertTrue(ctx.exception.fallback_available)

    @patch('src.analysis.ai_analyzer.AIAnalyzer._get_client')
    def test_api_error(self, mock_get_client):
        """Given: API 호출 실패
        When: analyze() 호출
        Then: AnalysisError 발생"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        with self.assertRaises(AnalysisError) as ctx:
            self.analyzer.analyze(self.test_chunk)

        self.assertTrue(ctx.exception.fallback_available)
        self.assertEqual(ctx.exception.analysis_type, "ai")


class TestAIAnalyzerBatch(unittest.TestCase):
    """배치 분석 테스트"""

    @patch('src.analysis.ai_analyzer.AIAnalyzer._get_client')
    def test_analyze_batch_success(self, mock_get_client):
        """Given: 여러 청크
        When: analyze_batch() 호출
        Then: 모두 분석"""
        chunks = [
            make_test_chunk("메시지1"),
            make_test_chunk("메시지2"),
        ]

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "primary_ground": "무관",
            "confidence": 0.9,
            "key_phrases": [],
            "reasoning": "일반",
            "mentioned_entities": [],
            "requires_review": False,
            "review_reason": None
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        analyzer = AIAnalyzer()
        results = analyzer.analyze_batch(chunks)

        self.assertEqual(len(results), 2)
        for chunk in results:
            self.assertIsNotNone(chunk.legal_analysis)


class TestUserPromptGeneration(unittest.TestCase):
    """사용자 프롬프트 생성 테스트"""

    def test_build_user_prompt_basic(self):
        """Given: 기본 청크
        When: _build_user_prompt() 호출
        Then: 메시지 내용 포함"""
        analyzer = AIAnalyzer()
        chunk = make_test_chunk("테스트 내용")

        prompt = analyzer._build_user_prompt(chunk)

        self.assertIn("테스트 내용", prompt)
        self.assertIn("메시지 내용", prompt)

    def test_build_user_prompt_with_context(self):
        """Given: 컨텍스트가 있는 청크
        When: _build_user_prompt() 호출
        Then: 컨텍스트 정보 포함"""
        analyzer = AIAnalyzer()
        chunk = make_test_chunk("테스트", sender="홍길동")

        prompt = analyzer._build_user_prompt(chunk)

        self.assertIn("홍길동", prompt)
        self.assertIn("발신자", prompt)


class TestConvenienceFunction(unittest.TestCase):
    """간편 함수 테스트"""

    @patch('src.analysis.ai_analyzer.AIAnalyzer._get_client')
    def test_analyze_with_ai(self, mock_get_client):
        """Given: analyze_with_ai() 호출
        When: 청크 전달
        Then: LegalAnalysis 반환"""
        chunk = make_test_chunk("테스트")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "primary_ground": "무관",
            "confidence": 0.9,
            "key_phrases": [],
            "reasoning": "테스트",
            "mentioned_entities": [],
            "requires_review": False,
            "review_reason": None
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = analyze_with_ai(chunk)

        self.assertIsInstance(result, LegalAnalysis)


if __name__ == "__main__":
    unittest.main()
