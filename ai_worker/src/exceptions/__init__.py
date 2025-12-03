"""
AI Worker 커스텀 예외 계층

모든 파서/분석 예외의 기본 클래스와 특화 예외 정의

Usage:
    from src.exceptions import ParserError, EncodingError, ParseError

    try:
        parser.parse(file)
    except EncodingError as e:
        logger.error(f"인코딩 실패: {e.context.encoding_attempted}")
    except ParseError as e:
        if e.partial_result:
            # 부분 결과 사용
            pass
"""

from dataclasses import dataclass, field
from typing import Optional, Any, List
from pathlib import Path


@dataclass
class ErrorContext:
    """
    에러 발생 컨텍스트 정보

    디버깅 및 로깅을 위한 상세 정보 저장
    """
    file_path: Optional[Path] = None
    file_name: Optional[str] = None
    line_number: Optional[int] = None
    page_number: Optional[int] = None
    encoding_attempted: Optional[str] = None
    encoding_detected: Optional[str] = None
    raw_content: Optional[str] = None  # 문제된 원본 내용 (일부)
    additional_info: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """로깅용 딕셔너리 변환"""
        return {
            "file_path": str(self.file_path) if self.file_path else None,
            "file_name": self.file_name,
            "line_number": self.line_number,
            "page_number": self.page_number,
            "encoding_attempted": self.encoding_attempted,
            "encoding_detected": self.encoding_detected,
            "raw_content": self.raw_content[:100] if self.raw_content else None,
            **self.additional_info
        }


class ParserError(Exception):
    """
    모든 파서 에러의 기본 클래스

    Attributes:
        message: 에러 메시지
        context: 에러 발생 컨텍스트
        recoverable: 복구 가능 여부 (부분 결과 사용 가능)
        original_error: 원본 예외 (체이닝용)
    """

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        recoverable: bool = False,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext()
        self.recoverable = recoverable
        self.original_error = original_error

    def __str__(self) -> str:
        base = self.message
        if self.context.file_name:
            base = f"[{self.context.file_name}] {base}"
        if self.context.line_number:
            base = f"{base} (line {self.context.line_number})"
        return base

    def to_log_dict(self) -> dict:
        """구조화 로깅용 딕셔너리"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "recoverable": self.recoverable,
            "context": self.context.to_dict(),
            "original_error": str(self.original_error) if self.original_error else None
        }


class EncodingError(ParserError):
    """
    인코딩 감지/디코딩 실패

    한국어 파일 처리 시 utf-8, cp949, euc-kr 등 다양한 인코딩 시도 후 실패
    """

    def __init__(
        self,
        message: str,
        attempted_encodings: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(message, recoverable=False, **kwargs)
        self.attempted_encodings = attempted_encodings or []
        if self.attempted_encodings:
            self.context.additional_info["attempted_encodings"] = self.attempted_encodings


class FileCorruptionError(ParserError):
    """
    파일 손상 에러

    - PDF 구조 손상
    - 이미지 헤더 손상
    - 오디오 코덱 오류
    """

    def __init__(self, message: str, corruption_type: Optional[str] = None, **kwargs):
        super().__init__(message, recoverable=False, **kwargs)
        self.corruption_type = corruption_type
        if corruption_type:
            self.context.additional_info["corruption_type"] = corruption_type


class ParseError(ParserError):
    """
    파싱 실패 (부분 결과 포함 가능)

    전체 파싱은 실패했지만 부분적으로 파싱된 결과가 있을 수 있음

    Attributes:
        partial_result: 부분적으로 파싱된 결과
        failed_lines: 파싱 실패한 라인 번호들
    """

    def __init__(
        self,
        message: str,
        partial_result: Any = None,
        failed_lines: Optional[List[int]] = None,
        **kwargs
    ):
        super().__init__(message, recoverable=True, **kwargs)
        self.partial_result = partial_result
        self.failed_lines = failed_lines or []
        if self.failed_lines:
            self.context.additional_info["failed_lines"] = self.failed_lines


class ValidationError(ParserError):
    """
    Pydantic 검증 실패

    스키마 검증 실패 시 발생
    """

    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[dict]] = None,
        **kwargs
    ):
        super().__init__(message, recoverable=False, **kwargs)
        self.validation_errors = validation_errors or []
        if self.validation_errors:
            self.context.additional_info["validation_errors"] = self.validation_errors


class AnalysisError(ParserError):
    """
    분석 실패 에러

    - AI API 호출 실패
    - 키워드 매칭 오류
    - 신뢰도 계산 오류
    """

    def __init__(
        self,
        message: str,
        analysis_type: Optional[str] = None,  # "ai", "keyword", "scoring"
        fallback_available: bool = True,
        **kwargs
    ):
        super().__init__(message, recoverable=fallback_available, **kwargs)
        self.analysis_type = analysis_type
        self.fallback_available = fallback_available
        if analysis_type:
            self.context.additional_info["analysis_type"] = analysis_type


class StorageError(ParserError):
    """
    저장소 관련 에러

    - Qdrant 연결 실패
    - 임베딩 생성 실패
    - 인덱싱 실패
    """

    def __init__(
        self,
        message: str,
        storage_type: Optional[str] = None,  # "qdrant", "embedding", "indexing"
        **kwargs
    ):
        super().__init__(message, recoverable=False, **kwargs)
        self.storage_type = storage_type
        if storage_type:
            self.context.additional_info["storage_type"] = storage_type


# 편의를 위한 예외 생성 헬퍼 함수
def create_encoding_error(
    file_path: Path,
    attempted_encodings: List[str],
    original_error: Optional[Exception] = None
) -> EncodingError:
    """인코딩 에러 생성 헬퍼"""
    context = ErrorContext(
        file_path=file_path,
        file_name=file_path.name if file_path else None
    )
    return EncodingError(
        message=f"파일 인코딩 감지 실패: {attempted_encodings}",
        attempted_encodings=attempted_encodings,
        context=context,
        original_error=original_error
    )


def create_parse_error(
    file_path: Path,
    line_number: Optional[int] = None,
    partial_result: Any = None,
    failed_lines: Optional[List[int]] = None,
    original_error: Optional[Exception] = None
) -> ParseError:
    """파싱 에러 생성 헬퍼"""
    context = ErrorContext(
        file_path=file_path,
        file_name=file_path.name if file_path else None,
        line_number=line_number
    )
    return ParseError(
        message=f"파싱 실패: {file_path.name}" if file_path else "파싱 실패",
        partial_result=partial_result,
        failed_lines=failed_lines,
        context=context,
        original_error=original_error
    )


# 모듈 export
__all__ = [
    "ErrorContext",
    "ParserError",
    "EncodingError",
    "FileCorruptionError",
    "ParseError",
    "ValidationError",
    "AnalysisError",
    "StorageError",
    "create_encoding_error",
    "create_parse_error",
]
