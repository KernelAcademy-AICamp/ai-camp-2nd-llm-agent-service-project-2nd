# Evidence Processing Schemas
# 증거 처리 파이프라인용 데이터 스키마

from .source_location import SourceLocation, FileType
from .legal_analysis import LegalCategory, LegalAnalysis, ConfidenceLevel
from .evidence_file import EvidenceFile, FileMetadata, ParsingStatus
from .evidence_chunk import EvidenceChunk
from .evidence_cluster import EvidenceCluster, ConnectionType, ClusterEvidence
from .search_result import SearchResult, SearchResultItem
from .ai_classification import (
    DivorceGround,
    EvidenceClassification,
    to_legal_category,
    to_divorce_ground,
    confidence_to_level,
    classification_to_legal_analysis,
    get_system_prompt_categories,
)

__all__ = [
    # Source Location
    "SourceLocation",
    "FileType",

    # Legal Analysis
    "LegalCategory",
    "LegalAnalysis",
    "ConfidenceLevel",

    # AI Classification (GPT-4 Structured Output용)
    "DivorceGround",
    "EvidenceClassification",
    "to_legal_category",
    "to_divorce_ground",
    "confidence_to_level",
    "classification_to_legal_analysis",
    "get_system_prompt_categories",

    # Evidence File
    "EvidenceFile",
    "FileMetadata",
    "ParsingStatus",

    # Evidence Chunk
    "EvidenceChunk",

    # Evidence Cluster
    "EvidenceCluster",
    "ConnectionType",
    "ClusterEvidence",

    # Search Result
    "SearchResult",
    "SearchResultItem",
]
