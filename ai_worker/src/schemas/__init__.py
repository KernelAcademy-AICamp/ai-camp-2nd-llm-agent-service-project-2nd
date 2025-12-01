# Evidence Processing Schemas
# 증거 처리 파이프라인용 데이터 스키마

from .source_location import SourceLocation, FileType
from .legal_analysis import LegalCategory, LegalAnalysis, ConfidenceLevel
from .evidence_file import EvidenceFile, FileMetadata, ParsingStatus
from .evidence_chunk import EvidenceChunk
from .evidence_cluster import EvidenceCluster, ConnectionType, ClusterEvidence
from .search_result import SearchResult, SearchResultItem

__all__ = [
    # Source Location
    "SourceLocation",
    "FileType",

    # Legal Analysis
    "LegalCategory",
    "LegalAnalysis",
    "ConfidenceLevel",

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
