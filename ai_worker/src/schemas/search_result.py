"""
Search Result Schema
검색 결과 - 정확한 위치 정보 포함

"외도 증거 찾아줘" 질문에 대한 응답 형식
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from .source_location import SourceLocation
from .legal_analysis import LegalCategory, ConfidenceLevel


class SearchResultItem(BaseModel):
    """
    개별 검색 결과 항목

    법정 인용 가능한 형식으로 위치 정보 포함
    """

    # ========================================
    # 식별자
    # ========================================
    chunk_id: str = Field(..., description="청크 ID")
    file_id: str = Field(..., description="파일 ID")
    case_id: str = Field(..., description="케이스 ID")

    # ========================================
    # 원본 위치 (핵심!)
    # ========================================
    source_location: SourceLocation = Field(
        ...,
        description="원본 파일 내 위치"
    )

    citation: str = Field(
        ...,
        description="법정 인용 형식 (예: '카톡_배우자.txt 247번째 줄')"
    )

    # ========================================
    # 내용
    # ========================================
    content: str = Field(..., description="청크 내용")
    content_highlight: Optional[str] = Field(
        None,
        description="검색어가 하이라이트된 내용"
    )

    # ========================================
    # 메시지 정보
    # ========================================
    sender: Optional[str] = Field(None, description="발신자")
    timestamp: Optional[datetime] = Field(None, description="시간")

    # ========================================
    # 법적 분류
    # ========================================
    legal_categories: List[LegalCategory] = Field(
        default_factory=list,
        description="법적 카테고리들"
    )

    confidence_level: ConfidenceLevel = Field(
        ConfidenceLevel.UNCERTAIN,
        description="신뢰도 레벨"
    )

    # ========================================
    # 검색 관련성
    # ========================================
    relevance_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="검색 관련성 점수"
    )

    match_reason: str = Field(
        "",
        description="매칭 이유"
    )

    # ========================================
    # 컨텍스트
    # ========================================
    context_before: List[str] = Field(
        default_factory=list,
        description="이전 컨텍스트 (주변 메시지)"
    )

    context_after: List[str] = Field(
        default_factory=list,
        description="이후 컨텍스트"
    )

    # ========================================
    # 연결된 증거
    # ========================================
    related_evidence_ids: List[str] = Field(
        default_factory=list,
        description="연결된 다른 증거 ID들"
    )

    event_id: Optional[str] = Field(
        None,
        description="소속 이벤트/클러스터 ID"
    )

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchResult(BaseModel):
    """
    검색 결과 전체

    사용자 질문에 대한 응답
    """

    # ========================================
    # 쿼리 정보
    # ========================================
    query: str = Field(..., description="원본 검색 쿼리")
    query_type: str = Field(
        "general",
        description="쿼리 유형 (category, time, person, event, composite)"
    )

    # ========================================
    # 결과
    # ========================================
    items: List[SearchResultItem] = Field(
        default_factory=list,
        description="검색 결과 항목들"
    )

    total_count: int = Field(0, ge=0, description="총 결과 수")

    # ========================================
    # 필터 정보
    # ========================================
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict,
        description="적용된 필터들"
    )

    # ========================================
    # 요약
    # ========================================
    summary: str = Field(
        "",
        description="검색 결과 요약"
    )

    # ========================================
    # 관련 클러스터
    # ========================================
    related_clusters: List[str] = Field(
        default_factory=list,
        description="관련된 증거 클러스터 ID들"
    )

    # ========================================
    # 메타데이터
    # ========================================
    search_time_ms: float = Field(
        0.0,
        ge=0,
        description="검색 소요 시간 (밀리초)"
    )

    searched_at: datetime = Field(
        default_factory=datetime.now,
        description="검색 시간"
    )

    def to_answer(self) -> str:
        """
        사용자에게 보여줄 응답 형식으로 변환

        Returns:
            str: 정확한 위치 정보가 포함된 응답
        """
        if not self.items:
            return f"'{self.query}'에 대한 검색 결과가 없습니다."

        lines = [
            f"**'{self.query}'** 검색 결과: {self.total_count}건",
            ""
        ]

        for i, item in enumerate(self.items[:10], 1):  # 상위 10개만
            time_str = ""
            if item.timestamp:
                time_str = f" ({item.timestamp.strftime('%Y-%m-%d %H:%M')})"

            sender_str = ""
            if item.sender:
                sender_str = f" [{item.sender}]"

            # 내용 미리보기
            preview = item.content[:100] + "..." if len(item.content) > 100 else item.content

            lines.append(f"**{i}. {item.citation}**{time_str}{sender_str}")
            lines.append(f"   \"{preview}\"")
            lines.append(f"   신뢰도: Level {item.confidence_level}, 카테고리: {', '.join([str(c) for c in item.legal_categories])}")
            lines.append("")

        if self.total_count > 10:
            lines.append(f"... 외 {self.total_count - 10}건 더 있음")

        if self.summary:
            lines.insert(2, f"요약: {self.summary}")
            lines.insert(3, "")

        return "\n".join(lines)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
