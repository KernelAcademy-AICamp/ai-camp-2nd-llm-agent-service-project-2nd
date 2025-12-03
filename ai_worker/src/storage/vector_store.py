"""
Vector Store Module - Qdrant Implementation
Handles vector embeddings storage for AWS Lambda environment

Architecture:
- Vector embeddings + metadata → Qdrant Cloud
- Collection: leh_evidence (single collection with case_id filter)
- Alternative: leh_{case_id} per-case collections
"""

import os
import logging
from typing import List, Dict, Optional, Any
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    Range,
    SparseVectorParams,
    SparseVector,
    Modifier,
)

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Qdrant 벡터 저장소 래퍼

    Qdrant Cloud를 사용하여 증거 벡터 임베딩을 저장하고 검색합니다.
    Lambda 환경에서 영구 저장을 위해 ChromaDB 대신 Qdrant Cloud 사용.

    Collection Strategy:
    - Default: Single collection 'leh_evidence' with case_id filter
    - Per-case: Use get_or_create_case_collection() for leh_{case_id}
    """

    def __init__(
        self,
        url: str = None,
        api_key: str = None,
        collection_name: str = "leh_evidence",
        vector_size: int = None,
        persist_directory: str = None  # Deprecated: kept for backwards compatibility
    ):
        """
        VectorStore 초기화

        Args:
            url: Qdrant Cloud URL (기본값: 환경변수 QDRANT_URL)
            api_key: Qdrant API Key (기본값: 환경변수 QDRANT_API_KEY)
            collection_name: 기본 컬렉션명
            vector_size: 벡터 차원 (기본값: 환경변수 VECTOR_SIZE 또는 1536)
            persist_directory: Deprecated - ignored (was used for ChromaDB)
        """
        # Note: persist_directory is ignored - Qdrant Cloud handles persistence
        if persist_directory:
            logger.warning(
                "persist_directory is deprecated and ignored. "
                "VectorStore now uses Qdrant Cloud."
            )
        self.persist_directory = persist_directory  # Keep for test compatibility

        self.url = url or os.environ.get('QDRANT_URL')
        self.api_key = api_key or os.environ.get('QDRANT_API_KEY')
        self.collection_name = collection_name
        self.vector_size = vector_size or int(os.environ.get('VECTOR_SIZE', '1536'))

        if not self.url:
            raise ValueError("QDRANT_URL is required")

        self._client = None
        self._initialized_collections = set()

    @property
    def client(self) -> QdrantClient:
        """Lazy initialization of Qdrant client"""
        if self._client is None:
            self._client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=30
            )
        return self._client

    def _ensure_collection(self, collection_name: str = None) -> str:
        """
        컬렉션 존재 확인 및 생성

        Args:
            collection_name: 컬렉션명 (None이면 기본 컬렉션)

        Returns:
            str: 사용할 컬렉션명
        """
        name = collection_name or self.collection_name

        if name in self._initialized_collections:
            return name

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {name}")

                # Create payload indexes for filtering
                self._create_payload_indexes(name)

            self._initialized_collections.add(name)
            return name

        except Exception as e:
            logger.error(f"Failed to ensure collection {name}: {e}")
            raise

    def _create_payload_indexes(self, collection_name: str) -> None:
        """
        필터링용 payload 인덱스 생성

        Args:
            collection_name: 컬렉션명
        """
        # Index fields commonly used for filtering
        index_fields = ["case_id", "file_id", "chunk_id", "sender"]

        for field in index_fields:
            try:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                logger.info(f"Created index for {field} in {collection_name}")
            except Exception as e:
                # Index might already exist
                logger.debug(f"Index creation skipped for {field}: {e}")

    def get_or_create_case_collection(self, case_id: str) -> str:
        """
        케이스별 컬렉션 생성/조회

        Args:
            case_id: 케이스 ID

        Returns:
            str: 컬렉션명 (leh_{case_id})
        """
        collection_name = f"leh_{case_id}"
        return self._ensure_collection(collection_name)

    # ========== Core Operations ==========

    def add_evidence(
        self,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        collection_name: str = None
    ) -> str:
        """
        단일 증거 추가

        Args:
            text: 증거 텍스트
            embedding: 벡터 임베딩
            metadata: 메타데이터 (chunk_id, file_id, case_id 등)
            collection_name: 컬렉션명 (선택)

        Returns:
            str: 생성된 벡터 ID
        """
        collection = self._ensure_collection(collection_name)
        vector_id = str(uuid.uuid4())

        # Metadata에 text 포함 (document 역할)
        payload = {**metadata, "document": text}

        try:
            self.client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=vector_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            return vector_id

        except Exception as e:
            logger.error(f"Failed to add evidence: {e}")
            raise

    def add_evidences(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        collection_name: str = None
    ) -> List[str]:
        """
        여러 증거 일괄 추가

        Args:
            texts: 증거 텍스트 리스트
            embeddings: 벡터 임베딩 리스트
            metadatas: 메타데이터 리스트
            collection_name: 컬렉션명 (선택)

        Returns:
            List[str]: 생성된 벡터 ID 리스트
        """
        collection = self._ensure_collection(collection_name)
        vector_ids = [str(uuid.uuid4()) for _ in texts]

        points = []
        for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
            payload = {**metadata, "document": text}
            points.append(
                PointStruct(
                    id=vector_ids[i],
                    vector=embedding,
                    payload=payload
                )
            )

        try:
            # Batch upsert (Qdrant handles batching internally)
            self.client.upsert(
                collection_name=collection,
                points=points
            )
            return vector_ids

        except Exception as e:
            logger.error(f"Failed to add evidences: {e}")
            raise

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        collection_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        벡터 유사도 검색

        Args:
            query_embedding: 쿼리 임베딩
            n_results: 반환할 결과 개수
            where: 메타데이터 필터 (예: {"case_id": "xxx"})
            collection_name: 컬렉션명 (선택)

        Returns:
            List[Dict]: 검색 결과
                - distance: 유사도 거리 (score)
                - metadata: 메타데이터
                - document: 원본 텍스트
                - id: 벡터 ID
        """
        collection = self._ensure_collection(collection_name)

        # Build filter
        query_filter = None
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            query_filter = Filter(must=conditions)

        try:
            results = self.client.search(
                collection_name=collection,
                query_vector=query_embedding,
                limit=n_results,
                query_filter=query_filter,
                with_payload=True
            )

            formatted_results = []
            for hit in results:
                payload = hit.payload or {}
                document = payload.pop("document", "")
                formatted_results.append({
                    "id": str(hit.id),
                    "distance": 1 - hit.score,  # Convert similarity to distance
                    "metadata": payload,
                    "document": document
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def get_by_id(
        self,
        vector_id: str,
        collection_name: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        ID로 벡터 조회

        Args:
            vector_id: 벡터 ID
            collection_name: 컬렉션명 (선택)

        Returns:
            Dict: 벡터 정보 (metadata, document)
        """
        collection = self._ensure_collection(collection_name)

        try:
            results = self.client.retrieve(
                collection_name=collection,
                ids=[vector_id],
                with_payload=True
            )

            if results:
                payload = results[0].payload or {}
                document = payload.pop("document", "")
                return {
                    "id": str(results[0].id),
                    "metadata": payload,
                    "document": document
                }

            return None

        except Exception as e:
            logger.error(f"Get by ID failed: {e}")
            return None

    def delete_by_id(
        self,
        vector_id: str,
        collection_name: str = None
    ) -> None:
        """
        ID로 벡터 삭제

        Args:
            vector_id: 삭제할 벡터 ID
            collection_name: 컬렉션명 (선택)
        """
        collection = self._ensure_collection(collection_name)

        try:
            self.client.delete(
                collection_name=collection,
                points_selector=models.PointIdsList(
                    points=[vector_id]
                )
            )

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise

    def count(self, collection_name: str = None) -> int:
        """
        컬렉션 내 벡터 개수 반환

        Args:
            collection_name: 컬렉션명 (선택)

        Returns:
            int: 벡터 개수
        """
        collection = self._ensure_collection(collection_name)

        try:
            info = self.client.get_collection(collection_name=collection)
            return info.points_count

        except Exception as e:
            logger.error(f"Count failed: {e}")
            return 0

    def clear(self, collection_name: str = None) -> None:
        """
        컬렉션 전체 삭제 (모든 벡터 제거)

        Args:
            collection_name: 컬렉션명 (선택)
        """
        collection = self._ensure_collection(collection_name)

        try:
            # Delete and recreate collection
            self.client.delete_collection(collection_name=collection)
            self._initialized_collections.discard(collection)
            self._ensure_collection(collection)

        except Exception as e:
            logger.error(f"Clear failed: {e}")
            raise

    # ========== Case Isolation Methods ==========

    def count_by_case(
        self,
        case_id: str,
        collection_name: str = None
    ) -> int:
        """
        케이스별 벡터 개수 반환

        Args:
            case_id: 케이스 ID
            collection_name: 컬렉션명 (선택)

        Returns:
            int: 해당 케이스의 벡터 개수
        """
        collection = self._ensure_collection(collection_name)

        try:
            result = self.client.count(
                collection_name=collection,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="case_id",
                            match=MatchValue(value=case_id)
                        )
                    ]
                )
            )
            return result.count

        except Exception as e:
            logger.error(f"Count by case failed: {e}")
            return 0

    def delete_by_case(
        self,
        case_id: str,
        collection_name: str = None
    ) -> int:
        """
        케이스별 벡터 삭제

        Args:
            case_id: 삭제할 케이스 ID
            collection_name: 컬렉션명 (선택)

        Returns:
            int: 삭제된 벡터 개수
        """
        collection = self._ensure_collection(collection_name)

        try:
            # Count before delete
            count = self.count_by_case(case_id, collection)

            if count > 0:
                self.client.delete(
                    collection_name=collection,
                    points_selector=models.FilterSelector(
                        filter=Filter(
                            must=[
                                FieldCondition(
                                    key="case_id",
                                    match=MatchValue(value=case_id)
                                )
                            ]
                        )
                    )
                )

            return count

        except Exception as e:
            logger.error(f"Delete by case failed: {e}")
            return 0

    def delete_case_collection(self, case_id: str) -> bool:
        """
        케이스 전용 컬렉션 삭제

        Args:
            case_id: 케이스 ID

        Returns:
            bool: 삭제 성공 여부
        """
        collection_name = f"leh_{case_id}"

        try:
            self.client.delete_collection(collection_name=collection_name)
            self._initialized_collections.discard(collection_name)
            return True

        except Exception as e:
            logger.warning(f"Delete case collection failed: {e}")
            return False

    def verify_case_isolation(
        self,
        case_id: str,
        collection_name: str = None
    ) -> bool:
        """
        케이스 격리 검증

        Args:
            case_id: 검증할 케이스 ID
            collection_name: 컬렉션명 (선택)

        Returns:
            bool: 격리되어 있으면 True
        """
        collection = self._ensure_collection(collection_name)

        try:
            # Get all points for this case
            results, _ = self.client.scroll(
                collection_name=collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="case_id",
                            match=MatchValue(value=case_id)
                        )
                    ]
                ),
                limit=100,
                with_payload=True
            )

            if not results:
                return True

            # Verify all results have matching case_id
            for point in results:
                if point.payload and point.payload.get("case_id") != case_id:
                    return False

            return True

        except Exception as e:
            logger.error(f"Verify case isolation failed: {e}")
            return False

    # ========== Hybrid Search (with chunk metadata) ==========

    def add_chunk_with_metadata(
        self,
        chunk_id: str,
        file_id: str,
        case_id: str,
        content: str,
        embedding: List[float],
        timestamp: str,
        sender: str,
        score: float = None,
        collection_name: str = None,
        # Extended metadata fields
        file_name: str = None,
        file_type: str = None,
        legal_categories: List[str] = None,
        confidence_level: int = None,
        line_number: int = None,
        line_number_end: int = None,
        page_number: int = None,
        segment_start_sec: float = None,
        segment_end_sec: float = None,
        is_fallback_embedding: bool = False
    ) -> str:
        """
        청크 메타데이터와 함께 벡터 저장

        이 메서드는 MetadataStore의 chunk 저장을 대체합니다.
        벡터와 메타데이터를 Qdrant payload에 함께 저장합니다.

        Args:
            chunk_id: 청크 ID
            file_id: 파일 ID
            case_id: 케이스 ID
            content: 청크 내용
            embedding: 벡터 임베딩
            timestamp: 타임스탬프 (ISO format)
            sender: 발신자
            score: 증거 점수 (선택)
            collection_name: 컬렉션명 (선택)
            file_name: 원본 파일명 (선택)
            file_type: 파일 타입 (선택, e.g., 'kakaotalk', 'pdf')
            legal_categories: 법적 카테고리 리스트 (선택)
            confidence_level: 신뢰도 레벨 1-5 (선택)
            line_number: 라인 번호 (텍스트용)
            line_number_end: 끝 라인 번호 (텍스트용)
            page_number: 페이지 번호 (PDF용)
            segment_start_sec: 시작 시간 (오디오/비디오용)
            segment_end_sec: 끝 시간 (오디오/비디오용)
            is_fallback_embedding: 폴백 임베딩 여부

        Returns:
            str: 벡터 ID (UUID)
        """
        collection = self._ensure_collection(collection_name)

        # Generate proper UUID for Qdrant point ID
        # (chunk_id format "chunk_xxx" is not valid for Qdrant)
        vector_id = str(uuid.uuid4())

        # Build payload with all available metadata
        payload = {
            "chunk_id": chunk_id,
            "file_id": file_id,
            "case_id": case_id,
            "document": content,
            "timestamp": timestamp,
            "sender": sender,
        }

        # Optional fields - only add if provided
        if score is not None:
            payload["score"] = score
        if file_name:
            payload["file_name"] = file_name
        if file_type:
            payload["file_type"] = file_type
        if legal_categories:
            payload["legal_categories"] = legal_categories
        if confidence_level is not None:
            payload["confidence_level"] = confidence_level
        if line_number is not None:
            payload["line_number"] = line_number
        if line_number_end is not None:
            payload["line_number_end"] = line_number_end
        if page_number is not None:
            payload["page_number"] = page_number
        if segment_start_sec is not None:
            payload["segment_start_sec"] = segment_start_sec
        if segment_end_sec is not None:
            payload["segment_end_sec"] = segment_end_sec
        if is_fallback_embedding:
            payload["is_fallback_embedding"] = True

        try:
            self.client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=vector_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            return vector_id

        except Exception as e:
            logger.error(f"Failed to add chunk with metadata: {e}")
            raise

    def get_chunks_by_case(
        self,
        case_id: str,
        collection_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        케이스의 모든 청크 조회 (메타데이터 포함)

        Args:
            case_id: 케이스 ID
            collection_name: 컬렉션명 (선택)

        Returns:
            List[Dict]: 청크 정보 리스트
        """
        collection = self._ensure_collection(collection_name)

        try:
            results = []
            offset = None

            while True:
                points, offset = self.client.scroll(
                    collection_name=collection,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="case_id",
                                match=MatchValue(value=case_id)
                            )
                        ]
                    ),
                    limit=100,
                    offset=offset,
                    with_payload=True
                )

                for point in points:
                    payload = point.payload or {}
                    document = payload.pop("document", "")
                    results.append({
                        "id": str(point.id),
                        "document": document,
                        **payload
                    })

                if offset is None:
                    break

            return results

        except Exception as e:
            logger.error(f"Get chunks by case failed: {e}")
            return []

    def hybrid_search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        case_id: str = None,
        categories: Optional[List[str]] = None,
        min_confidence: Optional[int] = None,
        sender: Optional[str] = None,
        file_types: Optional[List[str]] = None,
        collection_name: str = None,
        score_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 (향상된 필터링)

        Qdrant 네이티브 필터를 사용하여 검색 시점에 필터링합니다.
        후처리 필터링 대비 효율적입니다.

        Args:
            query_embedding: 쿼리 임베딩 벡터
            n_results: 반환할 결과 개수
            case_id: 케이스 ID 필터
            categories: 법적 카테고리 필터 (예: ["adultery", "violence"])
            min_confidence: 최소 신뢰도 레벨 (1-5)
            sender: 발신자 필터
            file_types: 파일 타입 필터 (예: ["kakaotalk", "pdf"])
            collection_name: 컬렉션명 (None이면 기본값)
            score_threshold: 최소 유사도 점수 (0-1)

        Returns:
            List[Dict]: 검색 결과 (score 내림차순)
                - id: 포인트 ID
                - score: 유사도 점수 (0-1, 높을수록 유사)
                - metadata: 페이로드 데이터
                - document: 원본 텍스트
        """
        collection = self._ensure_collection(collection_name)

        # 필터 조건 구성
        must_conditions = []

        # case_id 필터 (필수)
        if case_id:
            must_conditions.append(
                FieldCondition(key="case_id", match=MatchValue(value=case_id))
            )

        # 카테고리 필터 (OR 조건)
        if categories:
            must_conditions.append(
                FieldCondition(key="category", match=MatchAny(any=categories))
            )

        # 신뢰도 범위 필터
        if min_confidence is not None:
            must_conditions.append(
                FieldCondition(
                    key="confidence_level",
                    range=Range(gte=min_confidence)
                )
            )

        # 발신자 필터
        if sender:
            must_conditions.append(
                FieldCondition(key="sender", match=MatchValue(value=sender))
            )

        # 파일 타입 필터 (OR 조건)
        if file_types:
            must_conditions.append(
                FieldCondition(key="file_type", match=MatchAny(any=file_types))
            )

        # 필터 구성
        query_filter = None
        if must_conditions:
            query_filter = Filter(must=must_conditions)

        try:
            results = self.client.search(
                collection_name=collection,
                query_vector=query_embedding,
                limit=n_results,
                query_filter=query_filter,
                with_payload=True,
                score_threshold=score_threshold
            )

            formatted_results = []
            for hit in results:
                payload = hit.payload or {}
                document = payload.pop("document", "")

                formatted_results.append({
                    "id": str(hit.id),
                    "score": hit.score,  # 유사도 점수 (높을수록 유사)
                    "metadata": payload,
                    "document": document
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise

    def create_hybrid_collection(
        self,
        collection_name: str,
        dense_size: int = None,
        enable_sparse: bool = True
    ) -> str:
        """
        하이브리드 검색용 컬렉션 생성 (Dense + Sparse 벡터)

        Args:
            collection_name: 컬렉션명
            dense_size: Dense 벡터 차원 (기본값: self.vector_size)
            enable_sparse: 스파스 벡터 활성화 여부

        Returns:
            str: 생성된 컬렉션명
        """
        dense_size = dense_size or self.vector_size

        try:
            # 기존 컬렉션 확인
            collections = self.client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                logger.info(f"Collection {collection_name} already exists")
                return collection_name

            # 벡터 설정
            vectors_config = {
                "dense": VectorParams(
                    size=dense_size,
                    distance=Distance.COSINE
                )
            }

            # 스파스 벡터 설정 (BM25/IDF)
            sparse_config = None
            if enable_sparse:
                sparse_config = {
                    "sparse": SparseVectorParams(
                        modifier=Modifier.IDF
                    )
                }

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_config
            )

            logger.info(f"Created hybrid collection: {collection_name}")

            # 인덱스 생성
            self._create_hybrid_indexes(collection_name)

            self._initialized_collections.add(collection_name)
            return collection_name

        except Exception as e:
            logger.error(f"Failed to create hybrid collection: {e}")
            raise

    def _create_hybrid_indexes(self, collection_name: str) -> None:
        """
        하이브리드 컬렉션용 인덱스 생성

        Args:
            collection_name: 컬렉션명
        """
        # 기본 인덱스
        keyword_fields = ["case_id", "file_id", "chunk_id", "sender", "category", "file_type"]
        integer_fields = ["confidence_level", "line_number", "page_number"]

        for field in keyword_fields:
            try:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
            except Exception:
                pass  # 이미 존재할 수 있음

        for field in integer_fields:
            try:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.INTEGER
                )
            except Exception:
                pass

    def add_with_sparse(
        self,
        point_id: str,
        dense_vector: List[float],
        sparse_indices: List[int],
        sparse_values: List[float],
        payload: Dict[str, Any],
        collection_name: str = None
    ) -> bool:
        """
        Dense + Sparse 벡터로 포인트 추가

        Args:
            point_id: 포인트 ID
            dense_vector: Dense 임베딩 벡터
            sparse_indices: 스파스 벡터 인덱스 (비제로 위치)
            sparse_values: 스파스 벡터 값 (TF-IDF 등)
            payload: 메타데이터
            collection_name: 컬렉션명

        Returns:
            bool: 성공 여부
        """
        collection = collection_name or self.collection_name

        try:
            point = PointStruct(
                id=point_id,
                vector={
                    "dense": dense_vector,
                    "sparse": SparseVector(
                        indices=sparse_indices,
                        values=sparse_values
                    )
                },
                payload=payload
            )

            self.client.upsert(
                collection_name=collection,
                points=[point]
            )
            return True

        except Exception as e:
            logger.error(f"Add with sparse failed: {e}")
            return False
