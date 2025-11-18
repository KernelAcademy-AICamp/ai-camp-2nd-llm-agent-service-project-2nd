"""
EvidenceScorer Module
Analyzes messages and assigns evidence value scores (0-10)
"""

from typing import List
from pydantic import BaseModel, Field, field_validator
from src.parsers.base import Message


class ScoringResult(BaseModel):
    """
    증거 점수 계산 결과

    Attributes:
        score: 증거 가치 점수 (0-10)
        matched_keywords: 매칭된 키워드 목록
        reasoning: 점수 산정 이유
    """
    score: float
    matched_keywords: List[str] = Field(default_factory=list)
    reasoning: str = ""

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        """점수 범위 검증 (0-10)"""
        if v < 0 or v > 10:
            raise ValueError(f"Score must be between 0 and 10, got {v}")
        return v


class EvidenceScorer:
    """
    증거 가치 점수 계산기

    Given: 메시지 내용
    When: 키워드 분석 및 점수 계산
    Then: 증거 가치 점수 (0-10) 반환

    키워드 카테고리:
    - 이혼/소송: 3-5점
    - 폭력/폭행: 7-9점
    - 재산/금전: 4-6점
    - 불륜/외도: 6-8점
    - 증거: 2-4점
    """

    def __init__(self):
        """초기화 - 키워드 사전 구성"""
        self.keywords = {
            # 카테고리: (키워드 리스트, 기본 점수)
            "divorce": (["이혼", "소송", "합의서", "조정", "이혼 소송"], 4.0),
            "violence": (["폭행", "폭력", "상해", "병원", "진단서", "멍", "상처"], 8.0),
            "financial": (["재산", "통장", "계좌", "돈", "금전", "재산 분할", "자산"], 5.0),
            "affair": (["불륜", "외도", "바람", "다른 사람", "부정"], 7.0),
            "evidence": (["증거", "자료", "사진", "영상", "녹음", "기록"], 3.0),
            "child": (["양육권", "아이", "자녀", "면접교섭"], 6.0),
            "threat": (["협박", "위협", "죽이겠다", "해치겠다"], 9.0),
        }

    def score(self, message: Message) -> ScoringResult:
        """
        단일 메시지 점수 계산

        Given: Message 객체
        When: 키워드 매칭 및 점수 계산
        Then: ScoringResult 반환

        Args:
            message: 분석할 메시지

        Returns:
            ScoringResult: 점수 및 매칭 키워드
        """
        # 빈 메시지 처리
        if not message.content or message.content.strip() == "":
            return ScoringResult(
                score=0.0,
                matched_keywords=[],
                reasoning="Empty message"
            )

        content = message.content.lower()
        total_score = 0.0
        matched_keywords = []
        matched_categories = []

        # 각 카테고리별로 키워드 매칭
        for category, (keywords, base_score) in self.keywords.items():
            category_matched = False
            for keyword in keywords:
                if keyword in content:
                    if keyword not in matched_keywords:
                        matched_keywords.append(keyword)
                    category_matched = True

            # 카테고리에 매칭이 있으면 점수 추가
            if category_matched:
                total_score += base_score
                matched_categories.append(category)

        # 점수 정규화 (최대 10점)
        if total_score > 10.0:
            total_score = 10.0

        # 키워드가 없으면 기본 점수 1.0
        if len(matched_keywords) == 0:
            total_score = 1.0

        # 점수 산정 이유 생성
        reasoning = self._generate_reasoning(
            total_score,
            matched_categories,
            len(matched_keywords)
        )

        return ScoringResult(
            score=round(total_score, 1),
            matched_keywords=matched_keywords,
            reasoning=reasoning
        )

    def score_batch(self, messages: List[Message]) -> List[ScoringResult]:
        """
        여러 메시지 일괄 점수 계산

        Args:
            messages: 메시지 리스트

        Returns:
            List[ScoringResult]: 각 메시지의 점수 결과
        """
        results = []
        for message in messages:
            result = self.score(message)
            results.append(result)
        return results

    def _generate_reasoning(
        self,
        score: float,
        categories: List[str],
        keyword_count: int
    ) -> str:
        """
        점수 산정 이유 생성

        Args:
            score: 계산된 점수
            categories: 매칭된 카테고리
            keyword_count: 매칭된 키워드 개수

        Returns:
            str: 점수 이유 설명
        """
        if score == 0.0:
            return "No evidence keywords found"

        if score == 1.0:
            return "Neutral message with no significant evidence keywords"

        category_names = {
            "divorce": "divorce/lawsuit",
            "violence": "violence/assault",
            "financial": "financial/property",
            "affair": "affair/infidelity",
            "evidence": "evidence documentation",
            "child": "child custody",
            "threat": "threats/intimidation"
        }

        matched_names = [category_names.get(c, c) for c in categories]

        reasoning = f"High evidence value due to {keyword_count} keywords in categories: {', '.join(matched_names)}"

        if score >= 8.0:
            reasoning = "Critical evidence - " + reasoning
        elif score >= 6.0:
            reasoning = "Strong evidence - " + reasoning
        elif score >= 4.0:
            reasoning = "Moderate evidence - " + reasoning

        return reasoning
