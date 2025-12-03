"""
문맥 인식 키워드 매칭 모듈

Kiwi 형태소 분석기를 사용한 부정문 감지로 False Positive 방지

Features:
- 형태소 분석 기반 키워드 추출
- 부정문 패턴 감지 (안, 못, 지 않, 아니)
- 윈도우 기반 문맥 분석
- 기존 키워드 매칭과 통합

Usage:
    from src.analysis.context_matcher import ContextAwareKeywordMatcher

    matcher = ContextAwareKeywordMatcher()
    result = matcher.analyze("외도하지 않았어", keywords=["외도"])
    # result.is_negated = True, result.adjusted_score = -0.8
"""

import re
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class NegationType(str, Enum):
    """부정 유형"""
    NONE = "none"           # 부정 없음
    PREFIX = "prefix"       # 안 했다, 못 했다
    SUFFIX = "suffix"       # ~하지 않았다, ~지 못했다
    PREDICATE = "predicate" # ~가 아니다, ~적 없다
    QUESTION = "question"   # ~한 거 아니야? (의문형)


@dataclass
class MatchResult:
    """키워드 매칭 결과"""
    keyword: str
    found: bool
    position: Optional[int] = None  # 문자열 내 위치
    negation_type: NegationType = NegationType.NONE
    is_negated: bool = False
    is_question: bool = False
    context_window: str = ""  # 주변 문맥
    base_score: float = 1.0
    adjusted_score: float = 1.0  # 부정 시 음수


@dataclass
class AnalysisResult:
    """전체 분석 결과"""
    text: str
    matches: List[MatchResult] = field(default_factory=list)
    has_negation: bool = False
    overall_score: float = 0.0
    morphemes: List[str] = field(default_factory=list)  # 형태소 목록


# 부정 표현 패턴
NEGATION_PATTERNS = {
    # 접두 부정 (안, 못)
    'prefix': [
        r'안\s+',      # 안 했다
        r'못\s+',      # 못 했다
    ],
    # 접미 부정 (~지 않/못)
    'suffix': [
        r'지\s*않',    # ~하지 않았다
        r'지\s*못',    # ~하지 못했다
        r'지\s*말',    # ~하지 마
    ],
    # 서술어 부정
    'predicate': [
        r'아니',       # ~가 아니다
        r'없',         # ~적 없다, ~한 적 없다
    ],
    # 의문형 (부정적 의미일 수 있음)
    'question': [
        r'아니야\?',   # ~한 거 아니야?
        r'아닌가\?',
        r'않았어\?',
    ]
}

# 한국어 부정 형태소
NEGATION_MORPHEMES = ['않', '못', '말', '없', '아니']


class ContextAwareKeywordMatcher:
    """
    문맥 인식 키워드 매처

    Kiwi 형태소 분석기를 사용하여 부정문을 감지하고
    키워드 매칭의 False Positive를 줄입니다.

    Usage:
        matcher = ContextAwareKeywordMatcher()

        # 긍정 문맥
        result = matcher.analyze("외도했어", keywords=["외도"])
        # result.matches[0].is_negated = False

        # 부정 문맥
        result = matcher.analyze("외도하지 않았어", keywords=["외도"])
        # result.matches[0].is_negated = True
    """

    def __init__(self, use_kiwi: bool = True):
        """
        Args:
            use_kiwi: Kiwi 형태소 분석기 사용 여부 (미설치 시 자동 비활성화)
        """
        self.use_kiwi = use_kiwi
        self._kiwi = None

        if use_kiwi:
            self._init_kiwi()

    def _init_kiwi(self):
        """Kiwi 형태소 분석기 초기화"""
        try:
            from kiwipiepy import Kiwi
            self._kiwi = Kiwi()
            logger.info("Kiwi 형태소 분석기 초기화 완료")
        except ImportError:
            logger.warning("Kiwi 미설치. pip install kiwipiepy")
            self.use_kiwi = False
            self._kiwi = None

    def analyze(
        self,
        text: str,
        keywords: List[str],
        window_size: int = 4
    ) -> AnalysisResult:
        """
        텍스트 분석 및 키워드 매칭

        Args:
            text: 분석할 텍스트
            keywords: 찾을 키워드 목록
            window_size: 문맥 윈도우 크기 (형태소 개수)

        Returns:
            AnalysisResult: 분석 결과
        """
        if not text or not keywords:
            return AnalysisResult(text=text)

        # 형태소 분석
        morphemes = self._analyze_morphemes(text) if self.use_kiwi else []

        # 각 키워드 매칭
        matches = []
        for keyword in keywords:
            match_result = self._match_keyword(text, keyword, morphemes, window_size)
            if match_result.found:
                matches.append(match_result)

        # 전체 부정 여부
        has_negation = any(m.is_negated for m in matches)

        # 전체 점수 계산
        if matches:
            overall_score = sum(m.adjusted_score for m in matches) / len(matches)
        else:
            overall_score = 0.0

        return AnalysisResult(
            text=text,
            matches=matches,
            has_negation=has_negation,
            overall_score=overall_score,
            morphemes=morphemes
        )

    def _analyze_morphemes(self, text: str) -> List[str]:
        """형태소 분석"""
        if not self._kiwi:
            return []

        try:
            result = self._kiwi.analyze(text)
            if result:
                # 첫 번째 분석 결과의 형태소들
                return [token.form for token in result[0][0]]
        except Exception as e:
            logger.warning(f"형태소 분석 실패: {e}")

        return []

    def _match_keyword(
        self,
        text: str,
        keyword: str,
        morphemes: List[str],
        window_size: int
    ) -> MatchResult:
        """단일 키워드 매칭"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        # 키워드 위치 찾기
        position = text_lower.find(keyword_lower)
        if position == -1:
            return MatchResult(keyword=keyword, found=False)

        # 문맥 윈도우 추출
        context = self._extract_context(text, position, len(keyword))

        # 부정 여부 판단
        negation_type, is_negated = self._check_negation(
            text, keyword, position, morphemes, window_size
        )

        # 의문형 체크
        is_question = self._check_question(text, position)

        # 점수 조정
        base_score = 1.0
        if is_negated:
            adjusted_score = -0.8  # 부정은 음수 점수
        elif is_question:
            adjusted_score = 0.5   # 의문형은 불확실
        else:
            adjusted_score = base_score

        return MatchResult(
            keyword=keyword,
            found=True,
            position=position,
            negation_type=negation_type,
            is_negated=is_negated,
            is_question=is_question,
            context_window=context,
            base_score=base_score,
            adjusted_score=adjusted_score
        )

    def _extract_context(self, text: str, position: int, keyword_len: int) -> str:
        """키워드 주변 문맥 추출"""
        start = max(0, position - 20)
        end = min(len(text), position + keyword_len + 20)
        return text[start:end]

    def _check_negation(
        self,
        text: str,
        keyword: str,
        position: int,
        morphemes: List[str],
        window_size: int
    ) -> Tuple[NegationType, bool]:
        """부정 여부 판단"""
        # 1. 정규식 기반 체크 (빠름)
        negation_type = self._check_negation_regex(text, position)
        if negation_type != NegationType.NONE:
            return negation_type, True

        # 2. 형태소 기반 체크 (정확)
        if morphemes:
            is_negated = self._check_negation_morpheme(
                morphemes, keyword, window_size
            )
            if is_negated:
                return NegationType.SUFFIX, True

        return NegationType.NONE, False

    def _check_negation_regex(self, text: str, keyword_pos: int) -> NegationType:
        """정규식 기반 부정 체크"""
        # 키워드 앞부분만 확인 (효율성)
        before_text = text[max(0, keyword_pos - 30):keyword_pos]
        after_text = text[keyword_pos:min(len(text), keyword_pos + 30)]

        # 접두 부정 (안, 못)
        for pattern in NEGATION_PATTERNS['prefix']:
            if re.search(pattern + r'.*$', before_text):
                return NegationType.PREFIX

        # 접미 부정 (~지 않/못)
        for pattern in NEGATION_PATTERNS['suffix']:
            if re.search(pattern, after_text):
                return NegationType.SUFFIX

        # 서술어 부정 (아니, 없)
        for pattern in NEGATION_PATTERNS['predicate']:
            if re.search(pattern, after_text):
                return NegationType.PREDICATE

        # 의문형
        for pattern in NEGATION_PATTERNS['question']:
            if re.search(pattern, after_text):
                return NegationType.QUESTION

        return NegationType.NONE

    def _check_negation_morpheme(
        self,
        morphemes: List[str],
        keyword: str,
        window_size: int
    ) -> bool:
        """형태소 기반 부정 체크"""
        # 키워드 형태소 위치 찾기
        keyword_idx = None
        for i, morph in enumerate(morphemes):
            if keyword in morph or morph in keyword:
                keyword_idx = i
                break

        if keyword_idx is None:
            return False

        # 윈도우 내 부정 형태소 확인
        start = max(0, keyword_idx - window_size)
        end = min(len(morphemes), keyword_idx + window_size + 1)

        for morph in morphemes[start:end]:
            if morph in NEGATION_MORPHEMES:
                return True

        return False

    def _check_question(self, text: str, position: int) -> bool:
        """의문형 여부 확인"""
        # 키워드 이후 텍스트에서 물음표 확인
        after_text = text[position:]
        return '?' in after_text[:50]

    def get_effective_keywords(
        self,
        text: str,
        keywords: List[str]
    ) -> List[str]:
        """
        부정되지 않은 유효 키워드만 반환

        Args:
            text: 분석할 텍스트
            keywords: 키워드 목록

        Returns:
            부정되지 않은 키워드 목록
        """
        result = self.analyze(text, keywords)
        return [
            m.keyword for m in result.matches
            if not m.is_negated
        ]

    def calculate_confidence_adjustment(
        self,
        text: str,
        keywords: List[str],
        base_confidence: float
    ) -> float:
        """
        부정 문맥에 따른 신뢰도 조정

        Args:
            text: 분석할 텍스트
            keywords: 키워드 목록
            base_confidence: 기본 신뢰도

        Returns:
            조정된 신뢰도
        """
        result = self.analyze(text, keywords)

        if not result.matches:
            return base_confidence

        # 부정된 키워드 비율
        negated_ratio = sum(1 for m in result.matches if m.is_negated) / len(result.matches)

        # 부정 비율에 따라 신뢰도 감소
        if negated_ratio > 0.5:
            # 대부분 부정 → 신뢰도 크게 감소
            return base_confidence * 0.2
        elif negated_ratio > 0:
            # 일부 부정 → 신뢰도 약간 감소
            return base_confidence * (1 - negated_ratio * 0.5)

        return base_confidence


# 편의를 위한 간편 함수
def check_negation(text: str, keyword: str) -> bool:
    """
    간단한 부정 체크

    Args:
        text: 텍스트
        keyword: 키워드

    Returns:
        부정 여부
    """
    matcher = ContextAwareKeywordMatcher(use_kiwi=False)  # 정규식만 사용
    result = matcher.analyze(text, [keyword])
    return result.has_negation


def get_effective_keywords(text: str, keywords: List[str]) -> List[str]:
    """
    유효 키워드 추출 (간편 함수)

    Args:
        text: 텍스트
        keywords: 키워드 목록

    Returns:
        부정되지 않은 키워드들
    """
    matcher = ContextAwareKeywordMatcher()
    return matcher.get_effective_keywords(text, keywords)


# 모듈 export
__all__ = [
    "NegationType",
    "MatchResult",
    "AnalysisResult",
    "ContextAwareKeywordMatcher",
    "check_negation",
    "get_effective_keywords",
    "NEGATION_PATTERNS",
    "NEGATION_MORPHEMES",
]
