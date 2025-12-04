"""
OpenAI Provider Implementation

Concrete implementations of AI providers using OpenAI API.
"""

import base64
import logging
from typing import List, Dict, Optional, Any

from openai import OpenAI

from app.providers.base import (
    BaseLLMProvider,
    BaseEmbeddingProvider,
    BaseVisionProvider,
    BaseSTTProvider,
    ProviderConfig,
    ProviderCapability,
    LLMResponse,
    EmbeddingResponse,
    VisionResponse,
    STTResponse
)
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_default_config() -> ProviderConfig:
    """Get default config from settings"""
    return ProviderConfig(
        api_key=settings.OPENAI_API_KEY,
        api_base=settings.OPENAI_API_BASE if settings.OPENAI_API_BASE else None,
        timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS
    )


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI LLM provider for chat completions"""

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or _get_default_config())
        self._client: Optional[OpenAI] = None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def capabilities(self) -> List[ProviderCapability]:
        return [
            ProviderCapability.CHAT,
            ProviderCapability.FUNCTION_CALLING,
            ProviderCapability.JSON_MODE
        ]

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client"""
        if self._client is None:
            if not self.config.api_key:
                raise ValueError("OpenAI API key is not configured")
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base,
                timeout=self.config.timeout
            )
        return self._client

    def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion using OpenAI"""
        model = model or self.config.model or settings.OPENAI_MODEL_CHAT or self.DEFAULT_MODEL
        client = self._get_client()

        logger.info(f"OpenAI chat completion: model={model}")

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            usage = response.usage
            result = LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                finish_reason=response.choices[0].finish_reason or "stop",
                metadata={
                    "id": response.id,
                    "created": response.created
                }
            )

            logger.info(f"OpenAI response: tokens={result.total_tokens}")
            return result

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """Count tokens using tiktoken"""
        model = model or self.config.model or settings.OPENAI_MODEL_CHAT or self.DEFAULT_MODEL

        try:
            import tiktoken

            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")

            return len(encoding.encode(text))

        except ImportError:
            logger.warning("tiktoken not installed, using estimate")
            return len(text) // 2  # Conservative estimate for Korean


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider"""

    DEFAULT_MODEL = "text-embedding-3-small"
    DEFAULT_DIMENSIONS = 1536

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or _get_default_config())
        self._client: Optional[OpenAI] = None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def dimensions(self) -> int:
        return self.DEFAULT_DIMENSIONS

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client"""
        if self._client is None:
            if not self.config.api_key:
                raise ValueError("OpenAI API key is not configured")
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base,
                timeout=self.config.timeout
            )
        return self._client

    def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> EmbeddingResponse:
        """Generate embedding using OpenAI"""
        model = model or self.config.model or settings.OPENAI_MODEL_EMBEDDING or self.DEFAULT_MODEL
        client = self._get_client()

        logger.info(f"OpenAI embedding: model={model}")

        try:
            response = client.embeddings.create(
                model=model,
                input=text,
                **kwargs
            )

            embedding = response.data[0].embedding
            result = EmbeddingResponse(
                embedding=embedding,
                model=response.model,
                dimensions=len(embedding),
                tokens_used=response.usage.total_tokens if response.usage else 0,
                metadata={
                    "object": response.object
                }
            )

            logger.info(f"OpenAI embedding: dims={result.dimensions}")
            return result

        except Exception as e:
            logger.error(f"OpenAI embedding API error: {e}")
            raise

    def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts (optimized batch)"""
        model = model or self.config.model or settings.OPENAI_MODEL_EMBEDDING or self.DEFAULT_MODEL
        client = self._get_client()

        logger.info(f"OpenAI batch embedding: count={len(texts)}, model={model}")

        try:
            response = client.embeddings.create(
                model=model,
                input=texts,
                **kwargs
            )

            results = []
            for data in response.data:
                results.append(EmbeddingResponse(
                    embedding=data.embedding,
                    model=response.model,
                    dimensions=len(data.embedding),
                    tokens_used=0,  # Total split not available per item
                    metadata={"index": data.index}
                ))

            logger.info(f"OpenAI batch embedding: {len(results)} embeddings generated")
            return results

        except Exception as e:
            logger.error(f"OpenAI batch embedding API error: {e}")
            raise


class OpenAIVisionProvider(BaseVisionProvider):
    """OpenAI vision provider using GPT-4o Vision"""

    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or _get_default_config())
        self._client: Optional[OpenAI] = None

    @property
    def provider_name(self) -> str:
        return "openai"

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client"""
        if self._client is None:
            if not self.config.api_key:
                raise ValueError("OpenAI API key is not configured")
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base,
                timeout=self.config.timeout
            )
        return self._client

    def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> VisionResponse:
        """Analyze image using GPT-4o Vision"""
        model = model or self.config.model or self.DEFAULT_MODEL
        client = self._get_client()

        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")

        # Detect image type (simplified)
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            media_type = "image/png"
        elif image_data[:2] == b'\xff\xd8':
            media_type = "image/jpeg"
        else:
            media_type = "image/jpeg"  # Default assumption

        logger.info(f"OpenAI vision analysis: model={model}")

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_base64}",
                                    "detail": kwargs.get("detail", "auto")
                                }
                            }
                        ]
                    }
                ],
                max_tokens=kwargs.get("max_tokens", 1000)
            )

            content = response.choices[0].message.content or ""

            result = VisionResponse(
                description=content,
                labels=[],  # GPT-4o doesn't return structured labels
                confidence=1.0,  # Not available from API
                model=response.model,
                metadata={
                    "id": response.id,
                    "tokens": response.usage.total_tokens if response.usage else 0
                }
            )

            logger.info(f"OpenAI vision analysis complete")
            return result

        except Exception as e:
            logger.error(f"OpenAI vision API error: {e}")
            raise


class OpenAISTTProvider(BaseSTTProvider):
    """OpenAI STT provider using Whisper"""

    DEFAULT_MODEL = "whisper-1"

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or _get_default_config())
        self._client: Optional[OpenAI] = None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def supported_formats(self) -> List[str]:
        return ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client"""
        if self._client is None:
            if not self.config.api_key:
                raise ValueError("OpenAI API key is not configured")
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base,
                timeout=self.config.timeout
            )
        return self._client

    def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> STTResponse:
        """Transcribe audio using Whisper"""
        model = model or self.config.model or self.DEFAULT_MODEL
        client = self._get_client()

        logger.info(f"OpenAI STT: model={model}, language={language}")

        try:
            # Create a file-like object from bytes
            import io
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.mp3"  # Whisper needs a filename

            transcribe_kwargs: Dict[str, Any] = {
                "model": model,
                "file": audio_file,
                "response_format": kwargs.get("response_format", "verbose_json")
            }

            if language:
                transcribe_kwargs["language"] = language

            response = client.audio.transcriptions.create(**transcribe_kwargs)

            # Handle verbose_json response
            if hasattr(response, "text"):
                text = response.text
                duration = getattr(response, "duration", 0.0)
                detected_language = getattr(response, "language", language or "")
                segments = getattr(response, "segments", [])
            else:
                text = str(response)
                duration = 0.0
                detected_language = language or ""
                segments = []

            result = STTResponse(
                text=text,
                language=detected_language,
                duration_seconds=duration,
                segments=[
                    {
                        "start": seg.get("start", 0) if isinstance(seg, dict) else getattr(seg, "start", 0),
                        "end": seg.get("end", 0) if isinstance(seg, dict) else getattr(seg, "end", 0),
                        "text": seg.get("text", "") if isinstance(seg, dict) else getattr(seg, "text", "")
                    }
                    for seg in (segments or [])
                ],
                model=model,
                metadata={}
            )

            logger.info(f"OpenAI STT complete: duration={duration}s")
            return result

        except Exception as e:
            logger.error(f"OpenAI STT API error: {e}")
            raise
