"""
Evidence Summarizer (증거 요약기)

Given: 증거 메시지 또는 문서
When: LLM 기반 요약 수행
Then: 핵심 내용 추출 및 요약문 생성
"""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field
import openai

from src.parsers.base import Message
from src.prompts.tone_guidelines import DISCLAIMER_TEXT


class SummaryType(str, Enum):
    """
    요약 타입

    Types:
        CONVERSATION: 대화 요약
        DOCUMENT: 문서 요약
        EVIDENCE: 증거 요약
        GENERAL: 일반 요약
    """
    CONVERSATION = "conversation"
    DOCUMENT = "document"
    EVIDENCE = "evidence"
    GENERAL = "general"


class SummaryResult(BaseModel):
    """
    요약 결과

    Attributes:
        summary: 요약문
        summary_type: 요약 타입
        key_points: 핵심 포인트 리스트
        word_count: 요약 단어 수
    """
    summary: str
    summary_type: SummaryType
    key_points: List[str] = Field(default_factory=list)
    word_count: int = 0


class EvidenceSummarizer:
    """
    증거 요약기 (LLM 기반)

    Given: 증거 메시지 또는 문서 텍스트
    When: summarize() 호출
    Then: GPT-4로 요약 생성 및 핵심 포인트 추출

    Features:
    - 대화 요약 (summarize_conversation)
    - 문서 요약 (summarize_document)
    - 증거 요약 (summarize_evidence)
    - 핵심 포인트 자동 추출
    - 요약 길이 조절 (max_words)
    - 다국어 지원 (language)
    """

    def __init__(self, model: str = "gpt-4o"):
        """
        초기화

        Args:
            model: OpenAI 모델 (기본: gpt-4o)
        """
        self.model = model

    def summarize_conversation(
        self,
        messages: List[Message],
        max_words: Optional[int] = None,
        language: str = "ko"
    ) -> SummaryResult:
        """
        대화 요약

        Given: 대화 메시지 리스트
        When: GPT-4로 대화 분석
        Then: 요약문 및 핵심 포인트 반환

        Args:
            messages: 대화 메시지 리스트
            max_words: 최대 단어 수 (기본: None)
            language: 요약 언어 (기본: ko)

        Returns:
            SummaryResult: 요약 결과
        """
        # 빈 메시지 처리
        if not messages or len(messages) == 0:
            return SummaryResult(
                summary="",
                summary_type=SummaryType.CONVERSATION,
                key_points=[],
                word_count=0
            )

        # 대화 텍스트 생성
        conversation_text = self._format_conversation(messages)

        # 요약 프롬프트 생성
        prompt = self._create_conversation_prompt(
            conversation_text,
            max_words=max_words,
            language=language
        )

        # GPT-4 호출
        try:
            summary_text = self._call_llm(prompt)

            # 핵심 포인트 추출
            key_points = self._extract_key_points(summary_text)

            # 단어 수 계산
            word_count = len(summary_text.split())

            return SummaryResult(
                summary=summary_text,
                summary_type=SummaryType.CONVERSATION,
                key_points=key_points,
                word_count=word_count
            )
        except Exception as e:
            raise Exception(f"Summarization failed: {e}")

    def summarize_document(
        self,
        document: str,
        max_words: Optional[int] = None,
        language: str = "ko"
    ) -> SummaryResult:
        """
        문서 요약

        Given: 법률 문서 또는 일반 문서 텍스트
        When: GPT-4로 문서 분석
        Then: 요약문 반환

        Args:
            document: 문서 텍스트
            max_words: 최대 단어 수
            language: 요약 언어

        Returns:
            SummaryResult: 요약 결과
        """
        # 빈 문서 처리
        if not document or document.strip() == "":
            return SummaryResult(
                summary="",
                summary_type=SummaryType.DOCUMENT,
                key_points=[],
                word_count=0
            )

        # 요약 프롬프트 생성
        prompt = self._create_document_prompt(
            document,
            max_words=max_words,
            language=language
        )

        # GPT-4 호출
        try:
            summary_text = self._call_llm(prompt)

            # 핵심 포인트 추출
            key_points = self._extract_key_points(summary_text)

            # 단어 수 계산
            word_count = len(summary_text.split())

            return SummaryResult(
                summary=summary_text,
                summary_type=SummaryType.DOCUMENT,
                key_points=key_points,
                word_count=word_count
            )
        except Exception as e:
            raise Exception(f"Document summarization failed: {e}")

    def summarize_evidence(
        self,
        messages: List[Message],
        max_words: Optional[int] = None,
        language: str = "ko"
    ) -> SummaryResult:
        """
        증거 요약

        Given: 증거 메시지 리스트
        When: GPT-4로 증거 분석
        Then: 증거별 핵심 포인트 추출

        Args:
            messages: 증거 메시지 리스트
            max_words: 최대 단어 수
            language: 요약 언어

        Returns:
            SummaryResult: 요약 결과
        """
        # 빈 메시지 처리
        if not messages or len(messages) == 0:
            return SummaryResult(
                summary="",
                summary_type=SummaryType.EVIDENCE,
                key_points=[],
                word_count=0
            )

        # 증거 텍스트 생성
        evidence_text = "\n".join([f"- {msg.content}" for msg in messages])

        # 요약 프롬프트 생성
        prompt = self._create_evidence_prompt(
            evidence_text,
            max_words=max_words,
            language=language
        )

        # GPT-4 호출
        try:
            summary_text = self._call_llm(prompt)

            # 핵심 포인트 추출
            key_points = self._extract_key_points(summary_text)

            # 단어 수 계산
            word_count = len(summary_text.split())

            return SummaryResult(
                summary=summary_text,
                summary_type=SummaryType.EVIDENCE,
                key_points=key_points,
                word_count=word_count
            )
        except Exception as e:
            raise Exception(f"Evidence summarization failed: {e}")

    def _format_conversation(self, messages: List[Message]) -> str:
        """
        대화 메시지를 텍스트로 포맷

        Args:
            messages: 메시지 리스트

        Returns:
            str: 포맷된 대화 텍스트
        """
        conversation = []
        for msg in messages:
            conversation.append(f"{msg.sender}: {msg.content}")
        return "\n".join(conversation)

    def _create_conversation_prompt(
        self,
        conversation: str,
        max_words: Optional[int] = None,
        language: str = "ko"
    ) -> str:
        """
        대화 요약 프롬프트 생성

        Args:
            conversation: 대화 텍스트
            max_words: 최대 단어 수
            language: 요약 언어

        Returns:
            str: 프롬프트
        """
        length_instruction = ""
        if max_words:
            length_instruction = f"\n요약은 {max_words}단어 이내로 작성하세요."

        lang_instruction = "한국어로" if language == "ko" else "in English"

        prompt = f"""다음 대화를 {lang_instruction} 요약해주세요.{length_instruction}

대화 내용:
{conversation}

요약:"""
        return prompt

    def _create_document_prompt(
        self,
        document: str,
        max_words: Optional[int] = None,
        language: str = "ko"
    ) -> str:
        """
        문서 요약 프롬프트 생성

        Args:
            document: 문서 텍스트
            max_words: 최대 단어 수
            language: 요약 언어

        Returns:
            str: 프롬프트
        """
        length_instruction = ""
        if max_words:
            length_instruction = f"\n요약은 {max_words}단어 이내로 작성하세요."

        lang_instruction = "한국어로" if language == "ko" else "in English"

        prompt = f"""다음 문서를 {lang_instruction} 요약해주세요.{length_instruction}

문서 내용:
{document}

요약:"""
        return prompt

    def _create_evidence_prompt(
        self,
        evidence: str,
        max_words: Optional[int] = None,
        language: str = "ko"
    ) -> str:
        """
        증거 요약 프롬프트 생성

        Args:
            evidence: 증거 텍스트
            max_words: 최대 단어 수
            language: 요약 언어

        Returns:
            str: 프롬프트
        """
        length_instruction = ""
        if max_words:
            length_instruction = f"\n요약은 {max_words}단어 이내로 작성하세요."

        lang_instruction = "한국어로" if language == "ko" else "in English"

        prompt = f"""다음 증거들을 {lang_instruction} 요약하고 핵심 포인트를 추출해주세요.{length_instruction}

증거 목록:
{evidence}

핵심 증거:"""
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """
        LLM API 호출

        Args:
            prompt: 프롬프트

        Returns:
            str: LLM 응답

        Raises:
            Exception: API 호출 실패 시
        """
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 법률 증거 분석 전문가입니다. 주어진 대화나 문서의 객관적 사실만 요약합니다. 조언이나 판단 표현은 포함하지 않습니다. '~입니다', '~으로 확인됩니다' 형태로 작성합니다."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3  # 일관성 있는 요약을 위해 낮은 temperature
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"LLM API call failed: {e}")

    def _extract_key_points(self, summary: str) -> List[str]:
        """
        요약문에서 핵심 포인트 추출

        Args:
            summary: 요약 텍스트

        Returns:
            List[str]: 핵심 포인트 리스트
        """
        key_points = []

        # 줄 단위로 분리
        lines = summary.split('\n')

        for line in lines:
            line = line.strip()
            # 숫자. 또는 - 로 시작하는 항목 추출
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•', '*')):
                # 접두사 제거
                cleaned = line.lstrip('0123456789.-•* ')
                if cleaned:
                    key_points.append(cleaned)

        return key_points
