"""
Test suite for parsers module
Following TDD approach: RED-GREEN-REFACTOR
"""

import pytest
from datetime import datetime
from src.parsers.base import BaseParser, Message


class TestMessage:
    """Test Message data model"""

    def test_message_creation(self):
        """Message 객체 생성 테스트"""
        msg = Message(
            content="테스트 메시지",
            sender="홍길동",
            timestamp=datetime(2024, 1, 15, 14, 30),
            metadata={"type": "text"}
        )

        assert msg.content == "테스트 메시지"
        assert msg.sender == "홍길동"
        assert msg.timestamp.year == 2024
        assert msg.metadata["type"] == "text"

    def test_message_optional_fields(self):
        """Message 선택적 필드 테스트"""
        msg = Message(
            content="간단 메시지",
            sender="김철수",
            timestamp=datetime.now()
        )

        assert msg.score is None
        assert msg.metadata == {}

    def test_message_score_validation(self):
        """Message 점수 유효성 검증 (0-10 범위)"""
        msg = Message(
            content="점수 테스트",
            sender="이영희",
            timestamp=datetime.now(),
            score=8.5
        )

        assert 0 <= msg.score <= 10

    def test_message_invalid_score_raises_error(self):
        """잘못된 점수 값 에러 테스트"""
        with pytest.raises(ValueError):
            Message(
                content="잘못된 점수",
                sender="박민수",
                timestamp=datetime.now(),
                score=15.0  # 10 초과
            )


class TestBaseParser:
    """Test BaseParser abstract class"""

    def test_base_parser_cannot_be_instantiated(self):
        """추상 클래스는 직접 인스턴스화 불가"""
        with pytest.raises(TypeError):
            BaseParser()

    def test_base_parser_requires_parse_implementation(self):
        """parse() 메서드 구현 필수"""
        class IncompleteParser(BaseParser):
            pass

        with pytest.raises(TypeError):
            IncompleteParser()

    def test_base_parser_concrete_implementation(self):
        """parse() 구현 시 정상 인스턴스화"""
        class ConcreteParser(BaseParser):
            def parse(self, filepath: str) -> list[Message]:
                return []

        parser = ConcreteParser()
        assert isinstance(parser, BaseParser)

    def test_validate_file_exists_method(self):
        """파일 존재 검증 메서드 테스트"""
        class TestParser(BaseParser):
            def parse(self, filepath: str) -> list[Message]:
                self._validate_file_exists(filepath)
                return []

        parser = TestParser()

        # 존재하지 않는 파일
        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent_file.txt")

    def test_get_file_extension_method(self):
        """파일 확장자 추출 메서드 테스트"""
        class TestParser(BaseParser):
            def parse(self, filepath: str) -> list[Message]:
                return []

            def get_ext(self, filepath: str) -> str:
                return self._get_file_extension(filepath)

        parser = TestParser()

        assert parser.get_ext("document.txt") == ".txt"
        assert parser.get_ext("chat.pdf") == ".pdf"
        assert parser.get_ext("/path/to/file.json") == ".json"


class TestKakaoTalkParser:
    """Test KakaoTalk Parser"""

    @pytest.fixture
    def sample_file(self):
        """샘플 카카오톡 파일 경로"""
        return "tests/fixtures/kakaotalk_sample.txt"

    @pytest.fixture
    def parser(self):
        """KakaoTalkParser 인스턴스"""
        from src.parsers.kakaotalk import KakaoTalkParser
        return KakaoTalkParser()

    def test_parser_instantiation(self, parser):
        """파서 인스턴스 생성 테스트"""
        assert parser is not None
        assert isinstance(parser, BaseParser)

    def test_parse_file_returns_message_list(self, parser, sample_file):
        """파일 파싱 시 Message 리스트 반환"""
        messages = parser.parse(sample_file)

        assert isinstance(messages, list)
        assert len(messages) > 0
        assert all(isinstance(msg, Message) for msg in messages)

    def test_parse_korean_datetime(self, parser, sample_file):
        """한국어 날짜/시간 파싱 테스트"""
        messages = parser.parse(sample_file)

        # 첫 번째 메시지: "2024년 1월 10일 오후 2:30"
        first_msg = messages[0]
        assert first_msg.timestamp.year == 2024
        assert first_msg.timestamp.month == 1
        assert first_msg.timestamp.day == 10
        assert first_msg.timestamp.hour == 14  # 오후 2시 = 14시
        assert first_msg.timestamp.minute == 30

    def test_parse_sender_and_content(self, parser, sample_file):
        """발신자와 메시지 내용 파싱 테스트"""
        messages = parser.parse(sample_file)

        # 첫 번째 메시지
        assert messages[0].sender == "홍길동"
        assert messages[0].content == "안녕하세요"

        # 두 번째 메시지
        assert messages[1].sender == "김철수"
        assert messages[1].content == "네 안녕하세요. 잘 지내셨나요?"

    def test_parse_multiline_message(self, parser, sample_file):
        """멀티라인 메시지 파싱 테스트"""
        messages = parser.parse(sample_file)

        # 세 번째 메시지는 3줄짜리
        multiline_msg = messages[2]
        assert multiline_msg.sender == "홍길동"
        assert "이혼 소송 건" in multiline_msg.content
        assert "이번 주말에 시간 괜찮으신가요?" in multiline_msg.content
        # 멀티라인이 하나의 메시지로 합쳐져야 함
        assert "\n" in multiline_msg.content or " " in multiline_msg.content

    def test_parse_message_count(self, parser, sample_file):
        """메시지 개수 확인"""
        messages = parser.parse(sample_file)

        # 샘플 파일에는 9개의 메시지가 있음 ("사진" 제외)
        # 실제 메시지: 홍길동(1), 김철수(1), 홍길동(멀티라인 1),
        # 김철수(1), 홍길동(1), 홍길동(1), 김철수(멀티라인 1), 홍길동(1)
        assert len(messages) >= 8  # 최소 8개 (사진 메시지 처리 방식에 따라)

    def test_parse_am_pm_conversion(self, parser):
        """오전/오후 시간 변환 테스트"""
        # 오전 9시 메시지
        messages = parser.parse("tests/fixtures/kakaotalk_sample.txt")

        # "2024년 1월 11일 오전 9:00" 메시지 찾기
        am_msg = [m for m in messages if m.timestamp.hour == 9][0]
        assert am_msg.timestamp.hour == 9  # 오전 9시

        # "2024년 1월 10일 오후 2:30" 메시지 찾기
        pm_msg = [m for m in messages if m.timestamp.hour == 14][0]
        assert pm_msg.timestamp.hour == 14  # 오후 2시 = 14시

    def test_parse_excludes_header(self, parser, sample_file):
        """헤더 라인은 파싱에서 제외"""
        messages = parser.parse(sample_file)

        # "홍길동님과 카카오톡 대화"는 메시지가 아님
        # "저장한 날짜"도 메시지가 아님
        assert all("카카오톡 대화" not in msg.content for msg in messages)
        assert all("저장한 날짜" not in msg.content for msg in messages)

    def test_parse_invalid_file_raises_error(self, parser):
        """존재하지 않는 파일은 에러 발생"""
        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent_file.txt")

    def test_metadata_contains_file_type(self, parser, sample_file):
        """메타데이터에 파일 타입 정보 포함"""
        messages = parser.parse(sample_file)

        assert messages[0].metadata.get("source_type") == "kakaotalk"


class TestTextParser:
    """Test Text/PDF Parser"""

    @pytest.fixture
    def sample_text_file(self):
        """샘플 텍스트 파일 경로"""
        return "tests/fixtures/text_sample.txt"

    @pytest.fixture
    def parser(self):
        """TextParser 인스턴스"""
        from src.parsers.text import TextParser
        return TextParser()

    def test_parser_instantiation(self, parser):
        """파서 인스턴스 생성 테스트"""
        assert parser is not None
        assert isinstance(parser, BaseParser)

    def test_parse_text_file_returns_message(self, parser, sample_text_file):
        """텍스트 파일 파싱 시 Message 반환"""
        messages = parser.parse(sample_text_file)

        assert isinstance(messages, list)
        assert len(messages) == 1  # 텍스트 파일은 하나의 메시지로 처리
        assert isinstance(messages[0], Message)

    def test_parse_text_content(self, parser, sample_text_file):
        """텍스트 내용 파싱 테스트"""
        messages = parser.parse(sample_text_file)

        content = messages[0].content

        # 주요 키워드가 포함되어 있는지 확인
        assert "이혼 소송" in content
        assert "증거 자료" in content
        assert "홍길동" in content

    def test_parse_text_sender_is_system(self, parser, sample_text_file):
        """텍스트 파일의 발신자는 'System'"""
        messages = parser.parse(sample_text_file)

        assert messages[0].sender == "System"

    def test_parse_text_timestamp_is_current(self, parser, sample_text_file):
        """텍스트 파일의 타임스탬프는 현재 시간"""
        messages = parser.parse(sample_text_file)

        timestamp = messages[0].timestamp

        # 타임스탬프가 최근 1분 이내인지 확인
        from datetime import datetime
        now = datetime.now()
        assert abs((now - timestamp).total_seconds()) < 60

    def test_parse_text_metadata(self, parser, sample_text_file):
        """메타데이터에 파일 정보 포함"""
        messages = parser.parse(sample_text_file)

        metadata = messages[0].metadata

        assert metadata.get("source_type") == "text"
        assert "filename" in metadata
        assert metadata["filename"].endswith(".txt")

    def test_parse_invalid_file_raises_error(self, parser):
        """존재하지 않는 파일은 에러 발생"""
        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent_file.txt")

    def test_parse_preserves_newlines(self, parser, sample_text_file):
        """개행 문자가 보존되는지 확인"""
        messages = parser.parse(sample_text_file)

        content = messages[0].content

        # 여러 줄로 구성되어 있어야 함
        assert "\n" in content
        assert len(content.split("\n")) > 5

    def test_parse_supports_txt_extension(self, parser):
        """txt 확장자 지원 확인"""
        messages = parser.parse("tests/fixtures/text_sample.txt")

        assert len(messages) > 0
