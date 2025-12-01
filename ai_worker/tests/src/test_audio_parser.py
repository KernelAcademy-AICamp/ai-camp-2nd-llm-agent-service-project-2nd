"""
Test suite for AudioParser
Following TDD approach: RED-GREEN-REFACTOR
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
from src.parsers.audio_parser import AudioParser
from src.parsers.base import Message


class TestAudioParserInitialization:
    """Test AudioParser initialization"""

    def test_parser_creation(self):
        """AudioParser 생성 테스트"""
        parser = AudioParser()

        assert parser is not None

    def test_parser_is_base_parser(self):
        """BaseParser 상속 확인"""
        from src.parsers.base import BaseParser
        parser = AudioParser()

        assert isinstance(parser, BaseParser)


class TestAudioParsing:
    """Test audio parsing with Whisper"""

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_parse_simple_audio(self, mock_file, mock_path, mock_openai):
        """간단한 오디오 파싱 테스트"""
        # Mock file exists
        mock_path.return_value.exists.return_value = True

        # Mock Whisper response
        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[
                {'start': 0.0, 'text': '안녕하세요'},
                {'start': 2.5, 'text': '이혼 상담 부탁드립니다'}
            ]
        )

        parser = AudioParser()
        messages = parser.parse("test.mp3")

        assert len(messages) == 2
        assert isinstance(messages[0], Message)
        assert messages[0].content == "안녕하세요"
        assert messages[1].content == "이혼 상담 부탁드립니다"

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_parse_creates_messages(self, mock_file, mock_path, mock_openai):
        """Message 객체 생성 확인"""
        mock_path.return_value.exists.return_value = True

        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[
                {'start': 0.0, 'text': '테스트 메시지'}
            ]
        )

        parser = AudioParser()
        messages = parser.parse("test.mp3")

        assert all(isinstance(m, Message) for m in messages)
        assert all(hasattr(m, 'content') for m in messages)
        assert all(hasattr(m, 'sender') for m in messages)
        assert all(hasattr(m, 'timestamp') for m in messages)


class TestTimestampHandling:
    """Test timestamp extraction from audio"""

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_segment_timestamps(self, mock_file, mock_path, mock_openai):
        """세그먼트별 타임스탬프 테스트"""
        mock_path.return_value.exists.return_value = True

        base_time = datetime(2024, 1, 1, 10, 0, 0)

        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[
                {'start': 0.0, 'text': '첫 번째'},
                {'start': 5.5, 'text': '두 번째'},
                {'start': 12.3, 'text': '세 번째'}
            ]
        )

        parser = AudioParser()
        messages = parser.parse("test.mp3", base_timestamp=base_time)

        # 첫 번째 세그먼트: base_time + 0초
        assert messages[0].timestamp == base_time

        # 두 번째 세그먼트: base_time + 5.5초
        expected_time_2 = base_time + timedelta(seconds=5.5)
        assert messages[1].timestamp == expected_time_2

        # 세 번째 세그먼트: base_time + 12.3초
        expected_time_3 = base_time + timedelta(seconds=12.3)
        assert messages[2].timestamp == expected_time_3

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_default_timestamp(self, mock_file, mock_path, mock_openai):
        """기본 타임스탬프 테스트"""
        mock_path.return_value.exists.return_value = True

        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[
                {'start': 0.0, 'text': '테스트'}
            ]
        )

        parser = AudioParser()
        before = datetime.now()
        messages = parser.parse("test.mp3")
        after = datetime.now()

        # 타임스탬프가 현재 시간 범위 내에 있어야 함
        assert before <= messages[0].timestamp <= after


class TestWhisperAPICall:
    """Test Whisper API integration"""

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_whisper_api_called_correctly(self, mock_file, mock_path, mock_openai):
        """Whisper API 호출 확인"""
        mock_path.return_value.exists.return_value = True

        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[{'start': 0.0, 'text': '테스트'}]
        )

        parser = AudioParser()
        parser.parse("test.mp3")

        # Whisper API가 호출되었는지 확인
        mock_openai.audio.transcriptions.create.assert_called_once()

        # 호출 인자 확인
        call_kwargs = mock_openai.audio.transcriptions.create.call_args.kwargs
        assert call_kwargs['model'] == 'whisper-1'
        assert call_kwargs['response_format'] == 'verbose_json'
        assert 'segment' in call_kwargs['timestamp_granularities']


class TestMultipleSpeakers:
    """Test speaker handling"""

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_default_speaker(self, mock_file, mock_path, mock_openai):
        """기본 발신자 설정 테스트"""
        mock_path.return_value.exists.return_value = True

        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[
                {'start': 0.0, 'text': '첫 번째 발언'},
                {'start': 3.0, 'text': '두 번째 발언'}
            ]
        )

        parser = AudioParser()
        messages = parser.parse("test.mp3", default_sender="화자A")

        assert all(m.sender == "화자A" for m in messages)

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_speaker_unknown_default(self, mock_file, mock_path, mock_openai):
        """발신자 미지정 시 기본값 테스트"""
        mock_path.return_value.exists.return_value = True

        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[{'start': 0.0, 'text': '발언'}]
        )

        parser = AudioParser()
        messages = parser.parse("test.mp3")

        assert messages[0].sender == "Speaker"


class TestEdgeCases:
    """Test edge cases"""

    def test_invalid_file_path(self):
        """잘못된 파일 경로 처리"""
        parser = AudioParser()

        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent.mp3")

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_empty_transcription(self, mock_file, mock_path, mock_openai):
        """빈 변환 결과 처리"""
        mock_path.return_value.exists.return_value = True

        mock_openai.audio.transcriptions.create.return_value = MagicMock(segments=[])

        parser = AudioParser()
        messages = parser.parse("test.mp3")

        assert len(messages) == 0

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_whitespace_only_text(self, mock_file, mock_path, mock_openai):
        """공백만 있는 텍스트 처리"""
        mock_path.return_value.exists.return_value = True

        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[
                {'start': 0.0, 'text': '   '},
                {'start': 1.0, 'text': '유효한 텍스트'},
                {'start': 2.0, 'text': '\n\n'}
            ]
        )

        parser = AudioParser()
        messages = parser.parse("test.mp3")

        # 공백만 있는 세그먼트는 제외되어야 함
        assert len(messages) == 1
        assert messages[0].content == "유효한 텍스트"

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_whisper_api_error(self, mock_file, mock_path, mock_openai):
        """Whisper API 오류 처리"""
        mock_path.return_value.exists.return_value = True
        mock_openai.audio.transcriptions.create.side_effect = Exception("API Error")

        parser = AudioParser()

        with pytest.raises(Exception, match="API Error"):
            parser.parse("test.mp3")


class TestFileFormats:
    """Test different audio file formats"""

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_mp3_format(self, mock_file, mock_path, mock_openai):
        """MP3 형식 테스트"""
        mock_path.return_value.exists.return_value = True
        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[{'start': 0.0, 'text': 'MP3 테스트'}]
        )

        parser = AudioParser()
        messages = parser.parse("test.mp3")

        assert len(messages) == 1
        assert messages[0].content == "MP3 테스트"

    @patch('src.parsers.audio_parser.openai')
    @patch('src.parsers.audio_parser.Path')
    @patch('builtins.open', new_callable=mock_open, read_data=b'audio data')
    def test_m4a_format(self, mock_file, mock_path, mock_openai):
        """M4A 형식 테스트"""
        mock_path.return_value.exists.return_value = True
        mock_openai.audio.transcriptions.create.return_value = MagicMock(
            segments=[{'start': 0.0, 'text': 'M4A 테스트'}]
        )

        parser = AudioParser()
        messages = parser.parse("test.m4a")

        assert len(messages) == 1
        assert messages[0].content == "M4A 테스트"
