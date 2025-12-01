"""
Video Parser (비디오 → 오디오 추출 → Whisper STT)

Given: 비디오 파일 (mp4, mov, avi)
When: parse() 호출
Then: ffmpeg로 오디오 추출 → AudioParser로 STT → Message 리스트 반환
"""

from typing import List, Optional
from datetime import datetime
from pathlib import Path
import tempfile
import ffmpeg

from src.parsers.base import BaseParser, Message
from src.parsers.audio_parser import AudioParser


class VideoParser(BaseParser):
    """
    비디오 파일 파서 (Video → Audio → STT)

    ffmpeg로 비디오에서 오디오를 추출한 후 AudioParser를 사용하여
    Speech-to-Text 변환을 수행합니다.
    """

    def parse(
        self,
        file_path: str,
        default_sender: str = "Speaker",
        base_timestamp: Optional[datetime] = None
    ) -> List[Message]:
        """
        비디오 파일에서 오디오를 추출하고 STT 수행

        Args:
            file_path: 비디오 파일 경로 (mp4, mov, avi 등)
            default_sender: 기본 화자명 (AudioParser에 전달)
            base_timestamp: 기준 타임스탬프 (AudioParser에 전달)

        Returns:
            Message 객체 리스트 (타임스탬프별 텍스트)

        Raises:
            FileNotFoundError: 비디오 파일이 존재하지 않을 때
            Exception: ffmpeg 처리 중 에러 발생 시
        """
        # 파일 존재 확인
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")

        # 임시 오디오 파일 생성 (context manager로 자동 정리)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as temp_audio:
            # ffmpeg로 오디오 추출
            try:
                (
                    ffmpeg
                    .input(file_path)
                    .output(temp_audio.name, acodec='mp3', ac=1, ar='16000')
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            except Exception as e:
                raise Exception(f"ffmpeg audio extraction failed: {e}")

            # AudioParser로 STT 수행
            audio_parser = AudioParser()
            messages = audio_parser.parse(
                temp_audio.name,
                default_sender=default_sender,
                base_timestamp=base_timestamp
            )

            return messages
