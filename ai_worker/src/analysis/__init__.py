"""Analysis module for LEH AI Pipeline"""

from src.analysis.evidence_scorer import EvidenceScorer, ScoringResult
from src.analysis.risk_analyzer import RiskAnalyzer, RiskAssessment, RiskLevel
from src.analysis.analysis_engine import AnalysisEngine, AnalysisResult
from src.analysis.article_840_tagger import Article840Tagger, Article840Category, TaggingResult
from src.analysis.legal_analyzer import (
    LegalAnalyzer,
    analyze_chunk,
    analyze_chunks,
    score_to_confidence_level,
)
from src.analysis.context_matcher import (
    ContextAwareKeywordMatcher,
    NegationType,
    MatchResult,
    AnalysisResult as ContextAnalysisResult,
    check_negation,
    get_effective_keywords,
)
from src.analysis.timeline_generator import (
    TimelineGenerator,
    TimelineEvent,
    TimelineResult,
    TimelineEventType,
)

__all__ = [
    # Evidence Scorer
    "EvidenceScorer",
    "ScoringResult",

    # Risk Analyzer
    "RiskAnalyzer",
    "RiskAssessment",
    "RiskLevel",

    # Analysis Engine
    "AnalysisEngine",
    "AnalysisResult",

    # Article 840 Tagger
    "Article840Tagger",
    "Article840Category",
    "TaggingResult",

    # Legal Analyzer (통합)
    "LegalAnalyzer",
    "analyze_chunk",
    "analyze_chunks",
    "score_to_confidence_level",

    # Context Matcher (문맥 인식)
    "ContextAwareKeywordMatcher",
    "NegationType",
    "MatchResult",
    "ContextAnalysisResult",
    "check_negation",
    "get_effective_keywords",

    # Timeline Generator
    "TimelineGenerator",
    "TimelineEvent",
    "TimelineResult",
    "TimelineEventType",
]
