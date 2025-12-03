"""
인코딩 감지 및 처리 유틸리티

한국어 파일의 다양한 인코딩을 자동 감지하고 처리

지원 인코딩:
- UTF-8 (BOM 포함/미포함)
- CP949 (Windows 한국어)
- EUC-KR
- ISO-2022-KR

Usage:
    from src.utils.encoding import detect_encoding, read_file_with_encoding

    encoding, confidence = detect_encoding(file_path)
    content = read_file_with_encoding(file_path)
"""

from pathlib import Path
from typing import Tuple, Optional, List
from dataclasses import dataclass

from src.exceptions import create_encoding_error


# 한국어 인코딩 폴백 체인 (우선순위 순)
KOREAN_ENCODINGS = [
    'utf-8',
    'utf-8-sig',  # BOM 포함 UTF-8
    'cp949',      # Windows 한국어
    'euc-kr',
    'iso-2022-kr',
]

# BOM (Byte Order Mark) 시그니처
BOM_SIGNATURES = {
    b'\xef\xbb\xbf': 'utf-8-sig',
    b'\xff\xfe': 'utf-16-le',
    b'\xfe\xff': 'utf-16-be',
}


@dataclass
class EncodingResult:
    """인코딩 감지 결과"""
    encoding: str
    confidence: float  # 0.0 ~ 1.0
    method: str  # "bom", "charset_normalizer", "fallback", "heuristic"


def detect_bom(raw_data: bytes) -> Optional[str]:
    """
    BOM 시그니처로 인코딩 감지

    Args:
        raw_data: 파일의 바이트 데이터

    Returns:
        인코딩 문자열 또는 None
    """
    for bom, encoding in BOM_SIGNATURES.items():
        if raw_data.startswith(bom):
            return encoding
    return None


def detect_encoding_charset_normalizer(raw_data: bytes) -> Optional[EncodingResult]:
    """
    charset-normalizer 라이브러리로 인코딩 감지

    Args:
        raw_data: 파일의 바이트 데이터

    Returns:
        EncodingResult 또는 None
    """
    try:
        import charset_normalizer
        result = charset_normalizer.from_bytes(raw_data).best()
        if result:
            return EncodingResult(
                encoding=result.encoding,
                confidence=result.coherence,
                method="charset_normalizer"
            )
    except ImportError:
        pass  # charset-normalizer 미설치 시 폴백
    except Exception:
        pass
    return None


def detect_encoding_fallback(raw_data: bytes, encodings: List[str] = None) -> Optional[EncodingResult]:
    """
    폴백 체인으로 인코딩 감지 (디코딩 시도)

    Args:
        raw_data: 파일의 바이트 데이터
        encodings: 시도할 인코딩 목록

    Returns:
        EncodingResult 또는 None
    """
    encodings = encodings or KOREAN_ENCODINGS

    for encoding in encodings:
        try:
            raw_data.decode(encoding)
            # 디코딩 성공 - 폴백이므로 신뢰도 낮음
            return EncodingResult(
                encoding=encoding,
                confidence=0.5,
                method="fallback"
            )
        except (UnicodeDecodeError, LookupError):
            continue

    return None


def detect_encoding_heuristic(raw_data: bytes) -> EncodingResult:
    """
    휴리스틱 기반 인코딩 추정

    한국어 문자 패턴 분석으로 인코딩 추정

    Args:
        raw_data: 파일의 바이트 데이터

    Returns:
        EncodingResult (항상 결과 반환, 최후의 수단)
    """
    # 한글 바이트 패턴 분석
    # CP949: 0x81-0xFE 범위의 2바이트 시퀀스
    # UTF-8: 0xEA-0xED 범위의 3바이트 시퀀스 (한글)

    utf8_count = 0
    cp949_count = 0

    i = 0
    while i < len(raw_data) - 2:
        b = raw_data[i]

        # UTF-8 한글 패턴 (3바이트: 0xEA-0xED로 시작)
        if 0xEA <= b <= 0xED:
            if i + 2 < len(raw_data):
                if 0x80 <= raw_data[i+1] <= 0xBF and 0x80 <= raw_data[i+2] <= 0xBF:
                    utf8_count += 1
                    i += 3
                    continue

        # CP949 패턴 (2바이트: 0x81-0xFE로 시작)
        if 0x81 <= b <= 0xFE:
            if i + 1 < len(raw_data):
                next_b = raw_data[i+1]
                if 0x41 <= next_b <= 0xFE:
                    cp949_count += 1
                    i += 2
                    continue

        i += 1

    if utf8_count > cp949_count:
        return EncodingResult(encoding="utf-8", confidence=0.3, method="heuristic")
    elif cp949_count > 0:
        return EncodingResult(encoding="cp949", confidence=0.3, method="heuristic")
    else:
        # 최후의 수단: latin-1 (모든 바이트 디코딩 가능)
        return EncodingResult(encoding="latin-1", confidence=0.1, method="heuristic")


def detect_encoding(
    file_path: Path,
    sample_size: int = 100_000
) -> EncodingResult:
    """
    파일 인코딩 자동 감지

    감지 순서:
    1. BOM 체크
    2. charset-normalizer (설치된 경우)
    3. 한국어 인코딩 폴백 체인
    4. 휴리스틱 분석

    Args:
        file_path: 파일 경로
        sample_size: 샘플링할 바이트 수 (기본 100KB)

    Returns:
        EncodingResult: 감지된 인코딩과 신뢰도

    Raises:
        FileNotFoundError: 파일이 없을 때
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    with open(file_path, 'rb') as f:
        raw_data = f.read(sample_size)

    if not raw_data:
        # 빈 파일
        return EncodingResult(encoding="utf-8", confidence=1.0, method="empty_file")

    # 1. BOM 체크
    bom_encoding = detect_bom(raw_data)
    if bom_encoding:
        return EncodingResult(encoding=bom_encoding, confidence=1.0, method="bom")

    # 2. charset-normalizer
    result = detect_encoding_charset_normalizer(raw_data)
    if result and result.confidence > 0.7:
        return result

    # 3. 폴백 체인
    result = detect_encoding_fallback(raw_data)
    if result:
        return result

    # 4. 휴리스틱 (항상 결과 반환)
    return detect_encoding_heuristic(raw_data)


def read_file_with_encoding(
    file_path: Path,
    encoding: Optional[str] = None
) -> Tuple[str, EncodingResult]:
    """
    파일을 적절한 인코딩으로 읽기

    Args:
        file_path: 파일 경로
        encoding: 명시적 인코딩 (None이면 자동 감지)

    Returns:
        Tuple[str, EncodingResult]: (파일 내용, 인코딩 결과)

    Raises:
        EncodingError: 모든 인코딩 시도 실패 시
    """
    file_path = Path(file_path)

    if encoding:
        # 명시적 인코딩 사용
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, EncodingResult(encoding=encoding, confidence=1.0, method="explicit")
        except UnicodeDecodeError as e:
            raise create_encoding_error(
                file_path=file_path,
                attempted_encodings=[encoding],
                original_error=e
            )

    # 자동 감지
    encoding_result = detect_encoding(file_path)
    attempted = [encoding_result.encoding]

    try:
        with open(file_path, 'r', encoding=encoding_result.encoding) as f:
            content = f.read()
        return content, encoding_result
    except UnicodeDecodeError:
        pass

    # 감지된 인코딩 실패 시 폴백 시도
    for fallback_encoding in KOREAN_ENCODINGS:
        if fallback_encoding in attempted:
            continue
        attempted.append(fallback_encoding)

        try:
            with open(file_path, 'r', encoding=fallback_encoding) as f:
                content = f.read()
            return content, EncodingResult(
                encoding=fallback_encoding,
                confidence=0.4,
                method="fallback_read"
            )
        except UnicodeDecodeError:
            continue

    # 모든 시도 실패
    raise create_encoding_error(
        file_path=file_path,
        attempted_encodings=attempted
    )


def normalize_line_endings(content: str) -> str:
    """
    줄바꿈 문자 정규화 (모두 \n으로)

    Args:
        content: 원본 텍스트

    Returns:
        정규화된 텍스트
    """
    return content.replace('\r\n', '\n').replace('\r', '\n')


def remove_bom(content: str) -> str:
    """
    BOM 문자 제거

    Args:
        content: 원본 텍스트

    Returns:
        BOM 제거된 텍스트
    """
    if content.startswith('\ufeff'):
        return content[1:]
    return content


def clean_text(content: str) -> str:
    """
    텍스트 정리 (BOM 제거 + 줄바꿈 정규화)

    Args:
        content: 원본 텍스트

    Returns:
        정리된 텍스트
    """
    content = remove_bom(content)
    content = normalize_line_endings(content)
    return content


# 편의를 위한 export
__all__ = [
    "KOREAN_ENCODINGS",
    "EncodingResult",
    "detect_encoding",
    "read_file_with_encoding",
    "normalize_line_endings",
    "remove_bom",
    "clean_text",
]
