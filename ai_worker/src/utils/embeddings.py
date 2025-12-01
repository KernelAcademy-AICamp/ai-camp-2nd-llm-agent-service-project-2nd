"""
Embedding Utilities for LEH AI Worker
Generates vector embeddings using OpenAI API
"""

import os
import logging
from typing import List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

# Default embedding model
DEFAULT_MODEL = "text-embedding-ada-002"
DEFAULT_DIMENSIONS = 1536

# Singleton client
_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Get or create OpenAI client (singleton pattern)"""
    global _client
    if _client is None:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        _client = OpenAI(api_key=api_key)
    return _client


def get_embedding(
    text: str,
    model: str = DEFAULT_MODEL
) -> List[float]:
    """
    Generate embedding for a single text

    Args:
        text: Text to embed
        model: OpenAI embedding model name

    Returns:
        List of floats (embedding vector)

    Raises:
        ValueError: If text is empty
        Exception: If API call fails
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    # Truncate if too long (OpenAI limit is ~8191 tokens for ada-002)
    # Rough estimate: 1 token ≈ 4 characters
    max_chars = 30000  # Safe limit
    if len(text) > max_chars:
        text = text[:max_chars]
        logger.warning(f"Text truncated to {max_chars} characters for embedding")

    try:
        client = _get_client()
        response = client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


def get_embeddings_batch(
    texts: List[str],
    model: str = DEFAULT_MODEL
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batch

    Args:
        texts: List of texts to embed
        model: OpenAI embedding model name

    Returns:
        List of embedding vectors

    Note:
        OpenAI API can handle up to 2048 texts per batch
    """
    if not texts:
        return []

    # Filter empty texts and truncate long ones
    max_chars = 30000
    processed_texts = []
    for text in texts:
        if text and text.strip():
            processed_texts.append(text[:max_chars] if len(text) > max_chars else text)

    if not processed_texts:
        return []

    try:
        client = _get_client()

        # OpenAI batch limit is 2048
        batch_size = 2048
        all_embeddings = []

        for i in range(0, len(processed_texts), batch_size):
            batch = processed_texts[i:i + batch_size]
            response = client.embeddings.create(
                input=batch,
                model=model
            )
            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([item.embedding for item in sorted_data])

        return all_embeddings

    except Exception as e:
        logger.error(f"Batch embedding generation failed: {e}")
        raise


def get_embedding_dimension(model: str = DEFAULT_MODEL) -> int:
    """
    Get the dimension of embeddings for a given model

    Args:
        model: OpenAI embedding model name

    Returns:
        Embedding dimension
    """
    dimensions = {
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }
    return dimensions.get(model, DEFAULT_DIMENSIONS)
