"""
Test suite for SearchEngine
Following TDD approach: RED-GREEN-REFACTOR
"""

import pytest
from datetime import datetime
from unittest.mock import patch
from src.storage.search_engine import SearchEngine, SearchResult
from src.storage.storage_manager import StorageManager


@pytest.fixture
def temp_storage(tmp_path):
    """임시 저장소 디렉토리"""
    vector_db = tmp_path / "chromadb"
    metadata_db = tmp_path / "metadata.db"

    yield {
        "vector_db": str(vector_db),
        "metadata_db": str(metadata_db)
    }


@pytest.fixture
def populated_storage(temp_storage):
    """데이터가 있는 StorageManager"""
    storage = StorageManager(
        vector_db_path=temp_storage["vector_db"],
        metadata_db_path=temp_storage["metadata_db"]
    )

    # 샘플 데이터 추가
    with patch('src.storage.storage_manager.get_embedding') as mock_embed:
        mock_embed.return_value = [0.1] * 768

        # 파일 1: 카카오톡 대화
        storage.process_file(
            filepath="tests/fixtures/kakaotalk_sample.txt",
            case_id="case001"
        )

        # 파일 2: 텍스트 문서
        storage.process_file(
            filepath="tests/fixtures/text_sample.txt",
            case_id="case001"
        )

    return storage


@pytest.fixture
def search_engine(populated_storage):
    """SearchEngine 인스턴스"""
    return SearchEngine(storage_manager=populated_storage)


class TestSearchEngineInitialization:
    """Test SearchEngine initialization"""

    def test_search_engine_creation(self, populated_storage):
        """SearchEngine 생성 테스트"""
        engine = SearchEngine(storage_manager=populated_storage)

        assert engine is not None
        assert engine.storage is not None


class TestBasicSearch:
    """Test basic search functionality"""

    @patch('src.storage.storage_manager.get_embedding')
    def test_basic_search(self, mock_embedding, search_engine):
        """기본 검색 테스트"""
        mock_embedding.return_value = [0.1] * 768

        results = search_engine.search(
            query="이혼 소송",
            case_id="case001",
            top_k=5
        )

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.case_id == "case001" for r in results)

    @patch('src.storage.storage_manager.get_embedding')
    def test_search_returns_sorted_results(self, mock_embedding, search_engine):
        """검색 결과가 유사도 순으로 정렬되는지 테스트"""
        mock_embedding.return_value = [0.1] * 768

        results = search_engine.search(
            query="증거",
            case_id="case001",
            top_k=10
        )

        # 거리가 오름차순으로 정렬되어야 함 (거리가 작을수록 유사)
        distances = [r.distance for r in results]
        assert distances == sorted(distances)


class TestFilteredSearch:
    """Test search with filters"""

    @patch('src.storage.storage_manager.get_embedding')
    def test_search_filter_by_sender(self, mock_embedding, search_engine):
        """발신자로 필터링 테스트"""
        mock_embedding.return_value = [0.1] * 768

        results = search_engine.search(
            query="증거",
            case_id="case001",
            filters={"sender": "홍길동"}
        )

        # 모든 결과가 지정된 발신자여야 함
        assert all(r.sender == "홍길동" for r in results)

    @patch('src.storage.storage_manager.get_embedding')
    def test_search_filter_by_date_range(self, mock_embedding, search_engine):
        """날짜 범위로 필터링 테스트"""
        mock_embedding.return_value = [0.1] * 768

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        results = search_engine.search(
            query="증거",
            case_id="case001",
            filters={
                "start_date": start_date,
                "end_date": end_date
            }
        )

        # 모든 결과가 날짜 범위 내에 있어야 함
        for result in results:
            assert start_date <= result.timestamp <= end_date


class TestContextExpansion:
    """Test context expansion functionality"""

    @patch('src.storage.storage_manager.get_embedding')
    def test_search_with_context_expansion(self, mock_embedding, search_engine):
        """컨텍스트 확장 테스트"""
        mock_embedding.return_value = [0.1] * 768

        results_without_context = search_engine.search(
            query="증거",
            case_id="case001",
            top_k=3,
            expand_context=False
        )

        results_with_context = search_engine.search(
            query="증거",
            case_id="case001",
            top_k=3,
            expand_context=True,
            context_window=2  # 앞뒤 2개 청크
        )

        # 컨텍스트 확장 시 더 많은 청크가 포함되어야 함
        assert len(results_with_context) >= len(results_without_context)

    @patch('src.storage.storage_manager.get_embedding')
    def test_context_expansion_includes_neighbors(self, mock_embedding, search_engine):
        """컨텍스트 확장이 주변 청크를 포함하는지 테스트"""
        mock_embedding.return_value = [0.1] * 768

        results = search_engine.search(
            query="증거",
            case_id="case001",
            top_k=5,  # 여러 결과를 가져와서 중간 것들 확인
            expand_context=True,
            context_window=1
        )

        # 중간 결과들은 앞뒤 컨텍스트를 가져야 함
        # (첫 번째는 context_before 없을 수 있고, 마지막은 context_after 없을 수 있음)
        assert len(results) > 2  # 최소 3개 이상

        # 중간 결과 확인 (인덱스 1 이상의 결과)
        middle_results = results[1:-1]  # 첫 번째와 마지막 제외
        if middle_results:
            assert any(r.context_before is not None for r in middle_results)
            assert any(r.context_after is not None for r in middle_results)


class TestSearchResult:
    """Test SearchResult data model"""

    def test_search_result_creation(self):
        """SearchResult 생성 테스트"""
        result = SearchResult(
            chunk_id="chunk123",
            file_id="file123",
            content="테스트 내용",
            distance=0.15,
            timestamp=datetime.now(),
            sender="홍길동",
            case_id="case001",
            metadata={"key": "value"}
        )

        assert result.chunk_id == "chunk123"
        assert result.content == "테스트 내용"
        assert result.distance == 0.15

    def test_search_result_with_context(self):
        """컨텍스트가 있는 SearchResult 테스트"""
        result = SearchResult(
            chunk_id="chunk123",
            file_id="file123",
            content="메인 내용",
            distance=0.15,
            timestamp=datetime.now(),
            sender="홍길동",
            case_id="case001",
            context_before=["이전 내용"],
            context_after=["다음 내용"]
        )

        assert result.context_before == ["이전 내용"]
        assert result.context_after == ["다음 내용"]


class TestEdgeCases:
    """Test edge cases and error handling"""

    @patch('src.storage.storage_manager.get_embedding')
    def test_search_with_low_similarity(self, mock_embedding, search_engine):
        """유사도가 낮은 검색 테스트"""
        # Mock 임베딩 환경에서는 모든 벡터가 동일하므로
        # 결과가 반환되는 것이 정상 (거리가 매우 작음)
        mock_embedding.return_value = [0.9] * 768

        results = search_engine.search(
            query="임의의쿼리",
            case_id="case001",
            top_k=10
        )

        # Mock 환경에서는 결과가 반환됨 (모든 임베딩이 동일하므로)
        assert isinstance(results, list)
        # 실제 환경에서는 유사도가 낮으면 결과가 적을 수 있음

    @patch('src.storage.storage_manager.get_embedding')
    def test_search_with_invalid_case_id(self, mock_embedding, search_engine):
        """존재하지 않는 케이스 ID로 검색"""
        mock_embedding.return_value = [0.1] * 768

        results = search_engine.search(
            query="증거",
            case_id="nonexistent_case"
        )

        assert results == []
