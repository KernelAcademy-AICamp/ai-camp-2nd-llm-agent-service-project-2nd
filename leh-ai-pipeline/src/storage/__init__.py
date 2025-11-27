"""
Storage Module
Handles data storage with automatic backend selection:
- Local: ChromaDB (vectors) + SQLite (metadata)
- Cloud/Lambda: Qdrant (vectors) + DynamoDB (metadata)
"""

import os
import logging
from typing import Optional, Union
from .schemas import EvidenceFile, EvidenceChunk

logger = logging.getLogger(__name__)


def is_lambda_environment() -> bool:
    """
    AWS Lambda 환경인지 확인

    Returns:
        bool: Lambda 환경이면 True
    """
    return os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None


def get_metadata_store(
    local_db_path: str = "./data/metadata.db",
    table_name: Optional[str] = None
) -> Union["MetadataStore", "DynamoDBMetadataStore"]:
    """
    환경에 따라 적절한 메타데이터 저장소 반환

    Args:
        local_db_path: 로컬 SQLite DB 경로 (로컬 환경용)
        table_name: DynamoDB 테이블 이름 (Lambda 환경용)

    Returns:
        MetadataStore (로컬) 또는 DynamoDBMetadataStore (Lambda)
    """
    if is_lambda_environment():
        logger.info("Lambda environment detected, using DynamoDB for metadata")
        from .dynamodb_store import DynamoDBMetadataStore
        return DynamoDBMetadataStore(table_name=table_name)
    else:
        logger.info("Local environment detected, using SQLite for metadata")
        from .metadata_store import MetadataStore
        return MetadataStore(db_path=local_db_path)


def get_vector_store(
    local_persist_dir: str = "./data/chromadb",
    qdrant_url: Optional[str] = None,
    qdrant_api_key: Optional[str] = None,
    collection_name: str = "leh_evidence"
) -> Union["VectorStore", "QdrantVectorStore"]:
    """
    환경에 따라 적절한 벡터 저장소 반환

    Args:
        local_persist_dir: 로컬 ChromaDB 저장 경로 (로컬 환경용)
        qdrant_url: Qdrant 서버 URL (Cloud/Lambda 환경용)
        qdrant_api_key: Qdrant API 키 (Cloud 환경용)
        collection_name: 컬렉션 이름

    Returns:
        VectorStore (로컬 ChromaDB) 또는 QdrantVectorStore (Cloud/Lambda)
    """
    # 환경 변수에서 Qdrant 설정 확인
    qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
    qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
    
    if is_lambda_environment() or qdrant_url:
        logger.info("Using Qdrant for vectors (URL: %s)", qdrant_url or "memory")
        from .qdrant_store import QdrantVectorStore
        
        if qdrant_url:
            return QdrantVectorStore(
                mode="server",
                url=qdrant_url,
                api_key=qdrant_api_key,
                collection_name=collection_name
            )
        else:
            # Lambda without Qdrant URL: use in-memory (for testing)
            return QdrantVectorStore(
                mode="memory",
                collection_name=collection_name
            )
    else:
        logger.info("Local environment detected, using ChromaDB for vectors")
        from .vector_store import VectorStore
        return VectorStore(persist_directory=local_persist_dir)


def get_storage_info() -> dict:
    """
    현재 스토리지 환경 정보 반환

    Returns:
        dict: 스토리지 환경 정보
    """
    is_lambda = is_lambda_environment()
    qdrant_url = os.getenv("QDRANT_URL")

    return {
        "environment": "lambda" if is_lambda else "local",
        "metadata_backend": "dynamodb" if is_lambda else "sqlite",
        "vector_backend": "qdrant" if (is_lambda or qdrant_url) else "chromadb",
        "dynamodb_table": os.getenv("DYNAMODB_TABLE", "leh-evidence-metadata") if is_lambda else None,
        "qdrant_url": qdrant_url,
        "qdrant_collection": os.getenv("QDRANT_COLLECTION", "leh_evidence")
    }


__all__ = [
    "EvidenceFile",
    "EvidenceChunk",
    "get_metadata_store",
    "get_vector_store",
    "get_storage_info",
    "is_lambda_environment"
]