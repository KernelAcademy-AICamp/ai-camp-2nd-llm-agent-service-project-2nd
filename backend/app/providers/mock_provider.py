"""
Mock Provider Implementation

Mock implementations of AI providers for testing purposes.
These providers return deterministic results without making API calls.
"""

import hashlib
import logging
from typing import List, Dict, Optional

from app.providers.base import (
    BaseLLMProvider,
    BaseEmbeddingProvider,
    BaseVisionProvider,
    BaseSTTProvider,
    ProviderConfig,
    LLMResponse,
    EmbeddingResponse,
    VisionResponse,
    STTResponse
)

logger = logging.getLogger(__name__)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing"""

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig())
        self.call_count = 0
        self.last_messages: List[Dict[str, str]] = []
        self.custom_response: Optional[str] = None

    @property
    def provider_name(self) -> str:
        return "mock"

    def set_response(self, response: str) -> None:
        """Set a custom response for testing"""
        self.custom_response = response

    def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """Return mock completion"""
        self.call_count += 1
        self.last_messages = messages

        model = model or "mock-llm"

        # Generate deterministic response based on input
        if self.custom_response:
            content = self.custom_response
        else:
            last_message = messages[-1]["content"] if messages else ""
            content = f"Mock response for: {last_message[:50]}..."

        # Estimate tokens
        input_tokens = sum(len(m["content"]) // 4 for m in messages)
        output_tokens = len(content) // 4

        logger.debug(f"MockLLM complete: call #{self.call_count}")

        return LLMResponse(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            finish_reason="stop",
            metadata={"mock": True, "call_count": self.call_count}
        )

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Estimate tokens (4 chars per token)"""
        return len(text) // 4


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Mock embedding provider for testing"""

    MOCK_DIMENSIONS = 1536

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig())
        self.call_count = 0
        self.last_text: str = ""

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def dimensions(self) -> int:
        return self.MOCK_DIMENSIONS

    def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """Return mock embedding (deterministic based on text hash)"""
        self.call_count += 1
        self.last_text = text

        model = model or "mock-embedding"

        # Generate deterministic embedding from text hash
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        embedding = self._hash_to_embedding(text_hash, self.MOCK_DIMENSIONS)

        logger.debug(f"MockEmbedding embed: call #{self.call_count}")

        return EmbeddingResponse(
            embedding=embedding,
            model=model,
            dimensions=self.MOCK_DIMENSIONS,
            tokens_used=len(text) // 4,
            metadata={"mock": True, "call_count": self.call_count}
        )

    def _hash_to_embedding(self, hex_hash: str, dims: int) -> List[float]:
        """Convert hash to deterministic embedding vector"""
        # Use hash bytes to seed embedding values
        embedding = []
        hash_bytes = bytes.fromhex(hex_hash)

        for i in range(dims):
            # Cycle through hash bytes and normalize to [-1, 1]
            byte_val = hash_bytes[i % len(hash_bytes)]
            # Vary based on position
            val = ((byte_val + i) % 256) / 128.0 - 1.0
            embedding.append(val)

        # Normalize to unit vector
        magnitude = sum(v ** 2 for v in embedding) ** 0.5
        return [v / magnitude for v in embedding]


class MockVisionProvider(BaseVisionProvider):
    """Mock vision provider for testing"""

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig())
        self.call_count = 0
        self.last_prompt: str = ""
        self.custom_response: Optional[VisionResponse] = None

    @property
    def provider_name(self) -> str:
        return "mock"

    def set_response(self, response: VisionResponse) -> None:
        """Set a custom response for testing"""
        self.custom_response = response

    def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> VisionResponse:
        """Return mock vision analysis"""
        self.call_count += 1
        self.last_prompt = prompt

        model = model or "mock-vision"

        if self.custom_response:
            return self.custom_response

        # Generate mock response
        image_size = len(image_data)

        logger.debug(f"MockVision analyze: call #{self.call_count}, size={image_size}")

        return VisionResponse(
            description=f"Mock analysis for prompt: {prompt[:50]}. Image size: {image_size} bytes.",
            labels=["mock", "test", "image"],
            confidence=0.95,
            model=model,
            metadata={
                "mock": True,
                "call_count": self.call_count,
                "image_size": image_size
            }
        )


class MockSTTProvider(BaseSTTProvider):
    """Mock STT provider for testing"""

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig())
        self.call_count = 0
        self.last_language: Optional[str] = None
        self.custom_response: Optional[STTResponse] = None

    @property
    def provider_name(self) -> str:
        return "mock"

    def set_response(self, response: STTResponse) -> None:
        """Set a custom response for testing"""
        self.custom_response = response

    def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> STTResponse:
        """Return mock transcription"""
        self.call_count += 1
        self.last_language = language

        model = model or "mock-stt"

        if self.custom_response:
            return self.custom_response

        # Estimate duration (rough: 16kHz mono = 32KB per second)
        duration = len(audio_data) / 32000

        logger.debug(f"MockSTT transcribe: call #{self.call_count}, duration={duration:.1f}s")

        return STTResponse(
            text="This is a mock transcription of the audio file.",
            language=language or "en",
            duration_seconds=duration,
            segments=[
                {"start": 0.0, "end": duration / 2, "text": "This is a mock transcription"},
                {"start": duration / 2, "end": duration, "text": "of the audio file."}
            ],
            model=model,
            metadata={
                "mock": True,
                "call_count": self.call_count,
                "audio_size": len(audio_data)
            }
        )
