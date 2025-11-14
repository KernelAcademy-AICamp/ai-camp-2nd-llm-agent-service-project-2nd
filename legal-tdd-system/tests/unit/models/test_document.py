"""
Document Model Tests - TDD RED Phase
Given-When-Then 구조로 테스트 작성
"""

import pytest
from datetime import datetime
from typing import Optional
from uuid import UUID


@pytest.mark.red
class TestDocumentModel:
    """Document 모델 테스트 - RED Phase"""

    def test_create_document_with_required_fields(self):
        """Given: 필수 필드만으로 When: Document 생성시 Then: 성공"""
        # Given
        from src.models.document import Document

        # When
        doc = Document(
            title="근로계약서",
            content="계약 내용...",
            document_type="contract",
            user_id=1
        )

        # Then
        assert doc.title == "근로계약서"
        assert doc.content == "계약 내용..."
        assert doc.document_type == "contract"
        assert doc.user_id == 1
        assert doc.id is not None
        assert isinstance(doc.id, UUID)
        assert isinstance(doc.created_at, datetime)

    def test_create_document_with_all_fields(self):
        """Given: 모든 필드로 When: Document 생성시 Then: 성공"""
        # Given
        from src.models.document import Document
        metadata = {"template": "employment", "version": "1.0"}

        # When
        doc = Document(
            title="근로계약서",
            content="계약 내용...",
            document_type="contract",
            user_id=1,
            metadata=metadata,
            status="draft",
            risk_level="low",
            risk_score=0.2
        )

        # Then
        assert doc.metadata == metadata
        assert doc.status == "draft"
        assert doc.risk_level == "low"
        assert doc.risk_score == 0.2

    def test_document_type_validation(self):
        """Given: 잘못된 문서 타입으로 When: Document 생성시 Then: 검증 실패"""
        # Given
        from src.models.document import Document, DocumentType

        # When/Then
        with pytest.raises(ValueError, match="Invalid document type"):
            Document(
                title="테스트",
                content="내용",
                document_type="invalid_type",  # 잘못된 타입
                user_id=1
            )

    def test_document_status_validation(self):
        """Given: 잘못된 상태로 When: Document 생성시 Then: 검증 실패"""
        # Given
        from src.models.document import Document, DocumentStatus

        # When/Then
        with pytest.raises(ValueError, match="Invalid document status"):
            Document(
                title="테스트",
                content="내용",
                document_type="contract",
                user_id=1,
                status="invalid_status"  # 잘못된 상태
            )

    def test_risk_score_validation(self):
        """Given: 잘못된 리스크 점수로 When: Document 생성시 Then: 검증 실패"""
        # Given
        from src.models.document import Document

        # When/Then - 음수 점수
        with pytest.raises(ValueError, match="Risk score must be between 0 and 1"):
            Document(
                title="테스트",
                content="내용",
                document_type="contract",
                user_id=1,
                risk_score=-0.5
            )

        # When/Then - 1 초과 점수
        with pytest.raises(ValueError, match="Risk score must be between 0 and 1"):
            Document(
                title="테스트",
                content="내용",
                document_type="contract",
                user_id=1,
                risk_score=1.5
            )

    def test_document_update(self):
        """Given: 생성된 문서를 When: 업데이트시 Then: 변경사항 반영"""
        # Given
        from src.models.document import Document
        import time

        doc = Document(
            title="원본 제목",
            content="원본 내용",
            document_type="contract",
            user_id=1
        )
        original_updated_at = doc.updated_at

        # 시간 차이를 위한 짧은 대기
        time.sleep(0.001)

        # When
        doc.update(
            title="수정된 제목",
            content="수정된 내용",
            status="completed"
        )

        # Then
        assert doc.title == "수정된 제목"
        assert doc.content == "수정된 내용"
        assert doc.status == "completed"
        assert doc.updated_at > original_updated_at

    def test_document_to_dict(self):
        """Given: Document 객체를 When: dict로 변환시 Then: 모든 필드 포함"""
        # Given
        from src.models.document import Document
        doc = Document(
            title="테스트 문서",
            content="내용",
            document_type="contract",
            user_id=1,
            metadata={"key": "value"}
        )

        # When
        doc_dict = doc.to_dict()

        # Then
        assert doc_dict["title"] == "테스트 문서"
        assert doc_dict["content"] == "내용"
        assert doc_dict["document_type"] == "contract"
        assert doc_dict["user_id"] == 1
        assert doc_dict["metadata"] == {"key": "value"}
        assert "id" in doc_dict
        assert "created_at" in doc_dict
        assert "updated_at" in doc_dict

    def test_document_soft_delete(self):
        """Given: 활성 문서를 When: 소프트 삭제시 Then: deleted_at 설정"""
        # Given
        from src.models.document import Document
        doc = Document(
            title="삭제할 문서",
            content="내용",
            document_type="contract",
            user_id=1
        )
        assert doc.deleted_at is None

        # When
        doc.soft_delete()

        # Then
        assert doc.deleted_at is not None
        assert isinstance(doc.deleted_at, datetime)
        assert not doc.is_active()

    def test_document_version_increment(self):
        """Given: 문서를 When: 새 버전 생성시 Then: 버전 번호 증가"""
        # Given
        from src.models.document import Document
        original = Document(
            title="원본",
            content="내용",
            document_type="contract",
            user_id=1,
            version=1
        )

        # When
        new_version = original.create_new_version(
            content="수정된 내용"
        )

        # Then
        assert new_version.version == 2
        assert new_version.parent_id == original.id
        assert new_version.content == "수정된 내용"
        assert new_version.title == original.title


@pytest.mark.red
class TestDocumentTypes:
    """DocumentType Enum 테스트"""

    def test_document_type_enum_values(self):
        """Given: DocumentType enum When: 값 확인시 Then: 정의된 타입 존재"""
        # Given/When
        from src.models.document import DocumentType

        # Then
        assert DocumentType.CONTRACT == "contract"
        assert DocumentType.LAWSUIT == "lawsuit"
        assert DocumentType.NOTICE == "notice"
        assert DocumentType.AGREEMENT == "agreement"
        assert DocumentType.APPLICATION == "application"

    def test_document_type_validation_method(self):
        """Given: 문자열 When: DocumentType 검증시 Then: 유효성 확인"""
        # Given
        from src.models.document import DocumentType

        # When/Then
        assert DocumentType.is_valid("contract") is True
        assert DocumentType.is_valid("invalid") is False
        assert DocumentType.is_valid("") is False
        assert DocumentType.is_valid(None) is False


@pytest.mark.red
class TestDocumentStatus:
    """DocumentStatus Enum 테스트"""

    def test_document_status_enum_values(self):
        """Given: DocumentStatus enum When: 값 확인시 Then: 정의된 상태 존재"""
        # Given/When
        from src.models.document import DocumentStatus

        # Then
        assert DocumentStatus.DRAFT == "draft"
        assert DocumentStatus.IN_PROGRESS == "in_progress"
        assert DocumentStatus.REVIEW == "review"
        assert DocumentStatus.COMPLETED == "completed"
        assert DocumentStatus.ARCHIVED == "archived"

    def test_status_transitions(self):
        """Given: 현재 상태에서 When: 다음 상태 전환시 Then: 유효한 전환만 허용"""
        # Given
        from src.models.document import DocumentStatus

        # When/Then - draft에서 가능한 전환
        assert DocumentStatus.can_transition("draft", "in_progress") is True
        assert DocumentStatus.can_transition("draft", "completed") is False

        # in_progress에서 가능한 전환
        assert DocumentStatus.can_transition("in_progress", "review") is True
        assert DocumentStatus.can_transition("in_progress", "draft") is True
        assert DocumentStatus.can_transition("in_progress", "archived") is False

        # review에서 가능한 전환
        assert DocumentStatus.can_transition("review", "completed") is True
        assert DocumentStatus.can_transition("review", "in_progress") is True
        assert DocumentStatus.can_transition("review", "draft") is False

        # completed에서 가능한 전환
        assert DocumentStatus.can_transition("completed", "archived") is True
        assert DocumentStatus.can_transition("completed", "draft") is False


@pytest.mark.red
class TestDocumentRiskLevel:
    """RiskLevel Enum 테스트"""

    def test_risk_level_enum_values(self):
        """Given: RiskLevel enum When: 값 확인시 Then: 정의된 레벨 존재"""
        # Given/When
        from src.models.document import RiskLevel

        # Then
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.CRITICAL == "critical"

    def test_risk_level_from_score(self):
        """Given: 리스크 점수 When: 레벨 계산시 Then: 적절한 레벨 반환"""
        # Given
        from src.models.document import RiskLevel

        # When/Then
        assert RiskLevel.from_score(0.2) == "low"
        assert RiskLevel.from_score(0.5) == "medium"
        assert RiskLevel.from_score(0.75) == "high"
        assert RiskLevel.from_score(0.9) == "critical"
        assert RiskLevel.from_score(1.0) == "critical"

        # 범위 밖 값
        with pytest.raises(ValueError):
            RiskLevel.from_score(-0.1)
        with pytest.raises(ValueError):
            RiskLevel.from_score(1.1)