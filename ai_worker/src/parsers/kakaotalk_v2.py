"""
KakaoTalk Parser V2
카카오톡 대화 내보내기 파일 파서 - 법적 증거용

실제 카카오톡 내보내기 형식:
------------------------------
2023년 5월 10일 수요일
------------------------------
오전 9:23, 홍길동 : 오늘 몇시에 와?
오전 9:25, 김영희 : 7시쯤 갈 것 같아.

핵심 기능:
- 원본 라인 번호 추적 (법적 증거 인용용)
- 파싱 실패 라인 기록 (사람 검토용)
- 멀티라인 메시지 처리
"""

import re
import hashlib
from datetime import datetime, date
from typing import List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field

from src.schemas import (
    SourceLocation,
    FileType,
    EvidenceChunk,
    LegalAnalysis,
)


@dataclass
class ParsedMessage:
    """파싱된 메시지 (중간 결과)"""
    content: str
    sender: str
    timestamp: datetime
    line_number_start: int
    line_number_end: int
    raw_lines: List[str] = field(default_factory=list)


@dataclass
class ParsingResult:
    """파싱 결과"""
    messages: List[ParsedMessage]
    total_lines: int
    parsed_lines: int
    skipped_lines: List[int]
    error_lines: List[Tuple[int, str, str]]  # (line_num, line_content, error_reason)
    file_name: str


class KakaoTalkParserV2:
    """
    카카오톡 대화 파일 파서 V2

    실제 카카오톡 내보내기 형식을 정확히 파싱하고,
    모든 메시지에 원본 라인 번호를 기록합니다.

    Usage:
        parser = KakaoTalkParserV2()
        result = parser.parse("chat.txt")

        for msg in result.messages:
            print(f"Line {msg.line_number_start}: {msg.content}")
    """

    # ========================================
    # 정규표현식 패턴들
    # ========================================

    # 날짜 구분선: ----- 또는 ───── 등
    DATE_DIVIDER_PATTERN = re.compile(r'^[-─━═]{5,}$')

    # 날짜 라인: 2023년 5월 10일 수요일
    DATE_LINE_PATTERN = re.compile(
        r'^(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*([월화수목금토일]요일)?$'
    )

    # 메시지 라인: 오전 9:23, 홍길동 : 메시지 내용
    MESSAGE_PATTERN = re.compile(
        r'^(오전|오후)\s*(\d{1,2}):(\d{2}),\s*(.+?)\s*:\s*(.*)$'
    )

    # 시스템 메시지 패턴들
    SYSTEM_PATTERNS = [
        re.compile(r'^.+님이 들어왔습니다\.$'),
        re.compile(r'^.+님이 나갔습니다\.$'),
        re.compile(r'^.+님을 초대했습니다\.$'),
        re.compile(r'^채팅방 관리자가 메시지를 가렸습니다\.$'),
        re.compile(r'^삭제된 메시지입니다\.$'),
    ]

    # 헤더 키워드
    HEADER_KEYWORDS = [
        "카카오톡 대화",
        "저장한 날짜",
        "님과 카카오톡",
        "내보내기 한 날짜",
    ]

    def __init__(self):
        self.current_date: Optional[date] = None
        self.file_name: str = ""

    def parse(self, filepath: str) -> ParsingResult:
        """
        카카오톡 파일 파싱

        Args:
            filepath: 카카오톡 txt 파일 경로

        Returns:
            ParsingResult: 파싱 결과 (메시지 + 통계 + 오류)

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        self.file_name = path.name
        self.current_date = None

        messages: List[ParsedMessage] = []
        skipped_lines: List[int] = []
        error_lines: List[Tuple[int, str, str]] = []

        current_message: Optional[ParsedMessage] = None
        total_lines = 0
        parsed_lines = 0

        # 인코딩 시도 (UTF-8 우선, 실패시 CP949)
        encodings = ['utf-8', 'cp949', 'euc-kr']
        lines = []

        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue

        if not lines:
            raise ValueError(f"Could not decode file with encodings: {encodings}")

        for line_num, line in enumerate(lines, start=1):
            total_lines += 1
            line = line.rstrip('\n\r')

            # 빈 줄
            if not line.strip():
                skipped_lines.append(line_num)
                continue

            # 헤더 라인
            if self._is_header_line(line):
                skipped_lines.append(line_num)
                continue

            # 날짜 구분선 (-----)
            if self.DATE_DIVIDER_PATTERN.match(line.strip()):
                skipped_lines.append(line_num)
                continue

            # 날짜 라인 (2023년 5월 10일 수요일)
            date_match = self.DATE_LINE_PATTERN.match(line.strip())
            if date_match:
                year, month, day, _ = date_match.groups()
                self.current_date = date(int(year), int(month), int(day))
                skipped_lines.append(line_num)
                continue

            # 메시지 라인 (오전 9:23, 홍길동 : 내용)
            msg_match = self.MESSAGE_PATTERN.match(line)
            if msg_match:
                # 이전 메시지 저장
                if current_message:
                    messages.append(current_message)
                    parsed_lines += (current_message.line_number_end - current_message.line_number_start + 1)

                meridiem, hour, minute, sender, content = msg_match.groups()

                # 시간 계산
                timestamp = self._create_timestamp(
                    meridiem, int(hour), int(minute)
                )

                current_message = ParsedMessage(
                    content=content.strip(),
                    sender=sender.strip(),
                    timestamp=timestamp,
                    line_number_start=line_num,
                    line_number_end=line_num,
                    raw_lines=[line]
                )
                continue

            # 시스템 메시지 체크
            if self._is_system_message(line):
                # 시스템 메시지도 기록 (증거가 될 수 있음)
                if current_message:
                    messages.append(current_message)
                    parsed_lines += (current_message.line_number_end - current_message.line_number_start + 1)

                timestamp = self._create_timestamp("오전", 0, 0)  # 시간 불명
                current_message = ParsedMessage(
                    content=line.strip(),
                    sender="[시스템]",
                    timestamp=timestamp,
                    line_number_start=line_num,
                    line_number_end=line_num,
                    raw_lines=[line]
                )
                messages.append(current_message)
                parsed_lines += 1
                current_message = None
                continue

            # 멀티라인 메시지의 연속
            if current_message:
                current_message.content += "\n" + line.strip()
                current_message.line_number_end = line_num
                current_message.raw_lines.append(line)
                continue

            # 파싱 실패 (날짜 없이 시작된 메시지 등)
            if self.current_date is None:
                error_lines.append((line_num, line[:100], "날짜 정보 없음"))
            else:
                error_lines.append((line_num, line[:100], "패턴 불일치"))

        # 마지막 메시지 저장
        if current_message:
            messages.append(current_message)
            parsed_lines += (current_message.line_number_end - current_message.line_number_start + 1)

        return ParsingResult(
            messages=messages,
            total_lines=total_lines,
            parsed_lines=parsed_lines,
            skipped_lines=skipped_lines,
            error_lines=error_lines,
            file_name=self.file_name
        )

    def parse_to_chunks(
        self,
        filepath: str,
        case_id: str,
        file_id: str
    ) -> Tuple[List[EvidenceChunk], ParsingResult]:
        """
        파싱 후 EvidenceChunk 리스트로 변환

        Args:
            filepath: 파일 경로
            case_id: 케이스 ID
            file_id: 파일 ID

        Returns:
            Tuple[List[EvidenceChunk], ParsingResult]: 청크 리스트와 파싱 결과
        """
        result = self.parse(filepath)
        chunks: List[EvidenceChunk] = []

        for msg in result.messages:
            # 원본 위치 정보
            source_location = SourceLocation(
                file_name=result.file_name,
                file_type=FileType.KAKAOTALK,
                line_number=msg.line_number_start,
                line_number_end=msg.line_number_end if msg.line_number_end != msg.line_number_start else None
            )

            # 내용 해시
            content_hash = hashlib.sha256(msg.content.encode('utf-8')).hexdigest()[:16]

            chunk = EvidenceChunk(
                file_id=file_id,
                case_id=case_id,
                source_location=source_location,
                content=msg.content,
                content_hash=content_hash,
                sender=msg.sender,
                timestamp=msg.timestamp,
                legal_analysis=LegalAnalysis(),  # 나중에 분석
            )
            chunks.append(chunk)

        return chunks, result

    def _create_timestamp(self, meridiem: str, hour: int, minute: int) -> datetime:
        """타임스탬프 생성"""
        if self.current_date is None:
            # 날짜 정보 없으면 오늘 날짜 사용
            self.current_date = date.today()

        # 오전/오후 처리
        if meridiem == "오후" and hour != 12:
            hour += 12
        elif meridiem == "오전" and hour == 12:
            hour = 0

        return datetime(
            self.current_date.year,
            self.current_date.month,
            self.current_date.day,
            hour,
            minute
        )

    def _is_header_line(self, line: str) -> bool:
        """헤더 라인 여부"""
        return any(keyword in line for keyword in self.HEADER_KEYWORDS)

    def _is_system_message(self, line: str) -> bool:
        """시스템 메시지 여부"""
        line_stripped = line.strip()

        # 패턴 매칭
        for pattern in self.SYSTEM_PATTERNS:
            if pattern.match(line_stripped):
                return True

        # 단일 키워드 (사진, 동영상 등)
        single_keywords = ["사진", "동영상", "이모티콘", "파일", "음성메시지", "삭제된 메시지입니다."]
        if line_stripped in single_keywords:
            return True

        return False


# 하위 호환성을 위한 래퍼
def parse_kakaotalk(filepath: str) -> ParsingResult:
    """카카오톡 파일 파싱 (간편 함수)"""
    parser = KakaoTalkParserV2()
    return parser.parse(filepath)
