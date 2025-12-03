"""
커스텀 예외 계층 테스트

Given: 다양한 에러 상황
When: 커스텀 예외 발생
Then: 적절한 컨텍스트와 복구 가능 여부 확인
"""

import unittest
from pathlib import Path

from src.exceptions import (
    ErrorContext,
    ParserError,
    EncodingError,
    FileCorruptionError,
    ParseError,
    ValidationError,
    AnalysisError,
    StorageError,
    create_encoding_error,
    create_parse_error,
)


class TestErrorContext(unittest.TestCase):
    """ErrorContext 테스트"""

    def test_empty_context(self):
        """Given: 빈 컨텍스트
        When: ErrorContext 생성
        Then: 모든 필드 None"""
        context = ErrorContext()
        self.assertIsNone(context.file_path)
        self.assertIsNone(context.line_number)

    def test_context_with_file(self):
        """Given: 파일 정보
        When: ErrorContext 생성
        Then: 파일 정보 저장"""
        context = ErrorContext(
            file_path=Path("/test/file.txt"),
            file_name="file.txt",
            line_number=42
        )
        self.assertEqual(context.file_name, "file.txt")
        self.assertEqual(context.line_number, 42)

    def test_context_to_dict(self):
        """Given: 컨텍스트 정보
        When: to_dict() 호출
        Then: 딕셔너리로 변환"""
        context = ErrorContext(
            file_name="test.txt",
            line_number=10,
            encoding_attempted="utf-8"
        )
        result = context.to_dict()
        self.assertEqual(result["file_name"], "test.txt")
        self.assertEqual(result["line_number"], 10)
        self.assertEqual(result["encoding_attempted"], "utf-8")

    def test_context_raw_content_truncation(self):
        """Given: 긴 raw_content
        When: to_dict() 호출
        Then: 100자로 잘림"""
        long_content = "A" * 200
        context = ErrorContext(raw_content=long_content)
        result = context.to_dict()
        self.assertEqual(len(result["raw_content"]), 100)


class TestParserError(unittest.TestCase):
    """ParserError 기본 클래스 테스트"""

    def test_basic_error(self):
        """Given: 에러 메시지
        When: ParserError 생성
        Then: 메시지 저장"""
        error = ParserError("테스트 에러")
        self.assertEqual(error.message, "테스트 에러")
        self.assertFalse(error.recoverable)

    def test_error_with_context(self):
        """Given: 컨텍스트 정보
        When: ParserError 생성
        Then: 컨텍스트 저장"""
        context = ErrorContext(file_name="test.txt", line_number=10)
        error = ParserError("에러", context=context)
        self.assertEqual(error.context.file_name, "test.txt")

    def test_error_str_with_file(self):
        """Given: 파일명 포함 컨텍스트
        When: str() 호출
        Then: 파일명 포함"""
        context = ErrorContext(file_name="test.txt")
        error = ParserError("에러 발생", context=context)
        self.assertIn("test.txt", str(error))

    def test_error_str_with_line(self):
        """Given: 라인번호 포함 컨텍스트
        When: str() 호출
        Then: 라인번호 포함"""
        context = ErrorContext(file_name="test.txt", line_number=42)
        error = ParserError("에러", context=context)
        self.assertIn("line 42", str(error))

    def test_to_log_dict(self):
        """Given: ParserError
        When: to_log_dict() 호출
        Then: 로깅용 딕셔너리 반환"""
        error = ParserError("테스트", recoverable=True)
        log_dict = error.to_log_dict()
        self.assertEqual(log_dict["error_type"], "ParserError")
        self.assertEqual(log_dict["message"], "테스트")
        self.assertTrue(log_dict["recoverable"])

    def test_error_chaining(self):
        """Given: 원본 예외
        When: ParserError 생성
        Then: 원본 예외 보존"""
        original = ValueError("원본 에러")
        error = ParserError("래핑 에러", original_error=original)
        self.assertEqual(error.original_error, original)


class TestEncodingError(unittest.TestCase):
    """EncodingError 테스트"""

    def test_encoding_error_basic(self):
        """Given: 인코딩 에러 상황
        When: EncodingError 생성
        Then: recoverable=False"""
        error = EncodingError("인코딩 실패")
        self.assertFalse(error.recoverable)

    def test_encoding_error_with_attempts(self):
        """Given: 시도한 인코딩 목록
        When: EncodingError 생성
        Then: 인코딩 목록 저장"""
        error = EncodingError(
            "인코딩 실패",
            attempted_encodings=["utf-8", "cp949", "euc-kr"]
        )
        self.assertEqual(len(error.attempted_encodings), 3)
        self.assertIn("utf-8", error.attempted_encodings)

    def test_encoding_error_in_context(self):
        """Given: 시도한 인코딩 목록
        When: to_log_dict() 호출
        Then: additional_info에 포함"""
        error = EncodingError("실패", attempted_encodings=["utf-8"])
        log_dict = error.to_log_dict()
        self.assertIn("attempted_encodings", log_dict["context"])


class TestFileCorruptionError(unittest.TestCase):
    """FileCorruptionError 테스트"""

    def test_corruption_error_basic(self):
        """Given: 파일 손상
        When: FileCorruptionError 생성
        Then: recoverable=False"""
        error = FileCorruptionError("파일 손상")
        self.assertFalse(error.recoverable)

    def test_corruption_type(self):
        """Given: 손상 유형
        When: FileCorruptionError 생성
        Then: 유형 저장"""
        error = FileCorruptionError("PDF 손상", corruption_type="pdf_structure")
        self.assertEqual(error.corruption_type, "pdf_structure")


class TestParseError(unittest.TestCase):
    """ParseError 테스트"""

    def test_parse_error_recoverable(self):
        """Given: 파싱 에러
        When: ParseError 생성
        Then: recoverable=True (기본값)"""
        error = ParseError("파싱 실패")
        self.assertTrue(error.recoverable)

    def test_parse_error_with_partial(self):
        """Given: 부분 결과
        When: ParseError 생성
        Then: 부분 결과 접근 가능"""
        partial = [{"line": 1, "content": "test"}]
        error = ParseError("일부 파싱 실패", partial_result=partial)
        self.assertEqual(len(error.partial_result), 1)

    def test_parse_error_with_failed_lines(self):
        """Given: 실패한 라인 목록
        When: ParseError 생성
        Then: 실패 라인 목록 저장"""
        error = ParseError("파싱 실패", failed_lines=[5, 10, 15])
        self.assertEqual(error.failed_lines, [5, 10, 15])


class TestValidationError(unittest.TestCase):
    """ValidationError 테스트"""

    def test_validation_error(self):
        """Given: 검증 실패
        When: ValidationError 생성
        Then: 검증 에러 목록 저장"""
        errors = [{"field": "name", "error": "required"}]
        error = ValidationError("검증 실패", validation_errors=errors)
        self.assertEqual(len(error.validation_errors), 1)
        self.assertFalse(error.recoverable)


class TestAnalysisError(unittest.TestCase):
    """AnalysisError 테스트"""

    def test_analysis_error_with_fallback(self):
        """Given: fallback 가능한 분석 에러
        When: AnalysisError 생성
        Then: recoverable=True"""
        error = AnalysisError("AI API 실패", fallback_available=True)
        self.assertTrue(error.recoverable)

    def test_analysis_error_type(self):
        """Given: 분석 유형
        When: AnalysisError 생성
        Then: 분석 유형 저장"""
        error = AnalysisError("실패", analysis_type="ai")
        self.assertEqual(error.analysis_type, "ai")


class TestStorageError(unittest.TestCase):
    """StorageError 테스트"""

    def test_storage_error(self):
        """Given: 저장소 에러
        When: StorageError 생성
        Then: recoverable=False"""
        error = StorageError("Qdrant 연결 실패", storage_type="qdrant")
        self.assertFalse(error.recoverable)
        self.assertEqual(error.storage_type, "qdrant")


class TestHelperFunctions(unittest.TestCase):
    """헬퍼 함수 테스트"""

    def test_create_encoding_error(self):
        """Given: 파일 경로와 인코딩 목록
        When: create_encoding_error() 호출
        Then: EncodingError 생성"""
        error = create_encoding_error(
            file_path=Path("/test/file.txt"),
            attempted_encodings=["utf-8", "cp949"]
        )
        self.assertIsInstance(error, EncodingError)
        self.assertEqual(error.context.file_name, "file.txt")

    def test_create_parse_error(self):
        """Given: 파일 경로와 부분 결과
        When: create_parse_error() 호출
        Then: ParseError 생성"""
        error = create_parse_error(
            file_path=Path("/test/file.txt"),
            line_number=42,
            partial_result=["partial"],
            failed_lines=[10, 20]
        )
        self.assertIsInstance(error, ParseError)
        self.assertEqual(error.context.line_number, 42)
        self.assertEqual(error.partial_result, ["partial"])


class TestExceptionHierarchy(unittest.TestCase):
    """예외 계층 구조 테스트"""

    def test_all_inherit_from_parser_error(self):
        """Given: 모든 커스텀 예외
        When: isinstance 체크
        Then: 모두 ParserError 상속"""
        exceptions = [
            EncodingError("test"),
            FileCorruptionError("test"),
            ParseError("test"),
            ValidationError("test"),
            AnalysisError("test"),
            StorageError("test"),
        ]
        for exc in exceptions:
            self.assertIsInstance(exc, ParserError)

    def test_catch_all_with_parser_error(self):
        """Given: 다양한 예외 발생
        When: ParserError로 catch
        Then: 모두 잡힘"""
        def raise_encoding():
            raise EncodingError("test")

        def raise_parse():
            raise ParseError("test")

        for func in [raise_encoding, raise_parse]:
            with self.assertRaises(ParserError):
                func()


if __name__ == "__main__":
    unittest.main()
