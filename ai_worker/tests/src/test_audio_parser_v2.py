"""
Audio Parser V2 테스트

Given: 오디오 파일
When: AudioParserV2.parse() 호출
Then: 세그먼트별 텍스트와 시간 정보 반환
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import os

from src.parsers.audio_parser_v2 import (
    AudioParserV2,
    AudioSegment,
    AudioMetadata,
    AudioParsingResult
)


class TestAudioParserV2Initialization:
    """AudioParserV2 초기화 테스트"""

    def test_parser_creation(self):
        """Given: 기본 설정
        When: AudioParserV2() 생성
        Then: 파서 인스턴스 생성"""
        parser = AudioParserV2()
        assert parser is not None
        assert parser.model == "whisper-1"

    def test_parser_with_custom_model(self):
        """Given: 커스텀 모델
        When: AudioParserV2(model="custom") 생성
        Then: 설정값 반영"""
        parser = AudioParserV2(model="whisper-large")
        assert parser.model == "whisper-large"

    def test_supported_formats(self):
        """Given: AudioParserV2
        When: SUPPORTED_FORMATS 확인
        Then: 지원 형식 포함"""
        assert '.mp3' in AudioParserV2.SUPPORTED_FORMATS
        assert '.m4a' in AudioParserV2.SUPPORTED_FORMATS
        assert '.wav' in AudioParserV2.SUPPORTED_FORMATS


class TestAudioSegment:
    """AudioSegment 모델 테스트"""

    def test_segment_creation(self):
        """Given: 세그먼트 데이터
        When: AudioSegment 생성
        Then: 속성 정확히 설정"""
        segment = AudioSegment(
            segment_index=1,
            start_sec=0.0,
            end_sec=5.5,
            text="안녕하세요"
        )

        assert segment.segment_index == 1
        assert segment.start_sec == 0.0
        assert segment.end_sec == 5.5
        assert segment.text == "안녕하세요"

    def test_segment_duration(self):
        """Given: AudioSegment
        When: duration_sec 접근
        Then: 올바른 길이 계산"""
        segment = AudioSegment(
            segment_index=1,
            start_sec=10.0,
            end_sec=25.5,
            text="테스트"
        )

        assert segment.duration_sec == 15.5

    def test_segment_format_time_range(self):
        """Given: AudioSegment
        When: format_time_range() 호출
        Then: 시간 형식 문자열 반환"""
        segment = AudioSegment(
            segment_index=1,
            start_sec=65.0,  # 1분 5초
            end_sec=130.5,   # 2분 10.5초
            text="테스트"
        )

        time_range = segment.format_time_range()
        # 형식: "1:05-2:10" 또는 "01:05-02:10"
        assert "1:05" in time_range or "01:05" in time_range
        assert "2:10" in time_range or "02:10" in time_range


class TestAudioMetadata:
    """AudioMetadata 모델 테스트"""

    def test_metadata_defaults(self):
        """Given: 기본 AudioMetadata
        When: 생성
        Then: 기본값 설정"""
        metadata = AudioMetadata()

        assert metadata.duration_sec is None
        assert metadata.sample_rate is None
        assert metadata.channels is None

    def test_metadata_with_values(self):
        """Given: 메타데이터 값
        When: AudioMetadata 생성
        Then: 값 반영"""
        metadata = AudioMetadata(
            duration_sec=120.5,
            sample_rate=44100,
            channels=2,
            bitrate=320000,
            format="mp3"
        )

        assert metadata.duration_sec == 120.5
        assert metadata.sample_rate == 44100
        assert metadata.channels == 2
        assert metadata.bitrate == 320000
        assert metadata.format == "mp3"


class TestAudioParserV2Parse:
    """parse() 메서드 테스트"""

    def test_parse_file_not_found(self):
        """Given: 존재하지 않는 파일
        When: parse() 호출
        Then: FileNotFoundError 발생"""
        parser = AudioParserV2()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.mp3")

    def test_parse_unsupported_format(self):
        """Given: 지원하지 않는 형식
        When: parse() 호출
        Then: ValueError 발생"""
        parser = AudioParserV2()

        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'fake content')
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported format"):
                parser.parse(temp_path)
        finally:
            os.unlink(temp_path)

    @patch('src.parsers.audio_parser_v2.openai')
    def test_parse_returns_result(self, mock_openai):
        """Given: 유효한 오디오 파일
        When: parse() 호출
        Then: AudioParsingResult 반환"""
        # Mock Whisper API 응답
        mock_transcript = MagicMock()
        mock_transcript.text = "테스트 음성입니다."
        mock_transcript.language = "ko"
        mock_transcript.segments = [
            {"text": "테스트 음성입니다.", "start": 0.0, "end": 2.5}
        ]
        mock_openai.audio.transcriptions.create.return_value = mock_transcript

        parser = AudioParserV2()

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'fake mp3 content')
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert isinstance(result, AudioParsingResult)
            assert result.language == "ko"
            assert len(result.segments) >= 1
        finally:
            os.unlink(temp_path)

    @patch('src.parsers.audio_parser_v2.openai')
    def test_parse_with_language_hint(self, mock_openai):
        """Given: 언어 힌트
        When: parse(language='en') 호출
        Then: API에 언어 전달"""
        mock_transcript = MagicMock()
        mock_transcript.text = "Hello"
        mock_transcript.segments = []
        mock_openai.audio.transcriptions.create.return_value = mock_transcript

        parser = AudioParserV2()

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'fake mp3 content')
            temp_path = f.name

        try:
            parser.parse(temp_path, language="en")

            call_kwargs = mock_openai.audio.transcriptions.create.call_args.kwargs
            assert call_kwargs.get("language") == "en"
        finally:
            os.unlink(temp_path)


class TestAudioParsingResult:
    """AudioParsingResult 모델 테스트"""

    def test_result_creation(self):
        """Given: 파싱 결과 데이터
        When: AudioParsingResult 생성
        Then: 속성 정확히 설정"""
        segments = [
            AudioSegment(segment_index=1, start_sec=0.0, end_sec=5.0, text="첫 번째"),
            AudioSegment(segment_index=2, start_sec=5.0, end_sec=10.0, text="두 번째"),
        ]

        result = AudioParsingResult(
            segments=segments,
            file_name="test.mp3",
            total_segments=2,
            total_duration_sec=10.0,
            file_hash="abc123",
            file_size_bytes=1024,
            metadata=AudioMetadata(duration_sec=10.0),
            language="ko",
            full_transcript="첫 번째 두 번째"
        )

        assert result.total_segments == 2
        assert result.total_duration_sec == 10.0
        assert result.language == "ko"


class TestAudioParserV2ParseToChunks:
    """parse_to_chunks() 메서드 테스트"""

    @patch('src.parsers.audio_parser_v2.openai')
    def test_parse_to_chunks_returns_evidence_chunks(self, mock_openai):
        """Given: 오디오 파일
        When: parse_to_chunks() 호출
        Then: EvidenceChunk 리스트 반환"""
        mock_transcript = MagicMock()
        mock_transcript.text = "테스트"
        mock_transcript.segments = [
            {"text": "첫 번째 세그먼트", "start": 0.0, "end": 5.0},
            {"text": "두 번째 세그먼트", "start": 5.0, "end": 10.0},
        ]
        mock_openai.audio.transcriptions.create.return_value = mock_transcript

        parser = AudioParserV2()

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'fake mp3 content')
            temp_path = f.name

        try:
            chunks, result = parser.parse_to_chunks(
                filepath=temp_path,
                case_id="case_001",
                file_id="file_001"
            )

            assert len(chunks) == 2
            assert chunks[0].case_id == "case_001"
            assert chunks[0].file_id == "file_001"
        finally:
            os.unlink(temp_path)

    @patch('src.parsers.audio_parser_v2.openai')
    def test_parse_to_chunks_with_base_timestamp(self, mock_openai):
        """Given: 기준 타임스탬프
        When: parse_to_chunks(base_timestamp=...) 호출
        Then: 세그먼트 타임스탬프 계산"""
        mock_transcript = MagicMock()
        mock_transcript.text = "테스트"
        mock_transcript.segments = [
            {"text": "세그먼트", "start": 30.0, "end": 35.0}
        ]
        mock_openai.audio.transcriptions.create.return_value = mock_transcript

        parser = AudioParserV2()
        base_time = datetime(2024, 1, 15, 10, 0, 0)

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'fake mp3 content')
            temp_path = f.name

        try:
            chunks, _ = parser.parse_to_chunks(
                filepath=temp_path,
                case_id="case_001",
                file_id="file_001",
                base_timestamp=base_time
            )

            # 세그먼트 시작이 30초이므로 타임스탬프는 10:00:30
            expected_time = base_time + timedelta(seconds=30)
            assert chunks[0].timestamp == expected_time
        finally:
            os.unlink(temp_path)


class TestAudioParserV2FileMetadata:
    """get_file_metadata() 메서드 테스트"""

    def test_get_file_metadata(self):
        """Given: 오디오 파일
        When: get_file_metadata() 호출
        Then: FileMetadata 반환"""
        parser = AudioParserV2()

        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'fake mp3 content')
            temp_path = f.name

        try:
            metadata = parser.get_file_metadata(temp_path)

            assert metadata.file_hash_sha256 is not None
            assert metadata.file_size_bytes > 0
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
