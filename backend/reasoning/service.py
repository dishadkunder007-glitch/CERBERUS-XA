"""
CERBERUS-XA: AI Reasoning & Evidence Verification Module (Member 4)
Service Pipeline & FastAPI Router Integration

Integrates:
- Component 1: Evidence Reliability Evaluator
- Component 2: Conflict Analyzer
- Component 3: Suspicious Evidence Detector
- Component 4: Conflict-Aware Reasoning Engine
- Component 5: Citation & Traceability Builder
- Component 6: Local Ollama LLM Adapter & Deterministic Fallback
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Union, Any
from fastapi import APIRouter, HTTPException, status, FastAPI

from .schemas import (
    Claim,
    EvidenceItem,
    EvidenceReliabilityResult,
    ReasoningRequest,
    ReasoningResponse,
)
from .evidence_reliability import EvidenceReliabilityEvaluator
from .conflict_analyzer import ConflictAnalyzer
from .suspicion_detector import SuspicionDetector
from .citation_builder import CitationBuilder
from .reasoning_engine import DeterministicReasoningEngine
from .llm_adapter import OllamaAdapter

logger = logging.getLogger("cerberus_xa.reasoning.service")


class ReasoningPipeline:
    """
    Unified Orchestrator for the CERBERUS-XA Reasoning Module.
    Executes the multi-stage evidence verification and reasoning deliberation.
    """

    def __init__(
        self,
        reliability_evaluator: Optional[EvidenceReliabilityEvaluator] = None,
        conflict_analyzer: Optional[ConflictAnalyzer] = None,
        suspicion_detector: Optional[SuspicionDetector] = None,
        citation_builder: Optional[CitationBuilder] = None,
        reasoning_engine: Optional[DeterministicReasoningEngine] = None,
        llm_adapter: Optional[OllamaAdapter] = None,
    ):
        self.reliability_evaluator = reliability_evaluator or EvidenceReliabilityEvaluator()
        self.conflict_analyzer = conflict_analyzer or ConflictAnalyzer()
        self.suspicion_detector = suspicion_detector or SuspicionDetector()
        self.citation_builder = citation_builder or CitationBuilder()
        self.reasoning_engine = reasoning_engine or DeterministicReasoningEngine(
            citation_builder=self.citation_builder
        )
        self.llm_adapter = llm_adapter or OllamaAdapter()

    def evaluate_reliability(
        self,
        evidence_items: List[EvidenceItem],
        claims: Optional[List[Claim]] = None,
    ) -> List[EvidenceReliabilityResult]:
        """Evaluates reliability for a collection of evidence items."""
        claims = claims or []
        results: List[EvidenceReliabilityResult] = []
        for item in evidence_items:
            res = self.reliability_evaluator.evaluate_item(
                item=item,
                all_items=evidence_items,
                all_claims=claims,
            )
            results.append(res)
        return results

    def verify(self, request: ReasoningRequest) -> ReasoningResponse:
        """
        Executes end-to-end evidence verification and conflict-aware reasoning.
        Enforces offline-first local deliberation with mandatory deterministic fallback.
        """
        # Step 1: Reliability Scoring
        reliability_results = self.evaluate_reliability(
            evidence_items=request.evidence_items,
            claims=request.claims,
        )
        reliability_map: Dict[str, EvidenceReliabilityResult] = {
            r.evidence_id: r for r in reliability_results
        }

        # Step 2: Suspicion Detection
        suspicion_indicators = self.suspicion_detector.detect_indicators(
            evidence_items=request.evidence_items,
            claims=request.claims,
        )

        # Step 3: Conflict Analysis
        conflicts = self.conflict_analyzer.analyze_claims(
            claims=request.claims,
            evidence_items=request.evidence_items,
            reliability_map=reliability_map,
        )

        # Step 4: Citation Building
        citations = self.citation_builder.build_citations_for_evidence(
            evidence_items=request.evidence_items
        )

        # Step 5: Deterministic 7-Stage Reasoning
        base_response = self.reasoning_engine.reason(
            request=request,
            reliability_map=reliability_map,
            conflicts=conflicts,
            suspicion_indicators=suspicion_indicators,
            citations=citations,
        )

        # Step 6: Optional Local Ollama Synthesis with Deterministic Fallback
        final_response = self.llm_adapter.synthesize_response(
            request=request,
            base_response=base_response,
        )

        return final_response


# =============================================================================
# FastAPI Router for Member 1 Integration
# =============================================================================

router = APIRouter(prefix="/reasoning", tags=["Reasoning & Verification"])
pipeline = ReasoningPipeline()


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> Dict[str, Any]:
    """Health check endpoint confirming module readiness, Ollama status, and LLM metrics."""
    ollama_online = pipeline.llm_adapter.is_available()
    metrics = pipeline.llm_adapter.get_metrics()
    return {
        "status": "healthy",
        "module": "Member 4: AI Reasoning & Evidence Verification",
        "system": "CERBERUS-XA",
        "mode": "offline-first-deterministic",
        "version": "1.0.0",
        "ollama_available": ollama_online,
        "ollama_model": pipeline.llm_adapter.default_model,
        "llm_accepted": metrics["llm_accepted"],
        "llm_rejected": metrics["llm_rejected"],
        "llm_rejection_reasons": metrics["rejection_reasons"],
    }


@router.post("/verify", response_model=ReasoningResponse, status_code=status.HTTP_200_OK)
def verify_evidence(request: ReasoningRequest) -> ReasoningResponse:
    """Primary reasoning endpoint executing conflict-aware deliberation and citation building."""
    try:
        return pipeline.verify(request)
    except Exception as e:
        logger.exception("Reasoning pipeline error during verification")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reasoning module execution failed: {str(e)}",
        )


@router.post(
    "/evaluate_reliability",
    status_code=status.HTTP_200_OK,
)
def evaluate_reliability(request: Union[ReasoningRequest, List[EvidenceItem]]) -> Dict[str, Any]:
    """Dedicated endpoint to evaluate reliability of standalone evidence items."""
    try:
        evaluator = pipeline.reliability_evaluator
        if isinstance(request, list):
            items = request
            claims = []
        else:
            items = request.evidence_items
            claims = request.claims
        reports = evaluator.evaluate_all(items, claims)
        return {"evidence_reliability": reports}
    except Exception as e:
        logger.exception("Reliability evaluation error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reliability scoring failed: {str(e)}",
        )


app = FastAPI(
    title="CERBERUS-XA Reasoning API",
    description="Member 4: AI Reasoning & Evidence Verification Module",
    version="1.0.0",
)
app.include_router(router)


@app.get("/", tags=["Root"])
def root() -> Dict[str, Any]:
    """Root endpoint linking to OpenAPI documentation and service health."""
    return {
        "system": "CERBERUS-XA",
        "module": "Member 4: AI Reasoning & Evidence Verification",
        "status": "online",
        "docs_url": "/docs",
        "health_check": "/reasoning/health",
    }

