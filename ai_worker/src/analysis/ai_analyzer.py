"""
AI 기반 법적 분석 모듈

GPT-4o-mini를 사용한 민법 840조 이혼 사유 분류

Features:
- EvidenceClassification 스키마 사용
- Instructor 라이브러리 지원 (선택적)
- 키워드 기반 Fallback
- 토큰 최적화 (시스템 프롬프트 캐싱)

Usage:
    from src.analysis.ai_analyzer import AIAnalyzer

    analyzer = AIAnalyzer(model="gpt-4o-mini")
    result = analyzer.analyze(chunk)
"""

import os
import json
import logging
from typing import Optional, List
from dataclasses import dataclass

from src.schemas import (
    EvidenceChunk,
    LegalAnalysis,
    EvidenceClassification,
    classification_to_legal_analysis,
    get_system_prompt_categories,
)
from src.exceptions import AnalysisError

logger = logging.getLogger(__name__)


# 시스템 프롬프트 (1024+ 토큰으로 캐싱 최적화)
SYSTEM_PROMPT = """당신은 대한민국 가사소송 전문 법률 AI입니다.
주어진 메시지/증거를 분석하여 민법 제840조 이혼 사유에 해당하는지 판단합니다.

{categories}

## 신뢰도 기준 (confidence: 0.0-1.0)

- 0.0-0.2: 관련성 불확실 - 이혼 사유와 무관하거나 맥락 불명확
- 0.2-0.4: 약한 정황 - 간접적 암시, 단일 키워드만 존재
- 0.4-0.6: 의심 정황 - 의심스러운 패턴, 맥락상 가능성 있음
- 0.6-0.8: 강력한 정황 - 복수의 증거, 간접 인정 포함
- 0.8-1.0: 확정적 증거 - 직접 인정, 명백한 증거

## 분석 지침

1. 메시지 내용을 주의 깊게 읽고 이혼 사유 해당 여부 판단
2. 부정문/반어법 주의: "외도 안 했어" → 무관(부정), "외도 한 거 아니야?" → 의심(질문)
3. 핵심 증거 문구(key_phrases) 정확히 추출
4. 언급된 인물/장소/금액 추출
5. 신뢰도가 낮지만 중요한 경우 requires_review=true 설정

## Few-shot 예시

### 예시 1: 외도 증거
입력: "어제 호텔에서 그 사람 또 만났어"
출력:
- primary_ground: 부정행위
- confidence: 0.75
- key_phrases: ["호텔에서", "그 사람", "또 만났어"]
- reasoning: 호텔 만남과 '또'라는 표현이 반복적 외도를 암시

### 예시 2: 가정폭력
입력: "남편이 또 때렸어. 멍이 들었어."
출력:
- primary_ground: 가정폭력
- confidence: 0.85
- key_phrases: ["때렸어", "멍이 들었어"]
- reasoning: 신체 폭력의 직접적 진술과 상해 증거

### 예시 3: 무관한 메시지
입력: "오늘 저녁 뭐 먹을까?"
출력:
- primary_ground: 무관
- confidence: 0.95
- key_phrases: []
- reasoning: 일상 대화로 이혼 사유와 무관

### 예시 4: 부정문 (False Positive 방지)
입력: "바람 안 피웠어. 오해야."
출력:
- primary_ground: 무관
- confidence: 0.7
- key_phrases: ["바람 안 피웠어", "오해"]
- reasoning: 부정문으로 외도를 부인하는 내용

## 출력 형식

반드시 아래 JSON 스키마를 따르세요:
{{
    "primary_ground": "부정행위|악의의유기|배우자학대|시댁학대|직계존속학대|생사불명|가정폭력|재정비행|자녀학대|약물남용|기타중대사유|무관",
    "secondary_grounds": [],
    "confidence": 0.0-1.0,
    "key_phrases": ["핵심 문구"],
    "reasoning": "분류 이유 (한국어)",
    "mentioned_entities": ["인물/장소/금액"],
    "requires_review": true/false,
    "review_reason": "검토 필요 시 이유 또는 null"
}}"""


@dataclass
class AIAnalyzerConfig:
    """AI 분석기 설정"""
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 500
    max_retries: int = 3
    use_instructor: bool = False  # Instructor 라이브러리 사용 여부


class AIAnalyzer:
    """
    AI 기반 법적 분석기

    GPT-4o-mini를 사용하여 민법 840조 이혼 사유 분류

    Usage:
        analyzer = AIAnalyzer()
        result = analyzer.analyze(chunk)

        # 또는 설정 커스터마이징
        config = AIAnalyzerConfig(model="gpt-4o", temperature=0.2)
        analyzer = AIAnalyzer(config=config)
    """

    def __init__(self, config: Optional[AIAnalyzerConfig] = None):
        self.config = config or AIAnalyzerConfig()
        self._client = None
        self._system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """시스템 프롬프트 생성"""
        categories = get_system_prompt_categories()
        return SYSTEM_PROMPT.format(categories=categories)

    def _get_client(self):
        """OpenAI 클라이언트 가져오기 (lazy initialization)"""
        if self._client is None:
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise AnalysisError(
                        "OPENAI_API_KEY 환경변수가 설정되지 않았습니다",
                        analysis_type="ai",
                        fallback_available=True
                    )
                self._client = OpenAI(api_key=api_key)
            except ImportError:
                raise AnalysisError(
                    "OpenAI 패키지가 설치되지 않았습니다. pip install openai",
                    analysis_type="ai",
                    fallback_available=True
                )
        return self._client

    def analyze(self, chunk: EvidenceChunk) -> LegalAnalysis:
        """
        AI 기반 분석 수행

        Args:
            chunk: 분석할 증거 청크

        Returns:
            LegalAnalysis: 분석 결과

        Raises:
            AnalysisError: API 호출 실패 시 (fallback_available=True)
        """
        if self.config.use_instructor:
            return self._analyze_with_instructor(chunk)
        else:
            return self._analyze_with_openai(chunk)

    def _analyze_with_openai(self, chunk: EvidenceChunk) -> LegalAnalysis:
        """OpenAI API 직접 호출"""
        client = self._get_client()

        # 사용자 프롬프트 생성
        user_prompt = self._build_user_prompt(chunk)

        try:
            response = client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )

            # 응답 파싱
            result_text = response.choices[0].message.content
            result_dict = json.loads(result_text)

            # EvidenceClassification으로 변환
            classification = EvidenceClassification.model_validate(result_dict)

            # LegalAnalysis로 변환
            return classification_to_legal_analysis(classification)

        except json.JSONDecodeError as e:
            logger.error(f"AI 응답 JSON 파싱 실패: {e}")
            raise AnalysisError(
                f"AI 응답 파싱 실패: {e}",
                analysis_type="ai",
                fallback_available=True
            )
        except Exception as e:
            logger.error(f"AI 분석 실패: {e}")
            raise AnalysisError(
                f"AI 분석 실패: {e}",
                analysis_type="ai",
                fallback_available=True
            )

    def _analyze_with_instructor(self, chunk: EvidenceChunk) -> LegalAnalysis:
        """Instructor 라이브러리 사용 (자동 재시도, 검증)"""
        try:
            import instructor
            from openai import OpenAI

            client = instructor.from_openai(
                OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            )

            user_prompt = self._build_user_prompt(chunk)

            classification = client.chat.completions.create(
                model=self.config.model,
                response_model=EvidenceClassification,
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                max_retries=self.config.max_retries
            )

            return classification_to_legal_analysis(classification)

        except ImportError:
            logger.warning("Instructor 패키지 미설치, OpenAI 직접 호출로 전환")
            self.config.use_instructor = False
            return self._analyze_with_openai(chunk)
        except Exception as e:
            logger.error(f"Instructor 분석 실패: {e}")
            raise AnalysisError(
                f"Instructor 분석 실패: {e}",
                analysis_type="ai",
                fallback_available=True
            )

    def _build_user_prompt(self, chunk: EvidenceChunk) -> str:
        """사용자 프롬프트 생성"""
        parts = ["다음 메시지를 분석해주세요:\n"]

        # 메시지 내용
        parts.append(f"## 메시지 내용\n{chunk.content}\n")

        # 컨텍스트 정보
        context_parts = []
        if chunk.sender:
            context_parts.append(f"- 발신자: {chunk.sender}")
        if chunk.timestamp:
            context_parts.append(f"- 시간: {chunk.timestamp}")
        if chunk.source_location:
            context_parts.append(f"- 출처: {chunk.source_location.to_citation()}")

        if context_parts:
            parts.append("## 컨텍스트\n" + "\n".join(context_parts))

        return "\n".join(parts)

    def analyze_batch(
        self,
        chunks: List[EvidenceChunk],
        on_error: str = "fallback"  # "fallback" | "skip" | "raise"
    ) -> List[EvidenceChunk]:
        """
        여러 청크 일괄 분석

        Args:
            chunks: 분석할 청크 리스트
            on_error: 에러 처리 방식
                - "fallback": 키워드 분석으로 대체
                - "skip": 해당 청크 건너뛰기
                - "raise": 예외 발생

        Returns:
            분석 완료된 청크 리스트
        """
        from .legal_analyzer import LegalAnalyzer

        keyword_analyzer = LegalAnalyzer(use_ai=False)
        results = []

        for chunk in chunks:
            try:
                analysis = self.analyze(chunk)
                chunk.legal_analysis = analysis
                results.append(chunk)
            except AnalysisError as e:
                if on_error == "fallback" and e.fallback_available:
                    logger.warning(f"AI 분석 실패, 키워드 분석으로 대체: {chunk.chunk_id}")
                    chunk.legal_analysis = keyword_analyzer.analyze(chunk)
                    results.append(chunk)
                elif on_error == "skip":
                    logger.warning(f"분석 건너뛰기: {chunk.chunk_id}")
                    continue
                else:
                    raise

        return results


# 간편 함수
def analyze_with_ai(
    chunk: EvidenceChunk,
    model: str = "gpt-4o-mini"
) -> LegalAnalysis:
    """
    단일 청크 AI 분석 (간편 함수)

    Args:
        chunk: 분석할 청크
        model: 사용할 모델

    Returns:
        LegalAnalysis
    """
    config = AIAnalyzerConfig(model=model)
    analyzer = AIAnalyzer(config=config)
    return analyzer.analyze(chunk)


# 모듈 export
__all__ = [
    "AIAnalyzerConfig",
    "AIAnalyzer",
    "analyze_with_ai",
    "SYSTEM_PROMPT",
]
