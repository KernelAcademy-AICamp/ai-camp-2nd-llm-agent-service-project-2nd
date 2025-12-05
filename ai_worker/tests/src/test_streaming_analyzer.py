"""
Test suite for StreamingAnalyzer
실시간 GPT 응답 스트리밍 테스트

Note: API 호출이 필요한 테스트는 @pytest.mark.integration 마커 사용
"""

import pytest
import json
import hashlib
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.analysis.streaming_analyzer import (
    StreamingAnalyzer,
    StreamingConfig,
    stream_analysis,
    SYSTEM_PROMPT,
)
from src.schemas import EvidenceChunk, SourceLocation
from src.schemas.source_location import FileType
from src.exceptions import AnalysisError


def make_test_chunk(
    content: str = "테스트 메시지입니다",
    sender: str = None,
    timestamp: datetime = None,
    source_location: SourceLocation = None
) -> EvidenceChunk:
    """테스트용 EvidenceChunk 생성 헬퍼"""
    if source_location is None:
        source_location = SourceLocation(
            file_name="test_chat.txt",
            file_type=FileType.KAKAOTALK,
            line_number=1
        )

    return EvidenceChunk(
        chunk_id="test-001",
        file_id="file-001",
        case_id="case-001",
        content=content,
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
        source_location=source_location,
        sender=sender,
        timestamp=timestamp
    )


class TestStreamingConfig:
    """StreamingConfig 테스트"""

    def test_default_config(self):
        """기본 설정 테스트"""
        config = StreamingConfig()

        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.1
        assert config.max_tokens == 500

    def test_custom_config(self):
        """커스텀 설정 테스트"""
        config = StreamingConfig(
            model="gpt-4o",
            temperature=0.3,
            max_tokens=1000
        )

        assert config.model == "gpt-4o"
        assert config.temperature == 0.3
        assert config.max_tokens == 1000


class TestStreamingAnalyzerInitialization:
    """StreamingAnalyzer 초기화 테스트"""

    def test_analyzer_creation(self):
        """기본 생성 테스트"""
        analyzer = StreamingAnalyzer()

        assert analyzer is not None
        assert analyzer.config.model == "gpt-4o-mini"

    def test_analyzer_with_config(self):
        """설정과 함께 생성 테스트"""
        config = StreamingConfig(model="gpt-4o")
        analyzer = StreamingAnalyzer(config=config)

        assert analyzer.config.model == "gpt-4o"

    def test_system_prompt_built(self):
        """시스템 프롬프트 생성 테스트"""
        analyzer = StreamingAnalyzer()

        assert analyzer._system_prompt is not None
        assert len(analyzer._system_prompt) > 0
        # 톤 가이드라인 포함 확인
        assert "객관적" in analyzer._system_prompt or "AI 응답 가이드라인" in analyzer._system_prompt


class TestUserPromptBuilding:
    """사용자 프롬프트 생성 테스트"""

    def test_build_basic_prompt(self):
        """기본 프롬프트 생성 테스트"""
        analyzer = StreamingAnalyzer()
        chunk = make_test_chunk(content="테스트 메시지입니다")

        prompt = analyzer._build_user_prompt(chunk)

        assert "테스트 메시지입니다" in prompt
        assert "메시지 내용" in prompt

    def test_build_prompt_with_context(self):
        """컨텍스트 포함 프롬프트 생성 테스트"""
        analyzer = StreamingAnalyzer()
        chunk = make_test_chunk(
            content="테스트 메시지입니다",
            sender="홍길동",
            timestamp=datetime(2024, 1, 15, 14, 30)
        )

        prompt = analyzer._build_user_prompt(chunk)

        assert "발신자: 홍길동" in prompt
        assert "시간:" in prompt

    def test_build_prompt_with_source_location(self):
        """출처 정보 포함 프롬프트 생성 테스트"""
        analyzer = StreamingAnalyzer()
        source_loc = SourceLocation(
            file_name="chat.txt",
            file_type=FileType.KAKAOTALK,
            line_number=10
        )
        chunk = make_test_chunk(
            content="테스트 메시지입니다",
            source_location=source_loc
        )

        prompt = analyzer._build_user_prompt(chunk)

        assert "출처:" in prompt


class TestResponseParsing:
    """응답 파싱 테스트"""

    def test_parse_valid_response(self):
        """유효한 응답 파싱 테스트"""
        analyzer = StreamingAnalyzer()

        valid_response = json.dumps({
            "primary_ground": "부정행위",
            "secondary_grounds": [],
            "confidence": 0.75,
            "key_phrases": ["호텔", "만났어"],
            "reasoning": "호텔 만남 정황이 나타납니다",
            "mentioned_entities": [],
            "requires_review": False,
            "review_reason": None
        })

        result = analyzer._parse_response(valid_response)

        assert result is not None
        assert result.confidence_score > 0

    def test_parse_invalid_json(self):
        """잘못된 JSON 파싱 테스트"""
        analyzer = StreamingAnalyzer()

        with pytest.raises(AnalysisError) as exc_info:
            analyzer._parse_response("invalid json {{{")

        assert "파싱 실패" in str(exc_info.value)

    def test_parse_missing_fields(self):
        """필수 필드 누락 테스트"""
        analyzer = StreamingAnalyzer()

        incomplete_response = json.dumps({
            "primary_ground": "부정행위"
            # 다른 필수 필드 누락
        })

        # Pydantic validation이 실패해야 함
        with pytest.raises(AnalysisError):
            analyzer._parse_response(incomplete_response)


class TestClientInitialization:
    """클라이언트 초기화 테스트"""

    def test_client_lazy_initialization(self):
        """클라이언트 지연 초기화 테스트"""
        analyzer = StreamingAnalyzer()

        # 초기에는 None
        assert analyzer._client is None
        assert analyzer._async_client is None

    @patch.dict('os.environ', {'OPENAI_API_KEY': ''})
    def test_client_without_api_key(self):
        """API 키 없이 클라이언트 초기화 테스트"""
        analyzer = StreamingAnalyzer()

        with pytest.raises(AnalysisError) as exc_info:
            analyzer._get_client()

        assert "OPENAI_API_KEY" in str(exc_info.value)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.OpenAI')
    def test_client_with_api_key(self, mock_openai_class):
        """API 키로 클라이언트 초기화 테스트"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        analyzer = StreamingAnalyzer()
        client = analyzer._get_client()

        assert client is not None
        mock_openai_class.assert_called_once_with(api_key='test-key')


class TestStreamingAnalysis:
    """스트리밍 분석 테스트 (Mock 사용)"""

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.OpenAI')
    def test_analyze_stream_basic(self, mock_openai_class):
        """기본 스트리밍 분석 테스트"""
        # Mock 설정
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # 스트리밍 응답 Mock
        mock_chunk1 = Mock()
        mock_chunk1.choices = [Mock(delta=Mock(content='{"primary_ground":'))]

        mock_chunk2 = Mock()
        mock_chunk2.choices = [Mock(delta=Mock(content='"무관","secondary_grounds":[],"confidence":0.9,"key_phrases":[],"reasoning":"일상 대화입니다","mentioned_entities":[],"requires_review":false,"review_reason":null}'))]

        mock_stream = [mock_chunk1, mock_chunk2]
        mock_client.chat.completions.create.return_value = iter(mock_stream)

        # 테스트 실행
        analyzer = StreamingAnalyzer()
        chunk = make_test_chunk(content="오늘 날씨 좋네요")

        collected = []
        for text in analyzer.analyze_stream(chunk):
            collected.append(text)

        assert len(collected) == 2

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.OpenAI')
    def test_analyze_with_callback(self, mock_openai_class):
        """콜백 기반 스트리밍 테스트"""
        # Mock 설정
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        full_response = '{"primary_ground":"무관","secondary_grounds":[],"confidence":0.9,"key_phrases":[],"reasoning":"일상 대화입니다","mentioned_entities":[],"requires_review":false,"review_reason":null}'

        mock_chunk = Mock()
        mock_chunk.choices = [Mock(delta=Mock(content=full_response))]

        mock_client.chat.completions.create.return_value = iter([mock_chunk])

        # 콜백 함수
        chunks_received = []
        def on_chunk(content):
            chunks_received.append(content)

        complete_called = []
        def on_complete(analysis):
            complete_called.append(analysis)

        # 테스트 실행
        analyzer = StreamingAnalyzer()
        chunk = make_test_chunk(content="테스트")

        result = analyzer.analyze_with_callback(
            chunk,
            on_chunk=on_chunk,
            on_complete=on_complete
        )

        assert len(chunks_received) > 0
        assert len(complete_called) == 1
        assert result is not None


class TestAsyncStreaming:
    """비동기 스트리밍 테스트"""

    @pytest.mark.asyncio
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.AsyncOpenAI')
    async def test_analyze_stream_async(self, mock_async_openai_class):
        """비동기 스트리밍 분석 테스트"""
        # Mock 설정
        mock_client = AsyncMock()
        mock_async_openai_class.return_value = mock_client

        # 비동기 스트리밍 응답 Mock
        async def mock_stream():
            mock_chunk = Mock()
            mock_chunk.choices = [Mock(delta=Mock(content='{"test": "data"}'))]
            yield mock_chunk

        mock_client.chat.completions.create.return_value = mock_stream()

        # 테스트 실행
        analyzer = StreamingAnalyzer()
        chunk = make_test_chunk(content="테스트 메시지")

        collected = []
        async for text in analyzer.analyze_stream_async(chunk):
            collected.append(text)

        assert len(collected) > 0


class TestConvenienceFunctions:
    """간편 함수 테스트"""

    def test_stream_analysis_function_exists(self):
        """stream_analysis 함수 존재 테스트"""
        assert callable(stream_analysis)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.OpenAI')
    def test_stream_analysis_function(self, mock_openai_class):
        """stream_analysis 간편 함수 테스트"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        full_response = '{"primary_ground":"무관","secondary_grounds":[],"confidence":0.9,"key_phrases":[],"reasoning":"테스트","mentioned_entities":[],"requires_review":false,"review_reason":null}'

        mock_chunk = Mock()
        mock_chunk.choices = [Mock(delta=Mock(content=full_response))]

        mock_client.chat.completions.create.return_value = iter([mock_chunk])

        chunk = make_test_chunk(content="테스트")

        # Generator 반환 확인
        result = stream_analysis(chunk, model="gpt-4o-mini")
        assert hasattr(result, '__iter__') or hasattr(result, '__next__')


class TestSystemPrompt:
    """시스템 프롬프트 테스트"""

    def test_system_prompt_contains_categories(self):
        """시스템 프롬프트에 카테고리 포함 테스트"""
        assert "부정행위" in SYSTEM_PROMPT or "{categories}" in SYSTEM_PROMPT

    def test_system_prompt_contains_confidence_levels(self):
        """시스템 프롬프트에 신뢰도 기준 포함 테스트"""
        assert "confidence" in SYSTEM_PROMPT.lower()
        assert "0.0" in SYSTEM_PROMPT
        assert "1.0" in SYSTEM_PROMPT

    def test_system_prompt_json_format(self):
        """시스템 프롬프트에 JSON 형식 포함 테스트"""
        assert "primary_ground" in SYSTEM_PROMPT
        assert "reasoning" in SYSTEM_PROMPT


class TestErrorHandling:
    """에러 처리 테스트"""

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai.OpenAI')
    def test_api_error_handling(self, mock_openai_class):
        """API 에러 처리 테스트"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        analyzer = StreamingAnalyzer()
        chunk = make_test_chunk(content="테스트")

        with pytest.raises(AnalysisError) as exc_info:
            list(analyzer.analyze_stream(chunk))

        assert exc_info.value.fallback_available is True

    def test_analysis_error_attributes(self):
        """AnalysisError 속성 테스트"""
        error = AnalysisError(
            "테스트 에러",
            analysis_type="streaming",
            fallback_available=True
        )

        assert error.analysis_type == "streaming"
        assert error.fallback_available is True
