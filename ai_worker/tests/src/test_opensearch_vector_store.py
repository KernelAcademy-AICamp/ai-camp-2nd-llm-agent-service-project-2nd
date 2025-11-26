"""
OpenSearch Vector Store Tests
Tests for OpenSearchVectorStore class with mocked opensearchpy

TDD Phase: RED -> GREEN -> REFACTOR
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
import uuid


class TestOpenSearchVectorStoreInit:
    """OpenSearchVectorStore 초기화 테스트"""

    @patch("boto3.Session")
    @patch("opensearchpy.OpenSearch")
    def test_init_with_default_values(self, mock_opensearch, mock_boto_session):
        """기본값으로 초기화 테스트"""
        # Given: 모킹된 AWS 인증 및 OpenSearch
        mock_credentials = MagicMock()
        mock_credentials.access_key = "test-access-key"
        mock_credentials.secret_key = "test-secret-key"
        mock_credentials.token = "test-token"
        mock_boto_session.return_value.get_credentials.return_value = mock_credentials

        mock_client = MagicMock()
        mock_client.indices.exists.return_value = True
        mock_opensearch.return_value = mock_client

        # When: OpenSearchVectorStore 초기화
        with patch.dict(
            "os.environ",
            {
                "OPENSEARCH_ENDPOINT": "https://test-endpoint.es.amazonaws.com",
                "AWS_REGION": "ap-northeast-2",
            },
        ):
            from src.storage.opensearch_vector_store import OpenSearchVectorStore

            store = OpenSearchVectorStore()

        # Then: 기본값 사용
        assert store.index_name == "leh_evidence"
        assert store.vector_dimension == 768
        mock_opensearch.assert_called_once()

    @patch("boto3.Session")
    @patch("opensearchpy.OpenSearch")
    def test_init_with_custom_values(self, mock_opensearch, mock_boto_session):
        """커스텀 값으로 초기화 테스트"""
        # Given: 모킹된 AWS 인증
        mock_credentials = MagicMock()
        mock_credentials.access_key = "test-access-key"
        mock_credentials.secret_key = "test-secret-key"
        mock_credentials.token = "test-token"
        mock_boto_session.return_value.get_credentials.return_value = mock_credentials

        mock_client = MagicMock()
        mock_client.indices.exists.return_value = True
        mock_opensearch.return_value = mock_client

        # When: 커스텀 값으로 초기화
        from src.storage.opensearch_vector_store import OpenSearchVectorStore

        store = OpenSearchVectorStore(
            endpoint="https://custom-endpoint.es.amazonaws.com",
            index_name="custom_index",
            region_name="us-west-2",
            vector_dimension=1536,
        )

        # Then: 커스텀 값 사용
        assert store.index_name == "custom_index"
        assert store.vector_dimension == 1536
        assert store.region_name == "us-west-2"

    @patch("boto3.Session")
    @patch("opensearchpy.OpenSearch")
    def test_init_creates_index_if_not_exists(self, mock_opensearch, mock_boto_session):
        """인덱스가 없으면 생성 테스트"""
        # Given: 인덱스가 존재하지 않는 상태
        mock_credentials = MagicMock()
        mock_credentials.access_key = "test-access-key"
        mock_credentials.secret_key = "test-secret-key"
        mock_credentials.token = "test-token"
        mock_boto_session.return_value.get_credentials.return_value = mock_credentials

        mock_client = MagicMock()
        mock_client.indices.exists.return_value = False
        mock_opensearch.return_value = mock_client

        # When: 초기화
        from src.storage.opensearch_vector_store import OpenSearchVectorStore

        with patch.dict(
            "os.environ",
            {"OPENSEARCH_ENDPOINT": "https://test.es.amazonaws.com"},
        ):
            store = OpenSearchVectorStore()

        # Then: 인덱스 생성 호출됨
        mock_client.indices.create.assert_called_once()
        call_args = mock_client.indices.create.call_args
        assert "knn" in str(call_args)


class TestOpenSearchVectorStoreAddEvidence:
    """증거 추가 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 OpenSearchVectorStore 인스턴스"""
        with patch("boto3.Session") as mock_boto_session, patch(
            "opensearchpy.OpenSearch"
        ) as mock_opensearch:
            mock_credentials = MagicMock()
            mock_credentials.access_key = "test-access-key"
            mock_credentials.secret_key = "test-secret-key"
            mock_credentials.token = "test-token"
            mock_boto_session.return_value.get_credentials.return_value = (
                mock_credentials
            )

            mock_client = MagicMock()
            mock_client.indices.exists.return_value = True
            mock_opensearch.return_value = mock_client

            from src.storage.opensearch_vector_store import OpenSearchVectorStore

            with patch.dict(
                "os.environ",
                {"OPENSEARCH_ENDPOINT": "https://test.es.amazonaws.com"},
            ):
                store = OpenSearchVectorStore()
                store._mock_client = mock_client
                yield store

    def test_add_evidence_success(self, mock_store):
        """단일 증거 추가 성공 테스트"""
        # Given: 증거 데이터
        text = "테스트 증거 내용입니다."
        embedding = [0.1] * 768
        metadata = {
            "case_id": "case-001",
            "file_id": "file-123",
            "chunk_id": "chunk-456",
            "sender": "홍길동",
        }

        # When: 증거 추가
        with patch("uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = MagicMock(
                __str__=lambda x: "generated-uuid-123"
            )
            vector_id = mock_store.add_evidence(text, embedding, metadata)

        # Then: index 호출됨
        mock_store._mock_client.index.assert_called_once()
        call_args = mock_store._mock_client.index.call_args
        assert call_args[1]["index"] == "leh_evidence"
        assert call_args[1]["body"]["text"] == text
        assert call_args[1]["body"]["vector"] == embedding
        assert call_args[1]["body"]["case_id"] == "case-001"

    def test_add_evidences_bulk(self, mock_store):
        """여러 증거 일괄 추가 테스트"""
        # Given: 여러 증거 데이터
        texts = ["증거 1", "증거 2", "증거 3"]
        embeddings = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
        metadatas = [
            {"case_id": "case-001", "chunk_id": "chunk-1"},
            {"case_id": "case-001", "chunk_id": "chunk-2"},
            {"case_id": "case-001", "chunk_id": "chunk-3"},
        ]

        # When: 일괄 추가
        vector_ids = mock_store.add_evidences(texts, embeddings, metadatas)

        # Then: bulk 호출됨
        mock_store._mock_client.bulk.assert_called_once()
        assert len(vector_ids) == 3


class TestOpenSearchVectorStoreSearch:
    """검색 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 OpenSearchVectorStore 인스턴스"""
        with patch("boto3.Session") as mock_boto_session, patch(
            "opensearchpy.OpenSearch"
        ) as mock_opensearch:
            mock_credentials = MagicMock()
            mock_credentials.access_key = "test-access-key"
            mock_credentials.secret_key = "test-secret-key"
            mock_credentials.token = "test-token"
            mock_boto_session.return_value.get_credentials.return_value = (
                mock_credentials
            )

            mock_client = MagicMock()
            mock_client.indices.exists.return_value = True
            mock_opensearch.return_value = mock_client

            from src.storage.opensearch_vector_store import OpenSearchVectorStore

            with patch.dict(
                "os.environ",
                {"OPENSEARCH_ENDPOINT": "https://test.es.amazonaws.com"},
            ):
                store = OpenSearchVectorStore()
                store._mock_client = mock_client
                yield store

    def test_search_without_filter(self, mock_store):
        """필터 없이 검색 테스트"""
        # Given: 검색 결과
        mock_store._mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "vec-1",
                        "_score": 0.95,
                        "_source": {
                            "text": "증거 내용 1",
                            "case_id": "case-001",
                            "sender": "홍길동",
                        },
                    },
                    {
                        "_id": "vec-2",
                        "_score": 0.85,
                        "_source": {
                            "text": "증거 내용 2",
                            "case_id": "case-001",
                            "sender": "김철수",
                        },
                    },
                ]
            }
        }

        # When: 검색
        query_embedding = [0.1] * 768
        results = mock_store.search(query_embedding, n_results=10)

        # Then: 결과 반환
        assert len(results) == 2
        assert results[0]["id"] == "vec-1"
        assert results[0]["document"] == "증거 내용 1"
        assert results[0]["distance"] == pytest.approx(0.05, abs=0.01)  # 1 - 0.95

    def test_search_with_filter(self, mock_store):
        """필터로 검색 테스트"""
        # Given: 필터된 검색 결과
        mock_store._mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_id": "vec-1",
                        "_score": 0.90,
                        "_source": {
                            "text": "필터된 증거",
                            "case_id": "case-specific",
                        },
                    }
                ]
            }
        }

        # When: 필터와 함께 검색
        query_embedding = [0.1] * 768
        results = mock_store.search(
            query_embedding, n_results=5, where={"case_id": "case-specific"}
        )

        # Then: 필터가 포함된 쿼리 호출됨
        call_args = mock_store._mock_client.search.call_args
        assert "filter" in str(call_args) or "bool" in str(call_args)
        assert len(results) == 1

    def test_search_empty_results(self, mock_store):
        """검색 결과 없음 테스트"""
        # Given: 빈 검색 결과
        mock_store._mock_client.search.return_value = {"hits": {"hits": []}}

        # When: 검색
        query_embedding = [0.1] * 768
        results = mock_store.search(query_embedding)

        # Then: 빈 리스트 반환
        assert results == []


class TestOpenSearchVectorStoreGetById:
    """ID로 조회 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 OpenSearchVectorStore 인스턴스"""
        with patch("boto3.Session") as mock_boto_session, patch(
            "opensearchpy.OpenSearch"
        ) as mock_opensearch:
            mock_credentials = MagicMock()
            mock_credentials.access_key = "test-access-key"
            mock_credentials.secret_key = "test-secret-key"
            mock_credentials.token = "test-token"
            mock_boto_session.return_value.get_credentials.return_value = (
                mock_credentials
            )

            mock_client = MagicMock()
            mock_client.indices.exists.return_value = True
            mock_opensearch.return_value = mock_client

            from src.storage.opensearch_vector_store import OpenSearchVectorStore

            with patch.dict(
                "os.environ",
                {"OPENSEARCH_ENDPOINT": "https://test.es.amazonaws.com"},
            ):
                store = OpenSearchVectorStore()
                store._mock_client = mock_client
                yield store

    def test_get_by_id_found(self, mock_store):
        """ID로 조회 성공 테스트"""
        # Given: 존재하는 문서
        mock_store._mock_client.get.return_value = {
            "_source": {
                "text": "조회된 증거 내용",
                "case_id": "case-001",
                "sender": "홍길동",
            }
        }

        # When: ID로 조회
        result = mock_store.get_by_id("vec-123")

        # Then: 결과 반환
        assert result is not None
        assert result["id"] == "vec-123"
        assert result["document"] == "조회된 증거 내용"
        assert result["metadata"]["case_id"] == "case-001"

    def test_get_by_id_not_found(self, mock_store):
        """ID로 조회 실패 테스트"""
        # Given: 존재하지 않는 문서 (예외 발생)
        mock_store._mock_client.get.side_effect = Exception("Not found")

        # When: ID로 조회
        result = mock_store.get_by_id("non-existent")

        # Then: None 반환
        assert result is None


class TestOpenSearchVectorStoreDelete:
    """삭제 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 OpenSearchVectorStore 인스턴스"""
        with patch("boto3.Session") as mock_boto_session, patch(
            "opensearchpy.OpenSearch"
        ) as mock_opensearch:
            mock_credentials = MagicMock()
            mock_credentials.access_key = "test-access-key"
            mock_credentials.secret_key = "test-secret-key"
            mock_credentials.token = "test-token"
            mock_boto_session.return_value.get_credentials.return_value = (
                mock_credentials
            )

            mock_client = MagicMock()
            mock_client.indices.exists.return_value = True
            mock_opensearch.return_value = mock_client

            from src.storage.opensearch_vector_store import OpenSearchVectorStore

            with patch.dict(
                "os.environ",
                {"OPENSEARCH_ENDPOINT": "https://test.es.amazonaws.com"},
            ):
                store = OpenSearchVectorStore()
                store._mock_client = mock_client
                yield store

    def test_delete_by_id_success(self, mock_store):
        """ID로 삭제 성공 테스트"""
        # When: 삭제
        mock_store.delete_by_id("vec-123")

        # Then: delete 호출됨
        mock_store._mock_client.delete.assert_called_once_with(
            index="leh_evidence", id="vec-123", refresh=True
        )

    def test_delete_by_id_not_found_no_error(self, mock_store):
        """존재하지 않는 ID 삭제 시 에러 없음 테스트"""
        # Given: 삭제 시 예외 발생
        mock_store._mock_client.delete.side_effect = Exception("Not found")

        # When: 삭제 (에러 없이 통과해야 함)
        mock_store.delete_by_id("non-existent")

        # Then: 예외 발생하지 않음


class TestOpenSearchVectorStoreCount:
    """개수 조회 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 OpenSearchVectorStore 인스턴스"""
        with patch("boto3.Session") as mock_boto_session, patch(
            "opensearchpy.OpenSearch"
        ) as mock_opensearch:
            mock_credentials = MagicMock()
            mock_credentials.access_key = "test-access-key"
            mock_credentials.secret_key = "test-secret-key"
            mock_credentials.token = "test-token"
            mock_boto_session.return_value.get_credentials.return_value = (
                mock_credentials
            )

            mock_client = MagicMock()
            mock_client.indices.exists.return_value = True
            mock_opensearch.return_value = mock_client

            from src.storage.opensearch_vector_store import OpenSearchVectorStore

            with patch.dict(
                "os.environ",
                {"OPENSEARCH_ENDPOINT": "https://test.es.amazonaws.com"},
            ):
                store = OpenSearchVectorStore()
                store._mock_client = mock_client
                yield store

    def test_count_total(self, mock_store):
        """전체 벡터 개수 테스트"""
        # Given: 개수 응답
        mock_store._mock_client.count.return_value = {"count": 100}

        # When: 개수 조회
        count = mock_store.count()

        # Then: 개수 반환
        assert count == 100

    def test_count_by_case(self, mock_store):
        """케이스별 벡터 개수 테스트"""
        # Given: 케이스별 개수 응답
        mock_store._mock_client.count.return_value = {"count": 25}

        # When: 케이스별 개수 조회
        count = mock_store.count_by_case("case-001")

        # Then: 개수 반환
        assert count == 25
        call_args = mock_store._mock_client.count.call_args
        assert "case_id" in str(call_args)


class TestOpenSearchVectorStoreClear:
    """전체 삭제 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 OpenSearchVectorStore 인스턴스"""
        with patch("boto3.Session") as mock_boto_session, patch(
            "opensearchpy.OpenSearch"
        ) as mock_opensearch:
            mock_credentials = MagicMock()
            mock_credentials.access_key = "test-access-key"
            mock_credentials.secret_key = "test-secret-key"
            mock_credentials.token = "test-token"
            mock_boto_session.return_value.get_credentials.return_value = (
                mock_credentials
            )

            mock_client = MagicMock()
            mock_client.indices.exists.return_value = True
            mock_opensearch.return_value = mock_client

            from src.storage.opensearch_vector_store import OpenSearchVectorStore

            with patch.dict(
                "os.environ",
                {"OPENSEARCH_ENDPOINT": "https://test.es.amazonaws.com"},
            ):
                store = OpenSearchVectorStore()
                store._mock_client = mock_client
                yield store

    def test_clear_all(self, mock_store):
        """전체 삭제 테스트"""
        # When: 전체 삭제
        mock_store.clear()

        # Then: delete_by_query 호출됨
        mock_store._mock_client.delete_by_query.assert_called_once()
        call_args = mock_store._mock_client.delete_by_query.call_args
        assert "match_all" in str(call_args)


class TestOpenSearchVectorStoreCaseIsolation:
    """케이스 격리 테스트"""

    @pytest.fixture
    def mock_store(self):
        """모킹된 OpenSearchVectorStore 인스턴스"""
        with patch("boto3.Session") as mock_boto_session, patch(
            "opensearchpy.OpenSearch"
        ) as mock_opensearch:
            mock_credentials = MagicMock()
            mock_credentials.access_key = "test-access-key"
            mock_credentials.secret_key = "test-secret-key"
            mock_credentials.token = "test-token"
            mock_boto_session.return_value.get_credentials.return_value = (
                mock_credentials
            )

            mock_client = MagicMock()
            mock_client.indices.exists.return_value = True
            mock_opensearch.return_value = mock_client

            from src.storage.opensearch_vector_store import OpenSearchVectorStore

            with patch.dict(
                "os.environ",
                {"OPENSEARCH_ENDPOINT": "https://test.es.amazonaws.com"},
            ):
                store = OpenSearchVectorStore()
                store._mock_client = mock_client
                yield store

    def test_delete_by_case(self, mock_store):
        """케이스별 삭제 테스트"""
        # Given: 케이스에 벡터가 존재
        mock_store._mock_client.count.return_value = {"count": 10}

        # When: 케이스별 삭제
        deleted_count = mock_store.delete_by_case("case-001")

        # Then: delete_by_query 호출됨
        assert deleted_count == 10
        mock_store._mock_client.delete_by_query.assert_called_once()

    def test_delete_by_case_empty(self, mock_store):
        """케이스에 벡터가 없을 때 삭제 테스트"""
        # Given: 케이스에 벡터가 없음
        mock_store._mock_client.count.return_value = {"count": 0}

        # When: 케이스별 삭제
        deleted_count = mock_store.delete_by_case("case-empty")

        # Then: delete_by_query 호출되지 않음
        assert deleted_count == 0
        mock_store._mock_client.delete_by_query.assert_not_called()

    def test_verify_case_isolation_isolated(self, mock_store):
        """케이스 격리 검증 - 격리됨 테스트"""
        # Given: 동일 케이스의 벡터만 있음
        mock_store._mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"case_id": "case-001"}},
                    {"_source": {"case_id": "case-001"}},
                ]
            }
        }

        # When: 격리 검증
        is_isolated = mock_store.verify_case_isolation("case-001")

        # Then: True 반환
        assert is_isolated is True

    def test_verify_case_isolation_not_isolated(self, mock_store):
        """케이스 격리 검증 - 격리 안됨 테스트"""
        # Given: 다른 케이스의 벡터가 섞여 있음
        mock_store._mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"case_id": "case-001"}},
                    {"_source": {"case_id": "case-002"}},  # 다른 케이스!
                ]
            }
        }

        # When: 격리 검증
        is_isolated = mock_store.verify_case_isolation("case-001")

        # Then: False 반환
        assert is_isolated is False

    def test_verify_case_isolation_empty(self, mock_store):
        """케이스 격리 검증 - 빈 케이스 테스트"""
        # Given: 케이스에 벡터가 없음
        mock_store._mock_client.search.return_value = {"hits": {"hits": []}}

        # When: 격리 검증
        is_isolated = mock_store.verify_case_isolation("case-empty")

        # Then: True 반환 (빈 케이스는 격리된 것으로 간주)
        assert is_isolated is True
