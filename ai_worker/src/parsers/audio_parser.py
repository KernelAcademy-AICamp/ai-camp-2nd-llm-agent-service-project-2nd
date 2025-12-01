"""
Audio Parser Module
오디오 파일에서 음성을 텍스트로 변환 (STT)
"""

from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import openai
from src.parsers.base import BaseParser, Message


class AudioParser(BaseParser):
    """
    오디오 파일 파서 (Speech-to-Text)

    Given: 오디오 파일 (mp3, m4a)
    When: parse() 호출
    Then: Whisper API로 변환하여 타임스탬프별 Message 리스트 반환

    기능:
    - Whisper API 기반 STT
    - 세그먼트별 타임스탬프 추출
    - 한글/영어 음성 인식
    - 여러 오디오 형식 지원 (mp3, m4a)
    """

    def parse(
        self,
        file_path: str,
        default_sender: str = "Speaker",
        base_timestamp: Optional[datetime] = None
    ) -> List[Message]:
        """
        오디오 파일 파싱

        Given: 오디오 파일 경로
        When: Whisper API로 STT 실행
        Then: 세그먼트별 Message 객체 리스트 반환

        Args:
            file_path: 오디오 파일 경로 (mp3, m4a 등)
            default_sender: 기본 발신자 (기본값: "Speaker")
            base_timestamp: 기준 타임스탬프 (None이면 현재 시간)

        Returns:
            List[Message]: 세그먼트별 메시지 리스트

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
        """
        # 파일 존재 확인
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # 기본 타임스탬프 설정
        if base_timestamp is None:
            base_timestamp = datetime.now()

        # Whisper API 호출
        with open(file_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        messages = []

        # 세그먼트별 처리
        for segment in transcript.segments:
            text = segment['text'].strip()

            # 빈 텍스트 제외
            if not text:
                continue

            # 세그먼트 시작 시간 기준으로 타임스탬프 계산
            segment_time = base_timestamp + timedelta(seconds=segment['start'])

            message = Message(
                content=text,
                sender=default_sender,  # TODO: Speaker diarization 추가 가능
                timestamp=segment_time
            )
            messages.append(message)

        return messages
