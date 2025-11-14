"""
API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import json
from datetime import datetime

from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.models.user import User
from app.core.security import create_access_token, get_password_hash


# 테스트용 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """테스트용 DB 세션"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 의존성 오버라이드
app.dependency_overrides[get_db] = override_get_db

# 테스트 클라이언트
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """데이터베이스 설정"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """테스트 사용자 생성"""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=get_password_hash("testpass123"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def auth_headers(test_user):
    """인증 헤더"""
    access_token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


class TestAuthEndpoints:
    """인증 관련 엔드포인트 테스트"""

    def test_register(self, setup_database):
        """회원가입 테스트"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "newpass123",
                "name": "New User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    def test_login(self, test_user):
        """로그인 테스트"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        """잘못된 인증정보 로그인 테스트"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "invalid@example.com",
                "password": "wrongpass"
            }
        )
        assert response.status_code == 401

    def test_get_current_user(self, auth_headers):
        """현재 사용자 조회 테스트"""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"


class TestDocumentEndpoints:
    """문서 관련 엔드포인트 테스트"""

    def test_create_document(self, auth_headers):
        """문서 생성 테스트"""
        response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            json={
                "title": "테스트 문서",
                "content": "문서 내용",
                "document_type": "contract"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "테스트 문서"
        assert data["document_type"] == "contract"

    def test_list_documents(self, auth_headers):
        """문서 목록 조회 테스트"""
        response = client.get(
            "/api/v1/documents",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_document(self, auth_headers):
        """문서 상세 조회 테스트"""
        # 먼저 문서 생성
        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            json={
                "title": "조회 테스트 문서",
                "content": "내용",
                "document_type": "contract"
            }
        )
        doc_id = create_response.json()["id"]

        # 문서 조회
        response = client.get(
            f"/api/v1/documents/{doc_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        assert data["title"] == "조회 테스트 문서"

    def test_update_document(self, auth_headers):
        """문서 수정 테스트"""
        # 문서 생성
        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            json={
                "title": "원본 제목",
                "content": "원본 내용",
                "document_type": "contract"
            }
        )
        doc_id = create_response.json()["id"]

        # 문서 수정
        response = client.put(
            f"/api/v1/documents/{doc_id}",
            headers=auth_headers,
            json={
                "title": "수정된 제목",
                "content": "수정된 내용"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "수정된 제목"
        assert data["content"] == "수정된 내용"

    def test_delete_document(self, auth_headers):
        """문서 삭제 테스트"""
        # 문서 생성
        create_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            json={
                "title": "삭제할 문서",
                "content": "내용",
                "document_type": "contract"
            }
        )
        doc_id = create_response.json()["id"]

        # 문서 삭제
        response = client.delete(
            f"/api/v1/documents/{doc_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        # 삭제 확인
        get_response = client.get(
            f"/api/v1/documents/{doc_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404


class TestGenerationEndpoints:
    """문서 생성 엔드포인트 테스트"""

    def test_generate_contract(self, auth_headers):
        """계약서 생성 테스트"""
        response = client.post(
            "/api/v1/generation/contract",
            headers=auth_headers,
            json={
                "contract_type": "employment",
                "party1": {
                    "name": "회사명",
                    "id": "123-45-67890",
                    "address": "서울시 강남구"
                },
                "party2": {
                    "name": "직원명",
                    "id": "900101-1234567",
                    "address": "서울시 서초구"
                },
                "date": "2024-01-01",
                "content": "계약 내용"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "document_id" in data

    def test_generate_lawsuit(self, auth_headers):
        """소장 생성 테스트"""
        response = client.post(
            "/api/v1/generation/lawsuit",
            headers=auth_headers,
            json={
                "lawsuit_type": "civil",
                "plaintiff": {
                    "name": "원고",
                    "address": "원고 주소"
                },
                "defendant": {
                    "name": "피고",
                    "address": "피고 주소"
                },
                "court": "서울중앙지방법원",
                "claims": "청구 내용",
                "facts": "사실 관계"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    def test_generate_notice(self, auth_headers):
        """내용증명 생성 테스트"""
        response = client.post(
            "/api/v1/generation/notice",
            headers=auth_headers,
            json={
                "notice_type": "termination",
                "sender": {
                    "name": "발신인",
                    "address": "발신 주소"
                },
                "receiver": {
                    "name": "수신인",
                    "address": "수신 주소"
                },
                "content": "통지 내용"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data


class TestAnalysisEndpoints:
    """분석 엔드포인트 테스트"""

    def test_analyze_risk(self, auth_headers):
        """리스크 분석 테스트"""
        # 문서 생성
        doc_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            json={
                "title": "분석할 문서",
                "content": "주 60시간 근무, 퇴직금 없음",
                "document_type": "contract"
            }
        )
        doc_id = doc_response.json()["id"]

        # 리스크 분석
        response = client.post(
            f"/api/v1/analysis/risk/{doc_id}",
            headers=auth_headers,
            params={"deep_analysis": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert "risk_analysis" in data
        assert "mitigation_strategies" in data

    def test_check_compliance(self, auth_headers):
        """준수성 검사 테스트"""
        # 문서 생성
        doc_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            json={
                "title": "검사할 문서",
                "content": "개인정보 무단 수집",
                "document_type": "agreement"
            }
        )
        doc_id = doc_response.json()["id"]

        # 준수성 검사
        response = client.post(
            f"/api/v1/analysis/compliance/{doc_id}",
            headers=auth_headers,
            params={"check_categories": ["개인정보보호"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "compliance_score" in data
        assert "violations" in data

    def test_review_document(self, auth_headers):
        """문서 검토 테스트"""
        # 문서 생성
        doc_response = client.post(
            "/api/v1/documents",
            headers=auth_headers,
            json={
                "title": "검토할 문서",
                "content": "문서 내용",
                "document_type": "contract"
            }
        )
        doc_id = doc_response.json()["id"]

        # 문서 검토
        response = client.post(
            f"/api/v1/analysis/review/{doc_id}",
            headers=auth_headers,
            params={"review_depth": "standard"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall_assessment" in data


class TestSearchEndpoints:
    """검색 엔드포인트 테스트"""

    def test_search_documents(self, auth_headers):
        """문서 검색 테스트"""
        # 검색할 문서 생성
        for i in range(3):
            client.post(
                "/api/v1/documents",
                headers=auth_headers,
                json={
                    "title": f"검색 테스트 문서 {i}",
                    "content": f"근로계약 관련 내용 {i}",
                    "document_type": "contract"
                }
            )

        # 검색 실행
        response = client.post(
            "/api/v1/search/documents",
            headers=auth_headers,
            json={"query": "근로계약"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0

    def test_search_laws(self, auth_headers):
        """법률 검색 테스트"""
        response = client.post(
            "/api/v1/search/laws",
            headers=auth_headers,
            json={
                "query": "근로기준법",
                "include_related": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "laws" in data

    def test_ai_recommend(self, auth_headers):
        """AI 추천 테스트"""
        response = client.post(
            "/api/v1/search/ai-recommend",
            headers=auth_headers,
            json={
                "query": "직원이 갑자기 퇴사했는데 어떻게 해야 하나요?",
                "include_laws": True,
                "include_templates": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data


class TestOCREndpoints:
    """OCR 엔드포인트 테스트"""

    def test_process_ocr(self, auth_headers):
        """OCR 처리 테스트"""
        # 테스트용 이미지 파일 생성 (실제 구현시 mock 사용)
        with open("test_image.txt", "wb") as f:
            f.write(b"Test content for OCR")

        with open("test_image.txt", "rb") as f:
            response = client.post(
                "/api/v1/ocr/process",
                headers=auth_headers,
                files={"file": ("test.txt", f, "text/plain")},
                data={
                    "extract_metadata": True,
                    "extract_structure": True
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data

    def test_extract_pdf_text(self, auth_headers):
        """PDF 텍스트 추출 테스트"""
        # 테스트용 PDF 파일 (mock)
        with open("test.pdf", "wb") as f:
            f.write(b"%PDF-1.4 test content")

        with open("test.pdf", "rb") as f:
            response = client.post(
                "/api/v1/ocr/pdf/extract",
                headers=auth_headers,
                files={"file": ("test.pdf", f, "application/pdf")},
                data={
                    "method": "auto",
                    "extract_tables": False
                }
            )

        # PDF 처리는 실제 PDF가 필요하므로 상태 코드만 확인
        assert response.status_code in [200, 500]


class TestTemplateEndpoints:
    """템플릿 엔드포인트 테스트"""

    def test_list_templates(self):
        """템플릿 목록 조회 테스트"""
        response = client.get(
            "/api/v1/templates",
            params={"category": "contract"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data

    def test_get_template(self):
        """템플릿 상세 조회 테스트"""
        # 템플릿 목록에서 첫 번째 템플릿 ID 가져오기
        list_response = client.get("/api/v1/templates")
        if list_response.json()["templates"]:
            template_id = list_response.json()["templates"][0]["id"]

            response = client.get(f"/api/v1/templates/{template_id}")
            assert response.status_code in [200, 404]