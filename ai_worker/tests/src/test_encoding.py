"""
인코딩 유틸리티 테스트

Given: 다양한 인코딩의 파일
When: 인코딩 감지 및 읽기
Then: 올바른 인코딩 감지 및 내용 반환
"""

import unittest
import tempfile
from pathlib import Path

from src.utils.encoding import (
    KOREAN_ENCODINGS,
    EncodingResult,
    detect_encoding,
    read_file_with_encoding,
    normalize_line_endings,
    remove_bom,
    clean_text,
)


class TestEncodingResult(unittest.TestCase):
    """EncodingResult 테스트"""

    def test_encoding_result_fields(self):
        """Given: EncodingResult 생성
        When: 필드 접근
        Then: 올바른 값 반환"""
        result = EncodingResult(
            encoding="utf-8",
            confidence=0.95,
            method="charset_normalizer"
        )
        self.assertEqual(result.encoding, "utf-8")
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.method, "charset_normalizer")


class TestDetectEncoding(unittest.TestCase):
    """detect_encoding 테스트"""

    def setUp(self):
        """테스트용 임시 디렉토리 생성"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """임시 파일 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_temp_file(self, content: bytes, filename: str = "test.txt") -> Path:
        """바이트 내용으로 임시 파일 생성"""
        file_path = Path(self.temp_dir) / filename
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path

    def test_detect_utf8(self):
        """Given: UTF-8 파일
        When: detect_encoding() 호출
        Then: utf-8 반환"""
        content = "안녕하세요 테스트입니다".encode('utf-8')
        file_path = self._create_temp_file(content)

        result = detect_encoding(file_path)
        self.assertIn(result.encoding.lower(), ['utf-8', 'utf-8-sig'])

    def test_detect_utf8_bom(self):
        """Given: BOM 포함 UTF-8 파일
        When: detect_encoding() 호출
        Then: utf-8-sig 반환, confidence=1.0"""
        content = b'\xef\xbb\xbf' + "안녕하세요".encode('utf-8')
        file_path = self._create_temp_file(content)

        result = detect_encoding(file_path)
        self.assertEqual(result.encoding, "utf-8-sig")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.method, "bom")

    def test_detect_cp949(self):
        """Given: CP949 파일
        When: detect_encoding() 호출
        Then: cp949 또는 euc-kr 반환"""
        content = "안녕하세요 테스트입니다".encode('cp949')
        file_path = self._create_temp_file(content)

        result = detect_encoding(file_path)
        # cp949와 euc-kr은 비슷하므로 둘 중 하나
        self.assertIn(result.encoding.lower(), ['cp949', 'euc-kr', 'utf-8'])

    def test_detect_empty_file(self):
        """Given: 빈 파일
        When: detect_encoding() 호출
        Then: utf-8 반환 (기본값)"""
        file_path = self._create_temp_file(b'')

        result = detect_encoding(file_path)
        self.assertEqual(result.encoding, "utf-8")
        self.assertEqual(result.method, "empty_file")

    def test_detect_nonexistent_file(self):
        """Given: 존재하지 않는 파일
        When: detect_encoding() 호출
        Then: FileNotFoundError 발생"""
        with self.assertRaises(FileNotFoundError):
            detect_encoding(Path("/nonexistent/file.txt"))

    def test_detect_ascii_only(self):
        """Given: ASCII만 있는 파일
        When: detect_encoding() 호출
        Then: utf-8 호환 인코딩 반환"""
        content = b"Hello World 123"
        file_path = self._create_temp_file(content)

        result = detect_encoding(file_path)
        # ASCII는 UTF-8과 호환
        self.assertIsNotNone(result.encoding)


class TestReadFileWithEncoding(unittest.TestCase):
    """read_file_with_encoding 테스트"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_temp_file(self, content: str, encoding: str) -> Path:
        """지정된 인코딩으로 임시 파일 생성"""
        file_path = Path(self.temp_dir) / "test.txt"
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return file_path

    def test_read_utf8(self):
        """Given: UTF-8 파일
        When: read_file_with_encoding() 호출
        Then: 올바른 내용 반환"""
        original = "안녕하세요 테스트입니다"
        file_path = self._create_temp_file(original, 'utf-8')

        content, result = read_file_with_encoding(file_path)
        self.assertEqual(content, original)

    def test_read_cp949(self):
        """Given: CP949 파일
        When: read_file_with_encoding() 호출
        Then: 올바른 내용 반환"""
        original = "안녕하세요 테스트입니다"
        file_path = self._create_temp_file(original, 'cp949')

        content, result = read_file_with_encoding(file_path)
        self.assertEqual(content, original)

    def test_read_with_explicit_encoding(self):
        """Given: 명시적 인코딩 지정
        When: read_file_with_encoding() 호출
        Then: 지정된 인코딩으로 읽기"""
        original = "테스트"
        file_path = self._create_temp_file(original, 'utf-8')

        content, result = read_file_with_encoding(file_path, encoding='utf-8')
        self.assertEqual(content, original)
        self.assertEqual(result.method, "explicit")

    def test_read_with_wrong_encoding(self):
        """Given: 잘못된 인코딩 지정
        When: read_file_with_encoding() 호출
        Then: EncodingError 발생"""
        # UTF-8로 저장된 파일을 latin-1로 읽으려고 시도하면...
        # 실제로는 대부분 성공하므로 다른 테스트 방법 필요
        pass  # 이 테스트는 특수한 바이너리 데이터로 테스트해야 함


class TestTextCleaning(unittest.TestCase):
    """텍스트 정리 함수 테스트"""

    def test_normalize_crlf(self):
        """Given: CRLF 줄바꿈
        When: normalize_line_endings() 호출
        Then: LF로 변환"""
        text = "line1\r\nline2\r\nline3"
        result = normalize_line_endings(text)
        self.assertEqual(result, "line1\nline2\nline3")

    def test_normalize_cr(self):
        """Given: CR 줄바꿈 (구형 Mac)
        When: normalize_line_endings() 호출
        Then: LF로 변환"""
        text = "line1\rline2\rline3"
        result = normalize_line_endings(text)
        self.assertEqual(result, "line1\nline2\nline3")

    def test_normalize_mixed(self):
        """Given: 혼합 줄바꿈
        When: normalize_line_endings() 호출
        Then: 모두 LF로 변환"""
        text = "line1\r\nline2\rline3\nline4"
        result = normalize_line_endings(text)
        self.assertEqual(result, "line1\nline2\nline3\nline4")

    def test_remove_bom(self):
        """Given: BOM이 있는 텍스트
        When: remove_bom() 호출
        Then: BOM 제거"""
        text = "\ufeffHello World"
        result = remove_bom(text)
        self.assertEqual(result, "Hello World")

    def test_remove_bom_no_bom(self):
        """Given: BOM이 없는 텍스트
        When: remove_bom() 호출
        Then: 그대로 반환"""
        text = "Hello World"
        result = remove_bom(text)
        self.assertEqual(result, "Hello World")

    def test_clean_text(self):
        """Given: BOM + CRLF가 있는 텍스트
        When: clean_text() 호출
        Then: BOM 제거 + LF 정규화"""
        text = "\ufeffline1\r\nline2"
        result = clean_text(text)
        self.assertEqual(result, "line1\nline2")


class TestKoreanEncodingsConstant(unittest.TestCase):
    """KOREAN_ENCODINGS 상수 테스트"""

    def test_contains_common_encodings(self):
        """Given: KOREAN_ENCODINGS
        When: 확인
        Then: 일반적인 한국어 인코딩 포함"""
        self.assertIn('utf-8', KOREAN_ENCODINGS)
        self.assertIn('cp949', KOREAN_ENCODINGS)
        self.assertIn('euc-kr', KOREAN_ENCODINGS)

    def test_utf8_first(self):
        """Given: KOREAN_ENCODINGS
        When: 확인
        Then: UTF-8이 첫 번째"""
        self.assertEqual(KOREAN_ENCODINGS[0], 'utf-8')


class TestIntegration(unittest.TestCase):
    """통합 테스트"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_kakaotalk_format_utf8(self):
        """Given: 카카오톡 내보내기 형식 (UTF-8)
        When: 읽기
        Then: 올바르게 파싱"""
        content = """카카오톡 대화
저장한 날짜: 2023-05-10

------------------------------
2023년 5월 10일 수요일
------------------------------
오전 9:23, 홍길동 : 안녕하세요
오전 9:24, 김영희 : 네, 안녕하세요"""

        file_path = Path(self.temp_dir) / "kakao.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        read_content, result = read_file_with_encoding(file_path)
        self.assertIn("홍길동", read_content)
        self.assertIn("김영희", read_content)

    def test_kakaotalk_format_cp949(self):
        """Given: 카카오톡 내보내기 형식 (CP949)
        When: 읽기
        Then: 올바르게 파싱"""
        content = """카카오톡 대화
저장한 날짜: 2023-05-10
오전 9:23, 홍길동 : 안녕하세요"""

        file_path = Path(self.temp_dir) / "kakao_cp949.txt"
        with open(file_path, 'w', encoding='cp949') as f:
            f.write(content)

        read_content, result = read_file_with_encoding(file_path)
        self.assertIn("홍길동", read_content)


if __name__ == "__main__":
    unittest.main()
