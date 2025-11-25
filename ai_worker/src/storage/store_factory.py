"""
Storage Factory Module
Automatically selects appropriate storage implementation based on environment
"""

import os
from typing import Union

from .metadata_store import MetadataStore
from .vector_store import VectorStore


def get_metadata_store(
    local_db_path: str = "/tmp/metadata.db",
    table_name: str = None
) -> Union[MetadataStore, "DynamoDBMetadataStore"]:
    """
    환경에 따라 적절한 MetadataStore 반환

    Args:
        local_db_path: 로컬 SQLite 경로 (로컬 환경용)
        table_name: DynamoDB 테이블 이름 (프로덕션 환경용)

    Returns:
        MetadataStore (로컬) 또는 DynamoDBMetadataStore (프로덕션)

    Environment Variables:
        - ENVIRONMENT: 'local', 'dev', 'staging', 'prod'
        - USE_DYNAMODB: 'true' to force DynamoDB usage
        - DYNAMODB_TABLE_EVIDENCE_METADATA: DynamoDB table name
    """
    env = os.getenv("ENVIRONMENT", "local").lower()
    use_dynamodb = os.getenv("USE_DYNAMODB", "false").lower() == "true"

    # 프로덕션 환경 또는 명시적으로 DynamoDB 사용 요청 시
    if env in ["prod", "staging"] or use_dynamodb:
        try:
            from .dynamodb_metadata_store import DynamoDBMetadataStore
            return DynamoDBMetadataStore(table_name=table_name)
        except ImportError as e:
            print(f"Warning: Failed to import DynamoDBMetadataStore: {e}")
            print("Falling back to local SQLite MetadataStore")
            return MetadataStore(db_path=local_db_path)
        except Exception as e:
            print(f"Warning: Failed to initialize DynamoDB: {e}")
            print("Falling back to local SQLite MetadataStore")
            return MetadataStore(db_path=local_db_path)

    # 로컬/개발 환경은 SQLite 사용
    return MetadataStore(db_path=local_db_path)


def get_vector_store(
    local_persist_dir: str = "/tmp/chromadb",
    index_name: str = "leh_evidence",
    vector_dimension: int = 768
) -> Union[VectorStore, "OpenSearchVectorStore"]:
    """
    환경에 따라 적절한 VectorStore 반환

    Args:
        local_persist_dir: 로컬 ChromaDB 경로 (로컬 환경용)
        index_name: OpenSearch 인덱스 이름 (프로덕션 환경용)
        vector_dimension: 벡터 차원

    Returns:
        VectorStore (로컬) 또는 OpenSearchVectorStore (프로덕션)

    Environment Variables:
        - ENVIRONMENT: 'local', 'dev', 'staging', 'prod'
        - USE_OPENSEARCH: 'true' to force OpenSearch usage
        - OPENSEARCH_ENDPOINT: OpenSearch endpoint URL
    """
    env = os.getenv("ENVIRONMENT", "local").lower()
    use_opensearch = os.getenv("USE_OPENSEARCH", "false").lower() == "true"
    opensearch_endpoint = os.getenv("OPENSEARCH_ENDPOINT")

    # 프로덕션 환경 또는 명시적으로 OpenSearch 사용 요청 시
    if (env in ["prod", "staging"] or use_opensearch) and opensearch_endpoint:
        try:
            from .opensearch_vector_store import OpenSearchVectorStore
            return OpenSearchVectorStore(
                endpoint=opensearch_endpoint,
                index_name=index_name,
                vector_dimension=vector_dimension
            )
        except ImportError as e:
            print(f"Warning: Failed to import OpenSearchVectorStore: {e}")
            print("Falling back to local ChromaDB VectorStore")
            return VectorStore(persist_directory=local_persist_dir)
        except Exception as e:
            print(f"Warning: Failed to initialize OpenSearch: {e}")
            print("Falling back to local ChromaDB VectorStore")
            return VectorStore(persist_directory=local_persist_dir)

    # 로컬/개발 환경은 ChromaDB 사용
    return VectorStore(persist_directory=local_persist_dir)


def get_storage_info() -> dict:
    """
    현재 스토리지 설정 정보 반환

    Returns:
        dict: 스토리지 설정 정보
    """
    env = os.getenv("ENVIRONMENT", "local").lower()
    use_dynamodb = os.getenv("USE_DYNAMODB", "false").lower() == "true"
    use_opensearch = os.getenv("USE_OPENSEARCH", "false").lower() == "true"
    opensearch_endpoint = os.getenv("OPENSEARCH_ENDPOINT")

    metadata_backend = "DynamoDB" if (env in ["prod", "staging"] or use_dynamodb) else "SQLite"
    vector_backend = "OpenSearch" if ((env in ["prod", "staging"] or use_opensearch) and opensearch_endpoint) else "ChromaDB"

    return {
        "environment": env,
        "metadata_backend": metadata_backend,
        "vector_backend": vector_backend,
        "dynamodb_table": os.getenv("DYNAMODB_TABLE_EVIDENCE_METADATA"),
        "opensearch_endpoint": opensearch_endpoint,
        "is_production": env in ["prod", "staging"]
    }
