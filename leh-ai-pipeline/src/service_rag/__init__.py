"""Service RAG module for legal knowledge base"""

from src.service_rag.schemas import (
    Statute,
    CaseLaw,
    LegalChunk,
    LegalSearchResult
)
from src.service_rag.legal_parser import (
    LegalParser,
    StatuteParser,
    CaseLawParser
)

__all__ = [
    "Statute",
    "CaseLaw",
    "LegalChunk",
    "LegalSearchResult",
    "LegalParser",
    "StatuteParser",
    "CaseLawParser",
]
