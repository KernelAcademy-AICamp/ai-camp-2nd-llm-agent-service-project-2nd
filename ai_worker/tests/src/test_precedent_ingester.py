"""
Test suite for PrecedentIngester
AI Hub 판례 데이터 인제스천 테스트

TDD approach: RED-GREEN-REFACTOR
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import date


class TestPrecedentIngester:
    """Test PrecedentIngester functionality"""

    @pytest.fixture
    def sample_json_file_content(self):
        """샘플 JSON 판례 데이터"""
        return [
            {
                "info": {
                    "id": 1,
                    "caseNm": "이혼",
                    "courtNm": "대법원",
                    "judmnAdjuDe": "2020-01-01",
                    "caseNo": "2020다1234"
                },
                "jdgmn": "이혼 사유 인정",
                "Reference_info": {"reference_rules": "민법 제840조"},
                "Class_info": {"class_name": "가사"}
            },
            {
                "info": {
                    "id": 2,
                    "caseNm": "재산분할",
                    "courtNm": "서울가정법원",
                    "judmnAdjuDe": "2021-05-15",
                    "caseNo": "2021드단5678"
                },
                "jdgmn": "재산분할 청구 인용",
                "Reference_info": {"reference_rules": "민법 제839조의2"},
                "Class_info": {"class_name": "가사"}
            }
        ]

    def test_ingester_import(self):
        """PrecedentIngester 임포트 테스트 (RED)"""
        from src.service_rag.precedent_ingester import PrecedentIngester

        assert PrecedentIngester is not None

    @patch('src.service_rag.precedent_ingester.LegalVectorizer')
    def test_ingester_initialization(self, mock_vectorizer):
        """PrecedentIngester 초기화 테스트"""
        from src.service_rag.precedent_ingester import PrecedentIngester

        ingester = PrecedentIngester()

        assert ingester is not None
        assert hasattr(ingester, 'parser')
        assert hasattr(ingester, 'vectorizer')

    @patch('src.service_rag.precedent_ingester.LegalVectorizer')
    def test_ingest_single_case(self, mock_vectorizer_class, sample_json_file_content):
        """단일 판례 인제스천 테스트"""
        # Mock 설정
        mock_vectorizer = MagicMock()
        mock_vectorizer.vectorize_case_law.return_value = "chunk_001"
        mock_vectorizer_class.return_value = mock_vectorizer

        from src.service_rag.precedent_ingester import PrecedentIngester

        ingester = PrecedentIngester()
        result = ingester.ingest_case(sample_json_file_content[0])

        assert result is not None
        assert 'chunk_id' in result
        assert result['chunk_id'] == "chunk_001"
        assert 'case_number' in result
        assert result['case_number'] == "2020다1234"

    @patch('src.service_rag.precedent_ingester.LegalVectorizer')
    def test_ingest_from_json_file(self, mock_vectorizer_class, tmp_path, sample_json_file_content):
        """JSON 파일에서 인제스천 테스트"""
        mock_vectorizer = MagicMock()
        mock_vectorizer.vectorize_case_law.return_value = "chunk_001"
        mock_vectorizer_class.return_value = mock_vectorizer

        # 임시 JSON 파일 생성
        json_file = tmp_path / "precedents.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_json_file_content, f, ensure_ascii=False)

        from src.service_rag.precedent_ingester import PrecedentIngester

        ingester = PrecedentIngester()
        results = ingester.ingest_from_file(str(json_file))

        assert len(results) == 2
        assert all('chunk_id' in r for r in results)

    @patch('src.service_rag.precedent_ingester.LegalVectorizer')
    def test_ingest_batch(self, mock_vectorizer_class, sample_json_file_content):
        """배치 인제스천 테스트"""
        mock_vectorizer = MagicMock()
        mock_vectorizer.vectorize_case_law.return_value = "chunk_001"
        mock_vectorizer_class.return_value = mock_vectorizer

        from src.service_rag.precedent_ingester import PrecedentIngester

        ingester = PrecedentIngester()
        results = ingester.ingest_batch(sample_json_file_content)

        assert len(results) == 2
        assert results[0]['case_number'] == "2020다1234"
        assert results[1]['case_number'] == "2021드단5678"

    @patch('src.service_rag.precedent_ingester.LegalVectorizer')
    def test_ingest_with_progress_callback(self, mock_vectorizer_class, sample_json_file_content):
        """진행 콜백과 함께 인제스천 테스트"""
        mock_vectorizer = MagicMock()
        mock_vectorizer.vectorize_case_law.return_value = "chunk_001"
        mock_vectorizer_class.return_value = mock_vectorizer

        from src.service_rag.precedent_ingester import PrecedentIngester

        progress_calls = []

        def progress_callback(current, total, case_info):
            progress_calls.append((current, total, case_info))

        ingester = PrecedentIngester()
        results = ingester.ingest_batch(
            sample_json_file_content,
            progress_callback=progress_callback
        )

        assert len(progress_calls) == 2
        assert progress_calls[0][0] == 1  # 첫 번째 진행
        assert progress_calls[0][1] == 2  # 전체 개수
        assert progress_calls[1][0] == 2  # 두 번째 진행

    @patch('src.service_rag.precedent_ingester.LegalVectorizer')
    def test_ingest_handles_errors_gracefully(self, mock_vectorizer_class):
        """오류 처리 테스트"""
        mock_vectorizer = MagicMock()
        mock_vectorizer.vectorize_case_law.return_value = "chunk_001"
        mock_vectorizer_class.return_value = mock_vectorizer

        from src.service_rag.precedent_ingester import PrecedentIngester

        # 잘못된 날짜 형식을 포함한 데이터
        bad_data = [
            {
                "info": {
                    "id": 1,
                    "caseNm": "테스트",
                    "courtNm": "대법원",
                    "judmnAdjuDe": "invalid-date",  # 잘못된 형식
                    "caseNo": "2020다1234"
                },
                "jdgmn": "테스트"
            },
            {
                "info": {
                    "id": 2,
                    "caseNm": "정상",
                    "courtNm": "대법원",
                    "judmnAdjuDe": "2021-01-01",  # 정상
                    "caseNo": "2021다5678"
                },
                "jdgmn": "정상 판결"
            }
        ]

        ingester = PrecedentIngester()
        results = ingester.ingest_batch(bad_data, skip_errors=True)

        # 오류가 있어도 정상 데이터는 처리됨
        assert len(results) == 1
        assert results[0]['case_number'] == "2021다5678"

    @patch('src.service_rag.precedent_ingester.LegalVectorizer')
    def test_get_ingestion_stats(self, mock_vectorizer_class, sample_json_file_content):
        """인제스천 통계 테스트"""
        mock_vectorizer = MagicMock()
        mock_vectorizer.vectorize_case_law.return_value = "chunk_001"
        mock_vectorizer_class.return_value = mock_vectorizer

        from src.service_rag.precedent_ingester import PrecedentIngester

        ingester = PrecedentIngester()
        ingester.ingest_batch(sample_json_file_content)

        stats = ingester.get_stats()

        assert 'total_processed' in stats
        assert 'successful' in stats
        assert 'failed' in stats
        assert stats['total_processed'] == 2
        assert stats['successful'] == 2

    def test_ingest_article840_samples(self):
        """실제 article840_samples.json 파일 형식 테스트"""
        # 실제 파일 형식과 동일한 데이터
        article840_sample = {
            "info": {
                "id": 41055905,
                "dataType": "판결문",
                "caseNm": "이혼등",
                "caseTitle": "서울가정법원 2001. 5. 29. 선고 2000드단21348 판결",
                "courtType": "판례(하급심)",
                "courtNm": "서울가정법원",
                "judmnAdjuDe": "2001-05-29",
                "caseNoID": "2000드단21348",
                "caseNo": "2000드단21348"
            },
            "jdgmn": "유책배우자의 이혼청구를 인용한 사례",
            "jdgmnInfo": [
                {
                    "question": "유책배우자의 이혼청구권이 인정될 수 있는가?",
                    "answer": "긍정"
                }
            ],
            "Summary": [
                {
                    "summ_contxt": "상세한 판결 내용...",
                    "summ_pass": "요약된 판결 내용"
                }
            ],
            "keyword_tagg": [{"id": 1, "keyword": "이혼"}],
            "Reference_info": {
                "reference_rules": "민법 제840조",
                "reference_court_case": ""
            },
            "Class_info": {
                "class_name": "가사",
                "instance_name": "이혼"
            }
        }

        # CaseLawParser 직접 사용 (LegalVectorizer 없이)
        from src.service_rag.legal_parser import CaseLawParser

        parser = CaseLawParser()

        # 파싱만 테스트 (벡터화 없이)
        parsed = parser.parse_json(article840_sample)

        assert parsed.case_number == "2000드단21348"
        assert parsed.court == "서울가정법원"
        assert parsed.case_name == "이혼등"
        assert "민법 제840조" in parsed.related_statutes
