"""
DraftGenerator 테스트
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.analysis.draft_generator import (
    DraftGenerator,
    DIVORCE_COMPLAINT_TEMPLATE,
    FEW_SHOT_EXAMPLES
)
from src.analysis.evidence_scorer import ScoringResult
from src.analysis.risk_analyzer import RiskAssessment, RiskLevel
from src.analysis.analysis_engine import AnalysisResult
from src.service_rag.schemas import PartyInfo, DraftDocument


class TestDivorceComplaintTemplate:
    """이혼 소장 템플릿 테스트"""

    def test_template_has_required_sections(self):
        """필수 섹션이 모두 있는지 확인"""
        template = DIVORCE_COMPLAINT_TEMPLATE

        section_names = [s.section_name for s in template.sections]

        assert "사건명" in section_names
        assert "당사자" in section_names
        assert "청구취지" in section_names
        assert "청구원인" in section_names
        assert "입증방법" in section_names
        assert "첨부서류" in section_names

    def test_template_has_placeholders(self):
        """플레이스홀더가 정의되어 있는지 확인"""
        template = DIVORCE_COMPLAINT_TEMPLATE

        assert "plaintiff_name" in template.placeholders
        assert "defendant_name" in template.placeholders
        assert "alimony_amount" in template.placeholders
        assert "marriage_date" in template.placeholders

    def test_template_sections_are_ordered(self):
        """섹션 순서가 올바른지 확인"""
        template = DIVORCE_COMPLAINT_TEMPLATE

        sorted_sections = sorted(template.sections, key=lambda x: x.order)

        assert sorted_sections[0].section_name == "사건명"
        assert sorted_sections[1].section_name == "당사자"
        assert sorted_sections[2].section_name == "청구취지"


class TestFewShotExamples:
    """Few-shot 예시 테스트"""

    def test_examples_contain_article_840(self):
        """민법 제840조 관련 내용 포함 확인"""
        assert "제840조" in FEW_SHOT_EXAMPLES
        assert "부정한 행위" in FEW_SHOT_EXAMPLES
        assert "악의의 유기" in FEW_SHOT_EXAMPLES
        assert "부당한 대우" in FEW_SHOT_EXAMPLES

    def test_examples_have_structure(self):
        """예시가 구조화되어 있는지 확인"""
        assert "[증거 분석 결과]" in FEW_SHOT_EXAMPLES
        assert "[청구원인 작성 예시]" in FEW_SHOT_EXAMPLES


class TestDraftGenerator:
    """DraftGenerator 클래스 테스트"""

    @pytest.fixture
    def mock_analysis_result(self):
        """테스트용 분석 결과"""
        # ScoringResult 목 객체 (실제 ScoringResult 속성에 맞춤)
        mock_scoring = MagicMock(spec=ScoringResult)
        mock_scoring.score = 8.5
        mock_scoring.matched_keywords = ["부정행위", "외도", "사랑해"]
        mock_scoring.reasoning = "피고가 제3자와 '사랑해, 보고싶어' 등의 메시지를 주고받은 것은 부부 사이의 정조의무에 위반하는 부정한 행위에 해당함"

        # RiskAssessment 목 객체
        mock_risk = MagicMock(spec=RiskAssessment)
        mock_risk.risk_level = RiskLevel.HIGH
        mock_risk.primary_concerns = ["외도 의심 증거"]
        mock_risk.recommendations = ["추가 증거 수집 권장"]
        mock_risk.risk_factors = ["부정행위 증거"]

        # AnalysisResult 생성
        return AnalysisResult(
            case_id="test_case_001",
            total_messages=50,
            average_score=6.5,
            high_value_messages=[mock_scoring],
            risk_assessment=mock_risk,
            summary={"key_findings": ["부정행위 증거 발견"]}
        )

    @pytest.fixture
    def plaintiff_info(self):
        """테스트용 원고 정보"""
        return PartyInfo(
            name="김원고",
            resident_number="800101-1234567",
            address="서울시 강남구 테헤란로 123",
            phone="010-1234-5678",
            role="plaintiff"
        )

    @pytest.fixture
    def defendant_info(self):
        """테스트용 피고 정보"""
        return PartyInfo(
            name="이피고",
            resident_number="820202-2345678",
            address="서울시 서초구 반포대로 456",
            phone=None,
            role="defendant"
        )

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_api_key'})
    @patch('src.analysis.draft_generator.OpenAI')
    def test_draft_generator_initialization(self, mock_openai):
        """DraftGenerator 초기화 테스트"""
        generator = DraftGenerator()

        assert generator.api_key == 'test_api_key'
        assert "divorce_complaint" in generator.templates

    def test_draft_generator_requires_api_key(self):
        """API 키 없이 초기화 시 에러"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API 키가 필요합니다"):
                DraftGenerator()

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_api_key'})
    @patch('src.analysis.draft_generator.OpenAI')
    def test_extract_evidence_summary(
        self, mock_openai, mock_analysis_result
    ):
        """증거 요약 추출 테스트"""
        generator = DraftGenerator()

        summary = generator._extract_evidence_summary(mock_analysis_result)

        assert summary["case_id"] == "test_case_001"
        assert summary["total_messages"] == 50
        assert summary["average_score"] == 6.5
        assert len(summary["high_value_evidence"]) == 1

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_api_key'})
    @patch('src.analysis.draft_generator.OpenAI')
    def test_format_evidence_list(
        self, mock_openai, mock_analysis_result
    ):
        """증거 목록 포맷팅 테스트"""
        generator = DraftGenerator()

        evidence_list = generator._format_evidence_list(mock_analysis_result)

        assert "갑 제" in evidence_list
        assert "카카오톡 대화 내역" in evidence_list

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_api_key'})
    @patch('src.analysis.draft_generator.OpenAI')
    def test_fill_template(self, mock_openai):
        """템플릿 채우기 테스트"""
        generator = DraftGenerator()

        values = {
            "plaintiff_name": "김원고",
            "plaintiff_resident_number": "800101-1234567",
            "plaintiff_address": "서울시 강남구",
            "plaintiff_phone": "010-1234-5678",
            "defendant_name": "이피고",
            "defendant_resident_number": "820202-2345678",
            "defendant_address": "서울시 서초구",
            "alimony_amount": "30,000,000",
            "child_custody_claim": "해당 없음",
            "marriage_date": "2010년 5월 1일",
            "children_info": "슬하에 자녀가 없습니다.",
            "marriage_breakdown_reason": "피고의 외도로 인한 혼인 파탄",
            "divorce_grounds": "민법 제840조 제1호",
            "alimony_reason": "정신적 손해",
            "evidence_list": "3. 갑 제3호증: 카카오톡 대화 내역"
        }

        content = generator._fill_template(
            DIVORCE_COMPLAINT_TEMPLATE,
            values
        )

        assert "김원고" in content
        assert "이피고" in content
        assert "30,000,000" in content
        assert "2010년 5월 1일" in content
        assert "가정법원 귀중" in content

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_api_key'})
    @patch('src.analysis.draft_generator.OpenAI')
    def test_generate_divorce_complaint_integration(
        self,
        mock_openai,
        mock_analysis_result,
        plaintiff_info,
        defendant_info
    ):
        """이혼 소장 생성 통합 테스트 (GPT 호출 모킹)"""
        # GPT 응답 모킹
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """
1. 혼인파탄 경위 (breakdown_reason):
피고는 2023년 3월경부터 제3자와 부정한 관계를 맺어왔습니다.

2. 이혼 사유 (legal_grounds):
민법 제840조 제1호의 배우자의 부정한 행위에 해당합니다.

3. 위자료 청구 원인 (alimony_reason):
피고의 부정행위로 인해 원고는 심대한 정신적 고통을 받았습니다.
"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        generator = DraftGenerator()
        draft = generator.generate_divorce_complaint(
            analysis_result=mock_analysis_result,
            plaintiff=plaintiff_info,
            defendant=defendant_info,
            marriage_date="2010년 5월 1일",
            alimony_amount=50000000
        )

        # 검증
        assert isinstance(draft, DraftDocument)
        assert draft.document_type == "divorce_complaint"
        assert "김원고" in draft.content
        assert "이피고" in draft.content
        assert draft.case_id == "test_case_001"
        assert len(draft.legal_grounds) > 0

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_api_key'})
    @patch('src.analysis.draft_generator.OpenAI')
    def test_get_available_templates(self, mock_openai):
        """템플릿 목록 조회 테스트"""
        generator = DraftGenerator()

        templates = generator.get_available_templates()

        assert "divorce_complaint" in templates


class TestParseLogicalReasoning:
    """법적 논거 파싱 테스트"""

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_api_key'})
    @patch('src.analysis.draft_generator.OpenAI')
    def test_parse_structured_response(self, mock_openai):
        """구조화된 응답 파싱"""
        generator = DraftGenerator()

        text = """
1. 혼인파탄 경위 (breakdown_reason):
피고가 외도를 하였습니다.

2. 이혼 사유 (legal_grounds):
민법 제840조 제1호에 해당합니다.

3. 위자료 청구 원인 (alimony_reason):
정신적 손해를 입었습니다.
"""

        result = generator._parse_legal_reasoning(text)

        assert "외도" in result["breakdown_reason"]
        assert "제840조" in result["legal_grounds"]
        assert "정신적 손해" in result["alimony_reason"]

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_api_key'})
    @patch('src.analysis.draft_generator.OpenAI')
    def test_parse_unstructured_response(self, mock_openai):
        """비구조화된 응답 시 전체 텍스트 사용"""
        generator = DraftGenerator()

        text = "단순한 텍스트 응답입니다."

        result = generator._parse_legal_reasoning(text)

        # breakdown_reason에 전체 텍스트가 들어감
        assert result["breakdown_reason"] == text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
