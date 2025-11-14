"""
Document Model - REFACTOR Phase
코드 품질 개선 및 최적화
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, ClassVar
from uuid import UUID, uuid4
from enum import Enum
import json


class DocumentType(str, Enum):
    """문서 타입 정의"""
    CONTRACT = "contract"
    LAWSUIT = "lawsuit"
    NOTICE = "notice"
    AGREEMENT = "agreement"
    APPLICATION = "application"

    @classmethod
    def is_valid(cls, value: Any) -> bool:
        """
        문서 타입 유효성 검증

        Args:
            value: 검증할 값

        Returns:
            bool: 유효한 타입인 경우 True
        """
        if not value:
            return False
        return value in cls._value2member_map_


class DocumentStatus(str, Enum):
    """문서 상태 정의"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"

    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """
        상태 전환 가능 여부 확인

        Args:
            from_status: 현재 상태
            to_status: 전환하려는 상태

        Returns:
            bool: 전환 가능한 경우 True
        """
        transitions = {
            "draft": ["in_progress"],
            "in_progress": ["review", "draft"],
            "review": ["completed", "in_progress"],
            "completed": ["archived"],
            "archived": []
        }
        return to_status in transitions.get(from_status, [])

    @classmethod
    def get_allowed_transitions(cls, from_status: str) -> List[str]:
        """현재 상태에서 가능한 다음 상태 목록 반환"""
        transitions = {
            "draft": ["in_progress"],
            "in_progress": ["review", "draft"],
            "review": ["completed", "in_progress"],
            "completed": ["archived"],
            "archived": []
        }
        return transitions.get(from_status, [])


class RiskLevel(str, Enum):
    """리스크 레벨 정의"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: float) -> str:
        """
        리스크 점수로부터 레벨 계산

        Args:
            score: 리스크 점수 (0-1 사이)

        Returns:
            str: 리스크 레벨

        Raises:
            ValueError: 점수가 0-1 범위를 벗어난 경우
        """
        if not 0 <= score <= 1:
            raise ValueError(f"Risk score must be between 0 and 1, got {score}")

        # 리스크 점수 범위
        score_ranges = {
            "low": (0.0, 0.3),
            "medium": (0.3, 0.6),
            "high": (0.6, 0.8),
            "critical": (0.8, 1.0)
        }

        for level, (min_score, max_score) in score_ranges.items():
            if min_score <= score < max_score:
                return level

        return cls.CRITICAL.value  # score == 1.0

    @classmethod
    def get_score_range(cls, level: str) -> tuple[float, float]:
        """특정 레벨의 점수 범위 반환"""
        score_ranges = {
            "low": (0.0, 0.3),
            "medium": (0.3, 0.6),
            "high": (0.6, 0.8),
            "critical": (0.8, 1.0)
        }
        return score_ranges.get(level, (0.0, 0.0))


@dataclass
class Document:
    """
    법률 문서 모델

    Attributes:
        title: 문서 제목
        content: 문서 내용
        document_type: 문서 타입
        user_id: 작성자 ID
        metadata: 추가 메타데이터
        status: 문서 상태
        risk_level: 리스크 레벨
        risk_score: 리스크 점수 (0-1)
        version: 문서 버전
        parent_id: 부모 문서 ID (버전 관리용)
    """

    # 필수 필드
    title: str
    content: str
    document_type: str
    user_id: int

    # 선택 필드
    metadata: Optional[Dict[str, Any]] = None
    status: str = field(default=DocumentStatus.DRAFT.value)
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    version: int = 1
    parent_id: Optional[UUID] = None

    # 자동 생성 필드
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """초기화 후 유효성 검증 및 처리"""
        self._validate_document_type()
        self._validate_status()
        self._validate_risk_score()
        self._auto_calculate_risk_level()

    def _validate_document_type(self) -> None:
        """문서 타입 검증"""
        if not DocumentType.is_valid(self.document_type):
            raise ValueError(
                f"Invalid document type: {self.document_type}. "
                f"Valid types are: {', '.join([t.value for t in DocumentType])}"
            )

    def _validate_status(self) -> None:
        """문서 상태 검증"""
        valid_statuses = [status.value for status in DocumentStatus]
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid document status: {self.status}. "
                f"Valid statuses are: {', '.join(valid_statuses)}"
            )

    def _validate_risk_score(self) -> None:
        """리스크 점수 검증"""
        if self.risk_score is not None:
            if not 0 <= self.risk_score <= 1:
                raise ValueError(
                    f"Risk score must be between 0 and 1, got {self.risk_score}"
                )

    def _auto_calculate_risk_level(self) -> None:
        """리스크 점수가 있으면 자동으로 레벨 계산"""
        if self.risk_score is not None and self.risk_level is None:
            self.risk_level = RiskLevel.from_score(self.risk_score)

    def update(self, **kwargs: Any) -> None:
        """
        문서 필드 업데이트

        Args:
            **kwargs: 업데이트할 필드와 값
        """
        # 유효한 필드만 업데이트
        valid_fields = {
            'title', 'content', 'status', 'metadata',
            'risk_level', 'risk_score'
        }

        for key, value in kwargs.items():
            if key in valid_fields and hasattr(self, key):
                setattr(self, key, value)

        # 유효성 재검증
        if 'status' in kwargs:
            self._validate_status()
        if 'risk_score' in kwargs:
            self._validate_risk_score()
            self._auto_calculate_risk_level()

        # 업데이트 시간 갱신
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        객체를 딕셔너리로 변환

        Returns:
            Dict[str, Any]: 문서 데이터 딕셔너리
        """
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "document_type": self.document_type,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "status": self.status,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "version": self.version,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        }

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def soft_delete(self) -> None:
        """소프트 삭제 (deleted_at 설정)"""
        self.deleted_at = datetime.now()
        self.status = DocumentStatus.ARCHIVED.value

    def restore(self) -> None:
        """삭제된 문서 복원"""
        self.deleted_at = None
        self.status = DocumentStatus.DRAFT.value

    def is_active(self) -> bool:
        """
        활성 상태 확인

        Returns:
            bool: 삭제되지 않은 경우 True
        """
        return self.deleted_at is None

    def is_editable(self) -> bool:
        """
        편집 가능 상태 확인

        Returns:
            bool: 편집 가능한 상태인 경우 True
        """
        editable_statuses = {
            DocumentStatus.DRAFT.value,
            DocumentStatus.IN_PROGRESS.value,
            DocumentStatus.REVIEW.value
        }
        return self.status in editable_statuses and self.is_active()

    def can_transition_to(self, new_status: str) -> bool:
        """특정 상태로 전환 가능한지 확인"""
        return DocumentStatus.can_transition(self.status, new_status)

    def transition_to(self, new_status: str) -> None:
        """
        새로운 상태로 전환

        Args:
            new_status: 전환할 상태

        Raises:
            ValueError: 전환이 불가능한 경우
        """
        if not self.can_transition_to(new_status):
            allowed = DocumentStatus.get_allowed_transitions(self.status)
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}. "
                f"Allowed transitions: {', '.join(allowed)}"
            )
        self.status = new_status
        self.updated_at = datetime.now()

    def create_new_version(self, **kwargs: Any) -> Document:
        """
        새 버전 생성

        Args:
            **kwargs: 새 버전에서 변경할 필드

        Returns:
            Document: 새 버전 문서
        """
        # 기본값은 현재 문서의 값을 사용
        new_doc_data = {
            'title': self.title,
            'content': self.content,
            'document_type': self.document_type,
            'user_id': self.user_id,
            'metadata': self.metadata,
            'version': self.version + 1,
            'parent_id': self.id
        }

        # 전달된 인자로 덮어쓰기
        new_doc_data.update(kwargs)

        # 새 버전은 항상 DRAFT 상태로 시작
        new_doc_data['status'] = DocumentStatus.DRAFT.value

        return Document(**new_doc_data)

    def __str__(self) -> str:
        """문자열 표현"""
        return (
            f"Document(id={self.id}, title='{self.title}', "
            f"type={self.document_type}, status={self.status})"
        )

    def __repr__(self) -> str:
        """개발자용 표현"""
        return (
            f"Document(id={self.id!r}, title={self.title!r}, "
            f"document_type={self.document_type!r}, user_id={self.user_id!r}, "
            f"status={self.status!r}, version={self.version!r})"
        )