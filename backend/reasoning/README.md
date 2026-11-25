# CERBERUS-XA — Member 4: AI Reasoning & Evidence Verification Module

**Author:** Member 4 (AI Reasoning & Evidence Verification Engineer)  
**Location:** `backend/reasoning/`  
**Architecture:** 100% Local / Offline-First, Deterministic Baseline, Optional Local Ollama Enhancement

---

## 1. Module Overview

In the **CERBERUS-XA** multimodal intelligence system, Member 4 provides the core analytical and verification brain. The module is responsible for:

1. **Evaluating Evidence Reliability** across 5 transparent, weighted criteria (0–100 score).
2. **Multi-Dimensional Conflict Analysis** detecting contradictions across dates, units, entity names, scopes, and attributes without discarding opposing evidence.
3. **Suspicious Evidence Detection** identifying evidentiary anomalies (provenance gaps, date inversions, duplicate origins, injection attempts) as audit signals without falsely labeling content as fake.
4. **7-Stage Deliberation Reasoning Engine** generating structured conclusions (`ANSWERED`, `PARTIALLY_ANSWERED`, `CONFLICTED`, `INSUFFICIENT_EVIDENCE`) and defending against prompt injection.
5. **Zero-Fabrication Citation & Traceability System** generating auditable source references across all 7 supported modalities (PDF, Scan, Image, Table, CSV, Record, Text).
6. **Local LLM Adapter** interfacing with a local Ollama instance (`llama3`) for natural-language synthesis while guaranteeing seamless deterministic fallback if Ollama is unreachable.
7. **FastAPI Service Router** allowing Member 1 to mount and consume verification endpoints effortlessly.

---

## 2. Directory Structure

```
backend/reasoning/
├── __init__.py                # Package exports (schemas, components, router, pipeline)
├── schemas.py                 # Pydantic v2 data models, enums, request & response contracts
├── evidence_reliability.py    # Component 1: 5-dimension transparent reliability evaluator
├── conflict_analyzer.py       # Component 2: Multi-dimensional conflict & contradiction analyzer
├── suspicion_detector.py      # Component 3: Non-prejudicial suspicious evidence indicator detector
├── reasoning_engine.py        # Component 4: 7-stage deterministic conflict-aware deliberation engine
├── citation_builder.py        # Component 5: Zero-fabrication citation and traceability system
├── llm_adapter.py             # Component 6: Local Ollama LLM adapter with deterministic fallback
├── service.py                 # Component 7: Unified ReasoningPipeline & FastAPI APIRouter
├── sample_request.json        # Live sample request payload
├── sample_response.json       # Live sample response payload
├── README.md                  # Comprehensive module documentation and integration guide
└── tests/                     # 56 comprehensive unit tests
    ├── test_citation_builder.py
    ├── test_conflict_analyzer.py
    ├── test_evidence_reliability.py
    ├── test_llm_adapter.py
    ├── test_reasoning_engine.py
    ├── test_service_pipeline.py
    └── test_suspicion_detector.py
```

---

## 3. Core Components

### Component 1: `evidence_reliability.py`
Evaluates individual evidence items using a transparent, configurable weighted scoring system (weights sum to 100%):
- **Provenance & Traceability (25%)**: Identifiable source archive, filename, author, cryptographic checksum.
- **Directness (25%)**: Primary eyewitness/instrument records vs. secondary, contextual, or hearsay.
- **Corroboration (20%)**: Independent multi-source verification. **Safeguard:** Duplicate copies sharing origin or text hash are explicitly excluded from independent corroboration.
- **Consistency (15%)**: Chronological plausibility, author/format agreement, absence of unresolved internal contradictions.
- **Completeness & Context (15%)**: Presence of dates, measurements, units, entity names, and substantive detail.
- **Output:** `EvidenceReliabilityResult` with 0–100 score, qualitative label (`High`, `Moderate`, `Low`, `Unassessed`), itemized criterion breakdown, justifications, information gaps, and epistemic limitations.

### Component 2: `conflict_analyzer.py`
Analyzes extracted claims and evidence pairs to distinguish true contradictions from contextual differences:
- **Unit Standardization**: Normalizes metrics (e.g. km to meters, kg to grams) before assessing conflict.
- **Temporal Differentiation**: Recognizes that state changes over time (e.g. "active in 2021" vs "closed in 2023") represent chronological evolution, not logical contradiction.
- **Scope Differentiation**: Distinguishes between regional vs global measurements (e.g. "US revenue" vs "Global revenue").
- **Unresolved Deadlocks**: Preserves deadlock when conflicting sources have equal reliability, preventing confirmation bias.

### Component 3: `suspicion_detector.py`
Audits evidence for 12 suspicious indicators across 8 categories without declaring evidence fake:
- Categories: `PROVENANCE`, `TEMPORAL`, `METADATA_CONSISTENCY`, `CONTENT_INTEGRITY`, `CONTRADICTION`, `DUPLICATION`, `EXTRACTION`, `SECURITY`.
- Detects missing attribution, inverted dates, duplicate sources, low OCR confidence, and prompt injection attacks (`SUSP_UNTRUSTED_INSTRUCTION`).
- **Ethical Safeguard:** Appends non-accusatory caveats reminding analysts that indicators represent audit signals or extraction anomalies, not mathematical proof of forgery.

### Component 4: `reasoning_engine.py`
Implements the 7-stage evidence-based deliberation process:
1. **Question Understanding**: Identifies target entities, properties, time bounds, and query classification.
2. **Evidence Grouping**: Groups evidence by Entity, Claim, Topic, Time, and Source; applies co-origin discounting.
3. **Supporting Evidence Identification**: Identifies claims and graph edges directly supporting the answer.
4. **Contradictory Evidence Identification**: Catalogs counter-claims and opposing evidence; never silently ignores contradictions.
5. **Context Analysis**: Performs cross-checks on dates, units, entities, and scopes.
6. **Evidence Sufficiency Evaluation**: Determines if available evidence is adequate or triggers `INSUFFICIENT_EVIDENCE`.
7. **Conclusion & Synthesis**: Produces terminal status: `ANSWERED`, `PARTIALLY_ANSWERED`, `CONFLICTED`, or `INSUFFICIENT_EVIDENCE`.

### Component 5: `citation_builder.py`
Grounds every factual statement in verifiable input evidence:
- **Supported Source Types**: PDF documents, Scanned records, Images, Tables, CSV datasets, Structured records, and Text files.
- **Zero Fabrication**: Never invents page numbers, filenames, or source IDs. Missing metadata is cataloged in `missing_fields` and `missing_metadata`.
- **Deduplication**: Eliminates duplicate citations to the same source.
- **Invalid Reference Catching**: Catches and catalogs unmanifested evidence references in `invalid_evidence_ids`.
- **Structured JSON Schema**:
  ```json
  {
    "claim_id": "claim_01",
    "statement": "The report identifies the project as completed.",
    "citations": [
      {
        "evidence_id": "ev_001",
        "filename": "project_report.pdf",
        "page_number": 5,
        "section": "Results"
      }
    ]
  }
  ```

### Component 6: `llm_adapter.py`
Interfaces with a local Ollama instance (`http://localhost:11434`, model: `llama3`):
- Non-blocking timeout guard (defaults to 8.0s).
- Constrained system prompt strictly preventing hallucination or contradicting deterministic conclusion status.
- **Mandatory Fallback:** If Ollama is offline, unreachable, slow, or produces an error, gracefully returns the deterministic response with zero data loss.

### Component 7: `service.py`
Provides `ReasoningPipeline` and a ready-to-mount FastAPI `router`.

---

## 4. Integration Guide

### For Member 1 (FastAPI Backend in `backend/main.py`)
To integrate the reasoning module into the central FastAPI application, add just 2 lines:

```python
# In backend/main.py
from fastapi import FastAPI
from backend.reasoning import reasoning_router

app = FastAPI(title="CERBERUS-XA Intelligence Backend")

# Mount Member 4 reasoning routes
app.include_router(reasoning_router)
```

Available endpoints:
- `GET /reasoning/health`: System health and Ollama status check.
- `POST /reasoning/verify`: Full evidence verification pipeline (`ReasoningRequest` -> `ReasoningResponse`).
- `POST /reasoning/evaluate_reliability`: Standalone reliability scoring for evidence items.

### For Member 2 (Processor: Multimodal Extraction)
Supply evidence items conforming to `EvidenceItem`:
```python
from backend.reasoning import EvidenceItem, EvidenceMetadata, EvidenceModality, DirectnessLevel

evidence = EvidenceItem(
    id="EV-001",
    content="Flight certification specifies payload capacity of 15.5 kg.",
    modality=EvidenceModality.DOCUMENT,  # or SCAN, IMAGE, TABLE, RECORD, etc.
    directness=DirectnessLevel.PRIMARY,
    metadata=EvidenceMetadata(
        source_id="FAA-CERT-2024",
        filename="certification.pdf",
        page_number=4,
        section="Specifications",
        checksum_hash="sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    )
)
```

### For Member 3 (Knowledge Graph)
Supply relationship triples conforming to `KGRelationship`:
```python
from backend.reasoning import KGRelationship

kg_edge = KGRelationship(
    source_entity="Alpha-7",
    relation="has_certified_payload",
    target_entity="15.5 kg",
    confidence=0.98,
    evidence_ids=["EV-001"],
)
```

---

## 5. Verification & Testing

Execute the complete 56-test test suite from the project root:

```bash
python -m pytest backend/reasoning/tests -v
```

### Test Coverage Summary:
- **`test_audit_regressions.py`** (15 regression tests):
  - Bug 1: Identical numbers, equivalent values after unit normalization, truly different values, missing values, rounding tolerances, temporal shifts, distinct properties.
  - Bug 2: Claim status classification (`Extracted Claim`, `Evidence-Supported Claim`, `Corroborated Claim`, `Disputed Claim`, `Unverified Claim`, `Verified Fact`).
  - Bug 3: Explainable, deterministic confidence calculation with explicit derivation string.
  - Bug 4: Citation validation, invalid evidence rejection, zero-fabrication guarantees.
  - Bug 5: Malicious prompt injection neutralization and audit notice verification.
  - Bug 6: 100% offline-first execution with zero external network requirement.
  - Bug 7: FastAPI router mounting readiness verification.
- **`test_evidence_reliability.py`** (12 tests): Traceability, directness, corroboration, duplicate source exclusion, missing metadata safeguards, contradictory evidence, unassessed criteria, modality neutrality.
- **`test_conflict_analyzer.py`** (5 tests): Agreement, unit standardization, temporal differentiation, scope differentiation, unresolved conflict deadlocks.
- **`test_suspicion_detector.py`** (9 tests): Benign evidence, incomplete metadata, inconsistent dates, entity/unit mismatches, duplicate origins, OCR anomalies, upstream alterations, prompt injection detection.
- **`test_reasoning_engine.py`** (10 tests): Multi-source agreement, contradictory sources, co-origin discounting, temporal differentiation, partial answer conditions, insufficient evidence fallback, prompt injection neutralization, assumption auditing.
- **`test_citation_builder.py`** (10 tests): All 7 source types, supporting vs conflicting claims, multiple citations, zero-fabrication of page/file/source IDs, invalid reference catching, deduplication, structured dict serialization.
- **`test_llm_adapter.py`** (5 tests): Offline-first operation, connection failure fallback, timeout resilience, verification structure preservation, health checks.
- **`test_service_pipeline.py`** (5 tests): Health endpoint, full pipeline verification, Ollama graceful fallback, standalone reliability endpoint, adversarial empty inputs.

**Result:** **71 passed in 0.68s** (100% pass rate).
