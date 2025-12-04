"""
Date Extractor - 날짜/시간 추출 유틸리티

다양한 형식의 날짜/시간 문자열을 파싱하고,
텍스트에서 날짜를 자동 추출합니다.

Usage:
    from src.utils.date_extractor import DateExtractor, extract_dates_from_text

    # 문자열 파싱
    extractor = DateExtractor()
    dt = extractor.parse("2024년 3월 15일 오후 2시 30분")

    # 텍스트에서 날짜 추출
    dates = extract_dates_from_text("어제 오후 3시에 만났습니다")
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# 데이터 클래스
# =============================================================================

@dataclass
class ExtractedDate:
    """
    추출된 날짜 정보

    Attributes:
        datetime_obj: 파싱된 datetime 객체
        original_text: 원본 텍스트
        confidence: 신뢰도 (0.0~1.0)
        format_type: 포맷 유형 (iso, korean, relative 등)
    """
    datetime_obj: datetime
    original_text: str
    confidence: float = 1.0
    format_type: str = "unknown"

    def to_dict(self):
        return {
            "datetime": self.datetime_obj.isoformat(),
            "original_text": self.original_text,
            "confidence": self.confidence,
            "format_type": self.format_type,
        }


# =============================================================================
# 날짜 형식 패턴
# =============================================================================

# 표준 날짜/시간 형식
DATETIME_FORMATS = [
    # ISO 형식
    ("%Y-%m-%dT%H:%M:%S", "iso"),
    ("%Y-%m-%d %H:%M:%S", "iso"),
    ("%Y-%m-%d %H:%M", "iso"),
    ("%Y-%m-%d", "iso"),

    # 슬래시 형식
    ("%Y/%m/%d %H:%M:%S", "slash"),
    ("%Y/%m/%d %H:%M", "slash"),
    ("%Y/%m/%d", "slash"),

    # 점 형식
    ("%Y.%m.%d %H:%M:%S", "dot"),
    ("%Y.%m.%d %H:%M", "dot"),
    ("%Y.%m.%d", "dot"),

    # 한국어 형식
    ("%Y년 %m월 %d일 %H시 %M분 %S초", "korean"),
    ("%Y년 %m월 %d일 %H시 %M분", "korean"),
    ("%Y년 %m월 %d일 %H:%M:%S", "korean"),
    ("%Y년 %m월 %d일 %H:%M", "korean"),
    ("%Y년 %m월 %d일", "korean"),

    # 미국 형식
    ("%m/%d/%Y %H:%M:%S", "us"),
    ("%m/%d/%Y %H:%M", "us"),
    ("%m/%d/%Y", "us"),

    # 유럽 형식
    ("%d/%m/%Y %H:%M:%S", "eu"),
    ("%d/%m/%Y %H:%M", "eu"),
    ("%d/%m/%Y", "eu"),

    # 카카오톡 형식
    ("%Y. %m. %d. %H:%M", "kakaotalk"),
    ("%Y. %m. %d.", "kakaotalk"),
]

# 텍스트에서 날짜 추출 패턴
DATE_PATTERNS = [
    # YYYY-MM-DD 형식
    (r"(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)", "iso"),

    # 한국어 형식
    (r"(\d{4}년\s*\d{1,2}월\s*\d{1,2}일(?:\s+\d{1,2}시\s*\d{1,2}분)?)", "korean"),

    # 오전/오후 포함 한국어 형식
    (r"(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\s+(?:오전|오후)\s*\d{1,2}:\d{2})", "korean_ampm"),

    # 월/일만 있는 형식 (올해로 추정)
    (r"(\d{1,2}월\s*\d{1,2}일(?:\s+\d{1,2}시\s*\d{1,2}분)?)", "korean_md"),
]

# 상대 날짜 패턴
RELATIVE_DATE_PATTERNS = {
    "오늘": 0,
    "어제": -1,
    "그저께": -2,
    "그끄저께": -3,
    "내일": 1,
    "모레": 2,
    "글피": 3,
    "지난주": -7,
    "저번주": -7,
    "다음주": 7,
    "이번주": 0,
    "지난달": -30,
    "저번달": -30,
    "다음달": 30,
    "이번달": 0,
}

# 시간대 패턴
TIME_PATTERNS = [
    r"(\d{1,2})시\s*(\d{1,2})분",
    r"(\d{1,2}):(\d{2})",
    r"(오전|오후)\s*(\d{1,2})시\s*(\d{1,2})분?",
    r"(오전|오후)\s*(\d{1,2}):(\d{2})",
]


# =============================================================================
# DateExtractor 클래스
# =============================================================================

class DateExtractor:
    """
    날짜/시간 추출기

    다양한 형식의 날짜/시간 문자열을 파싱합니다.

    Usage:
        extractor = DateExtractor()

        # 단순 파싱
        dt = extractor.parse("2024-03-15 14:30")

        # 한국어 오전/오후 포함
        dt = extractor.parse("2024년 3월 15일 오후 2시 30분")

        # 상대 날짜
        dt = extractor.parse("어제 오후 3시")
    """

    def __init__(self, default_year: int = None):
        """
        DateExtractor 초기화

        Args:
            default_year: 연도 미지정 시 기본값 (None이면 현재 연도)
        """
        self.default_year = default_year or datetime.now().year

    def parse(
        self,
        date_str: str,
        base_date: datetime = None
    ) -> Optional[datetime]:
        """
        날짜/시간 문자열 파싱

        Args:
            date_str: 날짜/시간 문자열
            base_date: 상대 날짜 계산 기준 (None이면 현재)

        Returns:
            datetime or None
        """
        if not date_str or not date_str.strip():
            return None

        date_str = date_str.strip()
        base = base_date or datetime.now()

        # 1. 상대 날짜 처리
        result = self._parse_relative_date(date_str, base)
        if result:
            return result

        # 2. 한국어 오전/오후 변환
        converted = self._convert_korean_ampm(date_str)

        # 3. 표준 형식 파싱 시도
        for fmt, _ in DATETIME_FORMATS:
            try:
                return datetime.strptime(converted, fmt)
            except ValueError:
                continue

        # 4. 월/일만 있는 경우 올해로 추정
        result = self._parse_month_day_only(date_str, base)
        if result:
            return result

        return None

    def parse_with_info(
        self,
        date_str: str,
        base_date: datetime = None
    ) -> Optional[ExtractedDate]:
        """
        날짜/시간 파싱 + 추가 정보 반환

        Args:
            date_str: 날짜/시간 문자열
            base_date: 상대 날짜 계산 기준

        Returns:
            ExtractedDate or None
        """
        if not date_str:
            return None

        date_str = date_str.strip()
        base = base_date or datetime.now()

        # 상대 날짜
        for keyword, offset in RELATIVE_DATE_PATTERNS.items():
            if keyword in date_str:
                dt = self._parse_relative_date(date_str, base)
                if dt:
                    return ExtractedDate(
                        datetime_obj=dt,
                        original_text=date_str,
                        confidence=0.8,
                        format_type="relative",
                    )

        # 한국어 오전/오후 변환
        converted = self._convert_korean_ampm(date_str)

        # 표준 형식
        for fmt, fmt_type in DATETIME_FORMATS:
            try:
                dt = datetime.strptime(converted, fmt)
                return ExtractedDate(
                    datetime_obj=dt,
                    original_text=date_str,
                    confidence=1.0,
                    format_type=fmt_type,
                )
            except ValueError:
                continue

        # 월/일만 있는 경우
        result = self._parse_month_day_only(date_str, base)
        if result:
            return ExtractedDate(
                datetime_obj=result,
                original_text=date_str,
                confidence=0.7,
                format_type="korean_md",
            )

        return None

    def _parse_relative_date(
        self,
        date_str: str,
        base: datetime
    ) -> Optional[datetime]:
        """상대 날짜 파싱 (어제, 지난주 등)"""
        for keyword, offset in RELATIVE_DATE_PATTERNS.items():
            if keyword in date_str:
                result_date = base + timedelta(days=offset)

                # 시간 정보 추출
                time_match = self._extract_time(date_str)
                if time_match:
                    hour, minute = time_match
                    result_date = result_date.replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )
                else:
                    result_date = result_date.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )

                return result_date

        return None

    def _parse_month_day_only(
        self,
        date_str: str,
        base: datetime
    ) -> Optional[datetime]:
        """월/일만 있는 날짜 파싱"""
        # "3월 15일" 또는 "3/15" 형식
        patterns = [
            r"(\d{1,2})월\s*(\d{1,2})일",
            r"(\d{1,2})/(\d{1,2})",
        ]

        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))

                if 1 <= month <= 12 and 1 <= day <= 31:
                    try:
                        result = datetime(self.default_year, month, day)

                        # 시간 정보 추출
                        time_match = self._extract_time(date_str)
                        if time_match:
                            hour, minute = time_match
                            result = result.replace(hour=hour, minute=minute)

                        return result
                    except ValueError:
                        pass

        return None

    def _extract_time(self, text: str) -> Optional[Tuple[int, int]]:
        """텍스트에서 시간 정보 추출"""
        # 오전/오후 + 시:분
        ampm_patterns = [
            r"(오전|오후)\s*(\d{1,2})시\s*(\d{1,2})분?",
            r"(오전|오후)\s*(\d{1,2}):(\d{2})",
        ]

        for pattern in ampm_patterns:
            match = re.search(pattern, text)
            if match:
                ampm = match.group(1)
                hour = int(match.group(2))
                minute = int(match.group(3)) if len(match.groups()) > 2 else 0

                # 오후 변환
                if ampm == "오후" and hour < 12:
                    hour += 12
                elif ampm == "오전" and hour == 12:
                    hour = 0

                return (hour, minute)

        # 일반 시:분
        patterns = [
            r"(\d{1,2})시\s*(\d{1,2})분",
            r"(\d{1,2}):(\d{2})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return (hour, minute)

        return None

    def _convert_korean_ampm(self, date_str: str) -> str:
        """한국어 오전/오후를 24시간 형식으로 변환"""
        result = date_str

        # "오후 2:30" → "14:30"
        ampm_pattern = r"(오전|오후)\s*(\d{1,2}):(\d{2})"
        match = re.search(ampm_pattern, result)
        if match:
            ampm, hour_str, minute = match.groups()
            hour = int(hour_str)

            if ampm == "오후" and hour < 12:
                hour += 12
            elif ampm == "오전" and hour == 12:
                hour = 0

            result = re.sub(ampm_pattern, f"{hour:02d}:{minute}", result)

        # "오후 2시 30분" → "14시 30분" (후속 파싱을 위해)
        ampm_korean_pattern = r"(오전|오후)\s*(\d{1,2})시\s*(\d{1,2})분?"
        match = re.search(ampm_korean_pattern, result)
        if match:
            ampm, hour_str = match.group(1), match.group(2)
            minute = match.group(3) if match.lastindex >= 3 else "00"
            hour = int(hour_str)

            if ampm == "오후" and hour < 12:
                hour += 12
            elif ampm == "오전" and hour == 12:
                hour = 0

            if minute:
                result = re.sub(ampm_korean_pattern, f"{hour:02d}:{minute}", result)
            else:
                result = re.sub(ampm_korean_pattern, f"{hour:02d}:00", result)

        return result


# =============================================================================
# 텍스트에서 날짜 추출
# =============================================================================

def extract_dates_from_text(
    text: str,
    base_date: datetime = None
) -> List[ExtractedDate]:
    """
    텍스트에서 날짜/시간 추출

    Args:
        text: 분석할 텍스트
        base_date: 상대 날짜 기준

    Returns:
        List[ExtractedDate]: 추출된 날짜 목록
    """
    if not text:
        return []

    extractor = DateExtractor()
    base = base_date or datetime.now()
    results = []
    seen = set()

    # 1. 정규식 패턴으로 날짜 추출
    for pattern, fmt_type in DATE_PATTERNS:
        for match in re.finditer(pattern, text):
            date_str = match.group(1)
            if date_str in seen:
                continue
            seen.add(date_str)

            extracted = extractor.parse_with_info(date_str, base)
            if extracted:
                extracted.format_type = fmt_type
                results.append(extracted)

    # 2. 상대 날짜 추출
    for keyword, offset in RELATIVE_DATE_PATTERNS.items():
        if keyword in text and keyword not in seen:
            seen.add(keyword)

            # 키워드 주변 텍스트에서 시간 정보 추출
            pattern = rf"{keyword}(?:\s+(?:오전|오후)?\s*\d{{1,2}}(?:시|:)\s*\d{{1,2}}분?)?"
            match = re.search(pattern, text)
            if match:
                full_match = match.group(0)
                extracted = extractor.parse_with_info(full_match, base)
                if extracted:
                    results.append(extracted)

    # 시간순 정렬
    results.sort(key=lambda x: x.datetime_obj)

    return results


# =============================================================================
# 간편 함수
# =============================================================================

def parse_date(date_str: str) -> Optional[datetime]:
    """날짜 파싱 간편 함수"""
    extractor = DateExtractor()
    return extractor.parse(date_str)


def parse_date_safe(date_str: str, default: datetime = None) -> datetime:
    """날짜 파싱 (실패 시 기본값 반환)"""
    result = parse_date(date_str)
    if result:
        return result
    return default or datetime.now()


# =============================================================================
# 모듈 export
# =============================================================================

__all__ = [
    "DateExtractor",
    "ExtractedDate",
    "extract_dates_from_text",
    "parse_date",
    "parse_date_safe",
    "DATETIME_FORMATS",
    "RELATIVE_DATE_PATTERNS",
]
