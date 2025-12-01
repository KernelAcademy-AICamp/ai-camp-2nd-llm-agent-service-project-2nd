"""
OpenAI API utilities for Draft generation

Real OpenAI API implementation using official openai package.
"""

import logging
from typing import List, Dict, Optional
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client (singleton)
_openai_client: Optional[OpenAI] = None


def _get_openai_client() -> OpenAI:
    """Get or create OpenAI client (singleton pattern)"""
    global _openai_client
    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not configured. "
                "Please set it in your .env file."
            )
        _openai_client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE if settings.OPENAI_API_BASE else None,
            timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS
        )
    return _openai_client


def generate_chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 4000
) -> str:
    """
    Generate chat completion using OpenAI GPT model

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name (defaults to settings.OPENAI_MODEL_CHAT)
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate

    Returns:
        Generated text response

    Raises:
        ValueError: If API key is not configured
        openai.APIError: If API call fails
    """
    if model is None:
        model = settings.OPENAI_MODEL_CHAT

    client = _get_openai_client()

    try:
        logger.info(f"Calling OpenAI chat completion with model={model}")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        result = response.choices[0].message.content
        logger.info(f"OpenAI response received, tokens used: {response.usage.total_tokens}")

        return result

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise


def generate_embedding(text: str, model: Optional[str] = None) -> List[float]:
    """
    Generate text embedding using OpenAI embedding model

    Args:
        text: Text to embed
        model: Model name (defaults to settings.OPENAI_MODEL_EMBEDDING)

    Returns:
        Embedding vector (1536 dimensions for text-embedding-3-small)

    Raises:
        ValueError: If API key is not configured
        openai.APIError: If API call fails
    """
    if model is None:
        model = settings.OPENAI_MODEL_EMBEDDING

    client = _get_openai_client()

    try:
        logger.info(f"Generating embedding with model={model}")

        response = client.embeddings.create(
            model=model,
            input=text
        )

        embedding = response.data[0].embedding
        logger.info(f"Embedding generated, dimensions: {len(embedding)}")

        return embedding

    except Exception as e:
        logger.error(f"OpenAI embedding API error: {e}")
        raise


def count_tokens(text: str, model: Optional[str] = None) -> int:
    """
    Estimate token count for text using tiktoken

    Args:
        text: Text to count tokens for
        model: Model name for encoding selection

    Returns:
        Token count
    """
    try:
        import tiktoken

        if model is None:
            model = settings.OPENAI_MODEL_CHAT

        # Get encoding for model
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            encoding = tiktoken.get_encoding("cl100k_base")

        return len(encoding.encode(text))

    except ImportError:
        # Fallback: rough estimate (1 token ≈ 4 chars for English, 2 chars for Korean)
        logger.warning("tiktoken not installed, using rough token estimate")
        return len(text) // 2  # Conservative estimate for Korean text
