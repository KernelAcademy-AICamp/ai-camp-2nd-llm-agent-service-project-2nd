"""
LLM Service
다양한 LLM API를 통합 관리하는 서비스
"""

from typing import List, Dict, Any, Optional
import os
from enum import Enum
import asyncio
from openai import AsyncOpenAI
import anthropic
from abc import ABC, abstractmethod
import json


class LLMProvider(Enum):
    """LLM 제공자"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class BaseLLM(ABC):
    """LLM 기본 클래스"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """텍스트 생성"""
        pass

    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """대화 생성"""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI GPT 모델"""

    def __init__(self, api_key: str = None):
        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        self.model = "gpt-4-turbo-preview"

    async def generate(self, prompt: str, **kwargs) -> str:
        """텍스트 생성"""
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """대화 생성"""
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000)
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class AnthropicLLM(BaseLLM):
    """Anthropic Claude 모델"""

    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-3-sonnet-20240229"

    async def generate(self, prompt: str, **kwargs) -> str:
        """텍스트 생성"""
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=kwargs.get("model", self.model),
                max_tokens=kwargs.get("max_tokens", 1000),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """대화 생성"""
        try:
            # Claude API 형식으로 변환
            claude_messages = []
            for msg in messages:
                if msg["role"] != "system":
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            response = await asyncio.to_thread(
                self.client.messages.create,
                model=kwargs.get("model", self.model),
                max_tokens=kwargs.get("max_tokens", 1000),
                messages=claude_messages,
                system=messages[0]["content"] if messages and messages[0]["role"] == "system" else None
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")


class LLMService:
    """통합 LLM 서비스"""

    def __init__(self, provider: LLMProvider = LLMProvider.OPENAI):
        self.provider = provider
        self.llm = self._initialize_llm(provider)
        self.conversation_history: Dict[str, List[Dict]] = {}

    def _initialize_llm(self, provider: LLMProvider) -> BaseLLM:
        """LLM 초기화"""
        if provider == LLMProvider.OPENAI:
            return OpenAILLM()
        elif provider == LLMProvider.ANTHROPIC:
            return AnthropicLLM()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """텍스트 생성"""
        return await self.llm.generate(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def generate_summary(self, text: str, max_lines: int = 5) -> str:
        """텍스트 요약 생성"""
        prompt = f"""
        다음 텍스트를 {max_lines}줄 이내로 요약해주세요.
        핵심 내용만 포함하고 간결하게 작성하세요.

        텍스트:
        {text[:3000]}  # 토큰 제한을 위해 일부만 사용

        요약:
        """
        return await self.generate_text(prompt, temperature=0.3)

    async def answer_question(
        self,
        question: str,
        context: str = "",
        chat_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """질문에 대한 답변 생성"""

        # 시스템 프롬프트
        system_prompt = """
        당신은 친절하고 지능적인 학습 도우미입니다.
        주어진 컨텍스트를 기반으로 정확하고 도움이 되는 답변을 제공하세요.
        컨텍스트에 답이 없다면, 일반적인 지식을 활용하되 그 사실을 명시하세요.
        """

        # 메시지 구성
        messages = [{"role": "system", "content": system_prompt}]

        # 대화 히스토리 추가
        if chat_history:
            messages.extend(chat_history[-6:])  # 최근 3턴만 포함

        # 현재 질문 추가
        user_prompt = f"""
        컨텍스트: {context[:2000] if context else "컨텍스트가 제공되지 않았습니다."}

        질문: {question}

        답변:
        """
        messages.append({"role": "user", "content": user_prompt})

        # 답변 생성
        answer = await self.llm.chat(messages)

        # 신뢰도 계산 (간단한 휴리스틱)
        confidence = self._calculate_confidence(context, answer)

        return {
            "answer": answer,
            "confidence": confidence,
            "source": "context" if confidence > 0.7 else "general knowledge",
            "provider": self.provider.value
        }

    async def chat(
        self,
        message: str,
        chat_history: List[Dict] = None,
        session_id: str = None
    ) -> str:
        """대화형 채팅"""

        # 세션별 대화 기록 관리
        if session_id:
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            history = self.conversation_history[session_id]
        else:
            history = chat_history or []

        # 시스템 메시지
        messages = [{
            "role": "system",
            "content": "당신은 친절하고 도움이 되는 AI 학습 도우미입니다. 학생들의 질문에 명확하고 이해하기 쉽게 답변하세요."
        }]

        # 대화 히스토리 추가
        messages.extend(history[-10:])  # 최근 5턴만 유지

        # 현재 메시지 추가
        messages.append({"role": "user", "content": message})

        # 응답 생성
        response = await self.llm.chat(messages)

        # 세션 히스토리 업데이트
        if session_id:
            self.conversation_history[session_id].append(
                {"role": "user", "content": message}
            )
            self.conversation_history[session_id].append(
                {"role": "assistant", "content": response}
            )

        return response

    def _calculate_confidence(self, context: str, answer: str) -> float:
        """답변 신뢰도 계산 (간단한 휴리스틱)"""
        if not context:
            return 0.5

        # 컨텍스트와 답변의 단어 겹침 비율 계산
        context_words = set(context.lower().split())
        answer_words = set(answer.lower().split())

        # 공통 단어
        common_words = context_words & answer_words

        # 신뢰도 계산
        if len(answer_words) == 0:
            return 0.0

        overlap_ratio = len(common_words) / len(answer_words)
        confidence = min(overlap_ratio * 2, 1.0)  # 0~1 범위로 정규화

        return round(confidence, 2)

    async def generate_quiz(
        self,
        content: str,
        num_questions: int = 5,
        question_type: str = "multiple_choice"
    ) -> List[Dict]:
        """퀴즈 문제 생성"""

        prompt = f"""
        다음 내용을 바탕으로 {num_questions}개의 {'객관식' if question_type == 'multiple_choice' else '주관식'} 문제를 생성하세요.

        내용:
        {content[:2000]}

        각 문제는 다음 형식으로 작성하세요:
        1. 질문
        2. {'선택지 (A, B, C, D)' if question_type == 'multiple_choice' else '예시 답안'}
        3. 정답
        4. 해설

        JSON 형식으로 응답하세요.
        """

        response = await self.generate_text(prompt, temperature=0.5)

        try:
            # JSON 파싱 시도
            quiz_data = json.loads(response)
            return quiz_data
        except:
            # 파싱 실패 시 텍스트로 반환
            return [{
                "type": "text",
                "content": response
            }]

    async def explain_concept(
        self,
        concept: str,
        level: str = "beginner"
    ) -> str:
        """개념 설명"""

        level_map = {
            "beginner": "초보자도 이해할 수 있도록 쉽고 친절하게",
            "intermediate": "기본 지식이 있는 사람을 위해 적절한 깊이로",
            "advanced": "전문가 수준으로 깊이 있고 상세하게"
        }

        prompt = f"""
        '{concept}'에 대해 {level_map.get(level, level_map['beginner'])} 설명해주세요.

        다음 구조로 설명하세요:
        1. 개념 정의
        2. 핵심 특징
        3. 실제 예시
        4. 관련 개념
        5. 추가 학습 자료
        """

        return await self.generate_text(prompt, temperature=0.5)