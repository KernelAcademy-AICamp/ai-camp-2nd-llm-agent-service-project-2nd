"""
Qdrant Vector Store Module
Handles Qdrant operations for vector embeddings (Cloud/Local)
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
from typing import List, Dict, Optional, Any
import uuid


class QdrantVectorStore:
    """
    Qdrant 벡터 저장소 래퍼

    메모리 모드 또는 서버 모드로 Qdrant를 사용하여
    증거 벡터 임베딩을 저장하고 검색합니다.
    """

    def __init__(
        self,
        mode: str = "memory",
        url: str = None,
        api_key: str = None,
        collection_name: str = "leh_evidence",
        vector_size: int = 1536
    ):
        """
        QdrantVectorStore 초기화

        Args:
            mode: "memory" (인메모리) 또는 "server" (원격 서버)
            url: Qdrant 서버 URL (mode="server"일 때 필요)
            api_key: Qdrant API 키 (Cloud 사용 시)
            collection_name: 컬렉션 이름
            vector_size: 벡터 차원 (OpenAI: 1536)
        """
        self.mode = mode
        self.collection_name = collection_name
        self.vector_size = vector_size

        # 클라이언트 초기화
        if mode == "memory":
            self.client = QdrantClient(":memory:")
        else:
            self.client = QdrantClient(url=url, api_key=api_key)

        # 컬렉션 생성 (없으면)
        self._ensure_collection()

    def _ensure_collection(self):
        """컬렉션이 없으면 생성"""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )

    def add_evidence(
        self,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> str:
        """단일 증거 추가"""
        vector_id = str(uuid.uuid4())
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=vector_id,
                    vector=embedding,
                    payload={"document": text, **metadata}
                )
            ]
        )
        
        return vector_id

    def add_evidences(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> List[str]:
        """여러 증거 일괄 추가"""
        vector_ids = [str(uuid.uuid4()) for _ in texts]
        
        points = [
            PointStruct(
                id=vid,
                vector=emb,
                payload={"document": txt, **meta}
            )
            for vid, txt, emb, meta in zip(vector_ids, texts, embeddings, metadatas)
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return vector_ids

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """벡터 유사도 검색"""
        query_filter = None
        if where:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in where.items()
            ]
            query_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=n_results,
            query_filter=query_filter
        )

        return [
            {
                "id": str(r.id),
                "score": r.score,
                "metadata": {k: v for k, v in r.payload.items() if k != "document"},
                "document": r.payload.get("document", "")
            }
            for r in results
        ]

    def get_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """ID로 벡터 조회"""
        results = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[vector_id]
        )
        
        if results:
            r = results[0]
            return {
                "id": str(r.id),
                "metadata": {k: v for k, v in r.payload.items() if k != "document"},
                "document": r.payload.get("document", "")
            }
        return None

    def delete_by_id(self, vector_id: str) -> None:
        """ID로 벡터 삭제"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[vector_id]
        )

    def count(self) -> int:
        """컬렉션 내 벡터 개수 반환"""
        info = self.client.get_collection(self.collection_name)
        return info.points_count

    def clear(self) -> None:
        """컬렉션 전체 삭제 후 재생성"""
        self.client.delete_collection(self.collection_name)
        self._ensure_collection()

    # ========== Case Isolation Methods ==========

    def count_by_case(self, case_id: str) -> int:
        """케이스별 벡터 개수 반환"""
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="case_id", match=MatchValue(value=case_id))]
            ),
            limit=10000
        )
        return len(results[0])

    def delete_by_case(self, case_id: str) -> int:
        """케이스별 벡터 삭제"""
        # 먼저 개수 확인
        count = self.count_by_case(case_id)
        
        if count > 0:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="case_id", match=MatchValue(value=case_id))]
                )
            )
        
        return count

    def verify_case_isolation(self, case_id: str) -> bool:
        """케이스 격리 검증"""
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="case_id", match=MatchValue(value=case_id))]
            ),
            limit=10000
        )
        
        if not results[0]:
            return True
        
        for point in results[0]:
            if point.payload.get("case_id") != case_id:
                return False
        
        return True