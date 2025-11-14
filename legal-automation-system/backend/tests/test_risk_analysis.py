"""
리스크 분석 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.risk.risk_analyzer import DocumentRiskAnalyzer, RiskMitigator
from app.services.risk.compliance_checker import ComplianceChecker
from app.services.risk.review_system import ReviewSystem, LegalReviewer
from app.models.document import Document


@pytest.fixture
def risk_analyzer():
    """RiskAnalyzer 인스턴스"""
    return DocumentRiskAnalyzer()


@pytest.fixture
def compliance_checker():
    """ComplianceChecker 인스턴스"""
    return ComplianceChecker()


@pytest.fixture
def sample_contract_document():
    """샘플 계약서 문서"""
    return Document(
        id=1,
        title="근로계약서",
        content="""
        근로계약서

        갑(사용자): 주식회사 테스트
        을(근로자): 홍길동

        제1조 (계약기간)
        본 계약기간은 2024년 1월 1일부터 2024년 12월 31일까지로 한다.

        제2조 (임금)
        기본급은 월 3,000,000원으로 하며, 매월 25일에 지급한다.

        제3조 (근무시간)
        주 52시간을 초과하여 근무할 수 있다.

        제4조 (퇴직금)
        퇴직금은 지급하지 않는다.
        """,
        document_type="contract",
        user_id=1
    )


@pytest.fixture
def sample_lawsuit_document():
    """샘플 소장 문서"""
    return Document(
        id=2,
        title="대여금 청구 소장",
        content="""
        소장

        원고: 김원고
        피고: 이피고

        청구취지:
        피고는 원고에게 금 10,000,000원 및 이에 대한 연 12%의 이자를 지급하라.

        청구원인:
        1. 원고는 2023년 1월 1일 피고에게 1천만원을 대여하였습니다.
        2. 변제기일이 도과하였음에도 피고는 변제하지 않고 있습니다.
        """,
        document_type="lawsuit",
        user_id=1
    )


class TestRiskAnalyzer:
    """리스크 분석기 테스트"""

    @pytest.mark.asyncio
    async def test_analyze_contract_risks(self, risk_analyzer, sample_contract_document):
        """계약서 리스크 분석 테스트"""
        result = await risk_analyzer.analyze_document(
            sample_contract_document,
            deep_analysis=True
        )

        # 기본 결과 확인
        assert result is not None
        assert "risk_level" in result
        assert "risk_score" in result
        assert "risk_factors" in result

        # 리스크 레벨 확인
        assert result["risk_level"] in ["low", "medium", "high"]

        # 리스크 점수 범위 확인
        assert 0 <= result["risk_score"] <= 100

        # 리스크 요인 확인
        assert isinstance(result["risk_factors"], list)
        assert len(result["risk_factors"]) > 0

    @pytest.mark.asyncio
    async def test_identify_illegal_clauses(self, risk_analyzer, sample_contract_document):
        """불법 조항 식별 테스트"""
        # 분석 실행
        result = await risk_analyzer.analyze_document(sample_contract_document)

        # 불법 조항 확인 (주 52시간 초과, 퇴직금 미지급)
        risk_factors = result["risk_factors"]
        illegal_clauses = [r for r in risk_factors if r["severity"] == "high"]

        assert len(illegal_clauses) >= 2

        # 구체적인 위험 요소 확인
        risk_descriptions = [r["description"] for r in risk_factors]
        assert any("52시간" in desc or "근무시간" in desc for desc in risk_descriptions)
        assert any("퇴직금" in desc for desc in risk_descriptions)

    @pytest.mark.asyncio
    async def test_risk_scoring(self, risk_analyzer):
        """리스크 점수 계산 테스트"""
        # 저위험 문서
        low_risk_doc = Document(
            content="표준 근로계약서 내용",
            document_type="contract"
        )
        low_result = await risk_analyzer.analyze_document(low_risk_doc)

        # 고위험 문서
        high_risk_doc = Document(
            content="퇴직금 없음, 주 80시간 근무, 최저임금 미만",
            document_type="contract"
        )
        high_result = await risk_analyzer.analyze_document(high_risk_doc)

        # 점수 비교
        assert low_result["risk_score"] < high_result["risk_score"]
        assert low_result["risk_level"] == "low" or low_result["risk_level"] == "medium"
        assert high_result["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_risk_categories(self, risk_analyzer, sample_contract_document):
        """리스크 카테고리 분류 테스트"""
        result = await risk_analyzer.analyze_document(sample_contract_document)

        # 카테고리 확인
        categories = set(r["category"] for r in result["risk_factors"])
        expected_categories = {"legal", "financial", "operational", "compliance"}

        assert len(categories.intersection(expected_categories)) > 0


class TestComplianceChecker:
    """준수성 검사 테스트"""

    @pytest.mark.asyncio
    async def test_check_labor_law_compliance(self, compliance_checker, sample_contract_document):
        """근로기준법 준수성 검사"""
        result = await compliance_checker.check_compliance(
            sample_contract_document,
            check_categories=["근로계약"]
        )

        # 기본 결과 확인
        assert result is not None
        assert "compliance_score" in result
        assert "violations" in result
        assert "recommendations" in result

        # 위반 사항 확인
        violations = result["violations"]
        assert len(violations) > 0

        # 근로시간 위반 확인
        labor_violations = [v for v in violations if "근로기준법" in v.get("law", "")]
        assert len(labor_violations) > 0

    @pytest.mark.asyncio
    async def test_check_privacy_compliance(self, compliance_checker):
        """개인정보보호법 준수성 검사"""
        privacy_doc = Document(
            content="""
            개인정보 수집 동의서

            1. 수집항목: 이름, 주민등록번호, 주소, 전화번호, 이메일, 가족관계
            2. 수집목적: 마케팅
            3. 보유기간: 무기한
            4. 동의거부권: 없음
            """,
            document_type="agreement"
        )

        result = await compliance_checker.check_compliance(
            privacy_doc,
            check_categories=["개인정보보호"]
        )

        # 위반 사항 확인
        assert result["compliance_score"] < 50  # 낮은 준수율
        assert len(result["violations"]) > 0

        # 구체적 위반 내용
        violations = result["violations"]
        assert any("주민등록번호" in v["description"] for v in violations)
        assert any("무기한" in v["description"] for v in violations)

    @pytest.mark.asyncio
    async def test_multi_category_compliance(self, compliance_checker, sample_contract_document):
        """다중 카테고리 준수성 검사"""
        categories = ["근로계약", "개인정보보호", "전자상거래"]

        result = await compliance_checker.check_compliance(
            sample_contract_document,
            check_categories=categories
        )

        # 카테고리별 결과 확인
        assert "category_results" in result
        assert len(result["category_results"]) == len(categories)

        for category in categories:
            assert category in result["category_results"]
            cat_result = result["category_results"][category]
            assert "score" in cat_result
            assert "compliance" in cat_result


class TestRiskMitigation:
    """리스크 완화 전략 테스트"""

    @pytest.mark.asyncio
    async def test_suggest_mitigations(self, sample_contract_document):
        """리스크 완화 제안 테스트"""
        analyzer = DocumentRiskAnalyzer()
        mitigator = RiskMitigator()

        # 리스크 분석
        analysis = await analyzer.analyze_document(sample_contract_document)

        # 완화 전략 제안
        mitigations = await mitigator.suggest_mitigations(analysis)

        # 결과 확인
        assert mitigations is not None
        assert len(mitigations) > 0

        for mitigation in mitigations:
            assert "title" in mitigation
            assert "description" in mitigation
            assert "priority" in mitigation
            assert "action_items" in mitigation

    @pytest.mark.asyncio
    async def test_prioritize_mitigations(self):
        """완화 전략 우선순위 테스트"""
        mitigator = RiskMitigator()

        # 샘플 리스크 분석 결과
        analysis = {
            "risk_level": "high",
            "risk_score": 85,
            "risk_factors": [
                {"category": "legal", "severity": "high", "description": "불법 조항"},
                {"category": "financial", "severity": "medium", "description": "재무 리스크"},
                {"category": "operational", "severity": "low", "description": "운영 리스크"}
            ]
        }

        mitigations = await mitigator.suggest_mitigations(analysis)

        # 우선순위 확인 (high severity가 먼저)
        priorities = [m["priority"] for m in mitigations]
        assert priorities[0] == "high"
        assert priorities == sorted(priorities, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x])


class TestDocumentReview:
    """문서 검토 시스템 테스트"""

    @pytest.mark.asyncio
    async def test_standard_review(self, sample_contract_document):
        """표준 검토 테스트"""
        review_system = ReviewSystem()

        result = await review_system.review_document(
            sample_contract_document,
            review_depth="standard"
        )

        # 기본 검토 항목 확인
        assert "structure_review" in result
        assert "content_review" in result
        assert "legal_review" in result
        assert "overall_assessment" in result

    @pytest.mark.asyncio
    async def test_thorough_review(self, sample_lawsuit_document):
        """심층 검토 테스트"""
        review_system = ReviewSystem()

        result = await review_system.review_document(
            sample_lawsuit_document,
            review_depth="thorough"
        )

        # 심층 검토 항목 확인
        assert "structure_review" in result
        assert "content_review" in result
        assert "legal_review" in result
        assert "business_review" in result  # thorough에만 포함
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_expert_review(self, sample_contract_document):
        """전문가 검토 테스트"""
        reviewer = LegalReviewer()

        result = await reviewer.expert_review(
            sample_contract_document,
            focus_areas=["tax", "international"]
        )

        # 전문 영역 검토 확인
        assert "expert_opinions" in result
        assert "tax_review" in result
        assert "international_review" in result


class TestComparisonAnalysis:
    """문서 비교 분석 테스트"""

    @pytest.mark.asyncio
    async def test_risk_comparison(self):
        """리스크 비교 테스트"""
        documents = [
            Document(id=1, content="저위험 문서", risk_score=20),
            Document(id=2, content="중위험 문서", risk_score=50),
            Document(id=3, content="고위험 문서", risk_score=80)
        ]

        # 리스크 순위 확인
        sorted_docs = sorted(documents, key=lambda x: x.risk_score, reverse=True)
        assert sorted_docs[0].id == 3  # 고위험
        assert sorted_docs[-1].id == 1  # 저위험

    def test_similarity_comparison(self):
        """유사도 비교 테스트"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        documents = [
            "근로계약서 관련 내용",
            "근로계약에 대한 문서",
            "매매계약서 관련 내용"
        ]

        # TF-IDF 벡터화
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)

        # 코사인 유사도 계산
        similarity_matrix = cosine_similarity(tfidf_matrix)

        # 첫 두 문서(근로계약 관련)의 유사도가 가장 높아야 함
        assert similarity_matrix[0][1] > similarity_matrix[0][2]
        assert similarity_matrix[0][1] > similarity_matrix[1][2]


class TestRiskPatterns:
    """리스크 패턴 테스트"""

    def test_identify_risk_patterns(self):
        """리스크 패턴 식별 테스트"""
        risk_patterns = {
            "illegal_working_hours": r"주\s*\d{3,}시간|80시간\s*이상",
            "no_severance": r"퇴직금\s*없음|퇴직금\s*미지급|퇴직금을?\s*지급하지\s*않",
            "below_minimum_wage": r"최저임금\s*미만|시급\s*[0-8][,\d]+원",
            "unlimited_liability": r"무한\s*책임|제한\s*없는\s*책임"
        }

        test_content = "주 80시간 근무, 퇴직금 없음"

        # 패턴 매칭
        import re
        detected_risks = []
        for risk_name, pattern in risk_patterns.items():
            if re.search(pattern, test_content):
                detected_risks.append(risk_name)

        assert "illegal_working_hours" in detected_risks
        assert "no_severance" in detected_risks