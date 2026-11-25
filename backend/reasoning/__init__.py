"""
CERBERUS-XA: AI Reasoning & Evidence Verification Module (Member 4)

Provides:
- Evidence Reliability Scoring across 5 weighted dimensions.
- Multi-dimensional Conflict Analysis (temporal, unit, scope, attribute).
- Suspicious Evidence Detection (non-prejudicial auditing).
- 7-Stage Conflict-Aware Deliberation Engine.
- Zero-Fabrication Traceable Citation System.
- Local Ollama LLM Adapter with Mandatory Deterministic Fallback.
- FastAPI-ready Router and Unified Reasoning Pipeline.
"""

from .schemas import (
    Claim,
    Citation,
    CitationItem,
    ClaimCitation,
    ClaimStatus,
    ConclusionType,
    ConflictPair,
    ConflictType,
    CriterionScore,
    DirectnessLevel,
    EvidenceItem,
    EvidenceMetadata,
    EvidenceModality,
    EvidenceReliabilityReport,
    EvidenceReliabilityResult,
    IndicatorCategory,
    KGRelationship,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStatus,
    ReliabilityBreakdown,
    ReliabilityLabel,
    ReliabilityRating,
    ReliabilityScorerConfig,
    SuspicionAssessment,
    SuspicionAssessmentLabel,
    SuspicionIndicator,
    SuspicionSeverity,
)
from .evidence_reliability import EvidenceReliabilityEvaluator
from .conflict_analyzer import ConflictAnalyzer
from .suspicion_detector import SuspicionDetector
from .reasoning_engine import DeterministicReasoningEngine
from .citation_builder import CitationBuilder
from .llm_adapter import OllamaAdapter
from .adapter import InterMemberAdapter, AdapterError
from .service import ReasoningPipeline, router as reasoning_router, app as reasoning_app

__all__ = [
    "InterMemberAdapter",
    "reasoning_app",
    # Schemas & Enums
    "EvidenceModality",
    "DirectnessLevel",
    "ReliabilityRating",
    "ReliabilityLabel",
    "CriterionScore",
    "ReliabilityScorerConfig",
    "ReliabilityBreakdown",
    "EvidenceReliabilityResult",
    "EvidenceReliabilityReport",
    "ConflictType",
    "ConflictPair",
    "SuspicionSeverity",
    "SuspicionAssessmentLabel",
    "IndicatorCategory",
    "SuspicionIndicator",
    "SuspicionAssessment",
    "ConclusionType",
    "ReasoningStatus",
    "EvidenceMetadata",
    "EvidenceItem",
    "Claim",
    "KGRelationship",
    "CitationItem",
    "ClaimCitation",
    "ClaimStatus",
    "Citation",
    "ReasoningRequest",
    "ReasoningResponse",
    # Components
    "EvidenceReliabilityEvaluator",
    "ConflictAnalyzer",
    "SuspicionDetector",
    "DeterministicReasoningEngine",
    "CitationBuilder",
    "OllamaAdapter",
    "ReasoningPipeline",
    "reasoning_router",
]
