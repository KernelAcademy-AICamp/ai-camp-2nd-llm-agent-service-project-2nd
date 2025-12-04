"""
Event Summarizer - 이벤트 한 줄 요약 생성기

증거/이벤트 내용을 분석하여 한 줄 요약을 생성합니다.
LLM 미사용, 규칙 기반 요약.

Usage:
    from src.analysis.event_summarizer import EventSummarizer, summarize_event

    summarizer = EventSummarizer()
    summary = summarizer.summarize(
        content="남편이 또 바람을 피웠어요. 이번엔 직장 동료랑...",
        fault_types=["adultery"]
    )
    # "배우자 외도 관련 대화"
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# 데이터 클래스
# =============================================================================

class SummaryType(str, Enum):
    """요약 유형"""
    CONVERSATION = "conversation"      # 대화/메시지
    INCIDENT = "incident"              # 사건/이슈
    EVIDENCE = "evidence"              # 증거 자료
    RECORD = "record"                  # 기록 (진단서, 신고서 등)
    FINANCIAL = "financial"            # 금융/재산 관련


@dataclass
class EventSummary:
    """
    이벤트 요약 결과

    Attributes:
        summary: 한 줄 요약 (최대 50자)
        summary_type: 요약 유형
        keywords: 추출된 키워드
        fault_type: 감지된 유책사유
        confidence: 신뢰도
    """
    summary: str
    summary_type: SummaryType = SummaryType.CONVERSATION
    keywords: List[str] = None
    fault_type: Optional[str] = None
    confidence: float = 1.0

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "summary_type": self.summary_type.value,
            "keywords": self.keywords,
            "fault_type": self.fault_type,
            "confidence": self.confidence,
        }


# =============================================================================
# 요약 패턴 정의
# =============================================================================

# 유책사유별 요약 템플릿
FAULT_TYPE_TEMPLATES = {
    "adultery": {
        "label": "외도",
        "templates": [
            "배우자 외도 관련 {source}",
            "불륜 정황 {source}",
            "부정행위 관련 {source}",
        ],
        "keywords": ["외도", "바람", "불륜", "부정행위", "다른 사람", "만남"],
    },
    "violence": {
        "label": "폭력",
        "templates": [
            "가정폭력 관련 {source}",
            "폭행 {source}",
            "물리적 폭력 {source}",
        ],
        "keywords": ["폭행", "때리다", "맞다", "폭력", "상해", "멍", "피"],
    },
    "verbal_abuse": {
        "label": "폭언",
        "templates": [
            "폭언 {source}",
            "언어폭력 {source}",
            "정서적 학대 {source}",
        ],
        "keywords": ["욕", "폭언", "모욕", "무시", "비하", "협박"],
    },
    "economic_abuse": {
        "label": "경제적 학대",
        "templates": [
            "경제적 학대 관련 {source}",
            "생활비 관련 {source}",
            "재산 은닉 관련 {source}",
        ],
        "keywords": ["생활비", "돈", "재산", "은닉", "통장", "계좌"],
    },
    "desertion": {
        "label": "유기",
        "templates": [
            "악의의 유기 관련 {source}",
            "가출/별거 {source}",
            "연락 두절 {source}",
        ],
        "keywords": ["가출", "별거", "연락", "두절", "유기", "버림"],
    },
    "child_abuse": {
        "label": "자녀 학대",
        "templates": [
            "자녀 관련 {source}",
            "양육 문제 {source}",
            "아동 학대 관련 {source}",
        ],
        "keywords": ["아이", "자녀", "양육", "학대", "아동"],
    },
    "financial_misconduct": {
        "label": "재정 비행",
        "templates": [
            "도박/채무 관련 {source}",
            "재정 문제 {source}",
            "재산 탕진 {source}",
        ],
        "keywords": ["도박", "빚", "채무", "탕진", "낭비"],
    },
}

# 소스 유형별 접미사
SOURCE_TYPE_SUFFIX = {
    "chat_log": "대화",
    "kakaotalk": "대화",
    "message": "메시지",
    "photo": "사진 증거",
    "image": "이미지",
    "video": "영상 증거",
    "recording": "녹음 증거",
    "audio": "음성",
    "document": "문서",
    "pdf": "문서",
    "medical_record": "진단서",
    "police_report": "신고 기록",
    "bank_statement": "금융 거래 내역",
    "witness": "진술서",
}

# 감정 키워드 → 요약
EMOTION_PATTERNS = {
    "anger": {
        "keywords": ["화나", "짜증", "열받", "분노", "빡치"],
        "prefix": "갈등 상황",
    },
    "sadness": {
        "keywords": ["슬프", "우울", "힘들", "괴롭", "눈물"],
        "prefix": "정서적 고충",
    },
    "fear": {
        "keywords": ["무섭", "두렵", "불안", "걱정"],
        "prefix": "불안/공포 상황",
    },
}


# =============================================================================
# EventSummarizer 클래스
# =============================================================================

class EventSummarizer:
    """
    이벤트 한 줄 요약 생성기

    증거 내용을 분석하여 최대 50자의 한 줄 요약을 생성합니다.

    Usage:
        summarizer = EventSummarizer()

        # 기본 사용
        result = summarizer.summarize("남편이 또 바람을 피웠어요")

        # 유책사유 힌트 제공
        result = summarizer.summarize(
            content="...",
            fault_types=["adultery"],
            source_type="chat_log"
        )
    """

    MAX_SUMMARY_LENGTH = 50

    def __init__(self, max_length: int = None):
        """
        EventSummarizer 초기화

        Args:
            max_length: 요약 최대 길이 (기본값: 50자)
        """
        self.max_length = max_length or self.MAX_SUMMARY_LENGTH

    def summarize(
        self,
        content: str,
        fault_types: List[str] = None,
        source_type: str = None,
        speaker: str = None,
    ) -> EventSummary:
        """
        이벤트 한 줄 요약 생성

        Args:
            content: 원본 내용
            fault_types: 유책사유 힌트 (예: ["adultery", "violence"])
            source_type: 소스 유형 (예: "chat_log", "photo")
            speaker: 발화자/작성자

        Returns:
            EventSummary: 요약 결과
        """
        if not content or not content.strip():
            return EventSummary(
                summary="내용 없음",
                summary_type=SummaryType.EVIDENCE,
                confidence=0.5,
            )

        content = content.strip()

        # 1. 유책사유 기반 요약 시도
        if fault_types:
            result = self._summarize_by_fault_type(
                content, fault_types, source_type
            )
            if result:
                return result

        # 2. 키워드 기반 유책사유 감지
        detected_fault = self._detect_fault_type(content)
        if detected_fault:
            result = self._summarize_by_fault_type(
                content, [detected_fault], source_type
            )
            if result:
                result.confidence = 0.8  # 자동 감지는 신뢰도 낮춤
                return result

        # 3. 감정 기반 요약
        emotion_result = self._summarize_by_emotion(content, source_type)
        if emotion_result:
            return emotion_result

        # 4. 기본 요약 (내용 축약)
        return self._create_default_summary(content, source_type, speaker)

    def summarize_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> List[EventSummary]:
        """
        여러 이벤트 일괄 요약

        Args:
            items: 이벤트 목록
                [{"content": "...", "fault_types": [...], "source_type": "..."}]

        Returns:
            List[EventSummary]: 요약 목록
        """
        results = []
        for item in items:
            result = self.summarize(
                content=item.get("content", ""),
                fault_types=item.get("fault_types"),
                source_type=item.get("source_type"),
                speaker=item.get("speaker"),
            )
            results.append(result)
        return results

    def _summarize_by_fault_type(
        self,
        content: str,
        fault_types: List[str],
        source_type: str = None,
    ) -> Optional[EventSummary]:
        """유책사유 기반 요약"""
        for fault_type in fault_types:
            if fault_type not in FAULT_TYPE_TEMPLATES:
                continue

            template_info = FAULT_TYPE_TEMPLATES[fault_type]
            template = template_info["templates"][0]

            # 소스 유형 결정
            source_suffix = self._get_source_suffix(source_type)

            # 템플릿 적용
            summary = template.format(source=source_suffix)

            # 키워드 추출
            keywords = self._extract_keywords(content, template_info["keywords"])

            return EventSummary(
                summary=self._truncate(summary),
                summary_type=self._infer_summary_type(source_type),
                keywords=keywords,
                fault_type=fault_type,
                confidence=1.0,
            )

        return None

    def _detect_fault_type(self, content: str) -> Optional[str]:
        """내용에서 유책사유 자동 감지"""
        content_lower = content.lower()

        best_match = None
        best_score = 0

        for fault_type, info in FAULT_TYPE_TEMPLATES.items():
            score = 0
            for keyword in info["keywords"]:
                if keyword in content_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_match = fault_type

        # 최소 1개 키워드 매칭 필요
        return best_match if best_score >= 1 else None

    def _summarize_by_emotion(
        self,
        content: str,
        source_type: str = None,
    ) -> Optional[EventSummary]:
        """감정 키워드 기반 요약"""
        content_lower = content.lower()

        for emotion, info in EMOTION_PATTERNS.items():
            for keyword in info["keywords"]:
                if keyword in content_lower:
                    source_suffix = self._get_source_suffix(source_type)
                    summary = f"{info['prefix']} {source_suffix}"

                    return EventSummary(
                        summary=self._truncate(summary),
                        summary_type=SummaryType.CONVERSATION,
                        keywords=[keyword],
                        confidence=0.7,
                    )

        return None

    def _create_default_summary(
        self,
        content: str,
        source_type: str = None,
        speaker: str = None,
    ) -> EventSummary:
        """기본 요약 (내용 축약)"""
        # 첫 문장 또는 첫 줄 추출
        first_line = content.split("\n")[0].strip()

        # 문장 끝 찾기
        for end_char in [".", "!", "?"]:
            idx = first_line.find(end_char)
            if idx != -1 and idx < self.max_length:
                first_line = first_line[:idx + 1]
                break

        # 발화자 정보 추가
        if speaker:
            summary = f"[{speaker}] {first_line}"
        else:
            summary = first_line

        return EventSummary(
            summary=self._truncate(summary),
            summary_type=self._infer_summary_type(source_type),
            keywords=[],
            confidence=0.6,
        )

    def _get_source_suffix(self, source_type: str) -> str:
        """소스 유형에 따른 접미사"""
        if not source_type:
            return "내용"

        source_lower = source_type.lower()
        for key, suffix in SOURCE_TYPE_SUFFIX.items():
            if key in source_lower:
                return suffix

        return "내용"

    def _infer_summary_type(self, source_type: str) -> SummaryType:
        """소스 유형에서 요약 유형 추론"""
        if not source_type:
            return SummaryType.CONVERSATION

        source_lower = source_type.lower()

        if any(k in source_lower for k in ["chat", "message", "kakaotalk"]):
            return SummaryType.CONVERSATION
        elif any(k in source_lower for k in ["photo", "image", "video"]):
            return SummaryType.EVIDENCE
        elif any(k in source_lower for k in ["medical", "police", "record"]):
            return SummaryType.RECORD
        elif any(k in source_lower for k in ["bank", "financial", "statement"]):
            return SummaryType.FINANCIAL
        else:
            return SummaryType.CONVERSATION

    def _extract_keywords(
        self,
        content: str,
        target_keywords: List[str]
    ) -> List[str]:
        """내용에서 키워드 추출"""
        found = []
        content_lower = content.lower()

        for keyword in target_keywords:
            if keyword in content_lower and keyword not in found:
                found.append(keyword)

        return found[:5]  # 최대 5개

    def _truncate(self, text: str) -> str:
        """최대 길이로 자르기"""
        if len(text) <= self.max_length:
            return text
        return text[:self.max_length - 3] + "..."


# =============================================================================
# 간편 함수
# =============================================================================

def summarize_event(
    content: str,
    fault_types: List[str] = None,
    source_type: str = None,
) -> str:
    """
    이벤트 요약 간편 함수

    Args:
        content: 원본 내용
        fault_types: 유책사유 힌트
        source_type: 소스 유형

    Returns:
        str: 한 줄 요약
    """
    summarizer = EventSummarizer()
    result = summarizer.summarize(content, fault_types, source_type)
    return result.summary


def summarize_events_batch(
    items: List[Dict[str, Any]]
) -> List[str]:
    """
    여러 이벤트 일괄 요약 간편 함수

    Args:
        items: 이벤트 목록

    Returns:
        List[str]: 요약 목록
    """
    summarizer = EventSummarizer()
    results = summarizer.summarize_batch(items)
    return [r.summary for r in results]


# =============================================================================
# 모듈 export
# =============================================================================

__all__ = [
    "EventSummarizer",
    "EventSummary",
    "SummaryType",
    "summarize_event",
    "summarize_events_batch",
    "FAULT_TYPE_TEMPLATES",
]
