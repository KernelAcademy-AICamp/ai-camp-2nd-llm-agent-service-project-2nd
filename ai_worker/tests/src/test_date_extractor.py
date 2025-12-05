"""
DateExtractor 테스트

날짜/시간 추출 유틸리티 테스트
"""

from datetime import datetime

from src.utils.date_extractor import (
    DateExtractor,
    ExtractedDate,
    extract_dates_from_text,
    parse_date,
    parse_date_safe,
)


# =============================================================================
# DateExtractor 기본 테스트
# =============================================================================

class TestDateExtractorInit:
    """DateExtractor 초기화 테스트"""

    def test_default_init(self):
        """기본 초기화"""
        extractor = DateExtractor()
        assert extractor.default_year == datetime.now().year

    def test_custom_year(self):
        """커스텀 연도"""
        extractor = DateExtractor(default_year=2023)
        assert extractor.default_year == 2023


# =============================================================================
# ISO 형식 파싱 테스트
# =============================================================================

class TestISOFormat:
    """ISO 형식 날짜 파싱 테스트"""

    def test_iso_datetime(self):
        """YYYY-MM-DD HH:MM:SS"""
        extractor = DateExtractor()
        result = extractor.parse("2024-03-15 14:30:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30

    def test_iso_datetime_short(self):
        """YYYY-MM-DD HH:MM"""
        extractor = DateExtractor()
        result = extractor.parse("2024-03-15 14:30")
        assert result is not None
        assert result.hour == 14

    def test_iso_date_only(self):
        """YYYY-MM-DD"""
        extractor = DateExtractor()
        result = extractor.parse("2024-03-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15


# =============================================================================
# 한국어 형식 파싱 테스트
# =============================================================================

class TestKoreanFormat:
    """한국어 날짜 형식 파싱 테스트"""

    def test_korean_full(self):
        """YYYY년 MM월 DD일 HH시 MM분"""
        extractor = DateExtractor()
        result = extractor.parse("2024년 3월 15일 14시 30분")
        assert result is not None
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15

    def test_korean_date_only(self):
        """YYYY년 MM월 DD일"""
        extractor = DateExtractor()
        result = extractor.parse("2024년 3월 15일")
        assert result is not None
        assert result.year == 2024

    def test_korean_ampm_afternoon(self):
        """오후 시간"""
        extractor = DateExtractor()
        result = extractor.parse("2024-03-15 오후 2:30")
        assert result is not None
        assert result.hour == 14  # 오후 2시 → 14시

    def test_korean_ampm_morning(self):
        """오전 시간"""
        extractor = DateExtractor()
        result = extractor.parse("2024-03-15 오전 9:30")
        assert result is not None
        assert result.hour == 9

    def test_korean_ampm_noon(self):
        """오후 12시"""
        extractor = DateExtractor()
        result = extractor.parse("2024-03-15 오후 12:00")
        # 오후 12시는 12시 그대로
        assert result is not None

    def test_korean_ampm_midnight(self):
        """오전 12시"""
        extractor = DateExtractor()
        result = extractor.parse("2024-03-15 오전 12:30")
        assert result is not None
        assert result.hour == 0  # 오전 12시 → 0시


# =============================================================================
# 기타 형식 파싱 테스트
# =============================================================================

class TestOtherFormats:
    """기타 날짜 형식 파싱 테스트"""

    def test_slash_format(self):
        """슬래시 형식"""
        extractor = DateExtractor()
        result = extractor.parse("2024/03/15 14:30")
        assert result is not None
        assert result.year == 2024

    def test_dot_format(self):
        """점 형식"""
        extractor = DateExtractor()
        result = extractor.parse("2024.03.15 14:30")
        assert result is not None
        assert result.year == 2024

    def test_month_day_only(self):
        """월/일만 있는 형식"""
        extractor = DateExtractor(default_year=2024)
        result = extractor.parse("3월 15일")
        assert result is not None
        assert result.month == 3
        assert result.day == 15
        assert result.year == 2024


# =============================================================================
# 상대 날짜 파싱 테스트
# =============================================================================

class TestRelativeDate:
    """상대 날짜 파싱 테스트"""

    def test_yesterday(self):
        """어제"""
        extractor = DateExtractor()
        base = datetime(2024, 3, 15, 12, 0, 0)
        result = extractor.parse("어제", base_date=base)
        assert result is not None
        assert result.day == 14

    def test_today(self):
        """오늘"""
        extractor = DateExtractor()
        base = datetime(2024, 3, 15, 12, 0, 0)
        result = extractor.parse("오늘", base_date=base)
        assert result is not None
        assert result.day == 15

    def test_day_before_yesterday(self):
        """그저께"""
        extractor = DateExtractor()
        base = datetime(2024, 3, 15, 12, 0, 0)
        result = extractor.parse("그저께", base_date=base)
        assert result is not None
        assert result.day == 13

    def test_yesterday_with_time(self):
        """어제 + 시간"""
        extractor = DateExtractor()
        base = datetime(2024, 3, 15, 12, 0, 0)
        result = extractor.parse("어제 오후 3시 30분", base_date=base)
        assert result is not None
        assert result.day == 14
        assert result.hour == 15

    def test_last_week(self):
        """지난주"""
        extractor = DateExtractor()
        base = datetime(2024, 3, 15, 12, 0, 0)
        result = extractor.parse("지난주", base_date=base)
        assert result is not None
        assert result.day == 8  # 7일 전


# =============================================================================
# parse_with_info 테스트
# =============================================================================

class TestParseWithInfo:
    """parse_with_info 메서드 테스트"""

    def test_returns_extracted_date(self):
        """ExtractedDate 반환"""
        extractor = DateExtractor()
        result = extractor.parse_with_info("2024-03-15 14:30")
        assert result is not None
        assert isinstance(result, ExtractedDate)
        assert result.format_type == "iso"
        assert result.confidence == 1.0

    def test_relative_date_confidence(self):
        """상대 날짜 신뢰도"""
        extractor = DateExtractor()
        result = extractor.parse_with_info("어제")
        assert result is not None
        assert result.format_type == "relative"
        assert result.confidence < 1.0

    def test_month_day_confidence(self):
        """월/일만 있는 경우 신뢰도"""
        extractor = DateExtractor()
        result = extractor.parse_with_info("3월 15일")
        assert result is not None
        assert result.confidence < 1.0


# =============================================================================
# 텍스트에서 날짜 추출 테스트
# =============================================================================

class TestExtractDatesFromText:
    """extract_dates_from_text 함수 테스트"""

    def test_extract_single_date(self):
        """단일 날짜 추출"""
        text = "2024년 3월 15일에 만났습니다."
        results = extract_dates_from_text(text)
        assert len(results) >= 1

    def test_extract_multiple_dates(self):
        """여러 날짜 추출"""
        text = "2024-03-15에 시작해서 2024-03-20에 끝났습니다."
        results = extract_dates_from_text(text)
        assert len(results) >= 2

    def test_extract_relative_date(self):
        """상대 날짜 추출"""
        text = "어제 오후 3시에 만났습니다."
        results = extract_dates_from_text(text)
        assert len(results) >= 1

    def test_empty_text(self):
        """빈 텍스트"""
        results = extract_dates_from_text("")
        assert results == []

    def test_no_dates(self):
        """날짜 없는 텍스트"""
        results = extract_dates_from_text("안녕하세요")
        assert results == []


# =============================================================================
# 간편 함수 테스트
# =============================================================================

class TestConvenienceFunctions:
    """간편 함수 테스트"""

    def test_parse_date(self):
        """parse_date 함수"""
        result = parse_date("2024-03-15")
        assert result is not None
        assert result.year == 2024

    def test_parse_date_invalid(self):
        """parse_date 무효한 입력"""
        result = parse_date("invalid")
        assert result is None

    def test_parse_date_safe_valid(self):
        """parse_date_safe 유효한 입력"""
        result = parse_date_safe("2024-03-15")
        assert result.year == 2024

    def test_parse_date_safe_invalid(self):
        """parse_date_safe 무효한 입력 (기본값 반환)"""
        default = datetime(2024, 1, 1)
        result = parse_date_safe("invalid", default=default)
        assert result == default


# =============================================================================
# 엣지 케이스 테스트
# =============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_none_input(self):
        """None 입력"""
        extractor = DateExtractor()
        assert extractor.parse(None) is None

    def test_empty_string(self):
        """빈 문자열"""
        extractor = DateExtractor()
        assert extractor.parse("") is None

    def test_whitespace_only(self):
        """공백만 있는 문자열"""
        extractor = DateExtractor()
        assert extractor.parse("   ") is None

    def test_invalid_date(self):
        """무효한 날짜 (2월 30일)"""
        extractor = DateExtractor()
        result = extractor.parse("2024-02-30")
        assert result is None

    def test_partial_match(self):
        """부분 매칭"""
        extractor = DateExtractor()
        result = extractor.parse("날짜: 2024-03-15입니다")
        # 전체 문자열이 매칭되지 않으면 None
        # (extract_dates_from_text를 사용해야 함)
        assert result is None
