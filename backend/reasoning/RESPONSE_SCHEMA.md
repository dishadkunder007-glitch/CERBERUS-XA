# CERBERUS-XA: Member 4 (AI Reasoning & Evidence Verification) Response Schema Specification

> [!CAUTION]
> **FROZEN FOR DEMO; DO NOT CHANGE WITHOUT TELLING MEMBER 1.**
> Any modifications to route paths, payload structures, or field names will break frontend and inter-member contracts.

---

## 1. Overview & Endpoints

Member 4 provides two primary deliberation and verification endpoints mounted under `/reasoning`:

1. `POST /reasoning/verify`: Conflict-aware multi-stage evidential verification and reasoning engine.
2. `POST /reasoning/evaluate_reliability`: Standalone evidential reliability and provenance scoring.
3. `GET /reasoning/health`: Module health status and local Ollama availability.

---

## 2. `POST /reasoning/verify` Response Contract

### Top-Level Schema (`ReasoningResponse`)

| Field | Type | Description |
|---|---|---|
| `question` | `string` | The evaluated query or proposition. |
| `status` | `enum` | Core reasoning status: `ANSWERED`, `PARTIALLY_ANSWERED`, `CONFLICTED`, `INSUFFICIENT_EVIDENCE`. |
| `conclusion_type` | `enum` | Semantic conclusion category: `supported`, `refuted`, `inconclusive`, `insufficient_evidence`, `conflicting`. |
| `answer` | `string` | Detailed natural-language deliberation answer. |
| `summary` | `string` | High-level conclusion summary. |
| `supporting_claims` | `List[Claim]` | Claims verified to support the proposition. |
| `opposing_claims` | `List[Claim]` | Claims contradicting or refuting the proposition. |
| `unresolved_conflicts` | `List[ConflictPair]` | Active evidential contradictions that could not be resolved. |
| `reasoning_steps` | `List[string]` | Transparent step-by-step reasoning explanations across all 7 deliberation stages. |
| `assumptions` | `List[string]` | Explicit domain or data assumptions made during reasoning. |
| `limitations` | `List[string]` | Evidentiary gaps, missing metadata, or epistemic boundaries. |
| `confidence` | `float` (0.0–1.0) | Epistemic confidence score. |
| `confidence_score` | `float` (0.0–1.0) | Calibrated confidence score (alias for `confidence`). |
| `confidence_explanation` | `string` | Mathematical breakdown of confidence derivation. |
| `is_insufficient_evidence`| `bool` | True if evidence volume or relevance was inadequate. |
| `facts` | `List[string]` | Verified factual statements backed by evidence. |
| `inferences` | `List[string]` | Logical deductions derived from facts. |
| `unknowns` | `List[string]` | Explicitly flagged unverified properties. |
| `supporting_evidence_ids` | `List[string]` | List of evidence IDs confirming the answer. |
| `opposing_evidence_ids` | `List[string]` | List of evidence IDs contradicting the answer. |
| `evidence_reliability` | `Dict[str, Result]` | Reliability scoring breakdown per evidence item. |
| `conflicts` | `List[ConflictPair]` | All analyzed pairs of claims (resolved and unresolved). |
| `suspicion_indicators` | `List[Indicator]` | Cataloged suspicion indicators across sources. |
| `citations` | `List[Citation]` | Traceable bibliographical citations with non-null `source_type`. |
| `claim_citations` | `List[ClaimCitation]` | Fine-grained citations mapped per claim. |
| `reasoning_mode` | `string` | `"deterministic"`, `"ollama_augmented"`, or `"ollama_partial"`. |
| `llm_attempted` | `boolean` | `true` if local LLM generation was initiated. |
| `llm_synthesis_used` | `boolean` | `true` only when LLM output was accepted (augmented or partial) into `answer`. |
| `audit_trail` | `List[string]` | Cryptographic and execution audit records. |

### Nested Structure: `Citation`
```json
{
  "citation_id": "[1]",
  "evidence_id": "EV-001",
  "source_id": "FAA-TCDS",
  "filename": "alpha7_specs.pdf",
  "source_type": "document",
  "format": "pdf",
  "page_number": 4,
  "section": "Specifications",
  "location_locator": "Page 4, Section 'Specifications'",
  "formatted_citation": "[1] Source: FAA-TCDS | File: alpha7_specs.pdf | Type: document | Format: pdf | Page 4 | Section 'Specifications' | Evidence ID: EV-001",
  "verifiable_metadata": {
    "evidence_id": "EV-001",
    "source_id": "FAA-TCDS",
    "filename": "alpha7_specs.pdf",
    "source_type": "document",
    "format": "pdf",
    "page_number": "4",
    "checksum_hash": "a1b2c3d4..."
  }
}
```

### Traceability Metadata: `EvidenceMetadata.source_type`, `citation.source_type`, and `citation.format`
- **`EvidenceMetadata.source_type`**: Optional string on incoming evidence items allowing upstream modules (e.g. processor/ingestion) to explicitly declare the underlying source format (`document`, `image`, `table`, `structured_data`, `pdf`, `scan`, `csv`, etc.).
- **`citation.source_type`**: Required non-null string on every generated `Citation` object. Populated deterministically with the modality enum value (`document`, `image`, `table`, `structured_data`) ensuring UI consumers (Member 1) always receive a reliable source classification for visual iconography and badges.
- **`citation.format`**: Optional string on every generated `Citation` object providing the detailed file format/extension (e.g. `pdf`, `csv`, `png`, `tiff`, `docx`, `json`). Member 1's UI can use this for format-specific download links or badges.

---

## 3. Local Model Specification (`qwen2.5:7b-instruct`)

- **Exact Model Tag**: `qwen2.5:7b-instruct` (Qwen 2.5 7B Instruct)
- **License**: Apache 2.0 (*from public model card, NOT verified on this host*; pending `ollama show qwen2.5:7b-instruct --license`)
- **Fine-Tuning**: Base model, zero domain fine-tuning (pre-trained, instruction-tuned)
- **Role in CERBERUS-XA**: Fluent natural-language rephrasing and evidential summarization of pre-verified facts. It does not perform autonomous reasoning, does not invent facts, does not arbitrate evidential conflicts, and cannot alter deterministic epistemic status or confidence scores.
- **Fallback Guarantees**: Offline-first, mandatory deterministic fallback. If Ollama is offline, unreachable, times out (configurable via `CERBERUS_OLLAMA_TIMEOUT`, default 60.0s), or if output exhibits grounding violations (unsupplied citation IDs, ungrounded numbers/units, insufficient lexical overlap < 0.30, contradictory status assertions), the engine immediately falls back to rule-based deterministic outputs.
- **Resource Footprint**:
  - *Parameters*: 7.61 billion (*from public model card, NOT verified on this host*; pending `ollama show qwen2.5:7b-instruct`)
  - *Context Window*: 4,096 tokens (`num_ctx = 4096`)
  - *Disk Storage*: ~4.7 GB (Q4_K_M GGUF format; *from public model card, NOT verified on this host*)
  - *RAM / VRAM*: ~5.5 GB VRAM (GPU offload) or ~8.0 GB system RAM (CPU execution; *from public model card, NOT verified on this host*)
  - *Host Environment Status*: `ollama` CLI not installed on host machine (`The term 'ollama' is not recognized`). Live Qwen execution status: BLOCKED. All LLM-path integration components are MOCK-VERIFIED.

---

## 3. `POST /reasoning/evaluate_reliability` Response Contract

### Response Schema
```json
{
  "evidence_reliability": [
    {
      "evidence_id": "EV-001",
      "breakdown": {
        "evidence_id": "EV-001",
        "reliability_score": 83.0,
        "reliability_label": "High",
        "overall_score": 0.83,
        "criteria_scores": {
          "source_authority": {
            "criterion_name": "source_authority",
            "score": 0.90,
            "weight": 0.25,
            "weighted_score": 0.225,
            "is_assessed": true,
            "rationale": "Direct official regulatory source."
          },
          "traceability": {
            "criterion_name": "traceability",
            "score": 0.90,
            "weight": 0.20,
            "weighted_score": 0.180,
            "is_assessed": true,
            "rationale": "Filename and page number supplied."
          },
          "corroboration": {
            "criterion_name": "corroboration",
            "score": 0.60,
            "weight": 0.20,
            "weighted_score": 0.120,
            "is_assessed": true,
            "rationale": "Single primary source."
          },
          "freshness": {
            "criterion_name": "freshness",
            "score": 0.80,
            "weight": 0.15,
            "weighted_score": 0.120,
            "is_assessed": true,
            "rationale": "Recent certification record."
          },
          "directness": {
            "criterion_name": "directness",
            "score": 0.90,
            "weight": 0.10,
            "weighted_score": 0.090,
            "is_assessed": true,
            "rationale": "Primary empirical observation."
          },
          "contextual_coherence": {
            "criterion_name": "contextual_coherence",
            "score": 0.90,
            "weight": 0.10,
            "weighted_score": 0.090,
            "is_assessed": true,
            "rationale": "Internally coherent terminology."
          }
        },
        "reasons": [
          "Calculated reliability score of 0.83 using weighted assessment across 6 criteria."
        ],
        "missing_information": [],
        "limitations": []
      }
    }
  ]
}
```

---

## 4. Migration & Evolution Log (Changes Since v1)

1. **Flat Facts vs Nested Conclusion**:
   - In v1, responses presented a flat list of strings in `facts` and a single float `confidence`.
   - In v2, responses support both flat backward-compatible fields (`facts`, `confidence`, `confidence_score`) and structured claim-level breakdowns (`verified_facts`, `disputed_claims`, `supporting_claims`, `opposing_claims`).
2. **Criteria Count (5 -> 6 Dimensions)**:
   - v1 evaluated 5 basic criteria (`provenance`, `directness`, `corroboration`, `consistency`, `completeness`).
   - v2 evaluates 6 standardized evidential criteria:
     1. `source_authority` / `provenance`
     2. `traceability`
     3. `corroboration` (with co-origin deduplication)
     4. `freshness` (temporal recency)
     5. `directness` (primary vs secondary vs hearsay)
     6. `contextual_coherence` / `consistency`
3. **Evidence Reliability Collection Structure (Dict -> List)**:
   - v1 returned a raw dictionary map `{ "<evidence_id>": { ... } }`.
   - v2 returns a normalized list `{"evidence_reliability": [ { "evidence_id": ..., "breakdown": ... } ]}` for uniform JSON serialization and pagination support in Member 1's UI.
4. **Non-Null Source Type Modality Guarantee**:
   - `citation.source_type` is now strictly populated from evidence modality (`document`, `image`, `table`, `structured_data`).
   - Null values for known source types are strictly prevented.

---

## 5. Formal Changelog

### Version 2.3.0 — 2026-11-25
- **`llm_attempted` & `llm_synthesis_used` Added**: Added `llm_attempted` (`bool`) indicating whether LLM generation was invoked, and `llm_synthesis_used` (`bool`) set to `true` strictly when natural language synthesis was accepted into the final answer. **Note: Member 1 must be told of these new fields for UI status badges.**
- **`ollama_partial` Reasoning Mode**: Supported sentence-level filtering where ungrounded sentences are pruned while valid grounded sentences are retained, labeling `reasoning_mode` as `"ollama_partial"`.
- **Preponderance Constant Documentation**: Formally clarified preponderance thresholds: `PREPONDERANCE_HIGH_THRESHOLD = 0.70`, `PREPONDERANCE_LOW_THRESHOLD = 0.50`, and `PREPONDERANCE_MIN_SCORE_GAP = 0.25`.
- **Unit Normalization & Evidence ID Stripping**: Added canonical unit mapping and evidence identifier stripping before token extraction.

### Version 2.2.0 — 2026-11-25
- **`citation.source_type` Reverted to Modality**: Reverted `citation.source_type` from descriptive format strings (e.g. `"PDF document"`) strictly to the modality enum value (`document`, `image`, `table`, `structured_data`) to maintain inter-member consistency across CERBERUS-XA.
- **`citation.format` Added**: Added separate `citation.format` field (e.g. `"pdf"`, `"csv"`, `"png"`, `"tiff"`) explicitly carrying the file format/extension. **Note: Member 1 must be informed of this addition.**
- **General Grounding Validator**: Replaced keyword-specific injection defense with general entity, attribute, and numeric grounding validation against verified facts.
- **Evidence Breakout Escaping**: Added prompt injection breakout escaping for `"""` and XML delimiter tags before untrusted evidence prompt insertion.
- **Model Specification Documented**: Formally documented `qwen2.5:7b-instruct` specifications, Apache 2.0 license, zero fine-tuning, deterministic fallback role, and resource footprint.
- **Demo Freshness Definition**: Updated demo output verification to assert match after ignoring `request_id`.

### Version 2.1.0 — 2026-11-25
- **`EvidenceMetadata.source_type` Added**: Upstream evidence ingestors can supply explicit format strings (`pdf`, `scan`, `image`, `table`, `csv`, `record`, `text`).
- **`citation.source_type` Non-Null Guarantee**: Ensured `citation.source_type` is populated across all modalities (`document`, `image`, `table`, `structured_data`).
- **Preponderance Gap Hardening**: Enforced `PREPONDERANCE_MIN_SCORE_GAP = 0.25` alongside high (0.70) and low (0.50) thresholds.
- **Untrusted Wrapping & Injection Rejection**: Wrapped evidence inside `<untrusted_evidence>` tags and hardened Ollama synthesis against numeric and textual injection overrides.
- **Modality Validation Hardening**: Unrecognized modalities (e.g. `video`) strictly reject with HTTP 422 `ValidationError` rather than falling back silently.

