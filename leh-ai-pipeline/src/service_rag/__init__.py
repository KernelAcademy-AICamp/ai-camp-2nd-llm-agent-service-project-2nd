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
from src.service_rag.legal_vectorizer import LegalVectorizer
from src.service_rag.legal_search import LegalSearchEngine

__all__ = [
    "Statute",
    "CaseLaw",
    "LegalChunk",
    "LegalSearchResult",
    "LegalParser",
    "StatuteParser",
    "CaseLawParser",
    "LegalVectorizer",
    "LegalSearchEngine",
]
