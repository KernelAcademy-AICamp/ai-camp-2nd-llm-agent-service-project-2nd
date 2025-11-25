"""
OpenSearch Vector Store Module
Production-ready vector storage using AWS OpenSearch
"""

import os
import uuid
from typing import List, Dict, Optional, Any
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3


class OpenSearchVectorStore:
    """
    OpenSearch 벡터 저장소

    AWS OpenSearch를 사용하여 증거 벡터 임베딩을 저장하고 검색합니다.
    VectorStore와 동일한 인터페이스를 제공합니다.
    """

    def __init__(
        self,
        endpoint: str = None,
        index_name: str = "leh_evidence",
        region_name: str = None,
        vector_dimension: int = 768
    ):
        """
        OpenSearchVectorStore 초기화

        Args:
            endpoint: OpenSearch 엔드포인트 URL
            index_name: 인덱스 이름
            region_name: AWS 리전
            vector_dimension: 벡터 차원 (기본: 768)
        """
        self.endpoint = endpoint or os.getenv("OPENSEARCH_ENDPOINT")
        self.index_name = index_name
        self.region_name = region_name or os.getenv("AWS_REGION", "ap-northeast-2")
        self.vector_dimension = vector_dimension

        # 엔드포인트에서 호스트 추출
        host = self.endpoint.replace("https://", "").replace("http://", "")
        if "/" in host:
            host = host.split("/")[0]

        # AWS 인증 (IAM 기반)
        credentials = boto3.Session().get_credentials()
        self.awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.region_name,
            "es",
            session_token=credentials.token
        )

        # OpenSearch 클라이언트 생성
        self.client = OpenSearch(
            hosts=[{"host": host, "port": 443}],
            http_auth=self.awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )

        # 인덱스 생성 (없으면)
        self._ensure_index()

    def _ensure_index(self) -> None:
        """인덱스 존재 확인 및 생성"""
        if not self.client.indices.exists(index=self.index_name):
            index_body = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100
                    }
                },
                "mappings": {
                    "properties": {
                        "vector": {
                            "type": "knn_vector",
                            "dimension": self.vector_dimension,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                                "parameters": {
                                    "ef_construction": 128,
                                    "m": 24
                                }
                            }
                        },
                        "text": {"type": "text"},
                        "case_id": {"type": "keyword"},
                        "file_id": {"type": "keyword"},
                        "chunk_id": {"type": "keyword"},
                        "sender": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "chunk_index": {"type": "integer"}
                    }
                }
            }

            self.client.indices.create(index=self.index_name, body=index_body)

    def add_evidence(
        self,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> str:
        """
        단일 증거 추가

        Args:
            text: 증거 텍스트
            embedding: 벡터 임베딩
            metadata: 메타데이터

        Returns:
            str: 생성된 벡터 ID
        """
        vector_id = str(uuid.uuid4())

        document = {
            "vector": embedding,
            "text": text,
            **metadata
        }

        self.client.index(
            index=self.index_name,
            id=vector_id,
            body=document,
            refresh=True
        )

        return vector_id

    def add_evidences(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> List[str]:
        """
        여러 증거 일괄 추가

        Args:
            texts: 증거 텍스트 리스트
            embeddings: 벡터 임베딩 리스트
            metadatas: 메타데이터 리스트

        Returns:
            List[str]: 생성된 벡터 ID 리스트
        """
        vector_ids = []
        bulk_body = []

        for text, embedding, metadata in zip(texts, embeddings, metadatas):
            vector_id = str(uuid.uuid4())
            vector_ids.append(vector_id)

            # 인덱스 액션
            bulk_body.append({
                "index": {
                    "_index": self.index_name,
                    "_id": vector_id
                }
            })

            # 문서 데이터
            bulk_body.append({
                "vector": embedding,
                "text": text,
                **metadata
            })

        if bulk_body:
            self.client.bulk(body=bulk_body, refresh=True)

        return vector_ids

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        벡터 유사도 검색

        Args:
            query_embedding: 쿼리 임베딩
            n_results: 반환할 결과 개수
            where: 메타데이터 필터 (선택)

        Returns:
            List[Dict]: 검색 결과
        """
        # KNN 쿼리 구성
        knn_query = {
            "knn": {
                "vector": {
                    "vector": query_embedding,
                    "k": n_results
                }
            }
        }

        # 필터 적용
        if where:
            filter_clauses = []
            for key, value in where.items():
                filter_clauses.append({"term": {key: value}})

            query = {
                "bool": {
                    "must": [knn_query],
                    "filter": filter_clauses
                }
            }
        else:
            query = knn_query

        response = self.client.search(
            index=self.index_name,
            body={
                "size": n_results,
                "query": query,
                "_source": {"excludes": ["vector"]}  # 벡터는 결과에서 제외
            }
        )

        # 결과 변환
        formatted_results = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            formatted_results.append({
                "id": hit.get("_id"),
                "distance": 1 - hit.get("_score", 0),  # cosine similarity to distance
                "metadata": {k: v for k, v in source.items() if k != "text"},
                "document": source.get("text", "")
            })

        return formatted_results

    def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 벡터 조회

        Args:
            vector_id: 벡터 ID

        Returns:
            Dict: 벡터 정보 (metadata, document)
        """
        try:
            response = self.client.get(
                index=self.index_name,
                id=vector_id,
                _source_excludes=["vector"]
            )

            source = response.get("_source", {})
            return {
                "id": vector_id,
                "metadata": {k: v for k, v in source.items() if k != "text"},
                "document": source.get("text", "")
            }
        except Exception:
            return None

    def delete_by_id(self, vector_id: str) -> None:
        """
        ID로 벡터 삭제

        Args:
            vector_id: 삭제할 벡터 ID
        """
        try:
            self.client.delete(
                index=self.index_name,
                id=vector_id,
                refresh=True
            )
        except Exception:
            pass  # 이미 삭제되었거나 존재하지 않음

    def count(self) -> int:
        """
        인덱스 내 벡터 개수 반환

        Returns:
            int: 벡터 개수
        """
        response = self.client.count(index=self.index_name)
        return response.get("count", 0)

    def clear(self) -> None:
        """인덱스 전체 삭제 (모든 벡터 제거)"""
        self.client.delete_by_query(
            index=self.index_name,
            body={"query": {"match_all": {}}},
            refresh=True
        )

    # ========== Case Isolation Methods ==========

    def count_by_case(self, case_id: str) -> int:
        """
        케이스별 벡터 개수 반환

        Args:
            case_id: 케이스 ID

        Returns:
            int: 해당 케이스의 벡터 개수
        """
        response = self.client.count(
            index=self.index_name,
            body={"query": {"term": {"case_id": case_id}}}
        )
        return response.get("count", 0)

    def delete_by_case(self, case_id: str) -> int:
        """
        케이스별 벡터 삭제

        Args:
            case_id: 삭제할 케이스 ID

        Returns:
            int: 삭제된 벡터 개수
        """
        # 삭제 전 개수 확인
        count = self.count_by_case(case_id)

        if count > 0:
            self.client.delete_by_query(
                index=self.index_name,
                body={"query": {"term": {"case_id": case_id}}},
                refresh=True
            )

        return count

    def verify_case_isolation(self, case_id: str) -> bool:
        """
        케이스 격리 검증

        Args:
            case_id: 검증할 케이스 ID

        Returns:
            bool: 격리되어 있으면 True
        """
        response = self.client.search(
            index=self.index_name,
            body={
                "size": 100,
                "query": {"term": {"case_id": case_id}},
                "_source": ["case_id"]
            }
        )

        hits = response.get("hits", {}).get("hits", [])
        if not hits:
            return True

        for hit in hits:
            if hit.get("_source", {}).get("case_id") != case_id:
                return False

        return True
