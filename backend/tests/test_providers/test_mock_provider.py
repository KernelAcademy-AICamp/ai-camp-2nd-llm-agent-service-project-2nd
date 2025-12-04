"""
Tests for Mock AI Providers

Unit tests for mock provider implementations.
"""

import pytest
from app.providers import (
    MockLLMProvider,
    MockEmbeddingProvider,
    MockVisionProvider,
    MockSTTProvider
)
from app.providers.base import (
    ProviderConfig,
    LLMResponse,
    EmbeddingResponse,
    VisionResponse,
    STTResponse
)
from app.providers.factory import (
    get_provider,
    get_llm_provider,
    get_embedding_provider,
    get_vision_provider,
    get_stt_provider,
    ProviderType,
    ProviderCategory,
    clear_provider_cache
)


class TestMockLLMProvider:
    """Tests for MockLLMProvider"""

    def setup_method(self):
        """Setup test instance"""
        self.provider = MockLLMProvider()

    def test_provider_name(self):
        """Test provider name is 'mock'"""
        assert self.provider.provider_name == "mock"

    def test_complete_returns_llm_response(self):
        """Test complete returns LLMResponse"""
        messages = [{"role": "user", "content": "Hello"}]
        response = self.provider.complete(messages)

        assert isinstance(response, LLMResponse)
        assert response.content
        assert response.model == "mock-llm"
        assert response.finish_reason == "stop"

    def test_complete_increments_call_count(self):
        """Test call count increments"""
        messages = [{"role": "user", "content": "Test"}]

        assert self.provider.call_count == 0
        self.provider.complete(messages)
        assert self.provider.call_count == 1
        self.provider.complete(messages)
        assert self.provider.call_count == 2

    def test_complete_stores_last_messages(self):
        """Test last messages are stored"""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]
        self.provider.complete(messages)

        assert self.provider.last_messages == messages

    def test_set_custom_response(self):
        """Test custom response can be set"""
        custom = "Custom mock response"
        self.provider.set_response(custom)

        response = self.provider.complete([{"role": "user", "content": "Any"}])
        assert response.content == custom

    def test_count_tokens(self):
        """Test token counting"""
        text = "Hello world"
        tokens = self.provider.count_tokens(text)
        assert tokens == len(text) // 4

    def test_complete_text_convenience(self):
        """Test complete_text convenience method"""
        result = self.provider.complete_text("Hello", system_prompt="Be helpful")
        assert isinstance(result, str)


class TestMockEmbeddingProvider:
    """Tests for MockEmbeddingProvider"""

    def setup_method(self):
        """Setup test instance"""
        self.provider = MockEmbeddingProvider()

    def test_provider_name(self):
        """Test provider name is 'mock'"""
        assert self.provider.provider_name == "mock"

    def test_dimensions(self):
        """Test default dimensions"""
        assert self.provider.dimensions == 1536

    def test_embed_returns_embedding_response(self):
        """Test embed returns EmbeddingResponse"""
        response = self.provider.embed("Test text")

        assert isinstance(response, EmbeddingResponse)
        assert len(response.embedding) == 1536
        assert response.model == "mock-embedding"

    def test_embed_deterministic(self):
        """Test same input produces same embedding"""
        text = "Consistent text"
        response1 = self.provider.embed(text)
        response2 = self.provider.embed(text)

        assert response1.embedding == response2.embedding

    def test_embed_different_text_different_embedding(self):
        """Test different text produces different embedding"""
        response1 = self.provider.embed("Text one")
        response2 = self.provider.embed("Text two")

        assert response1.embedding != response2.embedding

    def test_embed_unit_normalized(self):
        """Test embedding is unit normalized"""
        response = self.provider.embed("Test")
        magnitude = sum(v ** 2 for v in response.embedding) ** 0.5
        assert abs(magnitude - 1.0) < 0.001

    def test_embed_batch(self):
        """Test batch embedding"""
        texts = ["Text 1", "Text 2", "Text 3"]
        responses = self.provider.embed_batch(texts)

        assert len(responses) == 3
        assert all(isinstance(r, EmbeddingResponse) for r in responses)


class TestMockVisionProvider:
    """Tests for MockVisionProvider"""

    def setup_method(self):
        """Setup test instance"""
        self.provider = MockVisionProvider()

    def test_provider_name(self):
        """Test provider name is 'mock'"""
        assert self.provider.provider_name == "mock"

    def test_analyze_image_returns_vision_response(self):
        """Test analyze_image returns VisionResponse"""
        image_data = b"fake image data"
        prompt = "Describe this image"

        response = self.provider.analyze_image(image_data, prompt)

        assert isinstance(response, VisionResponse)
        assert response.description
        assert response.model == "mock-vision"

    def test_analyze_image_stores_prompt(self):
        """Test last prompt is stored"""
        prompt = "Test prompt"
        self.provider.analyze_image(b"data", prompt)

        assert self.provider.last_prompt == prompt

    def test_set_custom_response(self):
        """Test custom response can be set"""
        custom = VisionResponse(
            description="Custom description",
            labels=["custom", "label"],
            confidence=0.99,
            model="custom-model"
        )
        self.provider.set_response(custom)

        response = self.provider.analyze_image(b"data", "prompt")
        assert response.description == "Custom description"


class TestMockSTTProvider:
    """Tests for MockSTTProvider"""

    def setup_method(self):
        """Setup test instance"""
        self.provider = MockSTTProvider()

    def test_provider_name(self):
        """Test provider name is 'mock'"""
        assert self.provider.provider_name == "mock"

    def test_transcribe_returns_stt_response(self):
        """Test transcribe returns STTResponse"""
        audio_data = b"fake audio data" * 1000  # ~15KB

        response = self.provider.transcribe(audio_data, language="en")

        assert isinstance(response, STTResponse)
        assert response.text
        assert response.language == "en"
        assert response.duration_seconds > 0

    def test_transcribe_stores_language(self):
        """Test last language is stored"""
        self.provider.transcribe(b"data", language="ko")
        assert self.provider.last_language == "ko"

    def test_set_custom_response(self):
        """Test custom response can be set"""
        custom = STTResponse(
            text="Custom transcription",
            language="ko",
            duration_seconds=5.0,
            model="custom-model"
        )
        self.provider.set_response(custom)

        response = self.provider.transcribe(b"data")
        assert response.text == "Custom transcription"


class TestProviderFactory:
    """Tests for provider factory functions"""

    def setup_method(self):
        """Clear cache before each test"""
        clear_provider_cache()

    def test_get_provider_llm(self):
        """Test getting LLM provider"""
        provider = get_provider(ProviderCategory.LLM, ProviderType.MOCK)
        assert isinstance(provider, MockLLMProvider)

    def test_get_provider_embedding(self):
        """Test getting embedding provider"""
        provider = get_provider(ProviderCategory.EMBEDDING, ProviderType.MOCK)
        assert isinstance(provider, MockEmbeddingProvider)

    def test_get_provider_vision(self):
        """Test getting vision provider"""
        provider = get_provider(ProviderCategory.VISION, ProviderType.MOCK)
        assert isinstance(provider, MockVisionProvider)

    def test_get_provider_stt(self):
        """Test getting STT provider"""
        provider = get_provider(ProviderCategory.STT, ProviderType.MOCK)
        assert isinstance(provider, MockSTTProvider)

    def test_get_llm_provider_convenience(self):
        """Test get_llm_provider convenience function"""
        provider = get_llm_provider(ProviderType.MOCK)
        assert isinstance(provider, MockLLMProvider)

    def test_get_embedding_provider_convenience(self):
        """Test get_embedding_provider convenience function"""
        provider = get_embedding_provider(ProviderType.MOCK)
        assert isinstance(provider, MockEmbeddingProvider)

    def test_singleton_behavior(self):
        """Test providers are cached as singletons"""
        provider1 = get_llm_provider(ProviderType.MOCK)
        provider2 = get_llm_provider(ProviderType.MOCK)
        assert provider1 is provider2

    def test_no_singleton_with_config(self):
        """Test new instance created with custom config"""
        provider1 = get_llm_provider(ProviderType.MOCK)
        provider2 = get_llm_provider(ProviderType.MOCK, config=ProviderConfig())
        assert provider1 is not provider2

    def test_clear_provider_cache(self):
        """Test cache clearing"""
        provider1 = get_llm_provider(ProviderType.MOCK)
        clear_provider_cache()
        provider2 = get_llm_provider(ProviderType.MOCK)
        assert provider1 is not provider2

    def test_invalid_provider_raises(self):
        """Test invalid provider/category raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            get_provider(ProviderCategory.LLM, ProviderType.AZURE)
        assert "Unsupported provider combination" in str(exc_info.value)
