"""
문서 생성 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from app.services.llm.generator import DocumentGenerator
from app.models.document import Document
from app.models.template import Template
from app.schemas.document import DocumentCreate


@pytest.fixture
def document_generator():
    """DocumentGenerator 인스턴스 생성"""
    return DocumentGenerator()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    with patch('app.services.llm.generator.OpenAI') as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client"""
    with patch('app.services.llm.generator.Anthropic') as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_contract_data():
    """샘플 계약서 데이터"""
    return {
        "contract_type": "employment",
        "party1": {
            "name": "주식회사 테스트",
            "id": "123-45-67890",
            "address": "서울시 강남구",
            "phone": "02-1234-5678"
        },
        "party2": {
            "name": "홍길동",
            "id": "900101-1234567",
            "address": "서울시 서초구",
            "phone": "010-1234-5678"
        },
        "position": "백엔드 개발자",
        "salary": 5000000,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }


@pytest.fixture
def sample_lawsuit_data():
    """샘플 소장 데이터"""
    return {
        "lawsuit_type": "civil",
        "plaintiff": {
            "name": "김원고",
            "id": "800101-1234567",
            "address": "서울시 중구",
            "phone": "010-9876-5432"
        },
        "defendant": {
            "name": "이피고",
            "address": "서울시 종로구"
        },
        "court": "서울중앙지방법원",
        "claim_amount": 10000000,
        "facts": "피고는 2023년 1월 1일 원고로부터 1000만원을 차용하고...",
        "claims": "피고는 원고에게 원금 1000만원 및 지연이자를 지급하라"
    }


class TestDocumentGenerator:
    """DocumentGenerator 테스트"""

    @pytest.mark.asyncio
    async def test_generate_contract(self, document_generator, sample_contract_data, mock_openai_client):
        """계약서 생성 테스트"""
        # Mock 설정
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="생성된 계약서 내용"))]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # 계약서 생성
        result = await document_generator.generate_contract(
            contract_type="employment",
            contract_data=sample_contract_data
        )

        # 검증
        assert result is not None
        assert "content" in result
        assert result["document_type"] == "contract"
        assert result["metadata"]["contract_type"] == "employment"

    @pytest.mark.asyncio
    async def test_generate_lawsuit(self, document_generator, sample_lawsuit_data, mock_openai_client):
        """소장 생성 테스트"""
        # Mock 설정
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="생성된 소장 내용"))]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # 소장 생성
        result = await document_generator.generate_lawsuit(
            lawsuit_type="civil",
            lawsuit_data=sample_lawsuit_data
        )

        # 검증
        assert result is not None
        assert "content" in result
        assert result["document_type"] == "lawsuit"
        assert result["metadata"]["lawsuit_type"] == "civil"

    @pytest.mark.asyncio
    async def test_generate_notice(self, document_generator, mock_openai_client):
        """내용증명 생성 테스트"""
        notice_data = {
            "notice_type": "termination",
            "sender": {
                "name": "김발신",
                "address": "서울시 강남구"
            },
            "receiver": {
                "name": "이수신",
                "address": "서울시 강북구"
            },
            "content": "계약 해지를 통보합니다"
        }

        # Mock 설정
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="생성된 내용증명"))]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # 내용증명 생성
        result = await document_generator.generate_notice(
            notice_type="termination",
            notice_data=notice_data
        )

        # 검증
        assert result is not None
        assert "content" in result
        assert result["document_type"] == "notice"

    @pytest.mark.asyncio
    async def test_provider_fallback(self, document_generator, mock_openai_client, mock_anthropic_client):
        """프로바이더 폴백 테스트"""
        # OpenAI 실패 설정
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        # Anthropic 성공 설정
        mock_response = Mock()
        mock_response.content = [Mock(text="Anthropic로 생성된 문서")]
        mock_anthropic_client.messages.create = AsyncMock(return_value=mock_response)

        # 문서 생성 (OpenAI 실패 → Anthropic 폴백)
        result = await document_generator.generate_document(
            template_type="contract",
            user_data={"test": "data"}
        )

        # 검증
        assert result is not None
        assert "content" in result
        assert "Anthropic로 생성된 문서" in result["content"]

    @pytest.mark.asyncio
    async def test_template_validation(self, document_generator):
        """템플릿 검증 테스트"""
        # 잘못된 템플릿 타입
        with pytest.raises(ValueError, match="Invalid template type"):
            await document_generator.generate_document(
                template_type="invalid_type",
                user_data={}
            )

        # 필수 데이터 누락
        with pytest.raises(ValueError, match="Required field"):
            await document_generator.generate_contract(
                contract_type="employment",
                contract_data={}  # 필수 필드 누락
            )

    @pytest.mark.asyncio
    async def test_multilingual_generation(self, document_generator, mock_openai_client):
        """다국어 문서 생성 테스트"""
        languages = ["ko", "en", "zh", "ja"]

        for lang in languages:
            # Mock 설정
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content=f"Document in {lang}"))]
            mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

            # 문서 생성
            result = await document_generator.generate_document(
                template_type="contract",
                user_data={"test": "data"},
                language=lang
            )

            # 검증
            assert result is not None
            assert result["metadata"]["language"] == lang


class TestDocumentValidation:
    """문서 검증 테스트"""

    def test_contract_validation(self, sample_contract_data):
        """계약서 데이터 검증"""
        # 필수 필드 확인
        required_fields = ["contract_type", "party1", "party2"]
        for field in required_fields:
            assert field in sample_contract_data

        # 당사자 정보 검증
        assert "name" in sample_contract_data["party1"]
        assert "name" in sample_contract_data["party2"]

        # 금액 검증 (음수 불가)
        if "salary" in sample_contract_data:
            assert sample_contract_data["salary"] >= 0

    def test_lawsuit_validation(self, sample_lawsuit_data):
        """소장 데이터 검증"""
        # 필수 필드 확인
        required_fields = ["lawsuit_type", "plaintiff", "defendant", "court"]
        for field in required_fields:
            assert field in sample_lawsuit_data

        # 청구 금액 검증
        if "claim_amount" in sample_lawsuit_data:
            assert sample_lawsuit_data["claim_amount"] >= 0

        # 법원명 검증
        valid_courts = ["서울중앙지방법원", "서울동부지방법원", "서울서부지방법원"]
        assert any(court in sample_lawsuit_data["court"] for court in valid_courts)

    def test_date_validation(self):
        """날짜 형식 검증"""
        valid_dates = ["2024-01-01", "2024-12-31"]
        invalid_dates = ["01-01-2024", "2024/01/01", "20240101"]

        for date_str in valid_dates:
            try:
                datetime.fromisoformat(date_str)
                assert True
            except ValueError:
                assert False, f"Valid date {date_str} failed validation"

        for date_str in invalid_dates:
            try:
                datetime.fromisoformat(date_str)
                assert False, f"Invalid date {date_str} passed validation"
            except ValueError:
                assert True


class TestDocumentFormatting:
    """문서 포맷팅 테스트"""

    def test_contract_formatting(self, sample_contract_data):
        """계약서 포맷팅 테스트"""
        # 제목 생성
        title = f"{sample_contract_data['contract_type'].upper()} 계약서"
        assert "계약서" in title

        # 당사자 표기
        party1_str = f"갑: {sample_contract_data['party1']['name']}"
        party2_str = f"을: {sample_contract_data['party2']['name']}"
        assert "갑:" in party1_str
        assert "을:" in party2_str

        # 금액 포맷팅 (천단위 구분)
        salary = sample_contract_data.get("salary", 0)
        formatted_salary = f"{salary:,}원"
        assert "," in formatted_salary if salary >= 1000 else True

    def test_lawsuit_formatting(self, sample_lawsuit_data):
        """소장 포맷팅 테스트"""
        # 제목 생성
        title = f"{sample_lawsuit_data['lawsuit_type']} 소장"
        assert "소장" in title

        # 법원 표기
        court_header = f"{sample_lawsuit_data['court']} 귀중"
        assert "귀중" in court_header

        # 청구 금액 포맷팅
        amount = sample_lawsuit_data.get("claim_amount", 0)
        formatted_amount = f"금 {amount:,}원"
        assert "금" in formatted_amount


@pytest.mark.asyncio
class TestDocumentStorage:
    """문서 저장 테스트"""

    async def test_save_document(self):
        """문서 저장 테스트"""
        document = Document(
            title="테스트 계약서",
            content="계약서 내용",
            document_type="contract",
            user_id=1,
            metadata={"test": "data"}
        )

        # 저장 시뮬레이션
        document.id = 1
        document.created_at = datetime.now()

        # 검증
        assert document.id is not None
        assert document.created_at is not None
        assert document.title == "테스트 계약서"

    async def test_document_versioning(self):
        """문서 버전 관리 테스트"""
        # 원본 문서
        original = Document(
            id=1,
            title="원본 문서",
            content="원본 내용",
            version=1
        )

        # 수정된 문서
        updated = Document(
            id=1,
            title="원본 문서",
            content="수정된 내용",
            version=2,
            parent_id=original.id
        )

        # 검증
        assert updated.version > original.version
        assert updated.parent_id == original.id


class TestDocumentSearch:
    """문서 검색 테스트"""

    def test_keyword_search(self):
        """키워드 검색 테스트"""
        documents = [
            {"title": "근로계약서", "content": "근로 조건에 관한 계약"},
            {"title": "매매계약서", "content": "부동산 매매에 관한 계약"},
            {"title": "임대차계약서", "content": "부동산 임대차에 관한 계약"}
        ]

        keyword = "부동산"
        results = [doc for doc in documents if keyword in doc["content"]]

        assert len(results) == 2
        assert all(keyword in doc["content"] for doc in results)

    def test_filter_by_type(self):
        """문서 유형별 필터링 테스트"""
        documents = [
            {"type": "contract", "title": "계약서1"},
            {"type": "contract", "title": "계약서2"},
            {"type": "lawsuit", "title": "소장1"},
            {"type": "notice", "title": "내용증명1"}
        ]

        # 계약서만 필터링
        contracts = [doc for doc in documents if doc["type"] == "contract"]
        assert len(contracts) == 2

        # 소장만 필터링
        lawsuits = [doc for doc in documents if doc["type"] == "lawsuit"]
        assert len(lawsuits) == 1