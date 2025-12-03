"""
구조화된 로깅 유틸리티

JSON 형식 로깅으로 파서/분석 이벤트 추적

Features:
- JSON 포맷 로그 출력
- 파서별 컨텍스트 정보 포함
- 에러 정보 구조화
- 성능 메트릭 로깅

Usage:
    from src.utils.logging import setup_logging, get_logger

    setup_logging(level="INFO", json_output=True)
    logger = get_logger("parser.kakaotalk")
    logger.info("파싱 시작", extra={"file": "test.txt", "lines": 100})
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from functools import wraps
import time


class JSONFormatter(logging.Formatter):
    """
    JSON 형식 로그 포매터

    구조화된 로그 출력으로 로그 분석 및 모니터링 용이
    """

    def __init__(self, include_timestamp: bool = True, include_extra: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if self.include_timestamp:
            log_data["timestamp"] = datetime.now(timezone.utc).isoformat()

        # 모듈/함수 정보
        log_data["module"] = record.module
        log_data["function"] = record.funcName
        log_data["line"] = record.lineno

        # 예외 정보
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }

        # extra 필드 추가 (logging.info(..., extra={...}))
        if self.include_extra:
            # 기본 LogRecord 속성 제외
            default_attrs = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                'taskName', 'message'
            }
            extra_data = {
                k: v for k, v in record.__dict__.items()
                if k not in default_attrs and not k.startswith('_')
            }
            if extra_data:
                log_data["extra"] = extra_data

        return json.dumps(log_data, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    콘솔용 컬러 포매터

    개발 환경에서 가독성 좋은 출력
    """

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 기본 메시지
        message = f"{color}[{timestamp}] {record.levelname:8}{self.RESET} {record.name}: {record.getMessage()}"

        # extra 필드 표시
        default_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'pathname', 'process', 'processName', 'relativeCreated',
            'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
            'taskName', 'message'
        }
        extra_data = {
            k: v for k, v in record.__dict__.items()
            if k not in default_attrs and not k.startswith('_')
        }
        if extra_data:
            extra_str = ' '.join(f"{k}={v}" for k, v in extra_data.items())
            message += f" | {extra_str}"

        return message


@dataclass
class ParserLogContext:
    """파서 로깅용 컨텍스트"""
    parser_name: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    case_id: Optional[str] = None
    total_lines: Optional[int] = None
    parsed_lines: Optional[int] = None
    error_count: Optional[int] = None
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AnalysisLogContext:
    """분석 로깅용 컨텍스트"""
    analyzer_name: str
    chunk_id: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None
    method: Optional[str] = None  # "keyword", "ai", "hybrid"
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


def setup_logging(
    level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[Path] = None
) -> None:
    """
    로깅 설정

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: JSON 형식 출력 여부
        log_file: 로그 파일 경로 (None이면 콘솔만)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    if json_output:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ConsoleFormatter())
    root_logger.addHandler(console_handler)

    # 파일 핸들러 (선택)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(JSONFormatter())  # 파일은 항상 JSON
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    로거 가져오기

    Args:
        name: 로거 이름 (예: "parser.kakaotalk", "analysis.legal")

    Returns:
        logging.Logger
    """
    return logging.getLogger(name)


def log_parser_start(logger: logging.Logger, context: ParserLogContext) -> None:
    """파서 시작 로깅"""
    logger.info(
        f"파싱 시작: {context.file_name}",
        extra=context.to_dict()
    )


def log_parser_complete(logger: logging.Logger, context: ParserLogContext) -> None:
    """파서 완료 로깅"""
    logger.info(
        f"파싱 완료: {context.file_name} ({context.parsed_lines}/{context.total_lines} lines)",
        extra=context.to_dict()
    )


def log_parser_error(
    logger: logging.Logger,
    context: ParserLogContext,
    error: Exception
) -> None:
    """파서 에러 로깅"""
    extra = context.to_dict()
    extra["error_type"] = type(error).__name__
    extra["error_message"] = str(error)

    logger.error(
        f"파싱 에러: {context.file_name} - {error}",
        extra=extra,
        exc_info=True
    )


def log_analysis_complete(logger: logging.Logger, context: AnalysisLogContext) -> None:
    """분석 완료 로깅"""
    logger.info(
        f"분석 완료: {context.category} (confidence={context.confidence})",
        extra=context.to_dict()
    )


def log_with_timing(logger: logging.Logger):
    """
    실행 시간 측정 데코레이터

    Usage:
        @log_with_timing(logger)
        def parse_file(path):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.debug(
                    f"{func.__name__} 완료",
                    extra={"duration_ms": round(duration_ms, 2)}
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"{func.__name__} 실패",
                    extra={
                        "duration_ms": round(duration_ms, 2),
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


# 로깅 설정 딕셔너리 (advanced 사용 시)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JSONFormatter,
        },
        "console": {
            "()": ConsoleFormatter,
        },
    },
    "handlers": {
        "console_json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
        "console_pretty": {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "parser": {
            "level": "INFO",
            "handlers": ["console_pretty"],
            "propagate": False,
        },
        "analysis": {
            "level": "INFO",
            "handlers": ["console_pretty"],
            "propagate": False,
        },
        "storage": {
            "level": "INFO",
            "handlers": ["console_pretty"],
            "propagate": False,
        },
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console_pretty"],
    },
}


# 편의를 위한 export
__all__ = [
    "JSONFormatter",
    "ConsoleFormatter",
    "ParserLogContext",
    "AnalysisLogContext",
    "setup_logging",
    "get_logger",
    "log_parser_start",
    "log_parser_complete",
    "log_parser_error",
    "log_analysis_complete",
    "log_with_timing",
    "LOGGING_CONFIG",
]
