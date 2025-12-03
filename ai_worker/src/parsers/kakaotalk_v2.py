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
import csv
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
        카카오톡 파일 파싱 (TXT 또는 CSV)

        Args:
            filepath: 카카오톡 txt 또는 csv 파일 경로

        Returns:
            ParsingResult: 파싱 결과 (메시지 + 통계 + 오류)

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            ValueError: 지원하지 않는 파일 형식
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        self.file_name = path.name
        extension = path.suffix.lower()

        if extension == '.csv':
            return self._parse_csv(filepath)
        elif extension == '.txt':
            return self._parse_txt(filepath)
        else:
            raise ValueError(f"Unsupported file format: {extension}. Supported: .txt, .csv")

    def _parse_txt(self, filepath: str) -> ParsingResult:
        """
        카카오톡 TXT 파일 파싱

        Args:
            filepath: 카카오톡 txt 파일 경로

        Returns:
            ParsingResult: 파싱 결과 (메시지 + 통계 + 오류)
        """
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

    def _parse_csv(self, filepath: str) -> ParsingResult:
        """
        카카오톡 CSV 파일 파싱

        지원하는 CSV 형식:
        - 날짜, 시간, 발신자, 메시지 (또는 유사한 컬럼명)
        - Date, Time, User, Message

        Args:
            filepath: 카카오톡 csv 파일 경로

        Returns:
            ParsingResult: 파싱 결과 (메시지 + 통계 + 오류)
        """
        self.current_date = None

        messages: List[ParsedMessage] = []
        skipped_lines: List[int] = []
        error_lines: List[Tuple[int, str, str]] = []

        total_lines = 0
        parsed_lines = 0

        # 인코딩 시도 (UTF-8 우선, 실패시 CP949)
        encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
        rows = []
        headers = []

        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding, newline='') as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])
                    rows = list(reader)
                break
            except (UnicodeDecodeError, csv.Error):
                continue

        if not headers:
            raise ValueError(f"Could not decode CSV file with encodings: {encodings}")

        # 컬럼 인덱스 매핑 (다양한 컬럼명 지원)
        col_map = self._detect_csv_columns(headers)

        if col_map['message'] == -1:
            raise ValueError(f"Required column 'message' not found. Headers: {headers}")

        total_lines = len(rows) + 1  # +1 for header

        for row_num, row in enumerate(rows, start=2):  # start=2 because row 1 is header
            try:
                # 빈 행 스킵
                if not row or all(not cell.strip() for cell in row):
                    skipped_lines.append(row_num)
                    continue

                # 메시지 내용 추출
                message_content = row[col_map['message']].strip() if col_map['message'] < len(row) else ""

                if not message_content:
                    skipped_lines.append(row_num)
                    continue

                # 발신자 추출
                sender = "[알 수 없음]"
                if col_map['sender'] != -1 and col_map['sender'] < len(row):
                    sender = row[col_map['sender']].strip() or "[알 수 없음]"

                # 타임스탬프 추출
                timestamp = self._parse_csv_timestamp(row, col_map, row_num)

                msg = ParsedMessage(
                    content=message_content,
                    sender=sender,
                    timestamp=timestamp,
                    line_number_start=row_num,
                    line_number_end=row_num,
                    raw_lines=[','.join(row)]
                )
                messages.append(msg)
                parsed_lines += 1

            except Exception as e:
                error_lines.append((row_num, str(row)[:100], str(e)))

        return ParsingResult(
            messages=messages,
            total_lines=total_lines,
            parsed_lines=parsed_lines,
            skipped_lines=skipped_lines,
            error_lines=error_lines,
            file_name=self.file_name
        )

    def _detect_csv_columns(self, headers: List[str]) -> dict:
        """
        CSV 컬럼명을 자동 감지

        Args:
            headers: CSV 헤더 리스트

        Returns:
            dict: 컬럼 인덱스 매핑 {'date': idx, 'time': idx, 'sender': idx, 'message': idx}
        """
        col_map = {'date': -1, 'time': -1, 'datetime': -1, 'sender': -1, 'message': -1}

        # 컬럼명 패턴 (한글/영어)
        patterns = {
            'date': ['날짜', 'date', '일자'],
            'time': ['시간', 'time'],
            'datetime': ['일시', 'datetime', '날짜시간'],
            'sender': ['발신자', '보낸사람', 'sender', 'user', '이름', 'name', '작성자'],
            'message': ['메시지', 'message', '내용', 'content', '메세지', 'text', '대화']
        }

        headers_lower = [h.lower().strip() for h in headers]

        for col_type, keywords in patterns.items():
            for idx, header in enumerate(headers_lower):
                if any(kw in header for kw in keywords):
                    col_map[col_type] = idx
                    break

        return col_map

    def _parse_csv_timestamp(self, row: List[str], col_map: dict, row_num: int) -> datetime:
        """
        CSV 행에서 타임스탬프 추출

        Args:
            row: CSV 행 데이터
            col_map: 컬럼 인덱스 매핑
            row_num: 행 번호 (디버깅용)

        Returns:
            datetime: 파싱된 타임스탬프
        """
        now = datetime.now()

        # datetime 컬럼이 있는 경우
        if col_map['datetime'] != -1 and col_map['datetime'] < len(row):
            dt_str = row[col_map['datetime']].strip()
            if dt_str:
                parsed = self._try_parse_datetime(dt_str)
                if parsed:
                    return parsed

        # date + time 분리된 경우
        date_str = ""
        time_str = ""

        if col_map['date'] != -1 and col_map['date'] < len(row):
            date_str = row[col_map['date']].strip()

        if col_map['time'] != -1 and col_map['time'] < len(row):
            time_str = row[col_map['time']].strip()

        if date_str and time_str:
            combined = f"{date_str} {time_str}"
            parsed = self._try_parse_datetime(combined)
            if parsed:
                return parsed

        if date_str:
            parsed = self._try_parse_datetime(date_str)
            if parsed:
                return parsed

        # 파싱 실패 시 현재 시간 반환
        return now

    def _try_parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """
        다양한 형식의 날짜/시간 문자열 파싱 시도

        Args:
            dt_str: 날짜/시간 문자열

        Returns:
            datetime or None: 파싱된 datetime 또는 None
        """
        # 지원하는 날짜/시간 형식
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y.%m.%d %H:%M:%S",
            "%Y.%m.%d %H:%M",
            "%Y년 %m월 %d일 %H:%M:%S",
            "%Y년 %m월 %d일 %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y.%m.%d",
            "%Y년 %m월 %d일",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
        ]

        # 오전/오후 처리
        dt_str_converted = dt_str
        if "오전" in dt_str or "오후" in dt_str:
            dt_str_converted = self._convert_korean_time(dt_str)

        for fmt in formats:
            try:
                return datetime.strptime(dt_str_converted, fmt)
            except ValueError:
                continue

        return None

    def _convert_korean_time(self, dt_str: str) -> str:
        """
        한국어 시간 형식 (오전/오후)을 24시간 형식으로 변환

        Args:
            dt_str: "2024-03-15 오후 2:30" 형태의 문자열

        Returns:
            str: "2024-03-15 14:30" 형태의 문자열
        """
        import re
        pattern = r'(오전|오후)\s*(\d{1,2}):(\d{2})'
        match = re.search(pattern, dt_str)

        if match:
            meridiem, hour, minute = match.groups()
            hour = int(hour)

            if meridiem == "오후" and hour != 12:
                hour += 12
            elif meridiem == "오전" and hour == 12:
                hour = 0

            time_24h = f"{hour:02d}:{minute}"
            dt_str = re.sub(pattern, time_24h, dt_str)

        return dt_str

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
