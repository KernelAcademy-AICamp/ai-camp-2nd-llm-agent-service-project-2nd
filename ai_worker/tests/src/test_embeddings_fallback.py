"""
Embedding Fallback 테스트

Given: OpenAI API 실패 상황
When: get_embedding_with_fallback() 호출
Then: 폴백 임베딩 반환 (데이터 손실 없음)
"""

import pytest
from unittest.mock import patch, MagicMock

from src.utils.embeddings import (
    generate_fallback_embedding,
    get_embedding_with_fallback,
    get_embedding_dimension,
    DEFAULT_DIMENSIONS,
)


class TestGenerateFallbackEmbedding:
    """generate_fallback_embedding 테스트"""

    def test_generates_correct_dimension(self):
        """Given: 텍스트
        When: generate_fallback_embedding() 호출
        Then: 지정된 차원의 벡터 반환"""
        text = "테스트 텍스트"
        embedding = generate_fallback_embedding(text, 1536)

        assert len(embedding) == 1536
        assert all(isinstance(v, float) for v in embedding)

    def test_deterministic_output(self):
        """Given: 동일한 텍스트
        When: 두 번 호출
        Then: 동일한 결과"""
        text = "동일한 텍스트"
        embedding1 = generate_fallback_embedding(text, 1536)
        embedding2 = generate_fallback_embedding(text, 1536)

        assert embedding1 == embedding2

    def test_different_texts_different_embeddings(self):
        """Given: 다른 텍스트들
        When: 각각 호출
        Then: 다른 임베딩"""
        text1 = "첫 번째 텍스트"
        text2 = "두 번째 텍스트"

        embedding1 = generate_fallback_embedding(text1, 1536)
        embedding2 = generate_fallback_embedding(text2, 1536)

        assert embedding1 != embedding2

    def test_empty_text_returns_zero_vector(self):
        """Given: 빈 텍스트
        When: generate_fallback_embedding() 호출
        Then: 제로 벡터 반환"""
        embedding = generate_fallback_embedding("", 1536)

        assert len(embedding) == 1536
        assert all(v == 0.0 for v in embedding)

    def test_values_normalized(self):
        """Given: 임의의 텍스트
        When: generate_fallback_embedding() 호출
        Then: 값들이 [-1, 1] 범위"""
        text = "정규화 테스트"
        embedding = generate_fallback_embedding(text, 1536)

        assert all(-1 <= v <= 1 for v in embedding)


class TestGetEmbeddingWithFallback:
    """get_embedding_with_fallback 테스트"""

    @patch('src.utils.embeddings._get_client')
    def test_returns_real_embedding_on_success(self, mock_get_client):
        """Given: OpenAI API 성공
        When: get_embedding_with_fallback() 호출
        Then: (실제 임베딩, True) 반환"""
        # Mock 설정
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        embedding, is_real = get_embedding_with_fallback("테스트")

        assert is_real is True
        assert len(embedding) == 1536

    @patch('src.utils.embeddings._get_client')
    def test_returns_fallback_on_api_failure(self, mock_get_client):
        """Given: OpenAI API 실패
        When: get_embedding_with_fallback() 호출
        Then: (폴백 임베딩, False) 반환"""
        # API 실패 시뮬레이션
        mock_get_client.side_effect = Exception("API Error")

        embedding, is_real = get_embedding_with_fallback("테스트")

        assert is_real is False
        assert len(embedding) == 1536
        assert all(-1 <= v <= 1 for v in embedding)

    def test_empty_text_returns_zero_vector(self):
        """Given: 빈 텍스트
        When: get_embedding_with_fallback() 호출
        Then: (제로 벡터, False) 반환"""
        embedding, is_real = get_embedding_with_fallback("")

        assert is_real is False
        assert len(embedding) == 1536
        assert all(v == 0.0 for v in embedding)

    def test_never_raises_exception(self):
        """Given: 어떤 상황에서도
        When: get_embedding_with_fallback() 호출
        Then: 예외 발생 안함"""
        # 빈 텍스트
        embedding1, _ = get_embedding_with_fallback("")
        assert len(embedding1) == 1536

        # 공백만
        embedding2, _ = get_embedding_with_fallback("   ")
        assert len(embedding2) == 1536

        # 매우 긴 텍스트
        long_text = "a" * 50000
        embedding3, _ = get_embedding_with_fallback(long_text)
        assert len(embedding3) == 1536


class TestEmbeddingDimension:
    """get_embedding_dimension 테스트"""

    def test_ada_002_dimension(self):
        """Given: ada-002 모델
        When: get_embedding_dimension() 호출
        Then: 1536 반환"""
        assert get_embedding_dimension("text-embedding-ada-002") == 1536

    def test_3_small_dimension(self):
        """Given: 3-small 모델
        When: get_embedding_dimension() 호출
        Then: 1536 반환"""
        assert get_embedding_dimension("text-embedding-3-small") == 1536

    def test_3_large_dimension(self):
        """Given: 3-large 모델
        When: get_embedding_dimension() 호출
        Then: 3072 반환"""
        assert get_embedding_dimension("text-embedding-3-large") == 3072

    def test_unknown_model_returns_default(self):
        """Given: 알 수 없는 모델
        When: get_embedding_dimension() 호출
        Then: 기본값 반환"""
        assert get_embedding_dimension("unknown-model") == DEFAULT_DIMENSIONS


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
