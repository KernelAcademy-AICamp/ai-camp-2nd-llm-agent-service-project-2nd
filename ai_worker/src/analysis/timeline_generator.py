"""
Timeline Generator

증거 청크들을 기반으로 사건 타임라인을 생성합니다.
Frontend에서 바로 렌더링 가능한 형태로 타임라인 이벤트를 구성합니다.

Usage:
    generator = TimelineGenerator()
    timeline = generator.generate(chunks, case_id="case_123")

    for event in timeline.events:
        print(f"[{event.timestamp}] {event.description}")
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class TimelineEventType(str, Enum):
    """타임라인 이벤트 유형"""
    MESSAGE = "message"       # 카카오톡/대화 메시지
    DOCUMENT = "document"     # PDF/문서
    IMAGE = "image"           # 이미지
    AUDIO = "audio"           # 음성
    VIDEO = "video"           # 비디오
    INCIDENT = "incident"     # 사건/이슈 (AI 분석 결과)


class TimelineEvent(BaseModel):
    """
    타임라인 이벤트

    Frontend에서 바로 렌더링 가능한 구조
    """

    event_id: str = Field(
        default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}",
        description="이벤트 고유 ID"
    )

    # 연결 정보
    evidence_id: str = Field(
        ...,
        description="연결된 증거(청크) ID"
    )

    case_id: str = Field(
        ...,
        description="소속 케이스 ID"
    )

    # 시간 정보
    timestamp: datetime = Field(
        ...,
        description="이벤트 발생 시간"
    )

    date: str = Field(
        ...,
        description="날짜 (YYYY-MM-DD)"
    )

    time: str = Field(
        ...,
        description="시간 (HH:MM)"
    )

    # 내용
    description: str = Field(
        ...,
        description="이벤트 설명 (요약)"
    )

    content_preview: Optional[str] = Field(
        None,
        description="원본 내용 미리보기 (100자)"
    )

    # 분류
    event_type: TimelineEventType = Field(
        default=TimelineEventType.MESSAGE,
        description="이벤트 유형"
    )

    labels: List[str] = Field(
        default_factory=list,
        description="유책사유 라벨 (예: 폭언, 부정행위)"
    )

    # 화자/출처
    speaker: Optional[str] = Field(
        None,
        description="발화자/작성자"
    )

    source_file: str = Field(
        ...,
        description="원본 파일명"
    )

    # 중요도
    significance: int = Field(
        default=1,
        ge=1,
        le=5,
        description="중요도 (1-5)"
    )

    is_pinned: bool = Field(
        default=False,
        description="핀 고정 여부"
    )

    is_key_evidence: bool = Field(
        default=False,
        description="핵심 증거 여부"
    )

    # 추가 메타데이터
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="추가 메타데이터"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """DynamoDB/JSON 저장용 딕셔너리 변환"""
        return {
            "event_id": self.event_id,
            "evidence_id": self.evidence_id,
            "case_id": self.case_id,
            "timestamp": self.timestamp.isoformat(),
            "date": self.date,
            "time": self.time,
            "description": self.description,
            "content_preview": self.content_preview,
            "event_type": self.event_type.value,
            "labels": self.labels,
            "speaker": self.speaker,
            "source_file": self.source_file,
            "significance": self.significance,
            "is_pinned": self.is_pinned,
            "is_key_evidence": self.is_key_evidence,
            "metadata": self.metadata
        }


class TimelineResult(BaseModel):
    """
    타임라인 생성 결과
    """

    case_id: str = Field(..., description="케이스 ID")

    events: List[TimelineEvent] = Field(
        default_factory=list,
        description="타임라인 이벤트 목록 (시간순 정렬)"
    )

    # 통계
    total_events: int = Field(default=0, description="전체 이벤트 수")

    date_range: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {"start": None, "end": None},
        description="타임라인 범위"
    )

    # 요약 통계
    events_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="유형별 이벤트 수"
    )

    events_by_label: Dict[str, int] = Field(
        default_factory=dict,
        description="라벨별 이벤트 수"
    )

    key_events_count: int = Field(
        default=0,
        description="핵심 증거 이벤트 수"
    )

    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="생성 시간"
    )

    def to_dict(self) -> Dict[str, Any]:
        """DynamoDB/JSON 저장용 딕셔너리 변환"""
        return {
            "case_id": self.case_id,
            "events": [e.to_dict() for e in self.events],
            "total_events": self.total_events,
            "date_range": self.date_range,
            "events_by_type": self.events_by_type,
            "events_by_label": self.events_by_label,
            "key_events_count": self.key_events_count,
            "generated_at": self.generated_at.isoformat()
        }


class TimelineGenerator:
    """
    타임라인 생성기

    증거 청크들을 분석하여 시간순 타임라인을 생성합니다.

    Usage:
        generator = TimelineGenerator()
        result = generator.generate(chunks, case_id="case_123")
    """

    # 핵심 증거로 판단하는 라벨들
    KEY_EVIDENCE_LABELS = {
        "부정행위", "폭행", "학대", "유기", "협박", "위협"
    }

    # 중요도 가중치 (라벨별)
    SIGNIFICANCE_WEIGHTS = {
        "부정행위": 5,
        "폭행": 5,
        "학대": 5,
        "유기": 4,
        "협박": 4,
        "위협": 4,
        "폭언": 3,
        "계속적_불화": 3,
        "혼인_파탄": 3,
        "재산_문제": 2,
        "양육_문제": 2,
    }

    def __init__(self, max_description_length: int = 100):
        """
        Args:
            max_description_length: 이벤트 설명 최대 길이
        """
        self.max_description_length = max_description_length

    def generate(
        self,
        chunks: List[Any],
        case_id: str,
        include_all: bool = True
    ) -> TimelineResult:
        """
        증거 청크들로부터 타임라인 생성

        Args:
            chunks: EvidenceChunk 리스트
            case_id: 케이스 ID
            include_all: 모든 청크 포함 여부 (False면 라벨 있는 것만)

        Returns:
            TimelineResult: 타임라인 결과
        """
        events: List[TimelineEvent] = []

        for chunk in chunks:
            # 타임스탬프 없는 청크는 스킵
            if not hasattr(chunk, 'timestamp') or chunk.timestamp is None:
                continue

            # 라벨 필터링 (include_all=False인 경우)
            labels = self._extract_labels(chunk)
            if not include_all and not labels:
                continue

            # 이벤트 생성
            event = self._create_event(chunk, case_id, labels)
            events.append(event)

        # 시간순 정렬
        events.sort(key=lambda e: e.timestamp)

        # 결과 생성
        result = self._build_result(events, case_id)

        return result

    def generate_from_analysis(
        self,
        analysis_results: List[Dict[str, Any]],
        case_id: str
    ) -> TimelineResult:
        """
        분석 결과(DynamoDB JSON)로부터 타임라인 생성

        Args:
            analysis_results: 분석 결과 JSON 리스트
            case_id: 케이스 ID

        Returns:
            TimelineResult: 타임라인 결과
        """
        events: List[TimelineEvent] = []

        for result in analysis_results:
            timestamp_str = result.get("timestamp")
            if not timestamp_str:
                continue

            # 타임스탬프 파싱
            try:
                if isinstance(timestamp_str, str):
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                else:
                    timestamp = timestamp_str
            except (ValueError, TypeError):
                continue

            labels = result.get("labels", [])
            content = result.get("content", "")

            event = TimelineEvent(
                evidence_id=result.get("evidence_id", result.get("id", "")),
                case_id=case_id,
                timestamp=timestamp,
                date=timestamp.strftime("%Y-%m-%d"),
                time=timestamp.strftime("%H:%M"),
                description=self._create_description(content, labels),
                content_preview=content[:100] if content else None,
                event_type=self._infer_event_type(result.get("type", "text")),
                labels=labels,
                speaker=result.get("speaker"),
                source_file=result.get("file_name", result.get("s3_key", "unknown")),
                significance=self._calculate_significance(labels),
                is_key_evidence=self._is_key_evidence(labels),
                metadata=result.get("insights", {})
            )
            events.append(event)

        # 시간순 정렬
        events.sort(key=lambda e: e.timestamp)

        return self._build_result(events, case_id)

    def _create_event(
        self,
        chunk: Any,
        case_id: str,
        labels: List[str]
    ) -> TimelineEvent:
        """단일 청크로부터 타임라인 이벤트 생성"""

        timestamp = chunk.timestamp
        content = chunk.content if hasattr(chunk, 'content') else ""

        # 이벤트 타입 추론
        event_type = TimelineEventType.MESSAGE
        if hasattr(chunk, 'source_location'):
            file_type = getattr(chunk.source_location, 'file_type', None)
            event_type = self._infer_event_type(file_type)

        # 파일명 추출
        source_file = "unknown"
        if hasattr(chunk, 'source_location') and chunk.source_location:
            source_file = getattr(chunk.source_location, 'file_name', "unknown")

        return TimelineEvent(
            evidence_id=getattr(chunk, 'chunk_id', str(uuid.uuid4())),
            case_id=case_id,
            timestamp=timestamp,
            date=timestamp.strftime("%Y-%m-%d"),
            time=timestamp.strftime("%H:%M"),
            description=self._create_description(content, labels),
            content_preview=content[:100] if content else None,
            event_type=event_type,
            labels=labels,
            speaker=getattr(chunk, 'sender', None),
            source_file=source_file,
            significance=self._calculate_significance(labels),
            is_key_evidence=self._is_key_evidence(labels)
        )

    def _extract_labels(self, chunk: Any) -> List[str]:
        """청크에서 라벨 추출"""
        labels = []

        if hasattr(chunk, 'legal_analysis') and chunk.legal_analysis:
            legal = chunk.legal_analysis
            if hasattr(legal, 'categories'):
                labels.extend(legal.categories)

        return labels

    def _create_description(
        self,
        content: str,
        labels: List[str]
    ) -> str:
        """이벤트 설명 생성"""

        if not content:
            if labels:
                return f"[{', '.join(labels)}] 관련 증거"
            return "증거 자료"

        # 내용 요약 (최대 길이 제한)
        description = content.strip()
        if len(description) > self.max_description_length:
            description = description[:self.max_description_length] + "..."

        return description

    def _infer_event_type(self, file_type: Any) -> TimelineEventType:
        """파일 타입에서 이벤트 유형 추론"""

        if file_type is None:
            return TimelineEventType.MESSAGE

        type_str = str(file_type).lower()

        if "kakaotalk" in type_str or "chat" in type_str or "text" in type_str:
            return TimelineEventType.MESSAGE
        elif "pdf" in type_str or "document" in type_str:
            return TimelineEventType.DOCUMENT
        elif "image" in type_str or "jpg" in type_str or "png" in type_str:
            return TimelineEventType.IMAGE
        elif "audio" in type_str or "mp3" in type_str or "wav" in type_str:
            return TimelineEventType.AUDIO
        elif "video" in type_str or "mp4" in type_str:
            return TimelineEventType.VIDEO
        else:
            return TimelineEventType.MESSAGE

    def _calculate_significance(self, labels: List[str]) -> int:
        """라벨 기반 중요도 계산 (1-5)"""

        if not labels:
            return 1

        max_weight = 1
        for label in labels:
            # 정확한 매칭
            if label in self.SIGNIFICANCE_WEIGHTS:
                max_weight = max(max_weight, self.SIGNIFICANCE_WEIGHTS[label])
            # 부분 매칭
            else:
                for key, weight in self.SIGNIFICANCE_WEIGHTS.items():
                    if key in label or label in key:
                        max_weight = max(max_weight, weight)
                        break

        return min(max_weight, 5)

    def _is_key_evidence(self, labels: List[str]) -> bool:
        """핵심 증거 여부 판단"""

        for label in labels:
            if label in self.KEY_EVIDENCE_LABELS:
                return True
            # 부분 매칭
            for key_label in self.KEY_EVIDENCE_LABELS:
                if key_label in label:
                    return True

        return False

    def _build_result(
        self,
        events: List[TimelineEvent],
        case_id: str
    ) -> TimelineResult:
        """타임라인 결과 객체 생성"""

        # 날짜 범위
        date_range = {"start": None, "end": None}
        if events:
            date_range["start"] = events[0].date
            date_range["end"] = events[-1].date

        # 유형별 집계
        events_by_type: Dict[str, int] = {}
        for event in events:
            type_key = event.event_type.value
            events_by_type[type_key] = events_by_type.get(type_key, 0) + 1

        # 라벨별 집계
        events_by_label: Dict[str, int] = {}
        for event in events:
            for label in event.labels:
                events_by_label[label] = events_by_label.get(label, 0) + 1

        # 핵심 증거 수
        key_events_count = sum(1 for e in events if e.is_key_evidence)

        return TimelineResult(
            case_id=case_id,
            events=events,
            total_events=len(events),
            date_range=date_range,
            events_by_type=events_by_type,
            events_by_label=events_by_label,
            key_events_count=key_events_count
        )

    def filter_by_date_range(
        self,
        result: TimelineResult,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> TimelineResult:
        """날짜 범위로 필터링"""

        filtered_events = result.events

        if start_date:
            filtered_events = [e for e in filtered_events if e.date >= start_date]

        if end_date:
            filtered_events = [e for e in filtered_events if e.date <= end_date]

        return self._build_result(filtered_events, result.case_id)

    def filter_by_labels(
        self,
        result: TimelineResult,
        labels: List[str]
    ) -> TimelineResult:
        """라벨로 필터링"""

        label_set = set(labels)
        filtered_events = [
            e for e in result.events
            if any(label in label_set for label in e.labels)
        ]

        return self._build_result(filtered_events, result.case_id)

    def filter_by_speaker(
        self,
        result: TimelineResult,
        speaker: str
    ) -> TimelineResult:
        """화자로 필터링"""

        filtered_events = [
            e for e in result.events
            if e.speaker and speaker.lower() in e.speaker.lower()
        ]

        return self._build_result(filtered_events, result.case_id)

    def get_key_events(self, result: TimelineResult) -> TimelineResult:
        """핵심 증거 이벤트만 추출"""

        key_events = [e for e in result.events if e.is_key_evidence]

        return self._build_result(key_events, result.case_id)
