"""
TemplateStore: 법률 문서 템플릿 저장소

Qdrant의 legal_templates 컬렉션에서 문서 템플릿(JSON 스키마)을 관리합니다.
- 템플릿 조회 (타입별, 검색)
- 템플릿 업로드
- 템플릿 목록 조회
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from src.utils.embeddings import get_embedding_with_fallback

logger = logging.getLogger(__name__)

# 템플릿 컬렉션명
TEMPLATE_COLLECTION = "legal_templates"


class TemplateStore:
    """
    법률 문서 템플릿 저장소

    Qdrant Cloud에 템플릿 JSON 스키마를 저장하고 검색합니다.
    """

    def __init__(
        self,
        url: str = None,
        api_key: str = None,
        vector_size: int = None
    ):
        """
        TemplateStore 초기화

        Args:
            url: Qdrant Cloud URL (기본값: 환경변수 QDRANT_URL)
            api_key: Qdrant API Key (기본값: 환경변수 QDRANT_API_KEY)
            vector_size: 벡터 차원 (기본값: 1536 for OpenAI)
        """
        self.url = url or os.environ.get('QDRANT_URL')
        self.api_key = api_key or os.environ.get('QDRANT_API_KEY')
        self.vector_size = vector_size or int(os.environ.get('VECTOR_SIZE', '1536'))
        self.collection_name = TEMPLATE_COLLECTION

        if not self.url:
            raise ValueError("QDRANT_URL is required")

        self._client = None
        self._collection_initialized = False

    @property
    def client(self) -> QdrantClient:
        """Qdrant 클라이언트 (lazy initialization)"""
        if self._client is None:
            self._client = QdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=30
            )
            logger.info(f"Connected to Qdrant: {self.url}")
        return self._client

    def _ensure_collection(self) -> None:
        """템플릿 컬렉션 존재 확인 및 생성"""
        if self._collection_initialized:
            return

        try:
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
                logger.info(f"Created template collection: {self.collection_name}")

                # 페이로드 인덱스 생성
                self._create_payload_indexes()

            self._collection_initialized = True

        except Exception as e:
            logger.error(f"Failed to ensure template collection: {e}")
            raise

    def _create_payload_indexes(self) -> None:
        """검색 최적화를 위한 페이로드 인덱스 생성"""
        index_fields = [
            "template_type",
            "version",
            "document_type",
        ]

        for field_name in index_fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                logger.debug(f"Created index for {field_name}")
            except Exception as e:
                # 이미 존재하는 경우 무시
                logger.debug(f"Index {field_name} may already exist: {e}")

    def get_template(self, template_type: str) -> Optional[Dict[str, Any]]:
        """
        템플릿 타입으로 JSON 스키마 조회

        Args:
            template_type: 템플릿 타입 (예: "이혼소장", "답변서")

        Returns:
            템플릿 딕셔너리 또는 None
        """
        self._ensure_collection()

        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="template_type",
                            match=MatchValue(value=template_type)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
                with_vectors=False
            )

            points, _ = results
            if points:
                payload = points[0].payload
                return {
                    "id": str(points[0].id),
                    "template_type": payload.get("template_type"),
                    "version": payload.get("version"),
                    "schema": payload.get("schema"),
                    "example": payload.get("example"),
                    "description": payload.get("description"),
                    "created_at": payload.get("created_at")
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get template '{template_type}': {e}")
            return None

    def search_templates(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        쿼리로 적합한 템플릿 검색 (벡터 유사도 기반)

        Args:
            query: 검색 쿼리 (예: "이혼 소송 소장 양식")
            limit: 반환할 최대 결과 수

        Returns:
            템플릿 목록 (유사도 순)
        """
        self._ensure_collection()

        try:
            # 쿼리 임베딩 생성
            embedding, _ = get_embedding_with_fallback(query)

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit,
                with_payload=True
            )

            templates = []
            for result in results:
                payload = result.payload
                templates.append({
                    "id": str(result.id),
                    "template_type": payload.get("template_type"),
                    "version": payload.get("version"),
                    "description": payload.get("description"),
                    "score": result.score,
                    "schema": payload.get("schema"),
                    "example": payload.get("example")
                })

            return templates

        except Exception as e:
            logger.error(f"Failed to search templates: {e}")
            return []

    def upload_template(
        self,
        template_type: str,
        schema: Dict[str, Any],
        example: Dict[str, Any] = None,
        description: str = "",
        version: str = "1.0.0",
        applicable_cases: List[str] = None
    ) -> str:
        """
        새 템플릿 업로드

        Args:
            template_type: 템플릿 타입 (예: "이혼소장")
            schema: JSON 스키마
            example: 예시 데이터 (선택)
            description: 템플릿 설명
            version: 버전 (기본값: 1.0.0)
            applicable_cases: 적용 가능한 사건 유형 목록

        Returns:
            생성된 템플릿 ID
        """
        self._ensure_collection()

        try:
            # 템플릿 ID 생성 (UUID 사용 - Qdrant 요구사항)
            template_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{template_type}_{version}"))

            # 설명 텍스트로 임베딩 생성
            embed_text = f"{template_type} {description}"
            embedding, _ = get_embedding_with_fallback(embed_text)

            # 페이로드 구성
            payload = {
                "template_type": template_type,
                "document_type": schema.get("document_type", template_type),
                "version": version,
                "description": description,
                "schema": schema,
                "example": example,
                "applicable_cases": applicable_cases or [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            # Qdrant에 저장
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=template_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

            logger.info(f"Uploaded template: {template_id}")
            return template_id

        except Exception as e:
            logger.error(f"Failed to upload template: {e}")
            raise

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        모든 템플릿 목록 조회

        Returns:
            템플릿 메타데이터 목록 (schema/example 제외)
        """
        self._ensure_collection()

        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                with_payload=True,
                with_vectors=False
            )

            templates = []
            points, _ = results
            for point in points:
                payload = point.payload
                templates.append({
                    "id": str(point.id),
                    "template_type": payload.get("template_type"),
                    "version": payload.get("version"),
                    "description": payload.get("description"),
                    "applicable_cases": payload.get("applicable_cases", []),
                    "created_at": payload.get("created_at")
                })

            return templates

        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []

    def delete_template(self, template_type: str) -> bool:
        """
        템플릿 삭제

        Args:
            template_type: 삭제할 템플릿 타입

        Returns:
            삭제 성공 여부
        """
        self._ensure_collection()

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="template_type",
                            match=MatchValue(value=template_type)
                        )
                    ]
                )
            )

            logger.info(f"Deleted template: {template_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return False

    def get_schema_for_generation(self, template_type: str) -> Optional[str]:
        """
        GPT 프롬프트에 사용할 스키마 텍스트 반환

        Args:
            template_type: 템플릿 타입

        Returns:
            JSON 스키마 문자열 (포맷팅됨)
        """
        template = self.get_template(template_type)
        if template and template.get("schema"):
            return json.dumps(template["schema"], ensure_ascii=False, indent=2)
        return None

    def get_example_for_reference(self, template_type: str) -> Optional[str]:
        """
        GPT 프롬프트에 참조용 예시 반환

        Args:
            template_type: 템플릿 타입

        Returns:
            JSON 예시 문자열 (포맷팅됨)
        """
        template = self.get_template(template_type)
        if template and template.get("example"):
            return json.dumps(template["example"], ensure_ascii=False, indent=2)
        return None
