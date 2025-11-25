"""
Storage Module
Handles data storage using:
- Local: ChromaDB (vectors) and SQLite (metadata)
- Production: OpenSearch (vectors) and DynamoDB (metadata)
"""

from .schemas import EvidenceFile, EvidenceChunk
from .store_factory import get_metadata_store, get_vector_store, get_storage_info

__all__ = [
    "EvidenceFile",
    "EvidenceChunk",
    "get_metadata_store",
    "get_vector_store",
    "get_storage_info"
]
