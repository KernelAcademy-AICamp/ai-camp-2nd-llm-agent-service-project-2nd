"""
Test suite for TextParser with KakaoTalk format detection
Following TDD approach: RED-GREEN-REFACTOR

Phase 3: 2.3 카톡/메신저 파싱 테스트
- TextParser가 KakaoTalk 형식을 감지
- 감지 시 KakaoTalkParser로 위임
"""

import pytest
from pathlib import Path
from src.parsers.text import TextParser


class TestKakaoTalkFormatDetection:
    """KakaoTalk 형식 자동 감지 테스트 (2.3)"""

    @pytest.fixture
    def text_parser(self):
        """TextParser 인스턴스"""
        return TextParser()

    @pytest.fixture
    def kakaotalk_sample_file(self):
        """카카오톡 샘플 파일 경로"""
        return str(Path(__file__).parent / "fixtures" / "kakaotalk_sample.txt")

    @pytest.fixture
    def plain_text_file(self, tmp_path):
        """일반 텍스트 파일 생성"""
        file_path = tmp_path / "plain.txt"
        file_path.write_text(
            "This is a plain text file.\nIt has multiple lines.\nBut no KakaoTalk format.",
            encoding="utf-8"
        )
        return str(file_path)

    def test_detect_kakaotalk_format(self, text_parser, kakaotalk_sample_file):
        """
        Given: 카카오톡 형식의 .txt 파일
        When: TextParser.parse() 호출
        Then: KakaoTalk 형식으로 감지
        """
        # When
        messages = text_parser.parse(kakaotalk_sample_file)

        # Then: 메시지가 여러 개로 파싱됨 (카카오톡 형식)
        assert len(messages) > 1, "KakaoTalk format should parse into multiple messages"

        # 각 메시지는 sender, timestamp, content를 가짐
        for msg in messages:
            assert msg.sender is not None
            assert msg.sender != "System"  # KakaoTalk은 실제 발신자 이름
            assert msg.timestamp is not None
            assert msg.content is not None

    def test_plain_text_returns_single_message(self, text_parser, plain_text_file):
        """
        Given: 일반 텍스트 파일
        When: TextParser.parse() 호출
        Then: 하나의 메시지로 파싱 (기존 동작)
        """
        # When
        messages = text_parser.parse(plain_text_file)

        # Then
        assert len(messages) == 1
        assert messages[0].sender == "System"
        assert messages[0].metadata["source_type"] == "text"

    def test_kakaotalk_messages_have_correct_metadata(self, text_parser, kakaotalk_sample_file):
        """
        Given: 카카오톡 파일
        When: parse() 호출
        Then: 메타데이터에 source_type='kakaotalk' 포함
        """
        # When
        messages = text_parser.parse(kakaotalk_sample_file)

        # Then
        assert len(messages) > 0
        assert messages[0].metadata["source_type"] == "kakaotalk"

    def test_kakaotalk_detection_pattern(self, text_parser):
        """
        Given: 카카오톡 형식 패턴이 포함된 텍스트 (최소 2개 메시지)
        When: _is_kakaotalk_format() 호출
        Then: True 반환
        """
        # Given: 최소 2개의 메시지 패턴 필요
        kakao_sample = """2024년 1월 10일 오후 2:30, 홍길동 : 안녕하세요
2024년 1월 10일 오후 2:31, 김철수 : 네, 안녕하세요"""

        # When
        is_kakao = text_parser._is_kakaotalk_format(kakao_sample)

        # Then
        assert is_kakao is True

    def test_plain_text_detection_pattern(self, text_parser):
        """
        Given: 일반 텍스트
        When: _is_kakaotalk_format() 호출
        Then: False 반환
        """
        # Given
        plain_text = "This is just a regular text file\nWith multiple lines\nNo special format"

        # When
        is_kakao = text_parser._is_kakaotalk_format(plain_text)

        # Then
        assert is_kakao is False
