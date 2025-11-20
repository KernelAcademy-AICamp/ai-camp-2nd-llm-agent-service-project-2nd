"""
OpenAI API utilities for Draft generation

Mock implementation for local development.
TODO: Replace with real OpenAI API calls when API key is configured.

Migration Guide:
1. Uncomment openai imports and client initialization
2. Replace mock responses with real API calls
3. No changes needed in service or API layers
"""

from typing import List, Dict, Optional
from app.core.config import settings

# TODO: Uncomment when OpenAI API key is configured
# from openai import OpenAI
# client = OpenAI(api_key=settings.OPENAI_API_KEY)


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
    """
    # TODO: Replace with OpenAI API when key is configured
    # if model is None:
    #     model = settings.OPENAI_MODEL_CHAT
    #
    # response = client.chat.completions.create(
    #     model=model,
    #     messages=messages,
    #     temperature=temperature,
    #     max_tokens=max_tokens
    # )
    #
    # return response.choices[0].message.content

    # Mock implementation
    # Return a simple template-based response
    system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    # Check if this is a draft generation request
    if "이혼 소송" in system_msg or "준비서면" in system_msg:
        return _generate_mock_draft(user_msg)

    # Generic mock response
    return f"Mock GPT response for: {user_msg[:50]}..."


def generate_embedding(text: str, model: Optional[str] = None) -> List[float]:
    """
    Generate text embedding using OpenAI embedding model

    Args:
        text: Text to embed
        model: Model name (defaults to settings.OPENAI_MODEL_EMBEDDING)

    Returns:
        Embedding vector (1536 dimensions for text-embedding-3-small)
    """
    # TODO: Replace with OpenAI API when key is configured
    # if model is None:
    #     model = settings.OPENAI_MODEL_EMBEDDING
    #
    # response = client.embeddings.create(
    #     model=model,
    #     input=text
    # )
    #
    # return response.data[0].embedding

    # Mock implementation - return fake 1536-dim vector
    # Use simple hash-based mock for consistency
    import hashlib
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)

    # Generate 1536 fake dimensions
    mock_embedding = []
    for i in range(1536):
        # Use hash to generate pseudo-random but consistent values
        val = ((hash_val + i) % 10000) / 10000.0 - 0.5  # Range: -0.5 to 0.5
        mock_embedding.append(val)

    return mock_embedding


def _generate_mock_draft(user_request: str) -> str:
    """
    Generate mock draft text for testing

    Args:
        user_request: User's draft generation request

    Returns:
        Mock draft text with proper structure
    """
    # Parse case info from request if available
    # (In real implementation, this would be in RAG context)

    mock_draft = """
# 준비서면 (이혼 청구)

## 청구취지

1. 원고와 피고는 이혼한다.
2. 피고는 원고에게 위자료로 금 30,000,000원 및 이에 대한 이 사건 소장 부본 송달 다음날부터 다 갚는 날까지 연 12%의 비율로 계산한 돈을 지급한다.
3. 소송비용은 피고가 부담한다.
라는 판결을 구합니다.

## 청구원인

### 1. 당사자의 관계

원고와 피고는 YYYY년 MM월 DD일 혼인신고를 마친 법률상 부부입니다.

### 2. 이혼 사유

피고는 혼인 기간 중 다음과 같은 행위로 원고에게 정신적 고통을 가하였습니다:

- 계속적인 폭언 및 모욕적 언사
- 가정 내 불화 지속
- 배우자로서의 의무 불이행

이러한 행위들은 민법 제840조 제6호에서 정한 "배우자에게 심히 부당한 대우를 하였을 때" 및 "기타 혼인을 계속하기 어려운 중대한 사유가 있을 때"에 해당합니다.

### 3. 위자료 청구

피고의 위와 같은 귀책사유로 인하여 원고는 심각한 정신적 고통을 받았으므로, 피고는 원고에게 위자료를 지급할 의무가 있습니다.

위자료 산정 시 고려사항:
- 혼인 기간
- 피고의 귀책 정도
- 원고가 받은 정신적 고통의 정도
- 당사자들의 재산 및 경제적 상황

이상의 사정을 종합하여 위자료를 금 30,000,000원으로 산정하였습니다.

---

**[주의]** 본 준비서면은 AI가 자동 생성한 초안입니다.
변호사의 검토 및 수정이 필요하며, 자동 제출되지 않습니다.
실제 증거 내용을 반영하여 수정 후 사용하시기 바랍니다.
"""

    return mock_draft.strip()


def count_tokens(text: str) -> int:
    """
    Estimate token count for text

    Args:
        text: Text to count tokens for

    Returns:
        Estimated token count
    """
    # TODO: Replace with tiktoken when OpenAI is configured
    # import tiktoken
    # encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL_CHAT)
    # return len(encoding.encode(text))

    # Mock implementation - rough estimate (1 token ≈ 4 chars)
    return len(text) // 4
