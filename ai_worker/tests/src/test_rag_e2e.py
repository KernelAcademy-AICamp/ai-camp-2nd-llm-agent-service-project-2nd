"""
Test suite for RAG System E2E (End-to-End) Tests
판례 인제스천 → 벡터화 → 검색 전체 파이프라인 테스트

TDD approach: RED-GREEN-REFACTOR
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import date


class TestRAGPipelineE2E:
    """RAG 파이프라인 E2E 테스트"""

    @pytest.fixture
    def sample_precedent_json(self):
        """AI Hub 판례 JSON 샘플 데이터"""
        return [
            {
                "info": {
                    "id": 41055905,
                    "caseNm": "이혼등",
                    "courtNm": "서울가정법원",
                    "judmnAdjuDe": "2001-05-29",
                    "caseNo": "2000드단21348"
                },
                "jdgmn": "유책배우자의 이혼청구를 인용한 사례",
                "Reference_info": {"reference_rules": "민법 제840조"},
                "Class_info": {"class_name": "가사"}
            },
            {
                "info": {
                    "id": 41055906,
                    "caseNm": "재산분할",
                    "courtNm": "대법원",
                    "judmnAdjuDe": "2020-03-15",
                    "caseNo": "2020다12345"
                },
                "jdgmn": "재산분할 청구에 관한 판례",
                "Reference_info": {"reference_rules": "민법 제839조의2"},
                "Class_info": {"class_name": "가사"}
            },
            {
                "info": {
                    "id": 41055907,
                    "caseNm": "이혼",
                    "courtNm": "대법원",
                    "judmnAdjuDe": "2019-07-20",
                    "caseNo": "2019다56789"
                },
                "jdgmn": "부정행위로 인한 이혼 청구 인용",
                "Reference_info": {"reference_rules": "민법 제840조 제1호"},
                "Class_info": {"class_name": "가사"}
            }
        ]

    def test_e2e_parse_ingest_search(self, sample_precedent_json, tmp_path):
        """
        E2E 테스트: JSON 파싱 → 인제스천 → 검색

        Given: AI Hub JSON 판례 데이터 3건
        When: 파싱 → 인제스천 → "이혼" 키워드로 검색
        Then: 관련 판례 2건 이상 반환
        """
        # Import all required modules
        from src.service_rag.legal_parser import CaseLawParser
        from src.service_rag.precedent_ingester import PrecedentIngester
        from src.service_rag.legal_search import LegalSearchEngine

        # Create temp JSON file
        json_file = tmp_path / "test_precedents.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_precedent_json, f, ensure_ascii=False)

        # Track stored vectors for search simulation (shared across mocks)
        stored_vectors = []

        # Mock VectorStore that captures add_evidence and returns in search
        mock_vector_store = MagicMock()

        def mock_add_evidence(text, embedding, metadata):
            chunk_id = f"chunk_{len(stored_vectors)}"
            stored_vectors.append({
                "id": chunk_id,
                "embedding": embedding,
                "metadata": {**metadata, "content": text}  # Store text in metadata for search
            })
            return chunk_id

        mock_vector_store.add_evidence.side_effect = mock_add_evidence

        def mock_search(query_embedding, top_k=5):
            # Return all stored vectors with content containing "이혼" or "부정행위"
            results = []
            for vec in stored_vectors:
                metadata = vec.get("metadata", {})
                content = metadata.get("content", "")
                case_name = metadata.get("case_name", "")
                # 이혼 관련 판례 필터링 시뮬레이션
                if "이혼" in content or "이혼" in case_name or "부정행위" in content:
                    results.append({
                        "id": vec["id"],
                        "distance": 0.1,
                        "metadata": metadata
                    })
            return results[:top_k * 2]  # Return extra for filtering

        mock_vector_store.search.side_effect = mock_search

        # Mock embedding generation (외부 API 의존성)
        with patch('src.service_rag.legal_vectorizer.get_embedding') as mock_embed_vec, \
             patch('src.service_rag.legal_search.get_embedding') as mock_embed_search, \
             patch('src.service_rag.legal_vectorizer.get_vector_store') as mock_vec_store_factory, \
             patch('src.service_rag.legal_search.get_vector_store') as mock_search_store_factory:

            # Setup mock embeddings (768 dimensions)
            mock_embed_vec.return_value = [0.1] * 768
            mock_embed_search.return_value = [0.1] * 768

            # Both vectorizer and search engine use the same mock vector store
            mock_vec_store_factory.return_value = mock_vector_store
            mock_search_store_factory.return_value = mock_vector_store

            # === Phase 1: Ingest precedents ===
            ingester = PrecedentIngester()
            results = ingester.ingest_from_file(str(json_file))

            # Verify ingestion
            assert len(results) == 3
            stats = ingester.get_stats()
            assert stats['successful'] == 3
            assert stats['failed'] == 0

            # Verify vectors were stored
            assert len(stored_vectors) == 3

            # === Phase 2: Search for "이혼" ===
            search_engine = LegalSearchEngine()
            search_results = search_engine.search("이혼", top_k=5)

            # Verify search results - should find 이혼등 and 이혼 cases
            assert len(search_results) >= 2, f"Expected at least 2 divorce-related cases, got {len(search_results)}"

    def test_e2e_search_by_court_filter(self, sample_precedent_json, tmp_path):
        """
        E2E 테스트: 법원별 필터링 검색

        Given: 여러 법원의 판례 데이터
        When: "대법원" 필터로 검색
        Then: 대법원 판례만 반환
        """
        from src.service_rag.legal_parser import CaseLawParser
        from src.service_rag.precedent_ingester import PrecedentIngester
        from src.service_rag.legal_search import LegalSearchEngine

        json_file = tmp_path / "test_precedents.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_precedent_json, f, ensure_ascii=False)

        with patch('src.service_rag.legal_vectorizer.get_embedding') as mock_embed_vec, \
             patch('src.service_rag.legal_search.get_embedding') as mock_embed_search, \
             patch('src.service_rag.legal_vectorizer.get_vector_store') as mock_vector_store_factory, \
             patch('src.service_rag.legal_search.get_vector_store') as mock_search_store_factory:

            mock_embed_vec.return_value = [0.1] * 768
            mock_embed_search.return_value = [0.1] * 768

            mock_vector_store = MagicMock()
            mock_vector_store_factory.return_value = mock_vector_store
            mock_search_store_factory.return_value = mock_vector_store

            stored_vectors = []

            def mock_add(text, embedding, metadata):
                chunk_id = f"chunk_{len(stored_vectors)}"
                stored_vectors.append({
                    "id": chunk_id,
                    "embedding": embedding,
                    "metadata": metadata
                })
                return chunk_id

            mock_vector_store.add_evidence.side_effect = mock_add

            def mock_search(query_embedding, top_k=5):
                # Return all stored vectors for filtering
                results = []
                for vec in stored_vectors:
                    results.append({
                        "id": vec["id"],
                        "distance": 0.1,
                        "metadata": vec.get("metadata", {})
                    })
                return results[:top_k * 2]

            mock_vector_store.search.side_effect = mock_search

            # Ingest
            ingester = PrecedentIngester()
            ingester.ingest_from_file(str(json_file))

            # Search with court filter
            search_engine = LegalSearchEngine()
            results = search_engine.search_cases("이혼", top_k=5, court="대법원")

            # 대법원 판례만 반환되어야 함
            for r in results:
                if r.metadata.get("court"):
                    assert r.metadata["court"] == "대법원"

    def test_e2e_search_by_category_filter(self, sample_precedent_json, tmp_path):
        """
        E2E 테스트: 카테고리별 필터링 검색

        Given: 가사 카테고리 판례 데이터
        When: "가사" 카테고리로 필터링 검색
        Then: 가사 판례만 반환
        """
        from src.service_rag.legal_parser import CaseLawParser
        from src.service_rag.precedent_ingester import PrecedentIngester
        from src.service_rag.legal_search import LegalSearchEngine

        json_file = tmp_path / "test_precedents.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_precedent_json, f, ensure_ascii=False)

        with patch('src.service_rag.legal_vectorizer.get_embedding') as mock_embed_vec, \
             patch('src.service_rag.legal_search.get_embedding') as mock_embed_search, \
             patch('src.service_rag.legal_vectorizer.get_vector_store') as mock_vector_store_factory, \
             patch('src.service_rag.legal_search.get_vector_store') as mock_search_store_factory:

            mock_embed_vec.return_value = [0.1] * 768
            mock_embed_search.return_value = [0.1] * 768

            mock_vector_store = MagicMock()
            mock_vector_store_factory.return_value = mock_vector_store
            mock_search_store_factory.return_value = mock_vector_store

            stored_vectors = []

            def mock_add(text, embedding, metadata):
                chunk_id = f"chunk_{len(stored_vectors)}"
                stored_vectors.append({
                    "id": chunk_id,
                    "embedding": embedding,
                    "metadata": metadata
                })
                return chunk_id

            mock_vector_store.add_evidence.side_effect = mock_add

            def mock_search(query_embedding, top_k=5):
                results = []
                for vec in stored_vectors:
                    results.append({
                        "id": vec["id"],
                        "distance": 0.1,
                        "metadata": vec.get("metadata", {})
                    })
                return results[:top_k * 2]

            mock_vector_store.search.side_effect = mock_search

            # Ingest
            ingester = PrecedentIngester()
            ingester.ingest_from_file(str(json_file))

            # Search with category filter
            search_engine = LegalSearchEngine()
            results = search_engine.search_cases("재산분할", top_k=5, category="가사")

            # 카테고리 필터 적용 검증
            for r in results:
                if r.metadata.get("category"):
                    assert r.metadata["category"] == "가사"

    def test_e2e_parser_to_vectorizer_integration(self, sample_precedent_json):
        """
        E2E 테스트: Parser → Vectorizer 통합

        Given: JSON 판례 데이터
        When: CaseLawParser로 파싱 후 LegalVectorizer로 벡터화
        Then: 올바른 메타데이터로 벡터 저장
        """
        from src.service_rag.legal_parser import CaseLawParser
        from src.service_rag.legal_vectorizer import LegalVectorizer
        from src.service_rag.schemas import CaseLaw

        parser = CaseLawParser()

        with patch('src.service_rag.legal_vectorizer.get_embedding') as mock_embed, \
             patch('src.service_rag.legal_vectorizer.get_vector_store') as mock_vector_store_factory:

            mock_embed.return_value = [0.1] * 768

            mock_vector_store = MagicMock()
            mock_vector_store_factory.return_value = mock_vector_store

            captured_metadata = {}

            def capture_add(text, embedding, metadata):
                chunk_id = f"chunk_{len(captured_metadata)}"
                captured_metadata[chunk_id] = {"text": text, "metadata": metadata}
                return chunk_id

            mock_vector_store.add_evidence.side_effect = capture_add

            vectorizer = LegalVectorizer()

            # Parse and vectorize first case
            case_law = parser.parse_json(sample_precedent_json[0])

            assert isinstance(case_law, CaseLaw)
            assert case_law.case_number == "2000드단21348"
            assert case_law.court == "서울가정법원"

            # Vectorize
            chunk_id = vectorizer.vectorize_case_law(case_law)

            # Verify metadata
            assert chunk_id in captured_metadata
            stored_data = captured_metadata[chunk_id]
            metadata = stored_data["metadata"]
            assert metadata["doc_type"] == "case_law"
            assert metadata["court"] == "서울가정법원"
            assert "유책배우자" in stored_data["text"]

    def test_e2e_real_file_parsing(self):
        """
        E2E 테스트: 실제 article840_samples.json 파일 파싱

        Given: 실제 AI Hub 판례 데이터 파일
        When: 첫 5건만 파싱
        Then: 모두 CaseLaw 객체로 변환 성공
        """
        import os
        from src.service_rag.legal_parser import CaseLawParser
        from src.service_rag.schemas import CaseLaw

        # 실제 데이터 파일 경로
        data_file = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "data", "precedents", "article840_samples.json"
        )

        if not os.path.exists(data_file):
            pytest.skip("article840_samples.json not found")

        parser = CaseLawParser()

        # 파일이 JSON array 또는 개별 JSON objects 형식일 수 있음
        with open(data_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        # JSON array로 감싸서 파싱 시도
        try:
            # 이미 array인 경우
            data = json.loads(content)
        except json.JSONDecodeError:
            # 개별 JSON objects가 콤마로 연결된 경우 array로 감싸기
            try:
                data = json.loads(f"[{content}]")
            except json.JSONDecodeError as e:
                pytest.skip(f"Unable to parse JSON file: {e}")

        # 단일 객체인 경우 리스트로 변환
        if isinstance(data, dict):
            data = [data]

        # 처음 5건만 테스트
        for i, json_case in enumerate(data[:5]):
            try:
                case_law = parser.parse_json(json_case)
                assert isinstance(case_law, CaseLaw)
                assert case_law.case_number != ""
                assert case_law.court != ""
            except Exception as e:
                pytest.fail(f"Failed to parse case {i}: {e}")

    def test_e2e_ingestion_with_progress(self, sample_precedent_json, tmp_path):
        """
        E2E 테스트: 진행 상황 콜백과 함께 인제스천

        Given: 3건의 판례 데이터
        When: progress_callback과 함께 ingest_batch 실행
        Then: 콜백이 3번 호출되고 진행 상황 정확
        """
        from src.service_rag.precedent_ingester import PrecedentIngester

        json_file = tmp_path / "test_precedents.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_precedent_json, f, ensure_ascii=False)

        with patch('src.service_rag.precedent_ingester.LegalVectorizer') as mock_vectorizer_class:
            mock_vectorizer = MagicMock()
            mock_vectorizer.vectorize_case_law.return_value = "chunk_001"
            mock_vectorizer_class.return_value = mock_vectorizer

            progress_log = []

            def progress_callback(current, total, case_info):
                progress_log.append({
                    "current": current,
                    "total": total,
                    "case_number": case_info.get("case_number")
                })

            ingester = PrecedentIngester()
            results = ingester.ingest_batch(
                sample_precedent_json,
                progress_callback=progress_callback
            )

            # 콜백 검증
            assert len(progress_log) == 3
            assert progress_log[0]["current"] == 1
            assert progress_log[0]["total"] == 3
            assert progress_log[1]["current"] == 2
            assert progress_log[2]["current"] == 3

    def test_e2e_error_handling_skip_mode(self, tmp_path):
        """
        E2E 테스트: 오류 데이터 건너뛰기 모드

        Given: 정상 1건 + 오류 1건 데이터
        When: skip_errors=True로 인제스천
        Then: 정상 1건만 성공, 오류 1건은 스킵
        """
        from src.service_rag.precedent_ingester import PrecedentIngester

        mixed_data = [
            {
                "info": {
                    "id": 1,
                    "caseNm": "정상케이스",
                    "courtNm": "대법원",
                    "judmnAdjuDe": "2020-01-01",
                    "caseNo": "2020다1234"
                },
                "jdgmn": "정상 판결"
            },
            {
                "info": {
                    "id": 2,
                    "caseNm": "오류케이스",
                    "courtNm": "대법원",
                    "judmnAdjuDe": "invalid-date",  # 잘못된 날짜
                    "caseNo": "2021다5678"
                },
                "jdgmn": "오류 판결"
            }
        ]

        json_file = tmp_path / "mixed_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(mixed_data, f, ensure_ascii=False)

        with patch('src.service_rag.precedent_ingester.LegalVectorizer') as mock_vectorizer_class:
            mock_vectorizer = MagicMock()
            mock_vectorizer.vectorize_case_law.return_value = "chunk_001"
            mock_vectorizer_class.return_value = mock_vectorizer

            ingester = PrecedentIngester()
            results = ingester.ingest_batch(mixed_data, skip_errors=True)

            # 검증
            assert len(results) == 1
            assert results[0]["case_number"] == "2020다1234"

            stats = ingester.get_stats()
            assert stats["successful"] == 1
            assert stats["failed"] == 1
            assert len(stats["errors"]) == 1
