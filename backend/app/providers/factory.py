"""
AI Provider Factory

Factory for creating AI provider instances based on configuration.
Supports switching between providers (OpenAI, Azure, Mock) at runtime.
"""

import logging
from enum import Enum
from typing import Union, Optional, Type

from app.providers.base import (
    BaseLLMProvider,
    BaseEmbeddingProvider,
    BaseVisionProvider,
    BaseSTTProvider,
    ProviderConfig
)
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
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported AI provider types"""
    OPENAI = "openai"
    AZURE = "azure"  # Future support
    MOCK = "mock"


class ProviderCategory(str, Enum):
    """Categories of AI capabilities"""
    LLM = "llm"
    EMBEDDING = "embedding"
    VISION = "vision"
    STT = "stt"


# Provider registry - maps (type, category) to implementation class
_PROVIDER_REGISTRY: dict = {
    (ProviderType.OPENAI, ProviderCategory.LLM): OpenAILLMProvider,
    (ProviderType.OPENAI, ProviderCategory.EMBEDDING): OpenAIEmbeddingProvider,
    (ProviderType.OPENAI, ProviderCategory.VISION): OpenAIVisionProvider,
    (ProviderType.OPENAI, ProviderCategory.STT): OpenAISTTProvider,
    (ProviderType.MOCK, ProviderCategory.LLM): MockLLMProvider,
    (ProviderType.MOCK, ProviderCategory.EMBEDDING): MockEmbeddingProvider,
    (ProviderType.MOCK, ProviderCategory.VISION): MockVisionProvider,
    (ProviderType.MOCK, ProviderCategory.STT): MockSTTProvider,
}

# Singleton instances for default providers
_provider_instances: dict = {}


def get_provider(
    category: ProviderCategory,
    provider_type: Optional[ProviderType] = None,
    config: Optional[ProviderConfig] = None,
    use_singleton: bool = True
) -> Union[BaseLLMProvider, BaseEmbeddingProvider, BaseVisionProvider, BaseSTTProvider]:
    """
    Get an AI provider instance.

    Args:
        category: The capability category (LLM, EMBEDDING, VISION, STT)
        provider_type: Provider type (defaults to OPENAI or MOCK based on settings)
        config: Optional custom configuration
        use_singleton: Whether to reuse existing instances (default True)

    Returns:
        Provider instance for the requested category

    Raises:
        ValueError: If provider/category combination is not supported
    """
    # Determine provider type
    if provider_type is None:
        # Use mock in test environment or when API key is missing
        if settings.APP_ENV == "test" or not settings.OPENAI_API_KEY:
            provider_type = ProviderType.MOCK
            logger.debug(f"Using mock provider for {category} (test mode or no API key)")
        else:
            provider_type = ProviderType.OPENAI

    # Check registry
    key = (provider_type, category)
    if key not in _PROVIDER_REGISTRY:
        raise ValueError(
            f"Unsupported provider combination: {provider_type}/{category}. "
            f"Available: {list(_PROVIDER_REGISTRY.keys())}"
        )

    # Return singleton if requested and available
    if use_singleton and config is None:
        cache_key = f"{provider_type}_{category}"
        if cache_key in _provider_instances:
            return _provider_instances[cache_key]

    # Create new instance
    provider_class = _PROVIDER_REGISTRY[key]
    instance = provider_class(config)

    # Cache singleton
    if use_singleton and config is None:
        _provider_instances[cache_key] = instance
        logger.info(f"Created {provider_type} provider for {category}")

    return instance


def get_llm_provider(
    provider_type: Optional[ProviderType] = None,
    config: Optional[ProviderConfig] = None
) -> BaseLLMProvider:
    """Get LLM provider (convenience function)"""
    return get_provider(ProviderCategory.LLM, provider_type, config)  # type: ignore


def get_embedding_provider(
    provider_type: Optional[ProviderType] = None,
    config: Optional[ProviderConfig] = None
) -> BaseEmbeddingProvider:
    """Get embedding provider (convenience function)"""
    return get_provider(ProviderCategory.EMBEDDING, provider_type, config)  # type: ignore


def get_vision_provider(
    provider_type: Optional[ProviderType] = None,
    config: Optional[ProviderConfig] = None
) -> BaseVisionProvider:
    """Get vision provider (convenience function)"""
    return get_provider(ProviderCategory.VISION, provider_type, config)  # type: ignore


def get_stt_provider(
    provider_type: Optional[ProviderType] = None,
    config: Optional[ProviderConfig] = None
) -> BaseSTTProvider:
    """Get STT provider (convenience function)"""
    return get_provider(ProviderCategory.STT, provider_type, config)  # type: ignore


def register_provider(
    provider_type: ProviderType,
    category: ProviderCategory,
    provider_class: Type
) -> None:
    """
    Register a custom provider implementation.

    Args:
        provider_type: Provider type identifier
        category: Capability category
        provider_class: Provider class to register

    Example:
        register_provider(
            ProviderType.AZURE,
            ProviderCategory.LLM,
            AzureLLMProvider
        )
    """
    key = (provider_type, category)
    _PROVIDER_REGISTRY[key] = provider_class
    logger.info(f"Registered provider: {provider_type}/{category} -> {provider_class.__name__}")


def clear_provider_cache() -> None:
    """Clear cached provider instances (useful for testing)"""
    global _provider_instances
    _provider_instances = {}
    logger.debug("Provider cache cleared")
