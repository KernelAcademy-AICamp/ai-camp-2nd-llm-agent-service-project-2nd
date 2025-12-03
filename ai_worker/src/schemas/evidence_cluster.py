"""
Evidence Cluster Schema
증거 클러스터 - 연결된 증거들의 그룹

"2024-03-15 외도 정황" 같이 여러 증거를 하나의 사건으로 묶음
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid

from .legal_analysis import LegalCategory, ConfidenceLevel


class ConnectionType(str, Enum):
    """증거 연결 유형"""

    # 시간적 연결: 비슷한 시간대에 발생
    TEMPORAL = "temporal"

    # 공간적 연결: 같은 장소에서 발생
    SPATIAL = "spatial"

    # 의미적 연결: 내용이 같은 사건을 언급
    SEMANTIC = "semantic"

    # 인물 연결: 같은 인물이 관련
    PERSON = "person"

    # 복합 연결: 여러 유형이 결합
    COMPOSITE = "composite"


class ClusterEvidence(BaseModel):
    """클러스터에 포함된 개별 증거 정보"""

    chunk_id: str = Field(..., description="청크 ID")
    file_id: str = Field(..., description="파일 ID")

    # 위치 정보 (빠른 참조용)
    file_name: str = Field(..., description="파일명")
    location_citation: str = Field(
        ...,
        description="위치 인용문 (예: '247번째 줄')"
    )

    # 내용 미리보기
    content_preview: str = Field(
        ...,
        max_length=200,
        description="내용 미리보기 (200자)"
    )

    # 이 증거의 역할
    relevance: str = Field(
        ...,
        description="이 증거의 역할 (예: 'direct_admission', 'location_proof')"
    )

    # 시간 정보
    timestamp: Optional[datetime] = Field(
        None,
        description="증거 시간"
    )


class EvidenceCluster(BaseModel):
    """
    증거 클러스터

    시간/장소/의미/인물로 연결된 증거들의 그룹

    Examples:
        event_id: "evt_20240315_affair_001"
        event_summary: "2024-03-15 배우자 외도 정황"
        evidences: [카톡 메시지, 호텔 사진, 카드 결제 내역]
        connection_type: "composite" (시간+공간+의미)
    """

    # ========================================
    # 식별자
    # ========================================
    event_id: str = Field(
        default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}",
        description="이벤트/클러스터 고유 ID"
    )

    case_id: str = Field(
        ...,
        description="소속 케이스 ID"
    )

    # ========================================
    # 이벤트 요약
    # ========================================
    event_summary: str = Field(
        ...,
        description="이벤트 요약 (예: '2024-03-15 외도 정황')"
    )

    event_description: str = Field(
        "",
        description="상세 설명"
    )

    # ========================================
    # 연결된 증거들
    # ========================================
    evidences: List[ClusterEvidence] = Field(
        default_factory=list,
        description="포함된 증거들"
    )

    evidence_count: int = Field(
        0,
        ge=0,
        description="증거 개수"
    )

    # ========================================
    # 연결 정보
    # ========================================
    connection_types: List[ConnectionType] = Field(
        default_factory=list,
        description="연결 유형들"
    )

    connection_reasoning: str = Field(
        "",
        description="연결 이유 설명"
    )

    # ========================================
    # 법적 분류
    # ========================================
    legal_category: LegalCategory = Field(
        LegalCategory.GENERAL,
        description="주요 법적 카테고리"
    )

    confidence_level: ConfidenceLevel = Field(
        ConfidenceLevel.UNCERTAIN,
        description="전체 신뢰도 레벨"
    )

    confidence_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="전체 신뢰도 점수"
    )

    # ========================================
    # 시간 범위
    # ========================================
    time_range_start: Optional[datetime] = Field(
        None,
        description="이벤트 시작 시간"
    )

    time_range_end: Optional[datetime] = Field(
        None,
        description="이벤트 종료 시간"
    )

    # ========================================
    # 타임스탬프
    # ========================================
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="클러스터 생성 시간"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="클러스터 수정 시간"
    )

    def add_evidence(
        self,
        chunk_id: str,
        file_id: str,
        file_name: str,
        location_citation: str,
        content_preview: str,
        relevance: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """증거 추가"""
        evidence = ClusterEvidence(
            chunk_id=chunk_id,
            file_id=file_id,
            file_name=file_name,
            location_citation=location_citation,
            content_preview=content_preview[:200],
            relevance=relevance,
            timestamp=timestamp
        )
        self.evidences.append(evidence)
        self.evidence_count = len(self.evidences)

        # 시간 범위 업데이트
        if timestamp:
            if self.time_range_start is None or timestamp < self.time_range_start:
                self.time_range_start = timestamp
            if self.time_range_end is None or timestamp > self.time_range_end:
                self.time_range_end = timestamp

        self.updated_at = datetime.now()

    def to_report(self) -> str:
        """
        보고서 형식으로 변환

        Returns:
            str: 사람이 읽을 수 있는 보고서
        """
        lines = [
            f"## {self.event_summary}",
            "",
            f"**신뢰도**: Level {self.confidence_level} ({self.confidence_score:.0%})",
            f"**법적 카테고리**: {self.legal_category}",
            f"**연결 유형**: {', '.join([ct.value for ct in self.connection_types])}",
            "",
            f"### 증거 목록 ({self.evidence_count}건)",
            ""
        ]

        for i, evidence in enumerate(self.evidences, 1):
            time_str = evidence.timestamp.strftime("%Y-%m-%d %H:%M") if evidence.timestamp else "시간 불명"
            lines.append(f"{i}. **{evidence.file_name}** ({evidence.location_citation})")
            lines.append(f"   - 시간: {time_str}")
            lines.append(f"   - 역할: {evidence.relevance}")
            lines.append(f"   - 내용: \"{evidence.content_preview}\"")
            lines.append("")

        if self.connection_reasoning:
            lines.append("### 연결 근거")
            lines.append(self.connection_reasoning)

        return "\n".join(lines)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
