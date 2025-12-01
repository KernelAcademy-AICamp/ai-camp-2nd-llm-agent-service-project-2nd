"""
Integration tests for OpenAI API
Requires: OPENAI_API_KEY in .env
"""

import pytest
from app.utils.openai_client import (
    generate_embedding,
    generate_chat_completion
)


class TestOpenAIIntegration:
    """Integration tests for OpenAI operations"""

    @pytest.mark.integration
    def test_generate_embedding_success(self):
        """Test generating embedding vector from text"""
        text = "이것은 테스트 문장입니다. 이혼 소송 증거 분석에 사용됩니다."

        embedding = generate_embedding(text)

        # OpenAI text-embedding-3-small returns 1536 dimensions
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.integration
    def test_generate_embedding_korean_text(self):
        """Test embedding generation with Korean legal text"""
        text = """
        배우자가 폭언을 하며 욕설을 했습니다.
        민법 제840조에 따른 이혼 사유에 해당합니다.
        증거 자료를 첨부합니다.
        """

        embedding = generate_embedding(text)

        assert len(embedding) == 1536

    @pytest.mark.integration
    def test_generate_embedding_short_text(self):
        """Test embedding generation with short text"""
        text = "폭언"

        embedding = generate_embedding(text)

        assert len(embedding) == 1536

    @pytest.mark.integration
    def test_generate_chat_completion_success(self):
        """Test chat completion with simple prompt"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello' in Korean."}
        ]

        response = generate_chat_completion(messages, max_tokens=50)

        assert isinstance(response, str)
        assert len(response) > 0
        # Should contain Korean greeting
        assert any(word in response for word in ["안녕", "하세요", "Hello"])

    @pytest.mark.integration
    def test_generate_chat_completion_legal_context(self):
        """Test chat completion with legal context"""
        messages = [
            {
                "role": "system",
                "content": "당신은 대한민국 법률 전문가입니다. 간단히 답변하세요."
            },
            {
                "role": "user",
                "content": "민법 840조는 무엇에 관한 조항인가요? 한 문장으로 답변하세요."
            }
        ]

        response = generate_chat_completion(messages, max_tokens=100)

        assert isinstance(response, str)
        assert len(response) > 0
        # Response should be meaningful (at least 10 chars for a sentence)

    @pytest.mark.integration
    def test_generate_chat_completion_with_temperature(self):
        """Test chat completion with different temperature settings"""
        messages = [
            {"role": "user", "content": "1+1=?"}
        ]

        # Low temperature for deterministic output
        response = generate_chat_completion(
            messages,
            temperature=0.0,
            max_tokens=10
        )

        assert "2" in response

    @pytest.mark.integration
    def test_embedding_similarity(self):
        """Test that similar texts have similar embeddings"""
        import numpy as np

        text1 = "배우자의 폭언과 욕설"
        text2 = "남편이 고성을 지르며 욕을 했다"
        text3 = "부동산 매매 계약서"

        emb1 = generate_embedding(text1)
        emb2 = generate_embedding(text2)
        emb3 = generate_embedding(text3)

        # Calculate cosine similarity
        def cosine_similarity(a, b):
            a = np.array(a)
            b = np.array(b)
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        sim_12 = cosine_similarity(emb1, emb2)  # Similar topics
        sim_13 = cosine_similarity(emb1, emb3)  # Different topics

        # Similar texts should have higher similarity than unrelated texts
        assert sim_12 > sim_13
