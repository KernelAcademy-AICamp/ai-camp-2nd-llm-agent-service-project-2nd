"""
Legal Analyzer - 통합 법적 분석 모듈

기존 Article840Tagger와 EvidenceScorer를 통합하여
새로운 LegalAnalysis 스키마를 자동 생성합니다.

핵심 기능:
- EvidenceChunk → LegalAnalysis 자동 변환
- 민법 840조 카테고리 자동 분류
- 신뢰도 레벨 (1-5) 자동 계산
- 키워드 기반 + AI 기반 분석 지원
"""

import os
import json
import logging
from typing import List

logger = logging.getLogger(__name__)

from src.schemas import (
    EvidenceChunk,
    LegalAnalysis,
    LegalCategory,
    ConfidenceLevel,
)
from src.parsers.base import Message
from src.prompts.tone_guidelines import OBJECTIVE_TONE_GUIDELINES
from .article_840_tagger import Article840Tagger, Article840Category
from .evidence_scorer import EvidenceScorer


# Article840Category → LegalCategory 매핑
CATEGORY_MAPPING = {
    Article840Category.ADULTERY: LegalCategory.ADULTERY,
    Article840Category.DESERTION: LegalCategory.DESERTION,
    Article840Category.MISTREATMENT_BY_INLAWS: LegalCategory.MISTREATMENT_BY_INLAWS,
    Article840Category.HARM_TO_OWN_PARENTS: LegalCategory.HARM_TO_OWN_PARENTS,
    Article840Category.UNKNOWN_WHEREABOUTS: LegalCategory.UNKNOWN_WHEREABOUTS,
    Article840Category.IRRECONCILABLE_DIFFERENCES: LegalCategory.IRRECONCILABLE_DIFFERENCES,
    Article840Category.DOMESTIC_VIOLENCE: LegalCategory.DOMESTIC_VIOLENCE,
    Article840Category.FINANCIAL_MISCONDUCT: LegalCategory.FINANCIAL_MISCONDUCT,
    Article840Category.GENERAL: LegalCategory.GENERAL,
}


def score_to_confidence_level(score: float) -> ConfidenceLevel:
    """
    증거 점수 (0-10)를 신뢰도 레벨 (1-5)로 변환

    변환 기준:
    - 0-2점: Level 1 (불확실)
    - 2-4점: Level 2 (약한 정황)
    - 4-6점: Level 3 (의심 정황)
    - 6-8점: Level 4 (강력한 정황)
    - 8-10점: Level 5 (확정적 증거)
    """
    if score < 2:
        return ConfidenceLevel.UNCERTAIN
    elif score < 4:
        return ConfidenceLevel.WEAK
    elif score < 6:
        return ConfidenceLevel.SUSPICIOUS
    elif score < 8:
        return ConfidenceLevel.STRONG
    else:
        return ConfidenceLevel.DEFINITIVE


def score_to_confidence_score(score: float) -> float:
    """증거 점수 (0-10)를 신뢰도 점수 (0.0-1.0)로 변환"""
    return min(score / 10.0, 1.0)


class LegalAnalyzer:
    """
    통합 법적 분석기

    EvidenceChunk를 분석하여 LegalAnalysis를 자동 생성합니다.

    Usage:
        analyzer = LegalAnalyzer()

        # 단일 청크 분석
        analysis = analyzer.analyze(chunk)
        chunk.legal_analysis = analysis

        # 일괄 분석
        chunks = analyzer.analyze_batch(chunks)
    """

    def __init__(
        self,
        use_ai: bool = False,
        ai_model: str = "gpt-4o-mini"
    ):
        """
        Args:
            use_ai: AI 기반 분석 사용 여부 (기본: False, 키워드 기반)
            ai_model: 사용할 AI 모델 (use_ai=True일 때만 사용)
        """
        self.tagger = Article840Tagger()
        self.scorer = EvidenceScorer()
        self.use_ai = use_ai
        self.ai_model = ai_model

    def analyze(self, chunk: EvidenceChunk) -> LegalAnalysis:
        """
        단일 청크 분석

        Args:
            chunk: 분석할 EvidenceChunk

        Returns:
            LegalAnalysis: 분석 결과
        """
        # EvidenceChunk → Message 변환 (기존 분석기 호환)
        message = Message(
            content=chunk.content,
            sender=chunk.sender or "Unknown",
            timestamp=chunk.timestamp
        )

        # 키워드 기반 분석
        if not self.use_ai:
            return self._analyze_keyword_based(message)
        else:
            return self._analyze_ai_based(chunk)

    def analyze_and_update(self, chunk: EvidenceChunk) -> EvidenceChunk:
        """
        청크 분석 후 legal_analysis 필드 업데이트

        Args:
            chunk: 분석할 EvidenceChunk

        Returns:
            EvidenceChunk: legal_analysis가 업데이트된 청크
        """
        analysis = self.analyze(chunk)
        chunk.legal_analysis = analysis
        return chunk

    def analyze_batch(self, chunks: List[EvidenceChunk]) -> List[EvidenceChunk]:
        """
        여러 청크 일괄 분석

        Args:
            chunks: 분석할 청크 리스트

        Returns:
            List[EvidenceChunk]: legal_analysis가 업데이트된 청크 리스트
        """
        analyzed_chunks = []
        for chunk in chunks:
            analyzed_chunk = self.analyze_and_update(chunk)
            analyzed_chunks.append(analyzed_chunk)
        return analyzed_chunks

    def _analyze_keyword_based(self, message: Message) -> LegalAnalysis:
        """키워드 기반 분석"""
        # Article 840 태깅
        tagging_result = self.tagger.tag(message)

        # 증거 점수 계산
        scoring_result = self.scorer.score(message)

        # LegalCategory로 변환
        categories = []
        for cat in tagging_result.categories:
            legal_cat = CATEGORY_MAPPING.get(cat, LegalCategory.GENERAL)
            categories.append(legal_cat)

        # 주요 카테고리 결정 (첫 번째 non-GENERAL)
        primary_category = None
        for cat in categories:
            if cat != LegalCategory.GENERAL:
                primary_category = cat
                break
        if primary_category is None and categories:
            primary_category = categories[0]

        # 신뢰도 계산
        confidence_level = score_to_confidence_level(scoring_result.score)
        confidence_score = max(
            tagging_result.confidence,
            score_to_confidence_score(scoring_result.score)
        )

        # 사람 검토 필요 여부 결정
        requires_human_review = False
        review_reason = None

        # 중요 증거이지만 신뢰도가 낮으면 검토 필요
        if (primary_category in [LegalCategory.ADULTERY, LegalCategory.DOMESTIC_VIOLENCE]
            and confidence_level.value <= 2):
            requires_human_review = True
            review_reason = "중요 카테고리이나 신뢰도가 낮아 검토 필요"

        # 다중 카테고리면 검토 필요
        non_general_cats = [c for c in categories if c != LegalCategory.GENERAL]
        if len(non_general_cats) > 2:
            requires_human_review = True
            review_reason = "다중 카테고리 해당으로 검토 필요"

        # 결과 조합
        reasoning = f"{tagging_result.reasoning}. Score: {scoring_result.score}/10 - {scoring_result.reasoning}"

        return LegalAnalysis(
            categories=categories,
            primary_category=primary_category,
            confidence_level=confidence_level,
            confidence_score=round(confidence_score, 2),
            reasoning=reasoning,
            matched_keywords=list(set(
                tagging_result.matched_keywords + scoring_result.matched_keywords
            )),
            requires_human_review=requires_human_review,
            review_reason=review_reason
        )

    def _analyze_ai_based(self, chunk: EvidenceChunk) -> LegalAnalysis:
        """
        AI 기반 분석 (GPT-4 사용)

        GPT-4를 사용하여 더 정확한 법적 분석을 수행합니다.
        API 오류 시 키워드 기반으로 fallback합니다.
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # 프롬프트 생성
            prompt = self._build_analysis_prompt(chunk)

            # GPT-4 호출
            response = client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 일관성을 위해 낮은 temperature
                response_format={"type": "json_object"}
            )

            # 응답 파싱
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            return self._parse_ai_response(result, chunk)

        except ImportError:
            logger.warning("OpenAI package not installed. Falling back to keyword-based analysis.")
            return self._fallback_to_keyword(chunk)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}. Falling back to keyword-based analysis.")
            return self._fallback_to_keyword(chunk)

    def _get_system_prompt(self) -> str:
        """AI 분석용 시스템 프롬프트 (톤 가이드라인 포함)"""
        base_prompt = """당신은 한국 이혼 소송 전문 법률 AI입니다.
주어진 메시지/증거를 분석하여 민법 840조 이혼 사유에 해당하는지 판단합니다.

## 민법 840조 이혼 사유 카테고리

1. **adultery** (제1호): 부정행위 - 외도, 불륜, 간통
2. **desertion** (제2호): 악의의 유기 - 가출, 연락두절, 부양의무 불이행
3. **mistreatment_by_inlaws** (제3호): 배우자 직계존속의 부당대우 - 시댁/처가의 학대
4. **harm_to_own_parents** (제4호): 자기 직계존속에 대한 해악 - 친정/처가 부모에 대한 폭행
5. **unknown_whereabouts** (제5호): 생사불명 3년 이상
6. **domestic_violence** (제6호 세부): 가정폭력 - 신체적/언어적/정서적 폭력
7. **financial_misconduct** (제6호 세부): 재정 비행 - 도박, 채무, 재산 은닉
8. **irreconcilable_differences** (제6호): 기타 혼인 지속 곤란 사유
9. **general**: 특정 사유에 해당하지 않는 일반 증거

## 신뢰도 레벨 (1-5)

1. **UNCERTAIN**: 관련성 불확실
2. **WEAK**: 약한 정황
3. **SUSPICIOUS**: 의심 정황
4. **STRONG**: 강력한 정황
5. **DEFINITIVE**: 확정적 증거 (직접 증거)

## 출력 형식 (JSON)

{
    "categories": ["primary_category", "secondary_category"],
    "primary_category": "main_category",
    "confidence_level": 1-5,
    "confidence_score": 0.0-1.0,
    "reasoning": "분류 이유 설명 (한국어, 객관적 톤 사용)",
    "matched_keywords": ["키워드1", "키워드2"],
    "requires_human_review": true/false,
    "review_reason": "검토 필요 시 이유"
}"""
        # 톤앤매너 가이드라인 추가
        return f"{base_prompt}\n\n{OBJECTIVE_TONE_GUIDELINES}"

    def _build_analysis_prompt(self, chunk: EvidenceChunk) -> str:
        """분석용 프롬프트 생성"""
        context_info = ""
        if chunk.sender:
            context_info += f"발신자: {chunk.sender}\n"
        if chunk.timestamp:
            context_info += f"시간: {chunk.timestamp}\n"
        if chunk.source_location:
            context_info += f"출처: {chunk.source_location.to_citation()}\n"

        return f"""다음 메시지를 분석해주세요:

## 메시지 내용
{chunk.content}

## 컨텍스트 정보
{context_info if context_info else "없음"}

## 분석 요청
위 메시지가 민법 840조 어떤 이혼 사유에 해당하는지, 신뢰도는 어느 정도인지 JSON 형식으로 분석해주세요."""

    def _parse_ai_response(self, result: dict, chunk: EvidenceChunk) -> LegalAnalysis:
        """AI 응답을 LegalAnalysis로 변환"""
        # 카테고리 파싱
        categories = []
        for cat_str in result.get("categories", ["general"]):
            try:
                categories.append(LegalCategory(cat_str))
            except ValueError:
                categories.append(LegalCategory.GENERAL)

        # 주요 카테고리
        primary_cat_str = result.get("primary_category", "general")
        try:
            primary_category = LegalCategory(primary_cat_str)
        except ValueError:
            primary_category = categories[0] if categories else LegalCategory.GENERAL

        # 신뢰도 레벨
        conf_level = result.get("confidence_level", 1)
        try:
            confidence_level = ConfidenceLevel(conf_level)
        except ValueError:
            confidence_level = ConfidenceLevel.UNCERTAIN

        # 신뢰도 점수
        confidence_score = float(result.get("confidence_score", 0.5))

        return LegalAnalysis(
            categories=categories,
            primary_category=primary_category,
            confidence_level=confidence_level,
            confidence_score=round(confidence_score, 2),
            reasoning=result.get("reasoning", "AI 분석 완료"),
            matched_keywords=result.get("matched_keywords", []),
            requires_human_review=result.get("requires_human_review", False),
            review_reason=result.get("review_reason")
        )

    def _fallback_to_keyword(self, chunk: EvidenceChunk) -> LegalAnalysis:
        """키워드 기반 분석으로 fallback"""
        message = Message(
            content=chunk.content,
            sender=chunk.sender or "Unknown",
            timestamp=chunk.timestamp
        )
        return self._analyze_keyword_based(message)

    def get_summary_stats(self, chunks: List[EvidenceChunk]) -> dict:
        """
        분석된 청크들의 통계 요약

        Args:
            chunks: 분석된 청크 리스트

        Returns:
            dict: 통계 요약
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "category_counts": {},
                "confidence_distribution": {},
                "high_value_count": 0,
                "requires_review_count": 0
            }

        # 카테고리별 카운트
        category_counts = {}
        confidence_dist = {level.name: 0 for level in ConfidenceLevel}
        high_value_count = 0
        requires_review_count = 0

        for chunk in chunks:
            analysis = chunk.legal_analysis

            # 카테고리 카운트
            for cat in analysis.categories:
                cat_name = cat.value if hasattr(cat, 'value') else cat
                category_counts[cat_name] = category_counts.get(cat_name, 0) + 1

            # 신뢰도 분포
            level = analysis.confidence_level
            level_name = level.name if hasattr(level, 'name') else str(level)
            if level_name in confidence_dist:
                confidence_dist[level_name] += 1

            # 고가치 증거 (Level 4-5)
            level_value = level.value if hasattr(level, 'value') else level
            if level_value >= 4:
                high_value_count += 1

            # 검토 필요
            if analysis.requires_human_review:
                requires_review_count += 1

        return {
            "total_chunks": len(chunks),
            "category_counts": category_counts,
            "confidence_distribution": confidence_dist,
            "high_value_count": high_value_count,
            "requires_review_count": requires_review_count
        }


# 간편 함수
def analyze_chunk(chunk: EvidenceChunk) -> LegalAnalysis:
    """단일 청크 분석 (간편 함수)"""
    analyzer = LegalAnalyzer()
    return analyzer.analyze(chunk)


def analyze_chunks(chunks: List[EvidenceChunk]) -> List[EvidenceChunk]:
    """여러 청크 분석 (간편 함수)"""
    analyzer = LegalAnalyzer()
    return analyzer.analyze_batch(chunks)
