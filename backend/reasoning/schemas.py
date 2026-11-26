"""
CERBERUS-X: AI Reasoning & Evidence Verification Module
Data Contracts and Pydantic Schemas

Member 4: AI Reasoning & Evidence Verification
Fully compatible with Member 1 (Ingestion) and Member 3 (Knowledge Graph).
"""

from __future__ import annotations
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class ReliabilityLabel(str, Enum):
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    UNASSESSED = "Unassessed"


class EvidenceModality(str, Enum):
    DOCUMENT = "document"
    IMAGE = "image"
    TABLE = "table"
    STRUCTURED = "structured"
    AUDIO = "audio"
    SCAN = "scan"
    RECORD = "record"
    OTHER = "other"

    @classmethod
    def _missing_(cls, value: Any) -> Any:
        if isinstance(value, str):
            val_norm = value.strip().lower().replace("-", "_")
            if val_norm in ("structured_data", "structured-data"):
                return cls.STRUCTURED
            for member in cls:
                if member.value.lower() == val_norm:
                    return member
        return super()._missing_(value)


class DirectnessLevel(str, Enum):
    PRIMARY = "primary"          # Direct observation, raw document, sensor reading, original record
    SECONDARY = "secondary"      # Analysis report, summary, editorial, synthesized document
    HEARSAY = "hearsay"          # Uncorroborated third-party statement, quote without transcript
    DERIVED = "derived"          # Mathematically or logically calculated from other data
    UNVERIFIED = "unverified"    # Unknown provenance, anonymous submission


class ReliabilityRating(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNRELIABLE = "UNRELIABLE"


class ConflictType(str, Enum):
    AGREEMENT = "agreement"
    CONTRADICTION = "contradiction"
    PARTIAL_CONTRADICTION = "partial_contradiction"
    UNRESOLVED_CONFLICT = "unresolved_conflict"
    NO_OVERLAP = "no_overlap"


class SuspicionSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @classmethod
    def _missing_(cls, value: Any) -> Any:
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return super()._missing_(value)


class SuspicionAssessmentLabel(str, Enum):
    NO_SIGNIFICANT_INDICATORS = "NO_SIGNIFICANT_INDICATORS"
    INDICATORS_FOUND = "INDICATORS_FOUND"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    UNASSESSED = "UNASSESSED"


class IndicatorCategory(str, Enum):
    PROVENANCE = "provenance"
    TEMPORAL = "temporal"
    METADATA_CONSISTENCY = "metadata_consistency"
    CONTENT_INTEGRITY = "content_integrity"
    CONTRADICTION = "contradiction"
    DUPLICATION = "duplication"
    EXTRACTION = "extraction"
    SECURITY = "security"


class ConclusionType(str, Enum):
    SUPPORTED = "supported"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING = "conflicting"


class ClaimStatus(str, Enum):
    EXTRACTED_CLAIM = "Extracted Claim"
    UNVERIFIED_CLAIM = "Unverified Claim"
    EVIDENCE_SUPPORTED = "Evidence-Supported Claim"
    CORROBORATED = "Corroborated Claim"
    DISPUTED = "Disputed Claim"
    VERIFIED_FACT = "Verified Fact"


class ReasoningStatus(str, Enum):
    ANSWERED = "ANSWERED"
    PARTIALLY_ANSWERED = "PARTIALLY_ANSWERED"
    CONFLICTED = "CONFLICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    source_id: str = Field(description="Unique identifier for the source system/archive")
    filename: Optional[str] = Field(default=None, description="Original filename if applicable")
    file_type: Optional[str] = Field(default=None, description="MIME type or file extension")
    source_type: Optional[str] = Field(default=None, description="Explicit source format/modality override")
    page_number: Optional[int] = Field(default=None, ge=1, description="1-indexed page number")
    section: Optional[str] = Field(default=None, description="Header, chapter, or section name")
    table_id: Optional[str] = Field(default=None, description="Identifier of the specific table")
    image_id: Optional[str] = Field(default=None, description="Identifier of the image/diagram")
    record_id: Optional[str] = Field(default=None, description="Database record or row index")
    paragraph: Optional[int] = Field(default=None, ge=1, description="1-indexed paragraph number")
    table_name: Optional[str] = Field(default=None, description="Table name if applicable")
    row_id: Optional[str] = Field(default=None, description="Row identifier or index")
    url: Optional[str] = Field(default=None, description="Source web or repository URL")
    timestamp: Optional[Union[datetime, str]] = Field(default=None, description="Content timestamp")
    creation_date: Optional[Union[datetime, str]] = Field(default=None, description="Metadata creation timestamp")
    modification_date: Optional[Union[datetime, str]] = Field(default=None, description="Metadata modification timestamp")
    author: Optional[str] = Field(default=None, description="Document author or recording party")
    organization: Optional[str] = Field(default=None, description="Originating organization")
    checksum_hash: Optional[str] = Field(default=None, description="Cryptographic hash (SHA256, MD5)")
    digital_signature: Optional[str] = Field(default=None, description="Signature status or public key ID")
    extraction_confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="OCR/Parser confidence")
    custom_attributes: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary member metadata")


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(description="Unique evidence item identifier (e.g. EV-001)")
    content: str = Field(min_length=1, description="Extracted content text or summary")
    modality: EvidenceModality = Field(default=EvidenceModality.DOCUMENT, description="Source modality")
    directness: DirectnessLevel = Field(default=DirectnessLevel.PRIMARY, description="Directness level")
    metadata: EvidenceMetadata = Field(description="Traceable metadata for citation and provenance")
    tags: List[str] = Field(default_factory=list, description="Categorical or semantic tags")

    @field_validator("id")
    @classmethod
    def id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Evidence ID cannot be blank.")
        return v.strip()


class Claim(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(description="Unique claim identifier (e.g. CLM-001)")
    statement: str = Field(min_length=1, description="Asserted claim statement")
    entity: Optional[str] = Field(default=None, description="Target entity or subject")
    property: Optional[str] = Field(default=None, description="Observed property or attribute")
    value: Optional[Any] = Field(default=None, description="Asserted value or status")
    unit: Optional[str] = Field(default=None, description="Unit of measurement if applicable")
    timestamp: Optional[Union[datetime, str]] = Field(default=None, description="Timestamp asserted for the claim")
    time_period: Optional[str] = Field(default=None, description="Time range or epoch (e.g. 'FY2023', 'Q3')")
    scope: Optional[str] = Field(default=None, description="Geographic, organizational, or domain scope")
    evidence_ids: List[str] = Field(default_factory=list, description="List of evidence IDs supporting or containing this claim")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence of the claim extraction")
    polarity: bool = Field(default=True, description="True for affirmation, False for negation")


class KGRelationship(BaseModel):
    """Knowledge Graph edge model conforming to Member 3 output contract."""
    model_config = ConfigDict(extra="allow")

    source_entity: str = Field(description="Subject node in Knowledge Graph")
    relation: str = Field(description="Edge type or predicate relation")
    target_entity: str = Field(description="Object node in Knowledge Graph")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties (e.g. timestamp, weight, scope)")
    evidence_ids: List[str] = Field(default_factory=list, description="Evidence items supporting this relationship")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction/Graph confidence")


class ReliabilityBreakdown(BaseModel):
    traceability_score: float = Field(ge=0.0, le=1.0, description="Presence of source IDs, page numbers, authors")
    directness_score: float = Field(ge=0.0, le=1.0, description="Primary vs secondary vs hearsay weighting")
    corroboration_score: float = Field(ge=0.0, le=1.0, description="Corroboration by other independent items")
    consistency_score: float = Field(ge=0.0, le=1.0, description="Internal date, author, and extraction consistency")
    completeness_score: float = Field(ge=0.0, le=1.0, description="Sufficiency of contextual fields")
    overall_score: float = Field(ge=0.0, le=1.0, description="Combined weighted reliability score")
    rating: ReliabilityRating = Field(description="Qualitative categorization")
    reasons: List[str] = Field(default_factory=list, description="Detailed transparent justification for the scores")
    modality_neutrality_flag: bool = Field(
        default=True,
        description="Confirms that reliability was evaluated based on provenance criteria and not biased by modality alone"
    )


class CriterionScore(BaseModel):
    name: str = Field(description="Name of the criterion (e.g. provenance, directness, etc.)")
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Criterion score (0-100) or None if unassessed")
    weight: float = Field(ge=0.0, le=1.0, description="Assigned criterion weight as a fraction of 1.0")
    is_assessed: bool = Field(default=True, description="Whether criterion was evaluated")
    explanation: str = Field(description="Transparent explanation of the score")
    missing_information: List[str] = Field(default_factory=list, description="Missing details relevant to this criterion")


class ReliabilityScorerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provenance_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    directness_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    corroboration_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    consistency_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    completeness_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    high_threshold: float = Field(default=75.0, ge=0.0, le=100.0)
    moderate_threshold: float = Field(default=50.0, ge=0.0, le=100.0)
    low_threshold: float = Field(default=25.0, ge=0.0, le=100.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_weights(cls, values: Any) -> Any:
        if isinstance(values, dict):
            weight_keys = [
                "provenance_weight",
                "directness_weight",
                "corroboration_weight",
                "consistency_weight",
                "completeness_weight",
            ]
            raw_weights = [values.get(k, 0.0) for k in weight_keys if k in values]
            total = sum(raw_weights)
            if abs(total - 100.0) < 1.0:
                for k in weight_keys:
                    if k in values:
                        values[k] = values[k] / 100.0
        return values

    @model_validator(mode="after")
    def validate_weight_sum(self) -> ReliabilityScorerConfig:
        total = (
            self.provenance_weight
            + self.directness_weight
            + self.corroboration_weight
            + self.consistency_weight
            + self.completeness_weight
        )
        if abs(total - 1.0) > 1e-3:
            raise ValueError(f"Criteria weights must sum to 1.0 (or 100%). Current total: {total:.4f}")
        return self


class EvidenceReliabilityResult(BaseModel):
    evidence_id: str = Field(description="Identifier of evaluated evidence item")
    reliability_score: float = Field(ge=0.0, le=100.0, description="Overall reliability score (0-100)")
    reliability_label: ReliabilityLabel = Field(description="Categorical label: High, Moderate, Low, Unassessed")
    criteria_scores: Dict[str, CriterionScore] = Field(description="Detailed breakdown of scores per criterion")
    reasons: List[str] = Field(default_factory=list, description="Explanations justifying the scoring across dimensions")
    missing_information: List[str] = Field(default_factory=list, description="Identified missing details and gaps")
    limitations: List[str] = Field(default_factory=list, description="Epistemic limitations and non-prejudicial safeguards")

    # Backward compatibility attributes for existing services
    traceability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    directness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    corroboration_score: float = Field(default=0.0, ge=0.0, le=1.0)
    consistency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    rating: ReliabilityRating = Field(default=ReliabilityRating.MEDIUM)
    modality_neutrality_flag: bool = Field(default=True)


class EvidenceReliabilityReport(BaseModel):
    evidence_id: str
    breakdown: Union[ReliabilityBreakdown, EvidenceReliabilityResult]



class ConflictPair(BaseModel):
    claim_a_id: str
    claim_b_id: str
    conflict_type: ConflictType
    description: str
    conflicting_attributes: List[str] = Field(default_factory=list)
    temporal_resolution: Optional[str] = None
    unit_resolution: Optional[str] = None
    scope_resolution: Optional[str] = None
    is_resolved: bool = False
    resolution_reason: Optional[str] = None


class SuspicionIndicator(BaseModel):
    model_config = ConfigDict(extra="allow")

    indicator_code: str = Field(description="Unique indicator machine-readable code (e.g. SUSP_INCONSISTENT_TIMESTAMP)")
    category: IndicatorCategory = Field(default=IndicatorCategory.PROVENANCE, description="Indicator category")
    title: str = Field(description="Concise indicator title")
    severity: SuspicionSeverity = Field(description="Assessment severity: LOW, MEDIUM, HIGH")
    explanation: str = Field(description="Detailed transparent explanation of the anomaly")
    caveat: str = Field(
        default="A suspicious indicator does not prove forgery, falsehood or manipulation.",
        description="Mandatory ethical boundary caveat"
    )
    affected_evidence_ids: List[str] = Field(default_factory=list)
    affected_claim_ids: List[str] = Field(default_factory=list)
    recommended_verification_action: Optional[str] = Field(default=None)
    recommended_checks: List[str] = Field(default_factory=list)


class SuspicionAssessment(BaseModel):
    model_config = ConfigDict(extra="allow")

    evidence_id: str
    assessment_label: SuspicionAssessmentLabel = Field(
        default=SuspicionAssessmentLabel.NO_SIGNIFICANT_INDICATORS,
        description="Overall assessment label: NO_SIGNIFICANT_INDICATORS, INDICATORS_FOUND, REQUIRES_REVIEW, UNASSESSED"
    )
    indicators: List[SuspicionIndicator] = Field(default_factory=list)
    severity: SuspicionSeverity = Field(default=SuspicionSeverity.LOW)
    explanation: str
    recommended_checks: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class CitationItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    evidence_id: str = Field(description="Unique evidence identifier")
    source_id: Optional[str] = Field(default=None, description="Source repository or system ID")
    filename: Optional[str] = Field(default=None, description="Original filename")
    source_type: Optional[str] = Field(default=None, description="Source format/modality: document, image, table, structured, scan, record, audio, other")
    format: Optional[str] = Field(default=None, description="Detailed format or file type: pdf, csv, png, tiff, json, etc.")
    page_number: Optional[int] = Field(default=None, description="Page number")
    section: Optional[str] = Field(default=None, description="Section or chapter name")
    paragraph: Optional[int] = Field(default=None, description="Paragraph index")
    table_name: Optional[str] = Field(default=None, description="Table name or identifier")
    row_id: Optional[str] = Field(default=None, description="Row identifier or record index")
    image_id: Optional[str] = Field(default=None, description="Image/figure identifier")
    url: Optional[str] = Field(default=None, description="Source URL if supplied")
    extracted_text: Optional[str] = Field(default=None, description="Extracted content excerpt")
    claim_id: Optional[str] = Field(default=None, description="Associated claim ID")
    formatted_citation: Optional[str] = Field(default=None, description="Standard citation representation")
    missing_fields: List[str] = Field(default_factory=list, description="Missing citation metadata for this reference")


class ClaimCitation(BaseModel):
    model_config = ConfigDict(extra="allow")

    claim_id: Optional[str] = Field(default=None, description="Claim identifier")
    statement: str = Field(description="Asserted claim statement")
    polarity: bool = Field(default=True, description="True for supporting, False for opposing/conflicting")
    citations: List[CitationItem] = Field(default_factory=list, description="Traceable citations grounding this statement")
    missing_metadata: List[str] = Field(default_factory=list, description="Missing citation metadata across referenced items")
    invalid_evidence_ids: List[str] = Field(default_factory=list, description="Referenced evidence IDs not found in manifest")

    def to_citation_dict(self) -> Dict[str, Any]:
        """Returns clean serialization matching the CERBERUS-X citation spec."""
        cit_list = []
        for c in self.citations:
            d: Dict[str, Any] = {"evidence_id": c.evidence_id}
            if c.source_id:
                d["source_id"] = c.source_id
            if c.filename:
                d["filename"] = c.filename
            if c.source_type:
                d["source_type"] = c.source_type
            if c.page_number is not None:
                d["page_number"] = c.page_number
            if c.section:
                d["section"] = c.section
            if c.paragraph is not None:
                d["paragraph"] = c.paragraph
            if c.table_name:
                d["table_name"] = c.table_name
            if c.row_id:
                d["row_id"] = c.row_id
            if c.image_id:
                d["image_id"] = c.image_id
            if c.url:
                d["url"] = c.url
            if c.extracted_text:
                d["extracted_text"] = c.extracted_text
            cit_list.append(d)

        res: Dict[str, Any] = {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "citations": cit_list,
        }
        if not self.polarity:
            res["polarity"] = self.polarity
        if self.missing_metadata:
            res["missing_metadata"] = self.missing_metadata
        if self.invalid_evidence_ids:
            res["invalid_evidence_ids"] = self.invalid_evidence_ids
        return res


class Citation(BaseModel):
    model_config = ConfigDict(extra="allow")

    citation_id: str = Field(description="Numeric or labeled citation reference (e.g. [1])")
    evidence_id: str = Field(description="ID of referenced evidence")
    source_id: str = Field(description="Source repository or system ID")
    filename: Optional[str] = None
    location_locator: str = Field(description="Formatted location e.g. 'Page 4, Sec. 2.1'")
    formatted_citation: str = Field(description="Human-readable citation string")
    verifiable_metadata: Dict[str, Any] = Field(default_factory=dict)
    source_type: Optional[str] = None
    format: Optional[str] = None
    page_number: Optional[int] = None
    section: Optional[str] = None
    paragraph: Optional[int] = None
    table_name: Optional[str] = None
    row_id: Optional[str] = None
    image_id: Optional[str] = None
    url: Optional[str] = None
    extracted_text: Optional[str] = None
    claim_id: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)


DEFAULT_OLLAMA_MODEL: str = os.getenv("CERBERUS_OLLAMA_MODEL", "qwen2.5:7b-instruct")


class ReasoningRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    question: str = Field(min_length=1, description="Question, query, or hypothesis to evaluate")
    claims: List[Claim] = Field(default_factory=list, description="Extracted claims to analyze")
    evidence_items: List[EvidenceItem] = Field(default_factory=list, description="All retrieved evidence pieces")
    kg_relationships: List[KGRelationship] = Field(default_factory=list, description="Knowledge graph edges from Member 3")
    context: Optional[str] = Field(default=None, description="Optional background domain context")
    strict_provenance: bool = Field(default=True, description="Enforce strict metadata citation checks")
    min_reliability_threshold: float = Field(default=0.30, ge=0.0, le=1.0, description="Minimum reliability to treat as factual evidence")
    enable_ollama: bool = Field(default=False, description="Enable local Ollama model if available")
    ollama_model: Optional[str] = Field(default=DEFAULT_OLLAMA_MODEL, description="Ollama model identifier")
    ollama_endpoint: Optional[str] = Field(default="http://localhost:11434", description="Local Ollama HTTP endpoint")


class ReasoningResponse(BaseModel):
    question: str
    status: ReasoningStatus = Field(default=ReasoningStatus.ANSWERED, description="Core reasoning conclusion status")
    conclusion_type: ConclusionType = Field(default=ConclusionType.SUPPORTED)
    answer: str
    summary: str = Field(default="", description="Clear summary of evidence and decision factors")
    supporting_claims: List[Claim] = Field(default_factory=list, description="Claims supporting the conclusion")
    opposing_claims: List[Claim] = Field(default_factory=list, description="Claims opposing or contradicting the conclusion")
    unresolved_conflicts: List[ConflictPair] = Field(default_factory=list, description="Unresolved contradictions")
    reasoning_steps: List[str] = Field(default_factory=list, description="Concise evidence-based stage explanations")
    assumptions: List[str] = Field(default_factory=list, description="Explicit assumptions made during analysis")
    limitations: List[str] = Field(default_factory=list, description="Evidential gaps and epistemic limitations")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence score (0.0 - 1.0)")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Alias for confidence")
    confidence_explanation: str = Field(default="", description="Explainable deterministic breakdown of confidence derivation")
    is_insufficient_evidence: bool = Field(default=False)
    facts: List[str] = Field(default_factory=list)
    inferences: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    opposing_evidence_ids: List[str] = Field(default_factory=list)
    evidence_reliability: Dict[str, Union[ReliabilityBreakdown, EvidenceReliabilityResult]] = Field(default_factory=dict)
    conflicts: List[ConflictPair] = Field(default_factory=list)
    suspicion_indicators: List[SuspicionIndicator] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    claim_citations: List[ClaimCitation] = Field(default_factory=list, description="Citations grouped per claim")
    reasoning_mode: str = Field(default="deterministic", description="'deterministic', 'ollama_augmented', or 'ollama_partial'")
    llm_attempted: bool = Field(default=False, description="True if local LLM generation was initiated")
    llm_synthesis_used: bool = Field(default=False, description="True only when LLM output was accepted into the final answer")
    audit_trail: List[str] = Field(default_factory=list)
