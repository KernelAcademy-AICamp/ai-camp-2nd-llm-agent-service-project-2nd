"""
Qdrant utilities for RAG (Retrieval-Augmented Generation)

Real Qdrant implementation using qdrant-client package.
Qdrant is used for vector similarity search to find relevant evidence documents.
"""

import logging
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from app.core.config import settings
from app.utils.openai_client import generate_embedding

logger = logging.getLogger(__name__)

# Initialize Qdrant client (singleton)
_qdrant_client: Optional[QdrantClient] = None


def _get_qdrant_client() -> QdrantClient:
    """Get or create Qdrant client (singleton pattern)"""
    global _qdrant_client
    if _qdrant_client is None:
        if settings.QDRANT_HOST:
            # Remote Qdrant server
            # Check if QDRANT_HOST contains protocol (URL format)
            if settings.QDRANT_HOST.startswith(("http://", "https://")):
                # Use url parameter for full URL
                _qdrant_client = QdrantClient(
                    url=settings.QDRANT_HOST,
                    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                )
            else:
                # Use host/port for hostname-only format
                _qdrant_client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                    https=settings.QDRANT_USE_HTTPS
                )
            logger.info(f"Connected to Qdrant at {settings.QDRANT_HOST}")
        else:
            # In-memory Qdrant for local development
            _qdrant_client = QdrantClient(":memory:")
            logger.info("Using in-memory Qdrant for local development")
    return _qdrant_client


def _get_collection_name(case_id: str) -> str:
    """Get Qdrant collection name for a case"""
    return f"{settings.QDRANT_COLLECTION_PREFIX}{case_id}"


def search_evidence_by_semantic(
    case_id: str,
    query: str,
    top_k: int = 5,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Search evidence using semantic similarity (vector search)

    Args:
        case_id: Case ID
        query: Search query text
        top_k: Number of top results to return
        filters: Optional filters (e.g., {"labels": ["폭언"]})

    Returns:
        List of evidence documents with similarity scores
    """
    client = _get_qdrant_client()
    collection_name = _get_collection_name(case_id)

    try:
        # Check if collection exists
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            logger.warning(f"Collection {collection_name} does not exist")
            return []

        # Generate query embedding using OpenAI
        query_embedding = generate_embedding(query)

        # Build filter conditions if provided
        qdrant_filter = None
        if filters:
            filter_conditions = []
            for field, values in filters.items():
                if isinstance(values, list):
                    # Match any of the values
                    filter_conditions.append(
                        models.FieldCondition(
                            key=field,
                            match=models.MatchAny(any=values)
                        )
                    )
                else:
                    filter_conditions.append(
                        models.FieldCondition(
                            key=field,
                            match=models.MatchValue(value=values)
                        )
                    )
            if filter_conditions:
                qdrant_filter = models.Filter(must=filter_conditions)

        # Execute search using query_points (qdrant-client >= 1.7)
        results = client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            query_filter=qdrant_filter,
            limit=top_k,
            with_payload=True
        ).points

        # Parse results
        evidence_list = []
        for hit in results:
            doc = hit.payload.copy() if hit.payload else {}
            doc["_score"] = hit.score
            evidence_list.append(doc)

        logger.info(f"Qdrant search returned {len(evidence_list)} results for case {case_id}")
        return evidence_list

    except Exception as e:
        logger.error(f"Qdrant search error for case {case_id}: {e}")
        return []


def index_evidence_document(case_id: str, document: Dict) -> str:
    """
    Index an evidence document in Qdrant

    This is typically called by AI Worker, not backend API.

    Args:
        case_id: Case ID
        document: Document to index (must include 'id', 'content', 'vector' or will be generated)

    Returns:
        Document ID in Qdrant
    """
    client = _get_qdrant_client()
    collection_name = _get_collection_name(case_id)

    try:
        # Ensure collection exists
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            create_case_collection(case_id)

        doc_id = document.get("id") or document.get("evidence_id")
        if not doc_id:
            raise ValueError("Document must have 'id' or 'evidence_id' field")

        # Get or generate embedding vector
        vector = document.get("vector")
        if not vector and document.get("content"):
            vector = generate_embedding(document["content"])

        if not vector:
            raise ValueError("Document must have 'vector' or 'content' for embedding")

        # Prepare payload (exclude vector from payload)
        payload = {k: v for k, v in document.items() if k != "vector"}

        # Upsert point
        client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=hash(doc_id) % (2**63),  # Convert string ID to int
                    vector=vector,
                    payload=payload
                )
            ]
        )

        logger.info(f"Indexed document {doc_id} in collection {collection_name}")
        return doc_id

    except Exception as e:
        logger.error(f"Qdrant index error for case {case_id}: {e}")
        raise


def create_case_collection(case_id: str) -> bool:
    """
    Create Qdrant collection for a case with vector configuration

    Args:
        case_id: Case ID

    Returns:
        True if created successfully
    """
    client = _get_qdrant_client()
    collection_name = _get_collection_name(case_id)

    try:
        # Check if collection already exists
        collections = client.get_collections().collections
        if any(c.name == collection_name for c in collections):
            logger.info(f"Collection {collection_name} already exists")
            return True

        # Create collection with vector config
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1536,  # OpenAI text-embedding-3-small dimension
                distance=Distance.COSINE
            )
        )

        logger.info(f"Created Qdrant collection: {collection_name}")
        return True

    except Exception as e:
        logger.error(f"Qdrant create collection error for case {case_id}: {e}")
        raise


def delete_case_collection(case_id: str) -> bool:
    """
    Delete Qdrant collection for a case

    Args:
        case_id: Case ID

    Returns:
        True if deleted successfully, False if not found
    """
    client = _get_qdrant_client()
    collection_name = _get_collection_name(case_id)

    try:
        # Check if collection exists
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            logger.warning(f"Collection {collection_name} does not exist")
            return False

        client.delete_collection(collection_name=collection_name)
        logger.info(f"Deleted Qdrant collection: {collection_name}")
        return True

    except Exception as e:
        logger.error(f"Qdrant delete collection error for case {case_id}: {e}")
        return False


def get_all_documents_in_case(case_id: str) -> List[Dict]:
    """
    Get all documents in a case collection (for debugging/testing)

    Args:
        case_id: Case ID

    Returns:
        List of all documents in the case
    """
    client = _get_qdrant_client()
    collection_name = _get_collection_name(case_id)

    try:
        # Check if collection exists
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            return []

        # Scroll through all points
        results = client.scroll(
            collection_name=collection_name,
            limit=10000,
            with_payload=True,
            with_vectors=False
        )

        documents = [point.payload for point in results[0] if point.payload]
        return documents

    except Exception as e:
        logger.error(f"Qdrant get all documents error for case {case_id}: {e}")
        return []


# ==================================================
# Legal Knowledge Search (법률 조문 검색)
# ==================================================

LEGAL_KNOWLEDGE_COLLECTION = "leh_legal_knowledge"


def search_legal_knowledge(
    query: str,
    top_k: int = 3,
    doc_type: Optional[str] = None
) -> List[Dict]:
    """
    Search legal knowledge (법률 조문, 판례) using semantic similarity

    Args:
        query: Search query text (e.g., "이혼 사유", "재판상 이혼")
        top_k: Number of top results to return
        doc_type: Optional filter by document type ("statute" or "case_law")

    Returns:
        List of legal documents with similarity scores
    """
    client = _get_qdrant_client()

    try:
        # Check if collection exists
        collections = client.get_collections().collections
        if not any(c.name == LEGAL_KNOWLEDGE_COLLECTION for c in collections):
            logger.warning(f"Legal knowledge collection {LEGAL_KNOWLEDGE_COLLECTION} does not exist")
            return []

        # Generate query embedding
        query_embedding = generate_embedding(query)

        # Build filter if doc_type specified
        qdrant_filter = None
        if doc_type:
            qdrant_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_type",
                        match=models.MatchValue(value=doc_type)
                    )
                ]
            )

        # Execute search
        results = client.query_points(
            collection_name=LEGAL_KNOWLEDGE_COLLECTION,
            query=query_embedding,
            query_filter=qdrant_filter,
            limit=top_k,
            with_payload=True
        ).points

        # Parse results
        legal_docs = []
        for hit in results:
            doc = hit.payload.copy() if hit.payload else {}
            doc["_score"] = hit.score
            legal_docs.append(doc)

        logger.info(f"Legal knowledge search returned {len(legal_docs)} results for query: {query[:50]}...")
        return legal_docs

    except Exception as e:
        logger.error(f"Legal knowledge search error: {e}")
        return []


# ==================================================
# Legal Document Templates (법률 문서 템플릿)
# ==================================================

TEMPLATE_COLLECTION = "legal_templates"


def get_template_by_type(template_type: str) -> Optional[Dict]:
    """
    Get legal document template by type

    Args:
        template_type: Template type (e.g., "이혼소장", "답변서")

    Returns:
        Template dict with schema and example, or None if not found
    """
    client = _get_qdrant_client()

    try:
        # Check if collection exists
        collections = client.get_collections().collections
        if not any(c.name == TEMPLATE_COLLECTION for c in collections):
            logger.warning(f"Template collection {TEMPLATE_COLLECTION} does not exist")
            return None

        # Search by template_type filter
        results = client.scroll(
            collection_name=TEMPLATE_COLLECTION,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="template_type",
                        match=models.MatchValue(value=template_type)
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
                "description": payload.get("description"),
                "schema": payload.get("schema"),
                "example": payload.get("example"),
                "applicable_cases": payload.get("applicable_cases", [])
            }

        logger.info(f"Template '{template_type}' not found")
        return None

    except Exception as e:
        logger.error(f"Get template error: {e}")
        return None


def get_template_schema_for_prompt(template_type: str) -> Optional[str]:
    """
    Get template schema as formatted JSON string for GPT prompt

    Args:
        template_type: Template type

    Returns:
        JSON schema string, or None if not found
    """
    import json

    template = get_template_by_type(template_type)
    if template and template.get("schema"):
        return json.dumps(template["schema"], ensure_ascii=False, indent=2)
    return None


def get_template_example_for_prompt(template_type: str) -> Optional[str]:
    """
    Get template example as formatted JSON string for GPT prompt

    Args:
        template_type: Template type

    Returns:
        JSON example string, or None if not found
    """
    import json

    template = get_template_by_type(template_type)
    if template and template.get("example"):
        return json.dumps(template["example"], ensure_ascii=False, indent=2)
    return None


# Backward compatibility aliases (for gradual migration)
def delete_case_index(case_id: str) -> bool:
    """Alias for delete_case_collection (backward compatibility)"""
    return delete_case_collection(case_id)


def create_case_index(case_id: str) -> bool:
    """Alias for create_case_collection (backward compatibility)"""
    return create_case_collection(case_id)
