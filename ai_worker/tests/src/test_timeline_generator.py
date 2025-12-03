"""
Timeline Generator 테스트

Given: 증거 청크들
When: TimelineGenerator.generate() 호출
Then: 시간순 정렬된 타임라인 이벤트 반환
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.analysis.timeline_generator import (
    TimelineGenerator,
    TimelineEvent,
    TimelineResult,
    TimelineEventType,
)


class TestTimelineGeneratorInitialization:
    """TimelineGenerator 초기화 테스트"""

    def test_generator_creation(self):
        """Given: 기본 설정
        When: TimelineGenerator() 생성
        Then: 인스턴스 생성"""
        generator = TimelineGenerator()
        assert generator is not None
        assert generator.max_description_length == 100

    def test_generator_with_custom_length(self):
        """Given: 커스텀 max_description_length
        When: TimelineGenerator(max_description_length=50)
        Then: 설정값 반영"""
        generator = TimelineGenerator(max_description_length=50)
        assert generator.max_description_length == 50


class TestTimelineEvent:
    """TimelineEvent 모델 테스트"""

    def test_event_creation(self):
        """Given: 이벤트 데이터
        When: TimelineEvent 생성
        Then: 속성 정확히 설정"""
        now = datetime.now()
        event = TimelineEvent(
            evidence_id="ev_001",
            case_id="case_123",
            timestamp=now,
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M"),
            description="테스트 이벤트",
            source_file="test.txt"
        )

        assert event.evidence_id == "ev_001"
        assert event.case_id == "case_123"
        assert event.description == "테스트 이벤트"
        assert event.event_type == TimelineEventType.MESSAGE

    def test_event_with_labels(self):
        """Given: 라벨 포함 이벤트
        When: TimelineEvent 생성
        Then: 라벨 저장"""
        now = datetime.now()
        event = TimelineEvent(
            evidence_id="ev_001",
            case_id="case_123",
            timestamp=now,
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M"),
            description="폭언 관련 메시지",
            labels=["폭언", "계속적_불화"],
            source_file="chat.txt"
        )

        assert "폭언" in event.labels
        assert len(event.labels) == 2

    def test_event_to_dict(self):
        """Given: TimelineEvent
        When: to_dict() 호출
        Then: 딕셔너리 변환"""
        now = datetime.now()
        event = TimelineEvent(
            evidence_id="ev_001",
            case_id="case_123",
            timestamp=now,
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M"),
            description="테스트",
            source_file="test.txt"
        )

        result = event.to_dict()

        assert result["evidence_id"] == "ev_001"
        assert result["case_id"] == "case_123"
        assert "timestamp" in result


class TestTimelineResult:
    """TimelineResult 모델 테스트"""

    def test_result_creation(self):
        """Given: 결과 데이터
        When: TimelineResult 생성
        Then: 통계 정확히 계산"""
        now = datetime.now()
        events = [
            TimelineEvent(
                evidence_id="ev_001",
                case_id="case_123",
                timestamp=now,
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M"),
                description="이벤트 1",
                source_file="test.txt"
            ),
            TimelineEvent(
                evidence_id="ev_002",
                case_id="case_123",
                timestamp=now + timedelta(hours=1),
                date=(now + timedelta(hours=1)).strftime("%Y-%m-%d"),
                time=(now + timedelta(hours=1)).strftime("%H:%M"),
                description="이벤트 2",
                source_file="test.txt"
            )
        ]

        result = TimelineResult(
            case_id="case_123",
            events=events,
            total_events=2
        )

        assert result.case_id == "case_123"
        assert result.total_events == 2
        assert len(result.events) == 2


class TestTimelineGeneratorGenerate:
    """generate() 메서드 테스트"""

    def test_generate_from_chunks(self):
        """Given: EvidenceChunk 리스트
        When: generate() 호출
        Then: TimelineResult 반환"""
        # Mock 청크 생성
        now = datetime.now()
        chunks = []
        for i in range(3):
            chunk = MagicMock()
            chunk.chunk_id = f"chunk_{i}"
            chunk.timestamp = now + timedelta(hours=i)
            chunk.content = f"메시지 내용 {i}"
            chunk.sender = "발신자"
            chunk.source_location = MagicMock()
            chunk.source_location.file_name = "chat.txt"
            chunk.source_location.file_type = "kakaotalk"
            chunk.legal_analysis = MagicMock()
            chunk.legal_analysis.categories = []
            chunks.append(chunk)

        generator = TimelineGenerator()
        result = generator.generate(chunks, case_id="case_123")

        assert isinstance(result, TimelineResult)
        assert result.case_id == "case_123"
        assert result.total_events == 3

    def test_generate_sorts_by_time(self):
        """Given: 시간순 아닌 청크들
        When: generate() 호출
        Then: 시간순 정렬된 이벤트"""
        now = datetime.now()

        # 역순으로 생성
        chunks = []
        for i in [2, 0, 1]:
            chunk = MagicMock()
            chunk.chunk_id = f"chunk_{i}"
            chunk.timestamp = now + timedelta(hours=i)
            chunk.content = f"메시지 {i}"
            chunk.sender = "발신자"
            chunk.source_location = MagicMock()
            chunk.source_location.file_name = "chat.txt"
            chunk.source_location.file_type = "text"
            chunk.legal_analysis = None
            chunks.append(chunk)

        generator = TimelineGenerator()
        result = generator.generate(chunks, case_id="case_123")

        # 시간순 정렬 확인
        timestamps = [e.timestamp for e in result.events]
        assert timestamps == sorted(timestamps)

    def test_generate_skips_no_timestamp(self):
        """Given: 타임스탬프 없는 청크
        When: generate() 호출
        Then: 해당 청크 스킵"""
        now = datetime.now()

        chunk1 = MagicMock()
        chunk1.chunk_id = "chunk_1"
        chunk1.timestamp = now
        chunk1.content = "내용"
        chunk1.sender = "발신자"
        chunk1.source_location = MagicMock()
        chunk1.source_location.file_name = "test.txt"
        chunk1.source_location.file_type = "text"
        chunk1.legal_analysis = None

        chunk2 = MagicMock()
        chunk2.chunk_id = "chunk_2"
        chunk2.timestamp = None  # 타임스탬프 없음
        chunk2.content = "내용 없음"

        generator = TimelineGenerator()
        result = generator.generate([chunk1, chunk2], case_id="case_123")

        assert result.total_events == 1

    def test_generate_with_labels(self):
        """Given: 라벨 있는 청크
        When: generate() 호출
        Then: 라벨 포함된 이벤트"""
        now = datetime.now()

        chunk = MagicMock()
        chunk.chunk_id = "chunk_1"
        chunk.timestamp = now
        chunk.content = "폭언 내용"
        chunk.sender = "피고"
        chunk.source_location = MagicMock()
        chunk.source_location.file_name = "chat.txt"
        chunk.source_location.file_type = "kakaotalk"
        chunk.legal_analysis = MagicMock()
        chunk.legal_analysis.categories = ["폭언", "학대"]

        generator = TimelineGenerator()
        result = generator.generate([chunk], case_id="case_123")

        assert result.total_events == 1
        assert "폭언" in result.events[0].labels
        assert result.events_by_label.get("폭언", 0) == 1


class TestTimelineGeneratorFromAnalysis:
    """generate_from_analysis() 메서드 테스트"""

    def test_generate_from_analysis_results(self):
        """Given: DynamoDB JSON 형태 분석 결과
        When: generate_from_analysis() 호출
        Then: TimelineResult 반환"""
        now = datetime.now()

        analysis_results = [
            {
                "evidence_id": "ev_001",
                "timestamp": now.isoformat(),
                "content": "폭언 메시지",
                "labels": ["폭언"],
                "speaker": "피고",
                "type": "kakaotalk",
                "file_name": "chat.txt"
            },
            {
                "evidence_id": "ev_002",
                "timestamp": (now + timedelta(days=1)).isoformat(),
                "content": "협박 메시지",
                "labels": ["협박", "위협"],
                "speaker": "피고",
                "type": "kakaotalk",
                "file_name": "chat.txt"
            }
        ]

        generator = TimelineGenerator()
        result = generator.generate_from_analysis(analysis_results, case_id="case_123")

        assert result.total_events == 2
        assert result.events[0].labels == ["폭언"]
        assert "협박" in result.events[1].labels


class TestTimelineGeneratorSignificance:
    """중요도 계산 테스트"""

    def test_key_evidence_detection(self):
        """Given: 핵심 증거 라벨
        When: 이벤트 생성
        Then: is_key_evidence=True"""
        now = datetime.now()

        chunk = MagicMock()
        chunk.chunk_id = "chunk_1"
        chunk.timestamp = now
        chunk.content = "폭행 내용"
        chunk.sender = "피고"
        chunk.source_location = MagicMock()
        chunk.source_location.file_name = "chat.txt"
        chunk.source_location.file_type = "text"
        chunk.legal_analysis = MagicMock()
        chunk.legal_analysis.categories = ["폭행"]

        generator = TimelineGenerator()
        result = generator.generate([chunk], case_id="case_123")

        assert result.events[0].is_key_evidence is True
        assert result.key_events_count == 1

    def test_significance_calculation(self):
        """Given: 다양한 라벨
        When: 중요도 계산
        Then: 가장 높은 중요도 반영"""
        generator = TimelineGenerator()

        # 부정행위 = 5점
        assert generator._calculate_significance(["부정행위"]) == 5

        # 폭언 = 3점
        assert generator._calculate_significance(["폭언"]) == 3

        # 복합 라벨 = 최대값
        assert generator._calculate_significance(["폭언", "부정행위"]) == 5

        # 라벨 없음 = 1점
        assert generator._calculate_significance([]) == 1


class TestTimelineGeneratorFilters:
    """필터링 메서드 테스트"""

    def setup_method(self):
        """테스트용 타임라인 결과 생성"""
        self.generator = TimelineGenerator()
        now = datetime.now()

        self.events = [
            TimelineEvent(
                evidence_id="ev_001",
                case_id="case_123",
                timestamp=now,
                date="2024-01-15",
                time="10:00",
                description="이벤트 1",
                labels=["폭언"],
                speaker="피고",
                source_file="chat.txt"
            ),
            TimelineEvent(
                evidence_id="ev_002",
                case_id="case_123",
                timestamp=now + timedelta(days=1),
                date="2024-01-16",
                time="14:00",
                description="이벤트 2",
                labels=["협박"],
                speaker="원고",
                source_file="chat.txt"
            ),
            TimelineEvent(
                evidence_id="ev_003",
                case_id="case_123",
                timestamp=now + timedelta(days=2),
                date="2024-01-17",
                time="09:00",
                description="이벤트 3",
                labels=["폭언", "학대"],
                speaker="피고",
                source_file="chat.txt"
            )
        ]

        self.result = TimelineResult(
            case_id="case_123",
            events=self.events,
            total_events=3
        )

    def test_filter_by_date_range(self):
        """Given: 날짜 범위
        When: filter_by_date_range() 호출
        Then: 범위 내 이벤트만"""
        filtered = self.generator.filter_by_date_range(
            self.result,
            start_date="2024-01-15",
            end_date="2024-01-16"
        )

        assert filtered.total_events == 2

    def test_filter_by_labels(self):
        """Given: 라벨 필터
        When: filter_by_labels() 호출
        Then: 해당 라벨 이벤트만"""
        filtered = self.generator.filter_by_labels(
            self.result,
            labels=["폭언"]
        )

        assert filtered.total_events == 2  # ev_001, ev_003

    def test_filter_by_speaker(self):
        """Given: 화자 필터
        When: filter_by_speaker() 호출
        Then: 해당 화자 이벤트만"""
        filtered = self.generator.filter_by_speaker(
            self.result,
            speaker="피고"
        )

        assert filtered.total_events == 2  # ev_001, ev_003

    def test_get_key_events(self):
        """Given: 핵심 증거 표시된 이벤트
        When: get_key_events() 호출
        Then: 핵심 증거만"""
        # 핵심 증거 설정
        self.events[0].is_key_evidence = True
        self.events[2].is_key_evidence = True

        key_result = self.generator.get_key_events(self.result)

        assert key_result.total_events == 2


class TestTimelineEventType:
    """이벤트 타입 추론 테스트"""

    def test_infer_message_type(self):
        """Given: kakaotalk 파일
        When: 타입 추론
        Then: MESSAGE"""
        generator = TimelineGenerator()

        assert generator._infer_event_type("kakaotalk") == TimelineEventType.MESSAGE
        assert generator._infer_event_type("text") == TimelineEventType.MESSAGE

    def test_infer_document_type(self):
        """Given: PDF 파일
        When: 타입 추론
        Then: DOCUMENT"""
        generator = TimelineGenerator()

        assert generator._infer_event_type("pdf") == TimelineEventType.DOCUMENT

    def test_infer_image_type(self):
        """Given: 이미지 파일
        When: 타입 추론
        Then: IMAGE"""
        generator = TimelineGenerator()

        assert generator._infer_event_type("image") == TimelineEventType.IMAGE
        assert generator._infer_event_type("jpg") == TimelineEventType.IMAGE

    def test_infer_audio_type(self):
        """Given: 오디오 파일
        When: 타입 추론
        Then: AUDIO"""
        generator = TimelineGenerator()

        assert generator._infer_event_type("audio") == TimelineEventType.AUDIO
        assert generator._infer_event_type("mp3") == TimelineEventType.AUDIO


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
