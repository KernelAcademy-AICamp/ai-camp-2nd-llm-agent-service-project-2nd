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
from src.analysis.ai_analyzer import (
    AIAnalyzer,
    AIAnalyzerConfig,
    analyze_with_ai,
)
from src.analysis.evidence_advisor import (
    EvidenceAdvisor,
    EvidenceAdvice,
    EvidenceAdviceResponse,
    AdviceType,
    Severity,
)
from src.analysis.streaming_analyzer import (
    StreamingAnalyzer,
    StreamingConfig,
    stream_analysis,
    stream_analysis_async,
)
from src.analysis.impact_rules import (
    FaultType,
    EvidenceType,
    ImpactDirection,
    ImpactRule,
    IMPACT_RULES,
    get_impact_rule,
    calculate_evidence_weight,
    calculate_single_impact,
)
from src.analysis.impact_analyzer import (
    ImpactAnalyzer,
    EvidenceImpact,
    SimilarCase,
    DivisionPrediction,
    analyze_case_impact,
)
from src.analysis.precedent_searcher import (
    PrecedentSearcher,
    PrecedentCase,
    search_similar_cases,
)
from src.analysis.event_summarizer import (
    EventSummarizer,
    EventSummary,
    SummaryType,
    summarize_event,
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

    # AI Analyzer
    "AIAnalyzer",
    "AIAnalyzerConfig",
    "analyze_with_ai",

    # Evidence Advisor (규칙 기반)
    "EvidenceAdvisor",
    "EvidenceAdvice",
    "EvidenceAdviceResponse",
    "AdviceType",
    "Severity",

    # Streaming Analyzer
    "StreamingAnalyzer",
    "StreamingConfig",
    "stream_analysis",
    "stream_analysis_async",

    # Impact Rules (규칙 기반)
    "FaultType",
    "EvidenceType",
    "ImpactDirection",
    "ImpactRule",
    "IMPACT_RULES",
    "get_impact_rule",
    "calculate_evidence_weight",
    "calculate_single_impact",

    # Impact Analyzer (재산분할 예측)
    "ImpactAnalyzer",
    "EvidenceImpact",
    "SimilarCase",
    "DivisionPrediction",
    "analyze_case_impact",

    # Precedent Searcher (유사 판례 검색)
    "PrecedentSearcher",
    "PrecedentCase",
    "search_similar_cases",

    # Event Summarizer (이벤트 요약)
    "EventSummarizer",
    "EventSummary",
    "SummaryType",
    "summarize_event",
]
