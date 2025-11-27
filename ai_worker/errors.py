"""
Error Types for LEH AI Worker
Defines retryable and fatal error categories for proper DLQ routing
"""


class RetryableError(Exception):
    """
    재시도 가능한 에러 (Lambda 자동 재시도 유도)

    Examples:
        - 네트워크 타임아웃
        - 임시 서비스 장애
        - Rate limiting
        - 일시적 DB 연결 실패
    """

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error
        self.is_retryable = True


class FatalError(Exception):
    """
    재시도 불가능한 에러 (DLQ로 전송)

    Examples:
        - 파일 손상
        - 지원하지 않는 파일 형식
        - 파싱 실패 (잘못된 데이터 구조)
        - 인증/권한 오류
    """

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error
        self.is_retryable = False


class ParseError(FatalError):
    """파일 파싱 실패 에러"""
    pass


class UnsupportedFileTypeError(FatalError):
    """지원하지 않는 파일 형식 에러"""
    pass


class S3DownloadError(RetryableError):
    """S3 파일 다운로드 실패 에러"""
    pass


class EmbeddingError(RetryableError):
    """임베딩 생성 실패 에러"""
    pass


class StorageError(RetryableError):
    """스토리지(DB/Vector) 저장 실패 에러"""
    pass


class ValidationError(FatalError):
    """데이터 검증 실패 에러"""
    pass
