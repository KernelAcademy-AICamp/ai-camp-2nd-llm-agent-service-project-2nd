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


class TestJSONCaseLawParser:
    """Test JSON case law parsing for AI Hub precedent data"""

    @pytest.fixture
    def sample_json_case(self):
        """AI Hub 판례 JSON 샘플 데이터"""
        return {
            "info": {
                "id": 41055905,
                "dataType": "판결문",
                "caseNm": "이혼등",
                "caseTitle": "서울가정법원 2001. 5. 29. 선고 2000드단21348 판결：항소기각, 확정",
                "courtType": "판례(하급심)",
                "courtNm": "서울가정법원",
                "judmnAdjuDe": "2001-05-29",
                "caseNoID": "2000드단21348",
                "caseNo": "2000드단21348"
            },
            "jdgmn": "유책배우자의 이혼청구를 인용한 사례",
            "jdgmnInfo": [
                {
                    "question": "유책배우자의 이혼청구권이 인정될 수 있는가?",
                    "answer": "긍정"
                }
            ],
            "Summary": [
                {
                    "summ_contxt": "상세한 판결 내용...",
                    "summ_pass": "요약된 판결 내용"
                }
            ],
            "keyword_tagg": [{"id": 1, "keyword": "이혼"}],
            "Reference_info": {
                "reference_rules": "민법 제840조",
                "reference_court_case": ""
            },
            "Class_info": {
                "class_name": "가사",
                "instance_name": "이혼"
            }
        }

    def test_parse_json_case(self, sample_json_case):
        """JSON 형식 판례 데이터 파싱 테스트 (RED)"""
        parser = CaseLawParser()

        result = parser.parse_json(sample_json_case)

        assert isinstance(result, CaseLaw)
        assert result.case_number == "2000드단21348"
        assert result.court == "서울가정법원"
        assert result.decision_date == date(2001, 5, 29)
        assert result.case_name == "이혼등"
        assert "유책배우자" in result.summary
        assert result.category == "가사"
        assert "민법 제840조" in result.related_statutes

    def test_parse_json_case_with_full_summary(self, sample_json_case):
        """JSON 판례의 상세 요약 포함 파싱 테스트 (RED)"""
        parser = CaseLawParser()

        result = parser.parse_json(sample_json_case, include_full_summary=True)

        assert result.full_text is not None
        assert "상세한 판결 내용" in result.full_text

    def test_parse_json_case_extracts_category(self, sample_json_case):
        """JSON 판례 카테고리 추출 테스트"""
        parser = CaseLawParser()

        result = parser.parse_json(sample_json_case)

        # Class_info에서 카테고리 추출 확인
        assert result.category == "가사"

    def test_parse_json_batch(self, sample_json_case):
        """여러 JSON 판례 일괄 파싱 테스트 (RED)"""
        parser = CaseLawParser()
        json_cases = [sample_json_case, sample_json_case]  # 2개 동일 데이터

        results = parser.parse_json_batch(json_cases)

        assert len(results) == 2
        assert all(isinstance(r, CaseLaw) for r in results)

    def test_parse_json_file(self, tmp_path):
        """JSON 파일에서 판례 파싱 테스트 (RED)"""
        import json
        parser = CaseLawParser()

        # 임시 JSON 파일 생성 (명시적 UTF-8 인코딩)
        json_data = [{
            "info": {
                "id": 1,
                "caseNm": "test",
                "courtNm": "Supreme Court",
                "judmnAdjuDe": "2020-01-01",
                "caseNo": "2020da1234"
            },
            "jdgmn": "test case summary",
            "Reference_info": {"reference_rules": ""},
            "Class_info": {"class_name": "civil"}
        }]
        json_file = tmp_path / "test_cases.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False)

        results = parser.parse_json_file(str(json_file))

        assert len(results) == 1
        assert results[0].case_number == "2020da1234"

    def test_parse_json_handles_missing_optional_fields(self):
        """선택적 필드 누락 시 기본값 처리 테스트 (RED)"""
        parser = CaseLawParser()
        minimal_json = {
            "info": {
                "id": 1,
                "caseNm": "테스트",
                "courtNm": "대법원",
                "judmnAdjuDe": "2020-01-01",
                "caseNo": "2020다1234"
            },
            "jdgmn": "테스트 요지"
        }

        result = parser.parse_json(minimal_json)

        assert result.case_number == "2020다1234"
        assert result.related_statutes == []
        assert result.category == "가사"  # 기본값

    def test_parse_json_invalid_date_format(self):
        """잘못된 날짜 형식 처리 테스트 (RED)"""
        parser = CaseLawParser()
        invalid_json = {
            "info": {
                "id": 1,
                "caseNm": "테스트",
                "courtNm": "대법원",
                "judmnAdjuDe": "2020/01/01",  # 잘못된 형식
                "caseNo": "2020다1234"
            },
            "jdgmn": "테스트"
        }

        with pytest.raises(ValueError, match="Invalid date format"):
            parser.parse_json(invalid_json)


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
