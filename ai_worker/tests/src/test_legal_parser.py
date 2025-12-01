"""
Test suite for LegalParser
Following TDD approach: RED-GREEN-REFACTOR
"""

import pytest
from datetime import date
from src.service_rag.legal_parser import LegalParser, StatuteParser, CaseLawParser
from src.service_rag.schemas import Statute, CaseLaw


class TestLegalParserInitialization:
    """Test LegalParser initialization"""

    def test_legal_parser_creation(self):
        """LegalParser 생성 테스트"""
        parser = LegalParser()

        assert parser is not None

    def test_parser_has_components(self):
        """내부 파서 컴포넌트 확인"""
        parser = LegalParser()

        assert hasattr(parser, 'statute_parser')
        assert hasattr(parser, 'case_parser')


class TestStatuteParser:
    """Test statute parsing"""

    def test_parse_simple_statute(self):
        """간단한 법령 조문 파싱 테스트"""
        parser = StatuteParser()
        text = """
        민법 제840조(이혼원인)

        ① 부부의 일방은 다음 각호의 사유가 있는 경우에는 가정법원에 이혼을 청구할 수 있다.
        1. 배우자에 부정한 행위가 있었을 때
        """

        result = parser.parse(text, statute_id="statute_001")

        assert isinstance(result, Statute)
        assert result.statute_id == "statute_001"
        assert result.name == "민법"
        assert result.article_number == "제840조"
        assert "이혼원인" in result.content or "부부의 일방" in result.content

    def test_parse_statute_with_metadata(self):
        """메타데이터 포함 법령 파싱 테스트"""
        parser = StatuteParser()
        text = """
        민법 제840조(이혼원인)

        ① 부부의 일방은 다음 각호의 사유가 있는 경우에는 가정법원에 이혼을 청구할 수 있다.
        """
        metadata = {
            "statute_number": "법률 제14965호",
            "effective_date": "2018-02-21",
            "category": "가족관계법"
        }

        result = parser.parse(text, statute_id="statute_002", metadata=metadata)

        assert result.statute_number == "법률 제14965호"
        assert result.category == "가족관계법"

    def test_extract_statute_name(self):
        """법령명 추출 테스트"""
        parser = StatuteParser()
        text = "민법 제840조(이혼원인)"

        name = parser._extract_statute_name(text)

        assert name == "민법"

    def test_extract_article_number(self):
        """조항 번호 추출 테스트"""
        parser = StatuteParser()
        text = "민법 제840조(이혼원인)"

        article = parser._extract_article_number(text)

        assert article == "제840조"

    def test_parse_multiple_statutes(self):
        """여러 조문 파싱 테스트"""
        parser = StatuteParser()
        texts = [
            "민법 제840조(이혼원인)\n① 부부의 일방은...",
            "민법 제841조(재판상 이혼)\n부부의 일방이..."
        ]

        results = parser.parse_batch(texts)

        assert len(results) == 2
        assert all(isinstance(r, Statute) for r in results)
        assert results[0].article_number == "제840조"
        assert results[1].article_number == "제841조"


class TestCaseLawParser:
    """Test case law parsing"""

    def test_parse_simple_case(self):
        """간단한 판례 파싱 테스트"""
        parser = CaseLawParser()
        text = """
        사건번호: 2019다12345
        법원: 대법원
        선고일: 2020-05-15
        사건명: 이혼 청구의 소

        [판결 요지]
        부부 일방의 부정행위가 인정되는 경우 이혼 사유에 해당한다.

        [판결 전문]
        원고는 피고의 부정행위를 이유로 이혼을 청구하였고...
        """

        result = parser.parse(text, case_id="case_001")

        assert isinstance(result, CaseLaw)
        assert result.case_id == "case_001"
        assert result.case_number == "2019다12345"
        assert result.court == "대법원"
        assert result.case_name == "이혼 청구의 소"
        assert "부정행위" in result.summary

    def test_parse_case_with_date(self):
        """날짜 파싱 테스트"""
        parser = CaseLawParser()
        text = """
        사건번호: 2019다12345
        법원: 대법원
        선고일: 2020-05-15
        사건명: 이혼 청구의 소

        [판결 요지]
        테스트 판결 요지
        """

        result = parser.parse(text, case_id="case_002")

        assert result.decision_date == date(2020, 5, 15)

    def test_extract_case_number(self):
        """사건번호 추출 테스트"""
        parser = CaseLawParser()
        text = "사건번호: 2019다12345"

        case_number = parser._extract_case_number(text)

        assert case_number == "2019다12345"

    def test_extract_court(self):
        """법원 추출 테스트"""
        parser = CaseLawParser()
        text = "법원: 대법원"

        court = parser._extract_court(text)

        assert court == "대법원"

    def test_extract_summary(self):
        """판결 요지 추출 테스트"""
        parser = CaseLawParser()
        text = """
        [판결 요지]
        부부 일방의 부정행위가 인정되는 경우 이혼 사유에 해당한다.

        [판결 전문]
        기타 내용...
        """

        summary = parser._extract_summary(text)

        assert "부정행위" in summary
        assert "판결 전문" not in summary

    def test_parse_multiple_cases(self):
        """여러 판례 파싱 테스트"""
        parser = CaseLawParser()
        texts = [
            "사건번호: 2019다12345\n법원: 대법원\n선고일: 2020-05-15\n사건명: 이혼 청구의 소\n[판결 요지]\n테스트1",
            "사건번호: 2020다67890\n법원: 서울고등법원\n선고일: 2021-03-10\n사건명: 재산분할\n[판결 요지]\n테스트2"
        ]

        results = parser.parse_batch(texts)

        assert len(results) == 2
        assert all(isinstance(r, CaseLaw) for r in results)
        assert results[0].case_number == "2019다12345"
        assert results[1].case_number == "2020다67890"


class TestIntegration:
    """Test LegalParser integration"""

    def test_parse_statute_through_main_parser(self):
        """메인 파서를 통한 법령 파싱 테스트"""
        parser = LegalParser()
        text = "민법 제840조(이혼원인)\n① 부부의 일방은..."

        result = parser.parse_statute(text, statute_id="s001")

        assert isinstance(result, Statute)
        assert result.name == "민법"

    def test_parse_case_through_main_parser(self):
        """메인 파서를 통한 판례 파싱 테스트"""
        parser = LegalParser()
        text = "사건번호: 2019다12345\n법원: 대법원\n선고일: 2020-05-15\n사건명: 이혼\n[판결 요지]\n테스트"

        result = parser.parse_case(text, case_id="c001")

        assert isinstance(result, CaseLaw)
        assert result.case_number == "2019다12345"


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_statute_text(self):
        """빈 법령 텍스트 테스트"""
        parser = StatuteParser()
        text = ""

        with pytest.raises(ValueError, match="Empty statute text"):
            parser.parse(text, statute_id="empty")

    def test_empty_case_text(self):
        """빈 판례 텍스트 테스트"""
        parser = CaseLawParser()
        text = ""

        with pytest.raises(ValueError, match="Empty case text"):
            parser.parse(text, case_id="empty")

    def test_malformed_statute(self):
        """잘못된 형식의 법령 테스트"""
        parser = StatuteParser()
        text = "잘못된 형식의 텍스트"

        # 파싱은 되지만 기본값 사용
        result = parser.parse(text, statute_id="malformed")

        assert result.statute_id == "malformed"
        assert result.content == text.strip()

    def test_malformed_case(self):
        """잘못된 형식의 판례 테스트"""
        parser = CaseLawParser()
        text = "잘못된 형식의 판례"

        # 필수 필드 누락 시 에러
        with pytest.raises(ValueError, match="Missing required fields"):
            parser.parse(text, case_id="malformed")
