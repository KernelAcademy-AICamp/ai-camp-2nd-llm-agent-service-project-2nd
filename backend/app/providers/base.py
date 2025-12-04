"""
Abstract Base Classes for AI Providers

Defines the interface that all AI provider implementations must follow.
This enables dependency injection and easy swapping of providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


@dataclass
class ProviderConfig:
    """Configuration for AI providers"""
    api_key: str = ""
    api_base: Optional[str] = None
    model: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    extra: Dict[str, Any] = field(default_factory=dict)


class ProviderCapability(str, Enum):
    """Capabilities that a provider may support"""
    CHAT = "chat"
    EMBEDDING = "embedding"
    VISION = "vision"
    STT = "stt"
    TTS = "tts"
    FUNCTION_CALLING = "function_calling"
    JSON_MODE = "json_mode"


@dataclass
class LLMResponse:
    """Response from LLM completion"""
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    """Response from embedding generation"""
    embedding: List[float]
    model: str
    dimensions: int = 0
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VisionResponse:
    """Response from vision analysis"""
    description: str
    labels: List[str] = field(default_factory=list)
    confidence: float = 0.0
    model: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class STTResponse:
    """Response from speech-to-text"""
    text: str
    language: str = ""
    duration_seconds: float = 0.0
    segments: List[Dict[str, Any]] = field(default_factory=list)
    model: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM (Language Model) providers.

    Implementations must provide chat completion functionality.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or ProviderConfig()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'azure', 'mock')"""
        pass

    @property
    def capabilities(self) -> List[ProviderCapability]:
        """Return list of capabilities this provider supports"""
        return [ProviderCapability.CHAT]

    @abstractmethod
    def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (provider-specific)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments

        Returns:
            LLMResponse with generated content and metadata
        """
        pass

    def complete_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Convenience method for simple text completion.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Passed to complete()

        Returns:
            Generated text content
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.complete(messages, **kwargs)
        return response.content

    @abstractmethod
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text for the given model.

        Args:
            text: Text to count tokens for
            model: Model name for tokenizer selection

        Returns:
            Token count
        """
        pass


class BaseEmbeddingProvider(ABC):
    """
    Abstract base class for text embedding providers.

    Implementations must provide vector embedding generation.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or ProviderConfig()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name"""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions for the default model"""
        pass

    @abstractmethod
    def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """
        Generate embedding for text.

        Args:
            text: Text to embed
            model: Model name (provider-specific)
            **kwargs: Additional provider-specific arguments

        Returns:
            EmbeddingResponse with embedding vector
        """
        pass

    def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[EmbeddingResponse]:
        """
        Generate embeddings for multiple texts.

        Default implementation calls embed() for each text.
        Providers may override for batch optimization.

        Args:
            texts: List of texts to embed
            model: Model name
            **kwargs: Additional arguments

        Returns:
            List of EmbeddingResponse objects
        """
        return [self.embed(text, model, **kwargs) for text in texts]


class BaseVisionProvider(ABC):
    """
    Abstract base class for vision/image analysis providers.

    Implementations must provide image understanding capabilities.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or ProviderConfig()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name"""
        pass

    @abstractmethod
    def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> VisionResponse:
        """
        Analyze an image with a prompt.

        Args:
            image_data: Image bytes (JPEG, PNG, etc.)
            prompt: Analysis prompt/question
            model: Model name
            **kwargs: Additional arguments

        Returns:
            VisionResponse with analysis results
        """
        pass

    def analyze_image_url(
        self,
        image_url: str,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> VisionResponse:
        """
        Analyze an image from URL.

        Args:
            image_url: URL to the image
            prompt: Analysis prompt
            model: Model name
            **kwargs: Additional arguments

        Returns:
            VisionResponse with analysis results
        """
        import urllib.request
        with urllib.request.urlopen(image_url) as response:
            image_data = response.read()
        return self.analyze_image(image_data, prompt, model, **kwargs)


class BaseSTTProvider(ABC):
    """
    Abstract base class for Speech-to-Text providers.

    Implementations must provide audio transcription capabilities.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or ProviderConfig()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name"""
        pass

    @property
    def supported_formats(self) -> List[str]:
        """Return list of supported audio formats"""
        return ["mp3", "wav", "m4a", "webm", "mp4", "mpeg", "mpga", "ogg"]

    @abstractmethod
    def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> STTResponse:
        """
        Transcribe audio to text.

        Args:
            audio_data: Audio bytes
            language: Language code (e.g., 'ko', 'en')
            model: Model name
            **kwargs: Additional arguments

        Returns:
            STTResponse with transcription
        """
        pass

    def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> STTResponse:
        """
        Transcribe audio from file path.

        Args:
            file_path: Path to audio file
            language: Language code
            model: Model name
            **kwargs: Additional arguments

        Returns:
            STTResponse with transcription
        """
        with open(file_path, "rb") as f:
            audio_data = f.read()
        return self.transcribe(audio_data, language, model, **kwargs)
