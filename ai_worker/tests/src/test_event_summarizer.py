"""
EventSummarizer 테스트

이벤트 한 줄 요약 생성기 테스트
"""


from src.analysis.event_summarizer import (
    EventSummarizer,
    EventSummary,
    SummaryType,
    summarize_event,
    summarize_events_batch,
    FAULT_TYPE_TEMPLATES,
)


# =============================================================================
# EventSummarizer 기본 테스트
# =============================================================================

class TestEventSummarizerInit:
    """EventSummarizer 초기화 테스트"""

    def test_default_init(self):
        """기본 초기화"""
        summarizer = EventSummarizer()
        assert summarizer.max_length == 50

    def test_custom_max_length(self):
        """커스텀 최대 길이"""
        summarizer = EventSummarizer(max_length=30)
        assert summarizer.max_length == 30


# =============================================================================
# 유책사유 기반 요약 테스트
# =============================================================================

class TestFaultTypeSummary:
    """유책사유 기반 요약 테스트"""

    def test_adultery_summary(self):
        """외도 관련 요약"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="남편이 또 바람을 피웠어요",
            fault_types=["adultery"]
        )
        assert result is not None
        assert "외도" in result.summary
        assert result.fault_type == "adultery"

    def test_violence_summary(self):
        """폭력 관련 요약"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="또 맞았어요",
            fault_types=["violence"]
        )
        assert result is not None
        assert "폭력" in result.summary or "폭행" in result.summary
        assert result.fault_type == "violence"

    def test_verbal_abuse_summary(self):
        """폭언 관련 요약"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="매일 욕을 해요",
            fault_types=["verbal_abuse"]
        )
        assert result is not None
        assert result.fault_type == "verbal_abuse"

    def test_economic_abuse_summary(self):
        """경제적 학대 요약"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="생활비를 안 줘요",
            fault_types=["economic_abuse"]
        )
        assert result is not None
        assert result.fault_type == "economic_abuse"

    def test_desertion_summary(self):
        """유기 관련 요약"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="연락 두절",
            fault_types=["desertion"]
        )
        assert result is not None
        assert result.fault_type == "desertion"

    def test_multiple_fault_types(self):
        """여러 유책사유"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="폭력과 외도",
            fault_types=["violence", "adultery"]
        )
        assert result is not None
        # 첫 번째 유책사유가 적용됨
        assert result.fault_type == "violence"


# =============================================================================
# 자동 감지 테스트
# =============================================================================

class TestAutoDetection:
    """유책사유 자동 감지 테스트"""

    def test_detect_adultery(self):
        """외도 키워드 감지"""
        summarizer = EventSummarizer()
        result = summarizer.summarize("남편이 바람을 피웠어요")
        assert result is not None
        assert result.fault_type == "adultery"
        assert result.confidence == 0.8  # 자동 감지는 낮은 신뢰도

    def test_detect_violence(self):
        """폭력 키워드 감지"""
        summarizer = EventSummarizer()
        result = summarizer.summarize("어제 또 때렸어요. 멍이 들었어요")
        assert result is not None
        assert result.fault_type == "violence"

    def test_detect_verbal_abuse(self):
        """폭언 키워드 감지"""
        summarizer = EventSummarizer()
        result = summarizer.summarize("매일 욕하고 무시해요")
        assert result is not None
        assert result.fault_type == "verbal_abuse"

    def test_no_detection_fallback(self):
        """키워드 없으면 기본 요약"""
        summarizer = EventSummarizer()
        result = summarizer.summarize("오늘 날씨가 좋았습니다")
        assert result is not None
        assert result.fault_type is None


# =============================================================================
# 소스 유형 테스트
# =============================================================================

class TestSourceType:
    """소스 유형별 요약 테스트"""

    def test_chat_log_source(self):
        """채팅 로그 소스"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="외도 관련 내용",
            fault_types=["adultery"],
            source_type="chat_log"
        )
        assert "대화" in result.summary

    def test_kakaotalk_source(self):
        """카카오톡 소스"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="외도 관련 내용",
            fault_types=["adultery"],
            source_type="kakaotalk"
        )
        assert "대화" in result.summary

    def test_photo_source(self):
        """사진 소스"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="외도 관련 내용",
            fault_types=["adultery"],
            source_type="photo"
        )
        assert "사진" in result.summary

    def test_recording_source(self):
        """녹음 소스"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="폭력 관련 내용",
            fault_types=["violence"],
            source_type="recording"
        )
        assert "녹음" in result.summary

    def test_medical_record_source(self):
        """진단서 소스"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="폭력 관련 내용",
            fault_types=["violence"],
            source_type="medical_record"
        )
        assert "진단서" in result.summary


# =============================================================================
# 감정 기반 요약 테스트
# =============================================================================

class TestEmotionSummary:
    """감정 기반 요약 테스트"""

    def test_anger_emotion(self):
        """분노 감정"""
        summarizer = EventSummarizer()
        # "화나" 키워드 포함
        result = summarizer.summarize("정말 화나네요")
        assert result is not None
        assert "갈등" in result.summary
        assert result.confidence == 0.7

    def test_sadness_emotion(self):
        """슬픔 감정"""
        summarizer = EventSummarizer()
        result = summarizer.summarize("너무 슬프고 우울해요")
        assert result is not None
        assert "고충" in result.summary

    def test_fear_emotion(self):
        """공포 감정"""
        summarizer = EventSummarizer()
        # "불안" 키워드 포함
        result = summarizer.summarize("불안해서 잠이 안 와요")
        assert result is not None
        assert "불안" in result.summary or "공포" in result.summary


# =============================================================================
# SummaryType 추론 테스트
# =============================================================================

class TestSummaryTypeInference:
    """요약 유형 추론 테스트"""

    def test_conversation_type(self):
        """대화 유형"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="테스트",
            source_type="chat_log"
        )
        assert result.summary_type == SummaryType.CONVERSATION

    def test_evidence_type(self):
        """증거 유형"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="테스트",
            source_type="photo"
        )
        assert result.summary_type == SummaryType.EVIDENCE

    def test_record_type(self):
        """기록 유형"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="테스트",
            source_type="medical_record"
        )
        assert result.summary_type == SummaryType.RECORD

    def test_financial_type(self):
        """금융 유형"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="테스트",
            source_type="bank_statement"
        )
        assert result.summary_type == SummaryType.FINANCIAL


# =============================================================================
# 일괄 처리 테스트
# =============================================================================

class TestBatchSummarize:
    """일괄 요약 테스트"""

    def test_batch_summarize(self):
        """여러 이벤트 일괄 요약"""
        summarizer = EventSummarizer()
        items = [
            {"content": "외도 관련 내용", "fault_types": ["adultery"]},
            {"content": "폭력 관련 내용", "fault_types": ["violence"]},
            {"content": "일반 대화"},
        ]
        results = summarizer.summarize_batch(items)
        assert len(results) == 3
        assert all(isinstance(r, EventSummary) for r in results)

    def test_batch_with_source_types(self):
        """소스 유형 포함 일괄 요약"""
        summarizer = EventSummarizer()
        items = [
            {"content": "외도", "fault_types": ["adultery"], "source_type": "chat_log"},
            {"content": "폭력", "fault_types": ["violence"], "source_type": "photo"},
        ]
        results = summarizer.summarize_batch(items)
        assert len(results) == 2
        assert "대화" in results[0].summary
        assert "사진" in results[1].summary


# =============================================================================
# 간편 함수 테스트
# =============================================================================

class TestConvenienceFunctions:
    """간편 함수 테스트"""

    def test_summarize_event(self):
        """summarize_event 함수"""
        result = summarize_event("외도 관련 내용", fault_types=["adultery"])
        assert isinstance(result, str)
        assert "외도" in result

    def test_summarize_events_batch(self):
        """summarize_events_batch 함수"""
        items = [
            {"content": "외도", "fault_types": ["adultery"]},
            {"content": "폭력", "fault_types": ["violence"]},
        ]
        results = summarize_events_batch(items)
        assert len(results) == 2
        assert all(isinstance(r, str) for r in results)


# =============================================================================
# 엣지 케이스 테스트
# =============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_content(self):
        """빈 내용"""
        summarizer = EventSummarizer()
        result = summarizer.summarize("")
        assert result.summary == "내용 없음"
        assert result.confidence == 0.5

    def test_whitespace_only(self):
        """공백만 있는 내용"""
        summarizer = EventSummarizer()
        result = summarizer.summarize("   ")
        assert result.summary == "내용 없음"

    def test_long_content_truncation(self):
        """긴 내용 자르기"""
        summarizer = EventSummarizer(max_length=20)
        result = summarizer.summarize(
            "이것은 매우 긴 내용입니다. 50자를 초과하는 내용은 잘려야 합니다.",
            fault_types=["adultery"]
        )
        assert len(result.summary) <= 20

    def test_speaker_included(self):
        """발화자 정보 포함"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="안녕하세요",
            speaker="김철수"
        )
        assert "[김철수]" in result.summary

    def test_unknown_fault_type(self):
        """알 수 없는 유책사유"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="테스트",
            fault_types=["unknown_type"]
        )
        assert result is not None
        # 알 수 없는 유책사유는 무시하고 기본 요약


# =============================================================================
# EventSummary 데이터 클래스 테스트
# =============================================================================

class TestEventSummaryDataclass:
    """EventSummary 데이터 클래스 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        summary = EventSummary(
            summary="테스트 요약",
            summary_type=SummaryType.CONVERSATION,
            keywords=["테스트"],
            fault_type="adultery",
            confidence=0.9
        )
        d = summary.to_dict()
        assert d["summary"] == "테스트 요약"
        assert d["summary_type"] == "conversation"
        assert d["keywords"] == ["테스트"]
        assert d["fault_type"] == "adultery"
        assert d["confidence"] == 0.9

    def test_default_keywords(self):
        """기본 키워드 리스트"""
        summary = EventSummary(summary="테스트")
        assert summary.keywords == []


# =============================================================================
# 키워드 추출 테스트
# =============================================================================

class TestKeywordExtraction:
    """키워드 추출 테스트"""

    def test_extract_keywords(self):
        """키워드 추출"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="남편이 바람을 피우고 외도했어요",
            fault_types=["adultery"]
        )
        assert len(result.keywords) > 0
        assert any(kw in result.keywords for kw in ["외도", "바람"])

    def test_max_keywords(self):
        """최대 키워드 수"""
        summarizer = EventSummarizer()
        result = summarizer.summarize(
            content="외도, 바람, 불륜, 부정행위, 다른 사람, 만남",
            fault_types=["adultery"]
        )
        assert len(result.keywords) <= 5


# =============================================================================
# FAULT_TYPE_TEMPLATES 테스트
# =============================================================================

class TestFaultTypeTemplates:
    """유책사유 템플릿 테스트"""

    def test_all_fault_types_have_templates(self):
        """모든 유책사유에 템플릿 있음"""
        expected_types = [
            "adultery", "violence", "verbal_abuse",
            "economic_abuse", "desertion", "child_abuse",
            "financial_misconduct"
        ]
        for fault_type in expected_types:
            assert fault_type in FAULT_TYPE_TEMPLATES
            assert "templates" in FAULT_TYPE_TEMPLATES[fault_type]
            assert "keywords" in FAULT_TYPE_TEMPLATES[fault_type]
            assert len(FAULT_TYPE_TEMPLATES[fault_type]["templates"]) > 0
