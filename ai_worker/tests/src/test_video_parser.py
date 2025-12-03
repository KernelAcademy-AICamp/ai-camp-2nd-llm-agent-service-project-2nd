"""
Video Parser 테스트 (TDD RED Phase)

Given: 비디오 파일 (mp4, mov, avi)
When: VideoParser.parse() 호출
Then: ffmpeg로 오디오 추출 → Whisper STT → Message 리스트 반환
"""

import pytest
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Skip entire module if ffmpeg-python is not installed
ffmpeg = pytest.importorskip("ffmpeg", reason="ffmpeg-python not installed")

from src.parsers.video_parser import VideoParser
from src.parsers.base import BaseParser, Message


class TestVideoParserInitialization(unittest.TestCase):
    """VideoParser 초기화 테스트"""

    def test_parser_creation(self):
        """Given: VideoParser 생성 요청
        When: VideoParser() 호출
        Then: 인스턴스 생성 성공"""
        parser = VideoParser()
        self.assertIsNotNone(parser)

    def test_parser_is_base_parser(self):
        """Given: VideoParser 인스턴스
        When: BaseParser 상속 확인
        Then: isinstance(parser, BaseParser) == True"""
        parser = VideoParser()
        self.assertIsInstance(parser, BaseParser)


class TestVideoParsing(unittest.TestCase):
    """비디오 파일 파싱 테스트"""

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_parse_simple_video(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: 간단한 비디오 파일
        When: parse() 호출
        Then: ffmpeg로 오디오 추출 → AudioParser로 STT"""
        # Setup
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        # Mock AudioParser
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = [
            Message(content="안녕하세요", sender="Speaker", timestamp=datetime(2024, 1, 1, 12, 0, 0)),
            Message(content="이혼 상담 부탁드립니다", sender="Speaker", timestamp=datetime(2024, 1, 1, 12, 0, 2))
        ]
        mock_audio_parser.return_value = mock_parser_instance

        # Execute
        parser = VideoParser()
        messages = parser.parse("test.mp4")

        # Verify
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].content, "안녕하세요")
        mock_ffmpeg.input.assert_called_once_with("test.mp4")

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_parse_creates_messages(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: 비디오 파일 파싱
        When: parse() 실행
        Then: Message 객체 리스트 반환"""
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = [
            Message(content="테스트", sender="Speaker", timestamp=datetime.now())
        ]
        mock_audio_parser.return_value = mock_parser_instance

        parser = VideoParser()
        messages = parser.parse("test.mp4")

        self.assertIsInstance(messages, list)
        self.assertIsInstance(messages[0], Message)


class TestAudioExtraction(unittest.TestCase):
    """오디오 추출 테스트"""

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_ffmpeg_audio_extraction(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: 비디오 파일
        When: 오디오 추출 수행
        Then: ffmpeg로 mp3 추출"""
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = []
        mock_audio_parser.return_value = mock_parser_instance

        # Mock ffmpeg chain (input -> output -> overwrite_output -> run)
        mock_input = MagicMock()
        mock_output = MagicMock()
        mock_overwrite = MagicMock()
        mock_ffmpeg.input.return_value = mock_input
        mock_input.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_overwrite

        parser = VideoParser()
        parser.parse("test.mp4")

        # Verify ffmpeg called correctly
        mock_ffmpeg.input.assert_called_once_with("test.mp4")
        mock_input.output.assert_called_once()
        mock_output.overwrite_output.assert_called_once()
        mock_overwrite.run.assert_called_once()

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_temporary_file_cleanup(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: 임시 오디오 파일 생성
        When: 파싱 완료
        Then: 임시 파일 자동 삭제 (context manager)"""
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = []
        mock_audio_parser.return_value = mock_parser_instance

        parser = VideoParser()
        parser.parse("test.mp4")

        # Verify tempfile context manager used (auto cleanup)
        mock_tempfile.NamedTemporaryFile.assert_called_once()


class TestTimestampHandling(unittest.TestCase):
    """타임스탬프 처리 테스트"""

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_base_timestamp_passed_to_audio_parser(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: base_timestamp 파라미터 제공
        When: parse() 호출
        Then: AudioParser에 base_timestamp 전달"""
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = []
        mock_audio_parser.return_value = mock_parser_instance

        base_time = datetime(2024, 1, 1, 12, 0, 0)
        parser = VideoParser()
        parser.parse("test.mp4", base_timestamp=base_time)

        # Verify AudioParser.parse called with base_timestamp
        mock_parser_instance.parse.assert_called_once()
        call_args = mock_parser_instance.parse.call_args
        self.assertIn('base_timestamp', call_args.kwargs)
        self.assertEqual(call_args.kwargs['base_timestamp'], base_time)


class TestMultipleSpeakers(unittest.TestCase):
    """화자 처리 테스트"""

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_default_speaker(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: default_sender 파라미터 제공
        When: parse() 호출
        Then: AudioParser에 default_sender 전달"""
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = []
        mock_audio_parser.return_value = mock_parser_instance

        parser = VideoParser()
        parser.parse("test.mp4", default_sender="Client")

        # Verify AudioParser.parse called with default_sender
        call_args = mock_parser_instance.parse.call_args
        self.assertIn('default_sender', call_args.kwargs)
        self.assertEqual(call_args.kwargs['default_sender'], "Client")


class TestEdgeCases(unittest.TestCase):
    """엣지 케이스 테스트"""

    @patch('src.parsers.video_parser.Path')
    def test_invalid_file_path(self, mock_path):
        """Given: 존재하지 않는 파일 경로
        When: parse() 호출
        Then: FileNotFoundError 발생"""
        mock_path.return_value.exists.return_value = False

        parser = VideoParser()
        with self.assertRaises(FileNotFoundError):
            parser.parse("nonexistent.mp4")

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_video_with_no_audio(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: 오디오가 없는 비디오
        When: parse() 호출
        Then: 빈 리스트 반환"""
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        # AudioParser returns empty list for no audio
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = []
        mock_audio_parser.return_value = mock_parser_instance

        parser = VideoParser()
        messages = parser.parse("silent_video.mp4")

        self.assertEqual(len(messages), 0)

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_ffmpeg_error_handling(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: ffmpeg 처리 중 에러
        When: parse() 호출
        Then: 적절한 예외 발생"""
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        # Mock ffmpeg to raise error (input -> output -> overwrite_output -> run)
        mock_input = MagicMock()
        mock_output = MagicMock()
        mock_overwrite = MagicMock()
        mock_overwrite.run.side_effect = Exception("ffmpeg error")
        mock_output.overwrite_output.return_value = mock_overwrite
        mock_input.output.return_value = mock_output
        mock_ffmpeg.input.return_value = mock_input

        parser = VideoParser()
        with self.assertRaises(Exception):
            parser.parse("corrupted.mp4")


class TestFileFormats(unittest.TestCase):
    """파일 포맷 지원 테스트"""

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_mp4_format(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: MP4 비디오 파일
        When: parse() 호출
        Then: 정상 처리"""
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = []
        mock_audio_parser.return_value = mock_parser_instance

        parser = VideoParser()
        messages = parser.parse("test.mp4")
        self.assertIsInstance(messages, list)

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_mov_format(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: MOV 비디오 파일
        When: parse() 호출
        Then: 정상 처리"""
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = []
        mock_audio_parser.return_value = mock_parser_instance

        parser = VideoParser()
        messages = parser.parse("test.mov")
        self.assertIsInstance(messages, list)

    @patch('src.parsers.video_parser.AudioParser')
    @patch('src.parsers.video_parser.ffmpeg')
    @patch('src.parsers.video_parser.Path')
    @patch('src.parsers.video_parser.tempfile')
    def test_avi_format(self, mock_tempfile, mock_path, mock_ffmpeg, mock_audio_parser):
        """Given: AVI 비디오 파일
        When: parse() 호출
        Then: 정상 처리"""
        mock_path.return_value.exists.return_value = True
        mock_temp_audio = MagicMock()
        mock_temp_audio.name = "/tmp/temp_audio.mp3"
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value = mock_temp_audio

        mock_parser_instance = MagicMock()
        mock_parser_instance.parse.return_value = []
        mock_audio_parser.return_value = mock_parser_instance

        parser = VideoParser()
        messages = parser.parse("test.avi")
        self.assertIsInstance(messages, list)


if __name__ == '__main__':
    unittest.main()
