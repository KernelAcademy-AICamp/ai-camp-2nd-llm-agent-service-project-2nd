"""
Evidence Summarizer 테스트 (TDD RED Phase)

Given: 증거 메시지 리스트 또는 텍스트
When: summarize() 호출
Then: LLM 기반 요약문 생성
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.analysis.summarizer import EvidenceSummarizer, SummaryResult, SummaryType
from src.parsers.base import Message


class TestEvidenceSummarizerInitialization(unittest.TestCase):
    """EvidenceSummarizer 초기화 테스트"""

    def test_summarizer_creation(self):
        """Given: EvidenceSummarizer 생성 요청
        When: EvidenceSummarizer() 호출
        Then: 인스턴스 생성 성공"""
        summarizer = EvidenceSummarizer()
        self.assertIsNotNone(summarizer)

    def test_summarizer_with_custom_model(self):
        """Given: 커스텀 모델 지정
        When: EvidenceSummarizer(model='gpt-4') 호출
        Then: 지정된 모델로 초기화"""
        summarizer = EvidenceSummarizer(model="gpt-4")
        self.assertEqual(summarizer.model, "gpt-4")


class TestSummaryResultDataModel(unittest.TestCase):
    """SummaryResult 데이터 모델 테스트"""

    def test_summary_result_creation(self):
        """Given: SummaryResult 생성
        When: 필수 필드 제공
        Then: 인스턴스 생성 성공"""
        result = SummaryResult(
            summary="이혼 증거 요약입니다.",
            summary_type=SummaryType.CONVERSATION,
            key_points=["외도 증거", "폭언 증거"],
            word_count=100
        )
        self.assertEqual(result.summary, "이혼 증거 요약입니다.")
        self.assertEqual(result.summary_type, SummaryType.CONVERSATION)

    def test_summary_result_default_values(self):
        """Given: SummaryResult 기본값 생성
        When: 선택 필드 없이 생성
        Then: 기본값 적용"""
        result = SummaryResult(
            summary="요약",
            summary_type=SummaryType.GENERAL
        )
        self.assertEqual(result.key_points, [])
        self.assertEqual(result.word_count, 0)


class TestConversationSummarization(unittest.TestCase):
    """대화 요약 테스트"""

    @patch('src.analysis.summarizer.openai')
    def test_summarize_conversation(self, mock_openai):
        """Given: 대화 메시지 리스트
        When: summarize_conversation() 호출
        Then: 대화 요약 반환"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "외도 관련 대화 증거입니다."
        mock_openai.chat.completions.create.return_value = mock_response

        messages = [
            Message(content="외도했어?", sender="Wife", timestamp=datetime.now()),
            Message(content="아니야", sender="Husband", timestamp=datetime.now()),
            Message(content="거짓말하지마", sender="Wife", timestamp=datetime.now())
        ]

        summarizer = EvidenceSummarizer()
        result = summarizer.summarize_conversation(messages)

        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.summary_type, SummaryType.CONVERSATION)
        self.assertIn("외도", result.summary)

    @patch('src.analysis.summarizer.openai')
    def test_summarize_long_conversation(self, mock_openai):
        """Given: 긴 대화 메시지 리스트 (100개 이상)
        When: summarize_conversation() 호출
        Then: 핵심 내용만 추출한 요약 반환"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "장기간에 걸친 폭언과 외도 증거가 포함된 대화입니다."
        mock_openai.chat.completions.create.return_value = mock_response

        # 100개 메시지 생성
        messages = [
            Message(content=f"메시지 {i}", sender="User", timestamp=datetime.now())
            for i in range(100)
        ]

        summarizer = EvidenceSummarizer()
        result = summarizer.summarize_conversation(messages)

        self.assertIsInstance(result, SummaryResult)
        self.assertGreater(len(result.summary), 0)


class TestDocumentSummarization(unittest.TestCase):
    """문서 요약 테스트"""

    @patch('src.analysis.summarizer.openai')
    def test_summarize_document(self, mock_openai):
        """Given: 법률 문서 텍스트
        When: summarize_document() 호출
        Then: 문서 요약 반환"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "민법 840조는 이혼 사유를 규정합니다."
        mock_openai.chat.completions.create.return_value = mock_response

        document = """
        민법 제840조 (재판상 이혼원인)
        부부의 일방은 다음 각호의 사유가 있는 경우에는 가정법원에 이혼을 청구할 수 있다.
        1. 배우자에 부정한 행위가 있었을 때
        2. 배우자가 악의로 다른 일방을 유기한 때
        """

        summarizer = EvidenceSummarizer()
        result = summarizer.summarize_document(document)

        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.summary_type, SummaryType.DOCUMENT)
        self.assertIn("민법", result.summary)

    @patch('src.analysis.summarizer.openai')
    def test_summarize_short_document(self, mock_openai):
        """Given: 짧은 문서 (100자 미만)
        When: summarize_document() 호출
        Then: 원본 그대로 또는 간단한 요약 반환"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "이혼 합의서입니다."
        mock_openai.chat.completions.create.return_value = mock_response

        document = "이혼 합의서"

        summarizer = EvidenceSummarizer()
        result = summarizer.summarize_document(document)

        self.assertIsInstance(result, SummaryResult)


class TestEvidenceSummarization(unittest.TestCase):
    """증거 요약 테스트"""

    @patch('src.analysis.summarizer.openai')
    def test_summarize_evidence_collection(self, mock_openai):
        """Given: 증거 메시지 컬렉션
        When: summarize_evidence() 호출
        Then: 증거별 핵심 포인트 추출"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """핵심 증거:
1. 외도 증거 (호텔 사진)
2. 폭언 증거 (녹음 파일)
3. 경제적 유기 (생활비 미지급)"""
        mock_openai.chat.completions.create.return_value = mock_response

        messages = [
            Message(content="호텔에서 찍은 사진입니다", sender="Client", timestamp=datetime.now()),
            Message(content="폭언 녹음 파일", sender="Client", timestamp=datetime.now()),
            Message(content="생활비를 주지 않습니다", sender="Client", timestamp=datetime.now())
        ]

        summarizer = EvidenceSummarizer()
        result = summarizer.summarize_evidence(messages)

        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.summary_type, SummaryType.EVIDENCE)
        self.assertGreater(len(result.key_points), 0)


class TestKeyPointExtraction(unittest.TestCase):
    """핵심 포인트 추출 테스트"""

    @patch('src.analysis.summarizer.openai')
    def test_extract_key_points(self, mock_openai):
        """Given: 요약문
        When: 핵심 포인트 추출
        Then: 리스트 형태로 반환"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """핵심 증거:
- 외도 증거 (2024년 1월)
- 폭언 증거 (지속적)
- 생활비 미지급 (3개월)"""
        mock_openai.chat.completions.create.return_value = mock_response

        summarizer = EvidenceSummarizer()
        messages = [Message(content="증거", sender="Client", timestamp=datetime.now())]
        result = summarizer.summarize_evidence(messages)

        # key_points should be extracted from summary
        self.assertIsInstance(result.key_points, list)


class TestSummaryLengthControl(unittest.TestCase):
    """요약 길이 조절 테스트"""

    @patch('src.analysis.summarizer.openai')
    def test_summarize_with_max_words(self, mock_openai):
        """Given: max_words 파라미터 지정
        When: summarize() 호출
        Then: 지정된 단어 수 이내로 요약"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "짧은 요약입니다."
        mock_openai.chat.completions.create.return_value = mock_response

        summarizer = EvidenceSummarizer()
        messages = [Message(content="긴 내용" * 100, sender="User", timestamp=datetime.now())]
        result = summarizer.summarize_conversation(messages, max_words=50)

        self.assertIsInstance(result, SummaryResult)
        # Verify max_words was passed to API prompt
        call_args = mock_openai.chat.completions.create.call_args
        self.assertIsNotNone(call_args)


class TestEdgeCases(unittest.TestCase):
    """엣지 케이스 테스트"""

    def test_summarize_empty_messages(self):
        """Given: 빈 메시지 리스트
        When: summarize_conversation() 호출
        Then: 빈 요약 또는 기본 메시지 반환"""
        summarizer = EvidenceSummarizer()
        result = summarizer.summarize_conversation([])

        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.summary, "")

    @patch('src.analysis.summarizer.openai')
    def test_summarize_single_message(self, mock_openai):
        """Given: 단일 메시지
        When: summarize_conversation() 호출
        Then: 메시지 내용 그대로 또는 간단한 요약"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "외도 증거입니다."
        mock_openai.chat.completions.create.return_value = mock_response

        messages = [Message(content="외도 증거입니다", sender="User", timestamp=datetime.now())]
        summarizer = EvidenceSummarizer()
        result = summarizer.summarize_conversation(messages)

        self.assertIsInstance(result, SummaryResult)

    @patch('src.analysis.summarizer.openai')
    def test_api_error_handling(self, mock_openai):
        """Given: OpenAI API 에러 발생
        When: summarize() 호출
        Then: 적절한 예외 처리 또는 기본값 반환"""
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        summarizer = EvidenceSummarizer()
        messages = [Message(content="test", sender="User", timestamp=datetime.now())]

        with self.assertRaises(Exception):
            summarizer.summarize_conversation(messages)


class TestMultiLanguageSupport(unittest.TestCase):
    """다국어 지원 테스트"""

    @patch('src.analysis.summarizer.openai')
    def test_summarize_korean_content(self, mock_openai):
        """Given: 한국어 콘텐츠
        When: summarize() 호출
        Then: 한국어 요약 반환"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "한국어 요약입니다."
        mock_openai.chat.completions.create.return_value = mock_response

        messages = [Message(content="한국어 내용", sender="User", timestamp=datetime.now())]
        summarizer = EvidenceSummarizer()
        result = summarizer.summarize_conversation(messages, language="ko")

        self.assertIsInstance(result, SummaryResult)


if __name__ == '__main__':
    unittest.main()
