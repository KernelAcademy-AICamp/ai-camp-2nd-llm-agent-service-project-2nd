"""
Audio Parser V2
음성 파일 파서 - 법적 증거용

핵심 기능:
- 세그먼트 시작/종료 시간 추적 (법적 증거 인용용)
- 파일 해시 (무결성 증명)
- 오디오 메타데이터 (길이, 포맷)
- Whisper API 기반 STT
"""

import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from dataclasses import dataclass

import openai

from src.schemas import (
    SourceLocation,
    FileType,
    EvidenceChunk,
    LegalAnalysis,
    FileMetadata,
)


@dataclass
class AudioSegment:
    """음성 세그먼트"""
    segment_index: int  # 세그먼트 번호 (1부터 시작)
    start_sec: float  # 시작 시간 (초)
    end_sec: float  # 종료 시간 (초)
    text: str  # 변환된 텍스트
    confidence: Optional[float] = None  # 신뢰도 (있는 경우)

    @property
    def duration_sec(self) -> float:
        """세그먼트 길이 (초)"""
        return self.end_sec - self.start_sec

    def format_time_range(self) -> str:
        """시간 범위 문자열 (MM:SS-MM:SS)"""
        start_str = self._format_seconds(self.start_sec)
        end_str = self._format_seconds(self.end_sec)
        return f"{start_str}-{end_str}"

    def _format_seconds(self, seconds: float) -> str:
        """초를 MM:SS 형식으로 변환"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"


@dataclass
class AudioMetadata:
    """오디오 메타데이터"""
    duration_sec: Optional[float] = None  # 전체 길이 (초)
    format: Optional[str] = None  # 파일 포맷 (mp3, m4a)
    sample_rate: Optional[int] = None  # 샘플 레이트
    channels: Optional[int] = None  # 채널 수
    bitrate: Optional[int] = None  # 비트레이트

    def format_duration(self) -> str:
        """길이 문자열 (HH:MM:SS)"""
        if self.duration_sec is None:
            return "Unknown"
        hours = int(self.duration_sec // 3600)
        minutes = int((self.duration_sec % 3600) // 60)
        seconds = int(self.duration_sec % 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


@dataclass
class AudioParsingResult:
    """오디오 파싱 결과"""
    segments: List[AudioSegment]
    file_name: str
    total_segments: int
    total_duration_sec: float
    file_hash: str
    file_size_bytes: int
    metadata: AudioMetadata
    language: Optional[str] = None  # 감지된 언어
    full_transcript: str = ""  # 전체 텍스트


class AudioParserV2:
    """
    음성 파일 파서 V2

    Whisper API로 음성을 텍스트로 변환하고,
    각 세그먼트에 시간 정보를 기록합니다.

    Usage:
        parser = AudioParserV2()
        result = parser.parse("recording.mp3")

        for seg in result.segments:
            print(f"[{seg.format_time_range()}] {seg.text}")
    """

    SUPPORTED_FORMATS = {'.mp3', '.m4a', '.wav', '.mp4', '.mpeg', '.mpga', '.webm'}

    def __init__(self, model: str = "whisper-1"):
        """
        Args:
            model: Whisper 모델 (기본: whisper-1)
        """
        self.model = model

    def parse(
        self,
        filepath: str,
        language: Optional[str] = None
    ) -> AudioParsingResult:
        """
        오디오 파일 파싱

        Args:
            filepath: 오디오 파일 경로
            language: 언어 힌트 (예: "ko", "en"). None이면 자동 감지

        Returns:
            AudioParsingResult: 파싱 결과

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            ValueError: 지원하지 않는 형식일 때
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # 파일 형식 확인
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {path.suffix}. Supported: {self.SUPPORTED_FORMATS}")

        # 파일 해시 및 크기
        file_hash = self._calculate_file_hash(filepath)
        file_size = path.stat().st_size

        # 오디오 메타데이터
        metadata = self._extract_metadata(filepath)

        # Whisper API 호출
        segments, full_text, detected_lang = self._transcribe(filepath, language)

        return AudioParsingResult(
            segments=segments,
            file_name=path.name,
            total_segments=len(segments),
            total_duration_sec=metadata.duration_sec or 0,
            file_hash=file_hash,
            file_size_bytes=file_size,
            metadata=metadata,
            language=detected_lang or language,
            full_transcript=full_text
        )

    def parse_to_chunks(
        self,
        filepath: str,
        case_id: str,
        file_id: str,
        base_timestamp: Optional[datetime] = None,
        language: Optional[str] = None
    ) -> Tuple[List[EvidenceChunk], AudioParsingResult]:
        """
        파싱 후 EvidenceChunk 리스트로 변환

        Args:
            filepath: 파일 경로
            case_id: 케이스 ID
            file_id: 파일 ID
            base_timestamp: 녹음 시작 시간 (None이면 현재 시간)
            language: 언어 힌트

        Returns:
            Tuple[List[EvidenceChunk], AudioParsingResult]: 청크 리스트와 파싱 결과
        """
        result = self.parse(filepath, language)
        chunks: List[EvidenceChunk] = []

        if base_timestamp is None:
            base_timestamp = datetime.now()

        for seg in result.segments:
            # 원본 위치 정보
            source_location = SourceLocation(
                file_name=result.file_name,
                file_type=FileType.AUDIO,
                segment_start_sec=seg.start_sec,
                segment_end_sec=seg.end_sec
            )

            # 내용 해시
            content_hash = hashlib.sha256(seg.text.encode('utf-8')).hexdigest()[:16]

            # 세그먼트 시작 시간 기준 타임스탬프
            segment_timestamp = base_timestamp + timedelta(seconds=seg.start_sec)

            chunk = EvidenceChunk(
                file_id=file_id,
                case_id=case_id,
                source_location=source_location,
                content=seg.text,
                content_hash=content_hash,
                sender="Speaker",  # TODO: Speaker diarization
                timestamp=segment_timestamp,
                legal_analysis=LegalAnalysis(),
                extra_metadata={
                    "segment_index": seg.segment_index,
                    "time_range": seg.format_time_range(),
                    "duration_sec": seg.duration_sec,
                    "confidence": seg.confidence
                }
            )
            chunks.append(chunk)

        return chunks, result

    def get_file_metadata(self, filepath: str) -> FileMetadata:
        """
        오디오 파일 메타데이터 추출

        Args:
            filepath: 파일 경로

        Returns:
            FileMetadata: 파일 메타데이터
        """
        path = Path(filepath)
        file_hash = self._calculate_file_hash(filepath)
        file_size = path.stat().st_size
        # Note: metadata extraction available via _extract_metadata() if needed

        return FileMetadata(
            file_hash_sha256=file_hash,
            file_size_bytes=file_size,
            total_pages=1  # 오디오는 1개
        )

    def _transcribe(
        self,
        filepath: str,
        language: Optional[str] = None
    ) -> Tuple[List[AudioSegment], str, Optional[str]]:
        """Whisper API로 음성 변환"""
        segments: List[AudioSegment] = []
        full_text = ""
        detected_lang = None

        try:
            with open(filepath, "rb") as audio_file:
                # API 호출 옵션
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "file": audio_file,
                    "response_format": "verbose_json",
                    "timestamp_granularities": ["segment"]
                }

                if language:
                    kwargs["language"] = language

                transcript = openai.audio.transcriptions.create(**kwargs)

            # 전체 텍스트
            full_text = transcript.text if hasattr(transcript, 'text') else ""

            # 감지된 언어
            if hasattr(transcript, 'language'):
                detected_lang = transcript.language

            # 세그먼트 처리
            if hasattr(transcript, 'segments') and transcript.segments:
                for idx, seg in enumerate(transcript.segments, start=1):
                    text = seg.get('text', '').strip() if isinstance(seg, dict) else getattr(seg, 'text', '').strip()

                    if not text:
                        continue

                    start = seg.get('start', 0) if isinstance(seg, dict) else getattr(seg, 'start', 0)
                    end = seg.get('end', 0) if isinstance(seg, dict) else getattr(seg, 'end', 0)

                    audio_segment = AudioSegment(
                        segment_index=idx,
                        start_sec=float(start),
                        end_sec=float(end),
                        text=text
                    )
                    segments.append(audio_segment)

        except Exception as e:
            raise ValueError(f"Whisper API error: {e}")

        return segments, full_text, detected_lang

    def _extract_metadata(self, filepath: str) -> AudioMetadata:
        """오디오 메타데이터 추출"""
        metadata = AudioMetadata()
        path = Path(filepath)

        # 파일 포맷
        metadata.format = path.suffix.lower().lstrip('.')

        # 추가 메타데이터 추출 시도 (mutagen 라이브러리 사용)
        try:
            from mutagen import File as MutagenFile
            audio = MutagenFile(filepath)
            if audio:
                # 길이
                if hasattr(audio.info, 'length'):
                    metadata.duration_sec = float(audio.info.length)
                # 샘플 레이트
                if hasattr(audio.info, 'sample_rate'):
                    metadata.sample_rate = int(audio.info.sample_rate)
                # 채널 수
                if hasattr(audio.info, 'channels'):
                    metadata.channels = int(audio.info.channels)
                # 비트레이트
                if hasattr(audio.info, 'bitrate'):
                    metadata.bitrate = int(audio.info.bitrate)
        except ImportError:
            # mutagen 미설치 시 기본값 유지
            pass
        except Exception:
            # 메타데이터 추출 실패해도 계속 진행
            pass

        return metadata

    def _calculate_file_hash(self, filepath: str) -> str:
        """파일 SHA-256 해시 계산"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# 간편 함수
def parse_audio(filepath: str, language: Optional[str] = None) -> AudioParsingResult:
    """오디오 파일 파싱 (간편 함수)"""
    parser = AudioParserV2()
    return parser.parse(filepath, language)
