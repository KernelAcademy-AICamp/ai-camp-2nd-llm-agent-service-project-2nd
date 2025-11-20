"""
OpenSearch utilities for RAG (Retrieval-Augmented Generation)

Mock implementation for local development.
TODO: Replace with boto3/opensearch-py when AWS OpenSearch is configured.

Migration Guide:
1. Uncomment opensearch-py imports and client initialization
2. Replace mock storage with real OpenSearch operations
3. No changes needed in service or API layers
"""

from typing import List, Dict, Optional
from app.core.config import settings

# TODO: Uncomment when AWS OpenSearch is configured
# from opensearchpy import OpenSearch, RequestsHttpConnection
# from requests_aws4auth import AWS4Auth
# import boto3

# Mock in-memory storage for local development
# TODO: Remove this when switching to real OpenSearch
_mock_opensearch_store: Dict[str, List[Dict]] = {}  # index_name -> list of documents


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
    # TODO: Replace with OpenSearch when AWS is configured
    # index_name = f"{settings.OPENSEARCH_CASE_INDEX_PREFIX}{case_id}"
    #
    # # Generate query embedding using OpenAI
    # query_embedding = generate_embedding(query)
    #
    # # OpenSearch KNN query
    # search_body = {
    #     "size": top_k,
    #     "query": {
    #         "bool": {
    #             "must": [
    #                 {
    #                     "knn": {
    #                         "vector": {
    #                             "vector": query_embedding,
    #                             "k": top_k
    #                         }
    #                     }
    #                 }
    #             ]
    #         }
    #     }
    # }
    #
    # # Add filters if provided
    # if filters:
    #     filter_clauses = []
    #     for field, values in filters.items():
    #         if isinstance(values, list):
    #             filter_clauses.append({"terms": {field: values}})
    #         else:
    #             filter_clauses.append({"term": {field: values}})
    #     search_body["query"]["bool"]["filter"] = filter_clauses
    #
    # # Execute search
    # client = get_opensearch_client()
    # response = client.search(index=index_name, body=search_body)
    #
    # # Parse results
    # results = []
    # for hit in response["hits"]["hits"]:
    #     doc = hit["_source"]
    #     doc["_score"] = hit["_score"]
    #     results.append(doc)
    #
    # return results

    # Mock implementation
    index_name = f"{settings.OPENSEARCH_CASE_INDEX_PREFIX}{case_id}"
    documents = _mock_opensearch_store.get(index_name, [])

    # Simple keyword-based mock search (not semantic)
    if not query:
        results = documents[:top_k]
    else:
        # Filter by query keywords (very simple mock)
        query_lower = query.lower()
        results = [
            doc for doc in documents
            if query_lower in doc.get("content", "").lower()
        ][:top_k]

    # Apply filters if provided
    if filters:
        for field, values in filters.items():
            if isinstance(values, list):
                results = [
                    doc for doc in results
                    if any(v in doc.get(field, []) for v in values)
                ]
            else:
                results = [doc for doc in results if doc.get(field) == values]

    # Add mock scores
    for i, doc in enumerate(results):
        doc["_score"] = 1.0 - (i * 0.1)  # Descending scores

    return results


def index_evidence_document(case_id: str, document: Dict) -> str:
    """
    Index an evidence document in OpenSearch

    This is typically called by AI Worker, not backend API.

    Args:
        case_id: Case ID
        document: Document to index (must include 'id', 'content', 'vector', etc.)

    Returns:
        Document ID in OpenSearch
    """
    # TODO: Replace with OpenSearch when AWS is configured
    # index_name = f"{settings.OPENSEARCH_CASE_INDEX_PREFIX}{case_id}"
    #
    # # Create index if not exists
    # client = get_opensearch_client()
    # if not client.indices.exists(index=index_name):
    #     create_case_index(case_id)
    #
    # # Index document
    # doc_id = document.get("id")
    # response = client.index(index=index_name, id=doc_id, body=document)
    #
    # return response["_id"]

    # Mock implementation
    index_name = f"{settings.OPENSEARCH_CASE_INDEX_PREFIX}{case_id}"

    if index_name not in _mock_opensearch_store:
        _mock_opensearch_store[index_name] = []

    doc_id = document.get("id")
    _mock_opensearch_store[index_name].append(document)

    return doc_id


def create_case_index(case_id: str) -> bool:
    """
    Create OpenSearch index for a case with vector field mapping

    Args:
        case_id: Case ID

    Returns:
        True if created successfully
    """
    # TODO: Replace with OpenSearch when AWS is configured
    # index_name = f"{settings.OPENSEARCH_CASE_INDEX_PREFIX}{case_id}"
    #
    # index_body = {
    #     "settings": {
    #         "index": {
    #             "knn": True,
    #             "knn.algo_param.ef_search": 100
    #         }
    #     },
    #     "mappings": {
    #         "properties": {
    #             "id": {"type": "keyword"},
    #             "content": {"type": "text"},
    #             "vector": {
    #                 "type": "knn_vector",
    #                 "dimension": 1536,  # OpenAI text-embedding-3-small
    #                 "method": {
    #                     "name": "hnsw",
    #                     "space_type": "cosinesimil",
    #                     "engine": "nmslib"
    #                 }
    #             },
    #             "labels": {"type": "keyword"},
    #             "timestamp": {"type": "date"},
    #             "speaker": {"type": "keyword"}
    #         }
    #     }
    # }
    #
    # client = get_opensearch_client()
    # client.indices.create(index=index_name, body=index_body)
    # return True

    # Mock implementation
    index_name = f"{settings.OPENSEARCH_CASE_INDEX_PREFIX}{case_id}"
    _mock_opensearch_store[index_name] = []
    return True


def delete_case_index(case_id: str) -> bool:
    """
    Delete OpenSearch index for a case

    Args:
        case_id: Case ID

    Returns:
        True if deleted successfully, False if not found
    """
    # TODO: Replace with OpenSearch when AWS is configured
    # index_name = f"{settings.OPENSEARCH_CASE_INDEX_PREFIX}{case_id}"
    # client = get_opensearch_client()
    # if client.indices.exists(index=index_name):
    #     client.indices.delete(index=index_name)
    #     return True
    # return False

    # Mock implementation
    index_name = f"{settings.OPENSEARCH_CASE_INDEX_PREFIX}{case_id}"
    if index_name in _mock_opensearch_store:
        del _mock_opensearch_store[index_name]
        return True
    return False


def get_all_documents_in_case(case_id: str) -> List[Dict]:
    """
    Get all documents in a case index (for debugging/testing)

    Args:
        case_id: Case ID

    Returns:
        List of all documents in the case
    """
    # TODO: Replace with OpenSearch when AWS is configured
    # index_name = f"{settings.OPENSEARCH_CASE_INDEX_PREFIX}{case_id}"
    # client = get_opensearch_client()
    # response = client.search(
    #     index=index_name,
    #     body={"query": {"match_all": {}}, "size": 10000}
    # )
    # return [hit["_source"] for hit in response["hits"]["hits"]]

    # Mock implementation
    index_name = f"{settings.OPENSEARCH_CASE_INDEX_PREFIX}{case_id}"
    return _mock_opensearch_store.get(index_name, [])


# TODO: Uncomment when AWS OpenSearch is configured
# def get_opensearch_client():
#     """Get configured OpenSearch client"""
#     # AWS authentication
#     credentials = boto3.Session().get_credentials()
#     awsauth = AWS4Auth(
#         credentials.access_key,
#         credentials.secret_key,
#         settings.AWS_REGION,
#         'es',
#         session_token=credentials.token
#     )
#
#     # Create client
#     client = OpenSearch(
#         hosts=[{'host': settings.OPENSEARCH_HOST, 'port': 443}],
#         http_auth=awsauth,
#         use_ssl=True,
#         verify_certs=True,
#         connection_class=RequestsHttpConnection
#     )
#
#     return client
