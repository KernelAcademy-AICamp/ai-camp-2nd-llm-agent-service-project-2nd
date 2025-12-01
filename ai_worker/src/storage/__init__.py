"""
Storage Module
Handles local data storage using ChromaDB (vectors) and SQLite (metadata)
"""

from .schemas import EvidenceFile, EvidenceChunk
from .storage_manager_v2 import StorageManagerV2
from .search_engine_v2 import SearchEngineV2

__all__ = [
    # Legacy schemas
    "EvidenceFile",
    "EvidenceChunk",

    # V2 modules
    "StorageManagerV2",
    "SearchEngineV2",
]
