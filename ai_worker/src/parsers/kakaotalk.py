"""
KakaoTalk Parser Module
Parses KakaoTalk chat export files (Korean format)
"""

import re
from datetime import datetime
from typing import List
from .base import BaseParser, Message


class KakaoTalkParser(BaseParser):
    """
    카카오톡 대화 파일 파서

    지원 형식:
    - 형식1: "2024년 1월 10일 오후 2:30, 발신자 : 메시지 내용"
    - 형식2: "[발신자] [오전 8:56] 메시지 내용" (PC/모바일 내보내기)
    - 멀티라인 메시지 처리
    - 한국어 날짜/시간 형식
    """

    # 정규표현식 패턴 - 형식1: 기존 형식
    DATE_TIME_PATTERN = re.compile(
        r"^(\d{4})년 (\d{1,2})월 (\d{1,2})일 (오전|오후) (\d{1,2}):(\d{2}), (.+?) : (.+)$"
    )

    # 정규표현식 패턴 - 형식2: [발신자] [오전/오후 시:분] 메시지
    BRACKET_PATTERN = re.compile(
        r"^\[(.+?)\] \[(오전|오후) (\d{1,2}):(\d{2})\] (.+)$"
    )

    # 날짜 구분선 패턴: "2025년 11월 14일 금요일" 또는 "----- 2024년 1월 10일 -----"
    DATE_LINE_PATTERN = re.compile(
        r"^-*\s*(\d{4})년 (\d{1,2})월 (\d{1,2})일.*$"
    )

    def parse(self, filepath: str) -> List[Message]:
        """
        카카오톡 파일 파싱

        Args:
            filepath: 카카오톡 txt 파일 경로

        Returns:
            List[Message]: 파싱된 메시지 리스트

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            ValueError: 파일 형식이 잘못되었을 때
        """
        self._validate_file_exists(filepath)

        messages = []
        current_message = None
        current_date = None  # 형식2용 현재 날짜 추적

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")

                # 빈 줄은 건너뛰기
                if not line.strip():
                    continue

                # 헤더 라인 건너뛰기
                if self._is_header_line(line):
                    continue

                # 형식1: 날짜/시간 패턴 매칭 (먼저 체크 - 더 구체적인 패턴)
                match = self.DATE_TIME_PATTERN.match(line)

                if match:
                    # 이전 메시지가 있으면 저장
                    if current_message:
                        messages.append(current_message)

                    # 새 메시지 시작
                    year, month, day, meridiem, hour, minute, sender, content = match.groups()

                    timestamp = self._parse_korean_datetime(
                        int(year), int(month), int(day),
                        meridiem, int(hour), int(minute)
                    )

                    current_message = Message(
                        content=content.strip(),
                        sender=sender.strip(),
                        timestamp=timestamp,
                        metadata={"source_type": "kakaotalk"}
                    )
                    continue

                # 날짜 구분선 체크 (형식2용 - 형식1 이후에 체크)
                date_match = self.DATE_LINE_PATTERN.match(line)
                if date_match:
                    year, month, day = date_match.groups()
                    current_date = (int(year), int(month), int(day))
                    continue

                # 형식2: [발신자] [오전/오후 시:분] 메시지
                bracket_match = self.BRACKET_PATTERN.match(line)
                if bracket_match:
                    # 이전 메시지가 있으면 저장
                    if current_message:
                        messages.append(current_message)

                    sender, meridiem, hour, minute, content = bracket_match.groups()

                    # 날짜가 설정되어 있으면 사용, 아니면 오늘 날짜
                    if current_date:
                        year, month, day = current_date
                    else:
                        from datetime import date
                        today = date.today()
                        year, month, day = today.year, today.month, today.day

                    timestamp = self._parse_korean_datetime(
                        year, month, day,
                        meridiem, int(hour), int(minute)
                    )

                    current_message = Message(
                        content=content.strip(),
                        sender=sender.strip(),
                        timestamp=timestamp,
                        metadata={"source_type": "kakaotalk"}
                    )
                    continue

                # 멀티라인 메시지의 연속 라인
                if current_message and not self._is_system_message(line):
                    # 개행 문자로 연결
                    current_message.content += "\n" + line.strip()

        # 마지막 메시지 저장
        if current_message:
            messages.append(current_message)

        return messages

    def _parse_korean_datetime(
        self,
        year: int,
        month: int,
        day: int,
        meridiem: str,
        hour: int,
        minute: int
    ) -> datetime:
        """
        한국어 날짜/시간을 datetime 객체로 변환

        Args:
            year: 연도
            month: 월
            day: 일
            meridiem: "오전" 또는 "오후"
            hour: 시간 (12시간 형식)
            minute: 분

        Returns:
            datetime: 파싱된 datetime 객체
        """
        # 오후/오전 처리
        if meridiem == "오후" and hour != 12:
            hour += 12
        elif meridiem == "오전" and hour == 12:
            hour = 0

        return datetime(year, month, day, hour, minute)

    def _is_header_line(self, line: str) -> bool:
        """
        헤더 라인 여부 확인

        Args:
            line: 검사할 라인

        Returns:
            bool: 헤더 라인이면 True
        """
        header_keywords = [
            "카카오톡 대화",
            "저장한 날짜",
            "님과 카카오톡"
        ]
        return any(keyword in line for keyword in header_keywords)

    def _is_system_message(self, line: str) -> bool:
        """
        시스템 메시지 여부 확인 (사진, 동영상 등)

        Args:
            line: 검사할 라인

        Returns:
            bool: 시스템 메시지이면 True
        """
        system_keywords = [
            "사진",
            "동영상",
            "이모티콘",
            "파일",
            "음성통화",
            "영상통화"
        ]
        # 단순히 "사진"만 있는 라인은 시스템 메시지
        return line.strip() in system_keywords
