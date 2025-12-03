"""
구조화된 로깅 유틸리티 테스트

Given: 다양한 로깅 시나리오
When: 로그 출력
Then: 올바른 형식의 로그 생성
"""

import unittest
import logging
import json
import io

from src.utils.logging import (
    JSONFormatter,
    ConsoleFormatter,
    ParserLogContext,
    AnalysisLogContext,
    setup_logging,
    get_logger,
    log_parser_start,
    log_parser_complete,
    log_parser_error,
    log_with_timing,
    LOGGING_CONFIG,
)


class TestJSONFormatter(unittest.TestCase):
    """JSONFormatter 테스트"""

    def setUp(self):
        """각 테스트 전 로거 설정"""
        self.logger = logging.getLogger("test_json")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        self.stream = io.StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def test_basic_log_is_json(self):
        """Given: 기본 로그 메시지
        When: JSONFormatter로 출력
        Then: 유효한 JSON"""
        self.logger.info("테스트 메시지")
        output = self.stream.getvalue()
        data = json.loads(output)

        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["message"], "테스트 메시지")

    def test_log_contains_timestamp(self):
        """Given: 로그 메시지
        When: JSONFormatter로 출력
        Then: timestamp 포함"""
        self.logger.info("test")
        output = self.stream.getvalue()
        data = json.loads(output)

        self.assertIn("timestamp", data)

    def test_log_contains_module_info(self):
        """Given: 로그 메시지
        When: JSONFormatter로 출력
        Then: module, function, line 포함"""
        self.logger.info("test")
        output = self.stream.getvalue()
        data = json.loads(output)

        self.assertIn("module", data)
        self.assertIn("function", data)
        self.assertIn("line", data)

    def test_log_with_extra(self):
        """Given: extra 필드가 있는 로그
        When: JSONFormatter로 출력
        Then: extra 데이터 포함"""
        self.logger.info("파일 처리", extra={"file_name": "test.txt", "lines": 100})
        output = self.stream.getvalue()
        data = json.loads(output)

        self.assertIn("extra", data)
        self.assertEqual(data["extra"]["file_name"], "test.txt")
        self.assertEqual(data["extra"]["lines"], 100)

    def test_log_with_exception(self):
        """Given: 예외 정보가 있는 로그
        When: JSONFormatter로 출력
        Then: exception 정보 포함"""
        try:
            raise ValueError("테스트 에러")
        except Exception:
            self.logger.error("에러 발생", exc_info=True)

        output = self.stream.getvalue()
        data = json.loads(output)

        self.assertIn("exception", data)
        self.assertEqual(data["exception"]["type"], "ValueError")

    def test_korean_message(self):
        """Given: 한국어 메시지
        When: JSONFormatter로 출력
        Then: 올바르게 인코딩"""
        self.logger.info("안녕하세요 테스트입니다")
        output = self.stream.getvalue()
        data = json.loads(output)

        self.assertEqual(data["message"], "안녕하세요 테스트입니다")


class TestConsoleFormatter(unittest.TestCase):
    """ConsoleFormatter 테스트"""

    def setUp(self):
        self.logger = logging.getLogger("test_console")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        self.stream = io.StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(ConsoleFormatter())
        self.logger.addHandler(handler)

    def test_basic_format(self):
        """Given: 기본 로그 메시지
        When: ConsoleFormatter로 출력
        Then: 읽기 쉬운 형식"""
        self.logger.info("테스트 메시지")
        output = self.stream.getvalue()

        self.assertIn("INFO", output)
        self.assertIn("테스트 메시지", output)

    def test_extra_fields_shown(self):
        """Given: extra 필드가 있는 로그
        When: ConsoleFormatter로 출력
        Then: extra 필드 표시"""
        self.logger.info("파싱", extra={"file": "test.txt"})
        output = self.stream.getvalue()

        self.assertIn("file=test.txt", output)


class TestParserLogContext(unittest.TestCase):
    """ParserLogContext 테스트"""

    def test_to_dict_excludes_none(self):
        """Given: 일부 필드만 설정된 컨텍스트
        When: to_dict() 호출
        Then: None 값 제외"""
        context = ParserLogContext(
            parser_name="kakaotalk",
            file_name="test.txt"
        )
        data = context.to_dict()

        self.assertEqual(data["parser_name"], "kakaotalk")
        self.assertEqual(data["file_name"], "test.txt")
        self.assertNotIn("case_id", data)

    def test_full_context(self):
        """Given: 모든 필드 설정
        When: to_dict() 호출
        Then: 모든 필드 포함"""
        context = ParserLogContext(
            parser_name="kakaotalk",
            file_name="test.txt",
            file_type="kakaotalk",
            case_id="case_001",
            total_lines=100,
            parsed_lines=95,
            error_count=5,
            duration_ms=123.45
        )
        data = context.to_dict()

        self.assertEqual(len(data), 8)
        self.assertEqual(data["duration_ms"], 123.45)


class TestAnalysisLogContext(unittest.TestCase):
    """AnalysisLogContext 테스트"""

    def test_to_dict(self):
        """Given: 분석 컨텍스트
        When: to_dict() 호출
        Then: 딕셔너리 반환"""
        context = AnalysisLogContext(
            analyzer_name="legal",
            category="adultery",
            confidence=0.85,
            method="keyword"
        )
        data = context.to_dict()

        self.assertEqual(data["analyzer_name"], "legal")
        self.assertEqual(data["confidence"], 0.85)


class TestSetupLogging(unittest.TestCase):
    """setup_logging 테스트"""

    def tearDown(self):
        """테스트 후 루트 로거 정리"""
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)

    def test_setup_default(self):
        """Given: 기본 설정
        When: setup_logging() 호출
        Then: INFO 레벨, 콘솔 출력"""
        setup_logging()
        root = logging.getLogger()

        self.assertEqual(root.level, logging.INFO)
        self.assertEqual(len(root.handlers), 1)

    def test_setup_debug_level(self):
        """Given: DEBUG 레벨 지정
        When: setup_logging() 호출
        Then: DEBUG 레벨 설정"""
        setup_logging(level="DEBUG")
        root = logging.getLogger()

        self.assertEqual(root.level, logging.DEBUG)

    def test_setup_json_output(self):
        """Given: JSON 출력 활성화
        When: setup_logging() 호출
        Then: JSONFormatter 사용"""
        setup_logging(json_output=True)
        root = logging.getLogger()

        self.assertIsInstance(root.handlers[0].formatter, JSONFormatter)


class TestGetLogger(unittest.TestCase):
    """get_logger 테스트"""

    def test_get_named_logger(self):
        """Given: 로거 이름
        When: get_logger() 호출
        Then: 해당 이름의 로거 반환"""
        logger = get_logger("parser.kakaotalk")

        self.assertEqual(logger.name, "parser.kakaotalk")

    def test_logger_hierarchy(self):
        """Given: 계층적 로거 이름
        When: 로거 가져오기
        Then: 부모-자식 관계 유지"""
        get_logger("parser")  # ensure parent exists
        child = get_logger("parser.kakaotalk")

        self.assertEqual(child.parent.name, "parser")


class TestLogHelpers(unittest.TestCase):
    """로그 헬퍼 함수 테스트"""

    def setUp(self):
        self.logger = logging.getLogger("test_helpers")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        self.stream = io.StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def test_log_parser_start(self):
        """Given: 파서 컨텍스트
        When: log_parser_start() 호출
        Then: 시작 로그 출력"""
        context = ParserLogContext(
            parser_name="kakaotalk",
            file_name="test.txt"
        )
        log_parser_start(self.logger, context)
        output = self.stream.getvalue()

        self.assertIn("파싱 시작", output)
        self.assertIn("test.txt", output)

    def test_log_parser_complete(self):
        """Given: 완료된 파서 컨텍스트
        When: log_parser_complete() 호출
        Then: 완료 로그 출력"""
        context = ParserLogContext(
            parser_name="kakaotalk",
            file_name="test.txt",
            total_lines=100,
            parsed_lines=95
        )
        log_parser_complete(self.logger, context)
        output = self.stream.getvalue()

        self.assertIn("파싱 완료", output)
        self.assertIn("95/100", output)

    def test_log_parser_error(self):
        """Given: 에러 상황
        When: log_parser_error() 호출
        Then: 에러 로그 출력"""
        context = ParserLogContext(
            parser_name="kakaotalk",
            file_name="test.txt"
        )
        error = ValueError("테스트 에러")
        log_parser_error(self.logger, context, error)
        output = self.stream.getvalue()

        self.assertIn("파싱 에러", output)
        self.assertIn("ValueError", output)


class TestLogWithTiming(unittest.TestCase):
    """log_with_timing 데코레이터 테스트"""

    def setUp(self):
        self.logger = logging.getLogger("test_timing")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        self.stream = io.StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def test_timing_decorator_success(self):
        """Given: 성공하는 함수
        When: @log_with_timing 데코레이터 적용
        Then: 실행 시간 로깅"""
        @log_with_timing(self.logger)
        def sample_func():
            return "result"

        result = sample_func()

        self.assertEqual(result, "result")
        output = self.stream.getvalue()
        self.assertIn("duration_ms", output)

    def test_timing_decorator_error(self):
        """Given: 실패하는 함수
        When: @log_with_timing 데코레이터 적용
        Then: 에러 및 실행 시간 로깅"""
        @log_with_timing(self.logger)
        def failing_func():
            raise ValueError("실패")

        with self.assertRaises(ValueError):
            failing_func()

        output = self.stream.getvalue()
        self.assertIn("duration_ms", output)
        self.assertIn("실패", output)


class TestLoggingConfig(unittest.TestCase):
    """LOGGING_CONFIG 테스트"""

    def test_config_structure(self):
        """Given: LOGGING_CONFIG
        When: 구조 확인
        Then: 올바른 구조"""
        self.assertEqual(LOGGING_CONFIG["version"], 1)
        self.assertIn("formatters", LOGGING_CONFIG)
        self.assertIn("handlers", LOGGING_CONFIG)
        self.assertIn("loggers", LOGGING_CONFIG)

    def test_config_has_parser_logger(self):
        """Given: LOGGING_CONFIG
        When: loggers 확인
        Then: parser 로거 정의됨"""
        self.assertIn("parser", LOGGING_CONFIG["loggers"])
        self.assertIn("analysis", LOGGING_CONFIG["loggers"])


if __name__ == "__main__":
    unittest.main()
