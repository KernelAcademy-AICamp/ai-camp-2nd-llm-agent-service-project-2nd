"""
Test suite for LegalVectorizer
Following TDD approach: RED-GREEN-REFACTOR
"""

import pytest
from unittest.mock import Mock, patch
from src.service_rag.legal_vectorizer import LegalVectorizer
from src.service_rag.schemas import Statute, CaseLaw
from datetime import date


class TestLegalVectorizerInitialization:
    """Test LegalVectorizer initialization"""

    @patch('src.service_rag.legal_vectorizer.VectorStore')
    def test_vectorizer_creation(self, mock_vector_store):
        """LegalVectorizer 생성 테스트"""
        vectorizer = LegalVectorizer()

        assert vectorizer is not None

    @patch('src.service_rag.legal_vectorizer.VectorStore')
    def test_vectorizer_has_vector_store(self, mock_vector_store):
        """VectorStore 초기화 확인"""
        vectorizer = LegalVectorizer()

        assert hasattr(vectorizer, 'vector_store')


class TestStatuteVectorization:
    """Test statute vectorization"""

    @patch('src.service_rag.legal_vectorizer.VectorStore')
    @patch('src.service_rag.legal_vectorizer.get_embedding')
    def test_vectorize_statute(self, mock_embedding, mock_vector_store):
        """법령 벡터화 테스트"""
        # Mock embedding
        mock_embedding.return_value = [0.1] * 768

        vectorizer = LegalVectorizer()
        statute = Statute(
            statute_id="s001",
            name="민법",
            article_number="제840조",
            content="이혼 원인에 관한 조항입니다.",
            category="가족관계법"
        )

        chunk_id = vectorizer.vectorize_statute(statute)

        assert chunk_id is not None
        mock_embedding.assert_called_once()

    @patch('src.service_rag.legal_vectorizer.VectorStore')
    @patch('src.service_rag.legal_vectorizer.get_embedding')
    def test_vectorize_statute_metadata(self, mock_embedding, mock_vector_store):
        """법령 메타데이터 포함 확인"""
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store_instance = Mock()
        mock_vector_store.return_value = mock_vector_store_instance

        vectorizer = LegalVectorizer()
        statute = Statute(
            statute_id="s002",
            name="민법",
            article_number="제840조",
            content="이혼 원인",
            category="가족관계법"
        )

        vectorizer.vectorize_statute(statute)

        # vector_store.add_evidence 호출 확인
        mock_vector_store_instance.add_evidence.assert_called_once()
        call_kwargs = mock_vector_store_instance.add_evidence.call_args[1]

        assert call_kwargs['metadata']['doc_type'] == 'statute'
        assert call_kwargs['metadata']['statute_name'] == '민법'
        assert call_kwargs['metadata']['article_number'] == '제840조'


class TestCaseLawVectorization:
    """Test case law vectorization"""

    @patch('src.service_rag.legal_vectorizer.VectorStore')
    @patch('src.service_rag.legal_vectorizer.get_embedding')
    def test_vectorize_case_law(self, mock_embedding, mock_vector_store):
        """판례 벡터화 테스트"""
        mock_embedding.return_value = [0.1] * 768

        vectorizer = LegalVectorizer()
        case_law = CaseLaw(
            case_id="c001",
            case_number="2019다12345",
            court="대법원",
            decision_date=date(2020, 5, 15),
            case_name="이혼 청구의 소",
            summary="부정행위가 인정되는 경우 이혼 사유에 해당한다.",
            category="가사"
        )

        chunk_id = vectorizer.vectorize_case_law(case_law)

        assert chunk_id is not None
        mock_embedding.assert_called_once()

    @patch('src.service_rag.legal_vectorizer.VectorStore')
    @patch('src.service_rag.legal_vectorizer.get_embedding')
    def test_vectorize_case_metadata(self, mock_embedding, mock_vector_store):
        """판례 메타데이터 포함 확인"""
        mock_embedding.return_value = [0.1] * 768
        mock_vector_store_instance = Mock()
        mock_vector_store.return_value = mock_vector_store_instance

        vectorizer = LegalVectorizer()
        case_law = CaseLaw(
            case_id="c002",
            case_number="2019다12345",
            court="대법원",
            decision_date=date(2020, 5, 15),
            case_name="이혼",
            summary="판결 요지",
            category="가사"
        )

        vectorizer.vectorize_case_law(case_law)

        mock_vector_store_instance.add_evidence.assert_called_once()
        call_kwargs = mock_vector_store_instance.add_evidence.call_args[1]

        assert call_kwargs['metadata']['doc_type'] == 'case_law'
        assert call_kwargs['metadata']['case_number'] == '2019다12345'
        assert call_kwargs['metadata']['court'] == '대법원'


class TestBatchVectorization:
    """Test batch vectorization"""

    @patch('src.service_rag.legal_vectorizer.VectorStore')
    @patch('src.service_rag.legal_vectorizer.get_embedding')
    def test_vectorize_statutes_batch(self, mock_embedding, mock_vector_store):
        """여러 법령 일괄 벡터화 테스트"""
        mock_embedding.return_value = [0.1] * 768

        vectorizer = LegalVectorizer()
        statutes = [
            Statute(statute_id=f"s{i}", name="민법", article_number=f"제{i}조", content=f"조문 {i}", category="민법")
            for i in range(3)
        ]

        chunk_ids = vectorizer.vectorize_statutes_batch(statutes)

        assert len(chunk_ids) == 3
        assert mock_embedding.call_count == 3

    @patch('src.service_rag.legal_vectorizer.VectorStore')
    @patch('src.service_rag.legal_vectorizer.get_embedding')
    def test_vectorize_cases_batch(self, mock_embedding, mock_vector_store):
        """여러 판례 일괄 벡터화 테스트"""
        mock_embedding.return_value = [0.1] * 768

        vectorizer = LegalVectorizer()
        cases = [
            CaseLaw(
                case_id=f"c{i}",
                case_number=f"2019다{i}",
                court="대법원",
                decision_date=date(2020, 1, 1),
                case_name=f"사건{i}",
                summary=f"요지{i}",
                category="가사"
            )
            for i in range(3)
        ]

        chunk_ids = vectorizer.vectorize_cases_batch(cases)

        assert len(chunk_ids) == 3
        assert mock_embedding.call_count == 3


class TestEdgeCases:
    """Test edge cases"""

    @patch('src.service_rag.legal_vectorizer.VectorStore')
    @patch('src.service_rag.legal_vectorizer.get_embedding')
    def test_empty_statute_content(self, mock_embedding, mock_vector_store):
        """빈 법령 내용 처리"""
        mock_embedding.return_value = [0.1] * 768

        vectorizer = LegalVectorizer()
        statute = Statute(
            statute_id="s_empty",
            name="법령",
            article_number="제1조",
            content="",
            category="일반"
        )

        with pytest.raises(ValueError, match="Empty content"):
            vectorizer.vectorize_statute(statute)

    @patch('src.service_rag.legal_vectorizer.VectorStore')
    @patch('src.service_rag.legal_vectorizer.get_embedding')
    def test_empty_case_summary(self, mock_embedding, mock_vector_store):
        """빈 판례 요지 처리"""
        mock_embedding.return_value = [0.1] * 768

        vectorizer = LegalVectorizer()
        case_law = CaseLaw(
            case_id="c_empty",
            case_number="2019다00000",
            court="법원",
            decision_date=date(2020, 1, 1),
            case_name="사건",
            summary="",
            category="가사"
        )

        with pytest.raises(ValueError, match="Empty summary"):
            vectorizer.vectorize_case_law(case_law)
