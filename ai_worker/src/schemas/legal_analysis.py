"""
Legal Analysis Schema
법적 분석 결과 - 민법 840조 기반 분류 및 신뢰도

AI가 "이것이 외도 증거"라고 판단한 근거와 신뢰도를 명시적으로 기록
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class LegalCategory(str, Enum):
    """
    민법 840조 이혼 사유 카테고리

    Korean Civil Code Article 840 - Grounds for Divorce
    """
    # 제1호: 배우자의 부정행위
    ADULTERY = "adultery"

    # 제2호: 악의의 유기
    DESERTION = "desertion"

    # 제3호: 배우자 또는 그 직계존속의 심히 부당한 대우
    MISTREATMENT_BY_SPOUSE = "mistreatment_by_spouse"
    MISTREATMENT_BY_INLAWS = "mistreatment_by_inlaws"

    # 제4호: 자기의 직계존속에 대한 배우자의 심히 부당한 대우
    HARM_TO_OWN_PARENTS = "harm_to_own_parents"

    # 제5호: 배우자의 생사가 3년 이상 분명하지 않은 때
    UNKNOWN_WHEREABOUTS = "unknown_whereabouts"

    # 제6호: 기타 혼인을 계속하기 어려운 중대한 사유
    DOMESTIC_VIOLENCE = "domestic_violence"  # 가정폭력
    FINANCIAL_MISCONDUCT = "financial_misconduct"  # 재산 은닉/낭비
    CHILD_ABUSE = "child_abuse"  # 자녀 학대
    SUBSTANCE_ABUSE = "substance_abuse"  # 약물/알코올 남용
    IRRECONCILABLE_DIFFERENCES = "irreconcilable_differences"  # 기타

    # 분류 불가
    GENERAL = "general"


class ConfidenceLevel(int, Enum):
    """
    신뢰도 레벨 (1-5)

    법적 증거로서의 확실성 정도
    """
    # Level 1: 불확실 - 추가 확인 필요
    UNCERTAIN = 1

    # Level 2: 약한 정황 - 단일 증거, 맥락 불명확
    WEAK = 2

    # Level 3: 의심 정황 - 의심스러운 패턴, 간접 증거
    SUSPICIOUS = 3

    # Level 4: 강력한 정황 - 간접 인정 + 일부 물증
    STRONG = 4

    # Level 5: 확정적 증거 - 직접 인정 + 다중 물증
    DEFINITIVE = 5


class LegalAnalysis(BaseModel):
    """
    법적 분석 결과

    AI가 증거를 분류한 결과와 그 근거를 기록

    Examples:
        외도 증거:
            categories=["adultery"]
            confidence_level=4
            reasoning="직접적 표현('그 사람 만났어') + 호텔 GPS 일치"
    """

    # ========================================
    # 분류 결과
    # ========================================
    categories: List[LegalCategory] = Field(
        default_factory=list,
        description="해당하는 법적 카테고리들 (복수 가능)"
    )

    primary_category: Optional[LegalCategory] = Field(
        None,
        description="가장 주요한 카테고리"
    )

    # ========================================
    # 신뢰도
    # ========================================
    confidence_level: ConfidenceLevel = Field(
        ConfidenceLevel.UNCERTAIN,
        description="신뢰도 레벨 (1-5)"
    )

    confidence_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="신뢰도 점수 (0.0-1.0)"
    )

    # ========================================
    # 판단 근거
    # ========================================
    reasoning: str = Field(
        "",
        description="분류 이유 (사람이 읽을 수 있는 형식)"
    )

    matched_keywords: List[str] = Field(
        default_factory=list,
        description="매칭된 키워드들"
    )

    # ========================================
    # 추가 분석
    # ========================================
    mentioned_persons: List[str] = Field(
        default_factory=list,
        description="언급된 인물들 (영희, 시어머니 등)"
    )

    mentioned_locations: List[str] = Field(
        default_factory=list,
        description="언급된 장소들 (호텔, 역삼역 등)"
    )

    mentioned_amounts: List[str] = Field(
        default_factory=list,
        description="언급된 금액들 (100만원, 전세금 등)"
    )

    # ========================================
    # 검토 필요 여부
    # ========================================
    requires_human_review: bool = Field(
        False,
        description="사람 검토가 필요한지 여부"
    )

    review_reason: Optional[str] = Field(
        None,
        description="검토가 필요한 이유"
    )

    def to_summary(self) -> str:
        """분석 결과 요약 문자열"""
        if not self.categories:
            return "분류되지 않음"

        # enum이거나 string일 수 있음 (use_enum_values=True일 때)
        cat_names = [
            cat.value if hasattr(cat, 'value') else cat
            for cat in self.categories
        ]
        level_desc = {
            1: "불확실",
            2: "약한 정황",
            3: "의심 정황",
            4: "강력한 정황",
            5: "확정적 증거"
        }

        # confidence_level도 enum이거나 int일 수 있음
        level_value = (
            self.confidence_level.value
            if hasattr(self.confidence_level, 'value')
            else self.confidence_level
        )

        return (
            f"카테고리: {', '.join(cat_names)} | "
            f"신뢰도: {level_desc.get(level_value, '?')} "
            f"({self.confidence_score:.0%})"
        )

    class Config:
        use_enum_values = True
