"""
AI Classification Schema
AI 분석용 Pydantic 모델 - Instructor/GPT-4 Structured Output용

연구 보고서 권장:
- DivorceGround: 민법 840조 한국어 레이블
- EvidenceClassification: AI 응답 파싱용
- LegalCategory 매핑 함수

Usage:
    from src.schemas.ai_classification import (
        DivorceGround,
        EvidenceClassification,
        to_legal_category
    )

    # GPT-4 응답 파싱
    classification = EvidenceClassification.model_validate(ai_response)

    # 기존 스키마로 변환
    legal_category = to_legal_category(classification.primary_ground)
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from .legal_analysis import LegalCategory, ConfidenceLevel


class DivorceGround(str, Enum):
    """
    민법 제840조 이혼 사유 (한국어 레이블)

    AI 분석 결과의 가독성을 위해 한국어 값 사용
    """
    # 제1호: 배우자의 부정행위
    UNCHASTITY = "부정행위"

    # 제2호: 악의의 유기
    MALICIOUS_DESERTION = "악의의유기"

    # 제3호: 배우자 또는 그 직계존속의 심히 부당한 대우
    MALTREATMENT_BY_SPOUSE = "배우자학대"
    MALTREATMENT_BY_INLAWS = "시댁학대"

    # 제4호: 자기의 직계존속에 대한 배우자의 심히 부당한 대우
    MALTREATMENT_OF_ASCENDANTS = "직계존속학대"

    # 제5호: 배우자의 생사가 3년 이상 분명하지 않은 때
    UNKNOWN_WHEREABOUTS = "생사불명"

    # 제6호: 기타 혼인을 계속하기 어려운 중대한 사유
    DOMESTIC_VIOLENCE = "가정폭력"
    FINANCIAL_MISCONDUCT = "재정비행"
    CHILD_ABUSE = "자녀학대"
    SUBSTANCE_ABUSE = "약물남용"
    OTHER_SERIOUS_CAUSE = "기타중대사유"

    # 분류 불가
    NOT_RELEVANT = "무관"


class EvidenceClassification(BaseModel):
    """
    AI 분류 결과 모델

    GPT-4 Structured Output / Instructor용
    100% JSON 스키마 준수 보장
    """

    primary_ground: DivorceGround = Field(
        ...,
        description="주요 이혼 사유 (민법 840조)"
    )

    secondary_grounds: List[DivorceGround] = Field(
        default_factory=list,
        description="부가적 이혼 사유들"
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="분류 신뢰도 (0.0-1.0)"
    )

    key_phrases: List[str] = Field(
        default_factory=list,
        description="핵심 증거 문구"
    )

    reasoning: str = Field(
        ...,
        description="분류 근거 설명"
    )

    mentioned_entities: List[str] = Field(
        default_factory=list,
        description="언급된 인물/장소/금액"
    )

    requires_review: bool = Field(
        False,
        description="사람 검토 필요 여부"
    )

    review_reason: Optional[str] = Field(
        None,
        description="검토 필요 이유"
    )


# DivorceGround → LegalCategory 매핑
DIVORCE_GROUND_TO_LEGAL_CATEGORY = {
    DivorceGround.UNCHASTITY: LegalCategory.ADULTERY,
    DivorceGround.MALICIOUS_DESERTION: LegalCategory.DESERTION,
    DivorceGround.MALTREATMENT_BY_SPOUSE: LegalCategory.MISTREATMENT_BY_SPOUSE,
    DivorceGround.MALTREATMENT_BY_INLAWS: LegalCategory.MISTREATMENT_BY_INLAWS,
    DivorceGround.MALTREATMENT_OF_ASCENDANTS: LegalCategory.HARM_TO_OWN_PARENTS,
    DivorceGround.UNKNOWN_WHEREABOUTS: LegalCategory.UNKNOWN_WHEREABOUTS,
    DivorceGround.DOMESTIC_VIOLENCE: LegalCategory.DOMESTIC_VIOLENCE,
    DivorceGround.FINANCIAL_MISCONDUCT: LegalCategory.FINANCIAL_MISCONDUCT,
    DivorceGround.CHILD_ABUSE: LegalCategory.CHILD_ABUSE,
    DivorceGround.SUBSTANCE_ABUSE: LegalCategory.SUBSTANCE_ABUSE,
    DivorceGround.OTHER_SERIOUS_CAUSE: LegalCategory.IRRECONCILABLE_DIFFERENCES,
    DivorceGround.NOT_RELEVANT: LegalCategory.GENERAL,
}

# LegalCategory → DivorceGround 역매핑
LEGAL_CATEGORY_TO_DIVORCE_GROUND = {v: k for k, v in DIVORCE_GROUND_TO_LEGAL_CATEGORY.items()}


def to_legal_category(ground: DivorceGround) -> LegalCategory:
    """
    DivorceGround를 LegalCategory로 변환

    Args:
        ground: AI 분류 결과

    Returns:
        LegalCategory: 기존 스키마 카테고리
    """
    return DIVORCE_GROUND_TO_LEGAL_CATEGORY.get(ground, LegalCategory.GENERAL)


def to_divorce_ground(category: LegalCategory) -> DivorceGround:
    """
    LegalCategory를 DivorceGround로 변환

    Args:
        category: 기존 스키마 카테고리

    Returns:
        DivorceGround: AI 분류용 카테고리
    """
    return LEGAL_CATEGORY_TO_DIVORCE_GROUND.get(category, DivorceGround.NOT_RELEVANT)


def confidence_to_level(confidence: float) -> ConfidenceLevel:
    """
    신뢰도 점수를 ConfidenceLevel로 변환

    Args:
        confidence: 0.0-1.0 범위의 신뢰도

    Returns:
        ConfidenceLevel: 1-5 레벨
    """
    if confidence < 0.2:
        return ConfidenceLevel.UNCERTAIN
    elif confidence < 0.4:
        return ConfidenceLevel.WEAK
    elif confidence < 0.6:
        return ConfidenceLevel.SUSPICIOUS
    elif confidence < 0.8:
        return ConfidenceLevel.STRONG
    else:
        return ConfidenceLevel.DEFINITIVE


def classification_to_legal_analysis(classification: EvidenceClassification):
    """
    EvidenceClassification을 LegalAnalysis로 변환

    Args:
        classification: AI 분류 결과

    Returns:
        LegalAnalysis: 기존 스키마 분석 결과
    """
    from .legal_analysis import LegalAnalysis

    # 카테고리 변환
    categories = [to_legal_category(classification.primary_ground)]
    for ground in classification.secondary_grounds:
        cat = to_legal_category(ground)
        if cat not in categories:
            categories.append(cat)

    return LegalAnalysis(
        categories=categories,
        primary_category=categories[0] if categories else None,
        confidence_level=confidence_to_level(classification.confidence),
        confidence_score=classification.confidence,
        reasoning=classification.reasoning,
        matched_keywords=classification.key_phrases,
        mentioned_persons=[e for e in classification.mentioned_entities if not any(c.isdigit() for c in e)],
        mentioned_amounts=[e for e in classification.mentioned_entities if any(c.isdigit() for c in e)],
        requires_human_review=classification.requires_review,
        review_reason=classification.review_reason
    )


# AI 시스템 프롬프트용 카테고리 설명
DIVORCE_GROUND_DESCRIPTIONS = {
    DivorceGround.UNCHASTITY: "제1호: 배우자의 부정행위 (외도, 불륜, 간통)",
    DivorceGround.MALICIOUS_DESERTION: "제2호: 악의의 유기 (가출, 연락두절, 부양의무 불이행)",
    DivorceGround.MALTREATMENT_BY_SPOUSE: "제3호: 배우자의 심히 부당한 대우",
    DivorceGround.MALTREATMENT_BY_INLAWS: "제3호: 배우자 직계존속(시댁/처가)의 부당한 대우",
    DivorceGround.MALTREATMENT_OF_ASCENDANTS: "제4호: 자기 직계존속에 대한 배우자의 부당한 대우",
    DivorceGround.UNKNOWN_WHEREABOUTS: "제5호: 배우자의 생사가 3년 이상 불명",
    DivorceGround.DOMESTIC_VIOLENCE: "제6호: 가정폭력 (신체적/정서적/언어적 폭력)",
    DivorceGround.FINANCIAL_MISCONDUCT: "제6호: 재정 비행 (도박, 채무, 재산 은닉/낭비)",
    DivorceGround.CHILD_ABUSE: "제6호: 자녀 학대",
    DivorceGround.SUBSTANCE_ABUSE: "제6호: 약물/알코올 남용",
    DivorceGround.OTHER_SERIOUS_CAUSE: "제6호: 기타 혼인 지속 곤란 사유",
    DivorceGround.NOT_RELEVANT: "이혼 사유와 무관한 일반 내용",
}


def get_system_prompt_categories() -> str:
    """AI 시스템 프롬프트용 카테고리 설명 생성"""
    lines = ["## 민법 제840조 이혼 사유 카테고리\n"]
    for ground, desc in DIVORCE_GROUND_DESCRIPTIONS.items():
        lines.append(f"- **{ground.value}**: {desc}")
    return "\n".join(lines)


# 편의를 위한 export
__all__ = [
    "DivorceGround",
    "EvidenceClassification",
    "DIVORCE_GROUND_TO_LEGAL_CATEGORY",
    "LEGAL_CATEGORY_TO_DIVORCE_GROUND",
    "DIVORCE_GROUND_DESCRIPTIONS",
    "to_legal_category",
    "to_divorce_ground",
    "confidence_to_level",
    "classification_to_legal_analysis",
    "get_system_prompt_categories",
]
