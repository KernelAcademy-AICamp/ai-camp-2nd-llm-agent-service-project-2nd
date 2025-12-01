"""
Article 840 Automatic Tagger

민법 840조 이혼 사유 자동 태깅 모듈

Given: 증거 메시지
When: 내용 분석
Then: 해당하는 민법 840조 카테고리 자동 분류
"""

from typing import List
from enum import Enum
from pydantic import BaseModel, Field
from src.parsers.base import Message


class Article840Category(str, Enum):
    """
    민법 840조 이혼 사유 카테고리

    Korean Civil Code Article 840 - Grounds for Divorce
    """
    ADULTERY = "adultery"  # 제1호: 배우자의 부정행위
    DESERTION = "desertion"  # 제2호: 악의의 유기
    MISTREATMENT_BY_INLAWS = "mistreatment_by_inlaws"  # 제3호: 배우자 직계존속의 부당대우
    HARM_TO_OWN_PARENTS = "harm_to_own_parents"  # 제4호: 자기 직계존속 피해
    UNKNOWN_WHEREABOUTS = "unknown_whereabouts"  # 제5호: 생사불명 3년
    IRRECONCILABLE_DIFFERENCES = "irreconcilable_differences"  # 제6호: 혼인 지속 곤란사유
    GENERAL = "general"  # 일반 증거 (특정 조항에 해당하지 않음)


class TaggingResult(BaseModel):
    """
    태깅 결과

    Attributes:
        categories: 분류된 카테고리 리스트 (다중 카테고리 가능)
        confidence: 신뢰도 점수 (0.0-1.0)
        matched_keywords: 매칭된 키워드 리스트
        reasoning: 분류 이유
    """
    categories: List[Article840Category] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_keywords: List[str] = Field(default_factory=list)
    reasoning: str = ""


class Article840Tagger:
    """
    민법 840조 자동 태거

    Given: 증거 메시지 내용
    When: 키워드 분석 수행
    Then: 해당하는 민법 840조 카테고리 자동 분류

    Features:
    - 7가지 카테고리 분류 (6개 조항 + 일반)
    - 다중 카테고리 태깅 지원
    - 신뢰도 점수 계산
    - 일괄 처리 (batch) 지원
    """

    def __init__(self):
        """초기화 - 카테고리별 키워드 사전 구성"""
        self.keywords = {
            Article840Category.ADULTERY: {
                "keywords": [
                    "외도", "불륜", "바람", "부정", "간통", "다른 사람",
                    "다른 여자", "다른 남자", "부적절한 관계", "밀회",
                    "호텔", "모텔", "연인", "정부", "정부인"
                ],
                "weight": 3
            },
            Article840Category.DESERTION: {
                "keywords": [
                    "유기", "버림", "집을 나갔", "집 나간", "연락 두절",
                    "생활비", "부양", "돌아오지 않", "가출", "떠났",
                    "양육비", "경제적 지원", "방치"
                ],
                "weight": 2
            },
            Article840Category.MISTREATMENT_BY_INLAWS: {
                "keywords": [
                    "시어머니", "시아버지", "시댁", "시집", "시부모",
                    "장인", "장모", "처가", "처갓집",
                    "구타", "폭행", "폭언", "구박", "괴롭힘",
                    "인격 모독", "무시", "학대"
                ],
                "weight": 2
            },
            Article840Category.HARM_TO_OWN_PARENTS: {
                "keywords": [
                    "친정", "친정 부모", "친정어머니", "친정아버지",
                    "제 부모님", "저희 부모님", "부모님",
                    "폭행", "상해", "폭언", "모욕", "학대",
                    "부당한 대우"
                ],
                "weight": 2
            },
            Article840Category.UNKNOWN_WHEREABOUTS: {
                "keywords": [
                    "행방불명", "생사불명", "3년", "실종", "종적",
                    "소재 불명", "연락 안 됨", "찾을 수 없", "사라졌"
                ],
                "weight": 2
            },
            Article840Category.IRRECONCILABLE_DIFFERENCES: {
                "keywords": [
                    "혼인 생활", "결혼 생활", "계속할 수 없", "지속 불가",
                    "이혼하고 싶", "이혼 원함", "갈등", "불화", "다툼",
                    "폭언", "무시", "냉대", "무관심", "가정 폭력",
                    "성격 차이", "가치관 차이", "생활 방식"
                ],
                "weight": 2
            },
            Article840Category.GENERAL: {
                "keywords": [
                    "증거", "자료", "사진", "녹음", "영상", "문자",
                    "카톡", "이메일", "이혼", "소송", "조정", "합의서"
                ],
                "weight": 1
            }
        }

    def tag(self, message: Message) -> TaggingResult:
        """
        단일 메시지 태깅

        Given: Message 객체
        When: 키워드 매칭 및 카테고리 분류
        Then: TaggingResult 반환

        Args:
            message: 태깅할 메시지

        Returns:
            TaggingResult: 분류 결과 (카테고리, 신뢰도, 키워드)
        """
        # 빈 메시지 처리
        if not message.content or message.content.strip() == "":
            return TaggingResult(
                categories=[Article840Category.GENERAL],
                confidence=0.0,
                matched_keywords=[],
                reasoning="Empty message - classified as general"
            )

        content_lower = message.content.lower()

        # 각 카테고리별로 키워드 매칭
        category_matches = {}
        all_matched_keywords = []

        for category, data in self.keywords.items():
            matched_keywords = []
            for keyword in data["keywords"]:
                if keyword in content_lower:
                    if keyword not in all_matched_keywords:
                        all_matched_keywords.append(keyword)
                        matched_keywords.append(keyword)

            if matched_keywords:
                category_matches[category] = {
                    "keywords": matched_keywords,
                    "count": len(matched_keywords),
                    "weight": data["weight"]
                }

        # 카테고리 결정
        if not category_matches:
            # 키워드 매칭이 없으면 GENERAL
            return TaggingResult(
                categories=[Article840Category.GENERAL],
                confidence=0.1,
                matched_keywords=[],
                reasoning="No specific keywords matched - classified as general"
            )

        # GENERAL만 매칭되면 GENERAL로 분류
        if len(category_matches) == 1 and Article840Category.GENERAL in category_matches:
            return TaggingResult(
                categories=[Article840Category.GENERAL],
                confidence=0.3,
                matched_keywords=all_matched_keywords,
                reasoning=f"Only general keywords matched: {', '.join(all_matched_keywords)}"
            )

        # 가중치 기반 정렬 (weight가 높고, 매칭 키워드가 많은 순서)
        sorted_categories = sorted(
            category_matches.items(),
            key=lambda x: (x[1]["weight"] * x[1]["count"], x[1]["count"]),
            reverse=True
        )

        # 상위 카테고리들 선택 (GENERAL 제외)
        selected_categories = []
        for category, match_data in sorted_categories:
            if category != Article840Category.GENERAL:
                selected_categories.append(category)

        # GENERAL 제외하고 매칭이 없으면 GENERAL 추가
        if not selected_categories:
            selected_categories = [Article840Category.GENERAL]

        # 신뢰도 계산
        confidence = self._calculate_confidence(
            total_keywords=len(all_matched_keywords),
            category_count=len(selected_categories)
        )

        # 분류 이유 생성
        reasoning = self._generate_reasoning(
            categories=selected_categories,
            matched_keywords=all_matched_keywords,
            category_matches=category_matches
        )

        return TaggingResult(
            categories=selected_categories,
            confidence=confidence,
            matched_keywords=all_matched_keywords,
            reasoning=reasoning
        )

    def tag_batch(self, messages: List[Message]) -> List[TaggingResult]:
        """
        여러 메시지 일괄 태깅

        Args:
            messages: 메시지 리스트

        Returns:
            List[TaggingResult]: 각 메시지의 태깅 결과
        """
        results = []
        for message in messages:
            result = self.tag(message)
            results.append(result)
        return results

    def _calculate_confidence(
        self,
        total_keywords: int,
        category_count: int
    ) -> float:
        """
        신뢰도 점수 계산

        Args:
            total_keywords: 매칭된 총 키워드 개수
            category_count: 분류된 카테고리 개수

        Returns:
            float: 신뢰도 점수 (0.0-1.0)
        """
        if total_keywords == 0:
            return 0.0

        # 기본 신뢰도: 키워드 개수에 비례
        base_confidence = min(0.3 + (total_keywords * 0.2), 1.0)

        # 다중 카테고리는 신뢰도 약간 감소
        if category_count > 1:
            base_confidence *= 0.9

        return round(base_confidence, 2)

    def _generate_reasoning(
        self,
        categories: List[Article840Category],
        matched_keywords: List[str],
        category_matches: dict
    ) -> str:
        """
        분류 이유 생성

        Args:
            categories: 분류된 카테고리 리스트
            matched_keywords: 매칭된 키워드 리스트
            category_matches: 카테고리별 매칭 정보

        Returns:
            str: 분류 이유 설명
        """
        if not categories or categories == [Article840Category.GENERAL]:
            return f"General evidence with keywords: {', '.join(matched_keywords[:3])}"

        # 카테고리 이름 매핑
        category_names = {
            Article840Category.ADULTERY: "Adultery (Article 840-1)",
            Article840Category.DESERTION: "Malicious Desertion (Article 840-2)",
            Article840Category.MISTREATMENT_BY_INLAWS: "Mistreatment by In-laws (Article 840-3)",
            Article840Category.HARM_TO_OWN_PARENTS: "Harm to Own Parents (Article 840-4)",
            Article840Category.UNKNOWN_WHEREABOUTS: "Unknown Whereabouts (Article 840-5)",
            Article840Category.IRRECONCILABLE_DIFFERENCES: "Irreconcilable Differences (Article 840-6)",
            Article840Category.GENERAL: "General Evidence"
        }

        category_list = [category_names[cat] for cat in categories]

        reasoning = f"Classified as {', '.join(category_list)} based on {len(matched_keywords)} keywords"

        # 주요 키워드 추가
        if matched_keywords:
            top_keywords = matched_keywords[:3]
            reasoning += f": {', '.join(top_keywords)}"

        return reasoning
