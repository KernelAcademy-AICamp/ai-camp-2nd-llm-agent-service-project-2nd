"""
AI Provider Abstraction Layer

Provides abstract interfaces and concrete implementations for AI services:
- LLM (Chat Completion)
- Embedding Generation
- Vision Analysis
- Speech-to-Text (STT)

This allows for easy switching between providers (OpenAI, Azure, local models)
and facilitates testing with mock implementations.
"""

from app.providers.base import (
    BaseLLMProvider,
    BaseEmbeddingProvider,
    BaseVisionProvider,
    BaseSTTProvider,
    ProviderConfig
)
from app.providers.factory import get_provider, ProviderType
from app.providers.openai_provider import (
    OpenAILLMProvider,
    OpenAIEmbeddingProvider,
    OpenAIVisionProvider,
    OpenAISTTProvider
)
from app.providers.mock_provider import (
    MockLLMProvider,
    MockEmbeddingProvider,
    MockVisionProvider,
    MockSTTProvider
)

__all__ = [
    # Base classes
    "BaseLLMProvider",
    "BaseEmbeddingProvider",
    "BaseVisionProvider",
    "BaseSTTProvider",
    "ProviderConfig",
    # Factory
    "get_provider",
    "ProviderType",
    # OpenAI implementations
    "OpenAILLMProvider",
    "OpenAIEmbeddingProvider",
    "OpenAIVisionProvider",
    "OpenAISTTProvider",
    # Mock implementations
    "MockLLMProvider",
    "MockEmbeddingProvider",
    "MockVisionProvider",
    "MockSTTProvider",
]
