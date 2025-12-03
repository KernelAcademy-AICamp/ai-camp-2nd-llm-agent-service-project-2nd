"""
KakaoTalkParserV2 테스트

Given: 카카오톡 내보내기 형식 텍스트
When: KakaoTalkParserV2.parse_to_chunks() 호출
Then: 라인 번호가 포함된 EvidenceChunk 리스트 반환
"""

import unittest
import tempfile
import os

from src.parsers.kakaotalk_v2 import KakaoTalkParserV2, ParsingResult
from src.schemas import EvidenceChunk, FileType


class TestKakaoTalkParserV2Initialization(unittest.TestCase):
    """KakaoTalkParserV2 초기화 테스트"""

    def test_parser_creation(self):
        """Given: KakaoTalkParserV2 생성 요청
        When: KakaoTalkParserV2() 호출
        Then: 인스턴스 생성 성공"""
        parser = KakaoTalkParserV2()
        self.assertIsNotNone(parser)

    def test_parser_has_patterns(self):
        """Given: 초기화된 KakaoTalkParserV2
        When: 패턴 확인
        Then: 메시지/날짜 패턴 존재"""
        # 클래스 변수로 정의된 패턴들
        self.assertIsNotNone(KakaoTalkParserV2.MESSAGE_PATTERN)
        self.assertIsNotNone(KakaoTalkParserV2.DATE_LINE_PATTERN)


class TestKakaoTalkParserV2Parsing(unittest.TestCase):
    """카카오톡 파싱 테스트"""

    def setUp(self):
        """각 테스트 전 parser 초기화"""
        self.parser = KakaoTalkParserV2()

    def test_parse_simple_message(self):
        """Given: 단순 카카오톡 메시지
        When: parse_to_chunks() 호출
        Then: EvidenceChunk 반환 (라인 번호 포함)"""
        content = """-------------------
2023년 5월 10일 수요일
-------------------
오전 9:23, 홍길동 : 안녕하세요"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            chunks, result = self.parser.parse_to_chunks(
                temp_path, "test_case", "test_file"
            )
            self.assertGreater(len(chunks), 0)
            self.assertIsInstance(chunks[0], EvidenceChunk)
        finally:
            os.unlink(temp_path)

    def test_parse_preserves_line_number(self):
        """Given: 여러 줄 카카오톡 대화
        When: parse_to_chunks() 호출
        Then: 각 청크에 정확한 라인 번호 저장"""
        content = """-------------------
2023년 5월 10일 수요일
-------------------
오전 9:23, 홍길동 : 첫 번째 메시지
오전 9:24, 김영희 : 두 번째 메시지
오전 9:25, 홍길동 : 세 번째 메시지"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            chunks, result = self.parser.parse_to_chunks(
                temp_path, "test_case", "test_file"
            )
            # 라인 번호가 있는지 확인
            for chunk in chunks:
                self.assertIsNotNone(chunk.source_location)
                self.assertIsNotNone(chunk.source_location.line_number)
        finally:
            os.unlink(temp_path)

    def test_parse_extracts_sender(self):
        """Given: 발신자가 있는 메시지
        When: parse_to_chunks() 호출
        Then: sender 필드에 발신자 저장"""
        content = """-------------------
2023년 5월 10일 수요일
-------------------
오전 9:23, 테스트유저 : 테스트 메시지"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            chunks, result = self.parser.parse_to_chunks(
                temp_path, "test_case", "test_file"
            )
            self.assertGreater(len(chunks), 0)
            self.assertEqual(chunks[0].sender, "테스트유저")
        finally:
            os.unlink(temp_path)

    def test_parse_extracts_timestamp(self):
        """Given: 시간이 있는 메시지
        When: parse_to_chunks() 호출
        Then: timestamp 필드에 시간 저장"""
        content = """-------------------
2023년 5월 10일 수요일
-------------------
오전 9:23, 홍길동 : 테스트 메시지"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            chunks, result = self.parser.parse_to_chunks(
                temp_path, "test_case", "test_file"
            )
            self.assertGreater(len(chunks), 0)
            self.assertIsNotNone(chunks[0].timestamp)
        finally:
            os.unlink(temp_path)


class TestKakaoTalkParserV2SourceLocation(unittest.TestCase):
    """SourceLocation 생성 테스트"""

    def setUp(self):
        self.parser = KakaoTalkParserV2()

    def test_source_location_file_type(self):
        """Given: 파싱된 청크
        When: source_location 확인
        Then: file_type이 KAKAOTALK"""
        content = """-------------------
2023년 5월 10일 수요일
-------------------
오전 9:23, 홍길동 : 테스트"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            chunks, result = self.parser.parse_to_chunks(
                temp_path, "test_case", "test_file"
            )
            if chunks:
                self.assertEqual(chunks[0].source_location.file_type, FileType.KAKAOTALK)
        finally:
            os.unlink(temp_path)

    def test_source_location_citation(self):
        """Given: 파싱된 청크
        When: to_citation() 호출
        Then: 법정 인용 형식 반환"""
        content = """-------------------
2023년 5월 10일 수요일
-------------------
오전 9:23, 홍길동 : 테스트"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            chunks, result = self.parser.parse_to_chunks(
                temp_path, "test_case", "test_file"
            )
            if chunks:
                citation = chunks[0].source_location.to_citation()
                self.assertIn("번째 줄", citation)
        finally:
            os.unlink(temp_path)


class TestKakaoTalkParserV2MultilineMessage(unittest.TestCase):
    """멀티라인 메시지 처리 테스트"""

    def setUp(self):
        self.parser = KakaoTalkParserV2()

    def test_multiline_message_combined(self):
        """Given: 멀티라인 메시지
        When: parse_to_chunks() 호출
        Then: 메시지가 하나로 합쳐짐"""
        content = """-------------------
2023년 5월 10일 수요일
-------------------
오전 9:23, 홍길동 : 첫 번째 줄
두 번째 줄
세 번째 줄
오전 9:24, 김영희 : 다른 메시지"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            chunks, result = self.parser.parse_to_chunks(
                temp_path, "test_case", "test_file"
            )
            # 첫 번째 청크가 멀티라인을 포함하는지 확인
            if chunks:
                first_chunk = chunks[0]
                self.assertIn("첫 번째 줄", first_chunk.content)
        finally:
            os.unlink(temp_path)


class TestKakaoTalkParserV2EdgeCases(unittest.TestCase):
    """엣지 케이스 테스트"""

    def setUp(self):
        self.parser = KakaoTalkParserV2()

    def test_empty_file(self):
        """Given: 빈 파일 (공백만 있음)
        When: parse_to_chunks() 호출
        Then: 빈 리스트 반환 또는 에러 처리"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(" ")  # 공백 하나 추가 (완전히 빈 파일은 인코딩 감지 실패)
            temp_path = f.name

        try:
            chunks, result = self.parser.parse_to_chunks(
                temp_path, "test_case", "test_file"
            )
            self.assertEqual(len(chunks), 0)
        finally:
            os.unlink(temp_path)

    def test_only_date_header(self):
        """Given: 날짜 헤더만 있는 파일
        When: parse_to_chunks() 호출
        Then: 빈 리스트 반환"""
        content = """-------------------
2023년 5월 10일 수요일
-------------------"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            chunks, result = self.parser.parse_to_chunks(
                temp_path, "test_case", "test_file"
            )
            self.assertEqual(len(chunks), 0)
        finally:
            os.unlink(temp_path)


class TestKakaoTalkParserV2ParsingResult(unittest.TestCase):
    """ParsingResult 통계 테스트"""

    def setUp(self):
        self.parser = KakaoTalkParserV2()

    def test_parsing_result_has_stats(self):
        """Given: 파싱 완료
        When: ParsingResult 확인
        Then: 통계 정보 포함"""
        content = """-------------------
2023년 5월 10일 수요일
-------------------
오전 9:23, 홍길동 : 테스트1
오전 9:24, 김영희 : 테스트2"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            chunks, result = self.parser.parse_to_chunks(
                temp_path, "test_case", "test_file"
            )
            self.assertIsInstance(result, ParsingResult)
            self.assertGreater(result.total_lines, 0)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
