# CHANGELOG — CERBERUX-XA Contradiction Detection System

All notable changes and upgrades implemented in accordance with Member 3 engineering scope.

---

## [2.1.0] - 2026-11-25

### 1. Resolved Missed Conflicts in Real-World Validation
- **Root Cause Fix 1 (Address Noise):** Prevented address numbers (e.g. "Sector 4" in `filing_q1.txt`) from falsely registering as production claims. Bare numbers with no units and no metric keywords are now safely ignored.
- **Root Cause Fix 2 (Leadership Attribute Canonicalization):** Canonicalized leadership roles (`ceo`, `chief executive officer`, `managing director`, `executive`) so that filing CEO (`Sarah Jenkins`) and audit executive (`Robert Vance`) evaluate in the same comparison group.
- **Root Cause Fix 3 (Compliance Pattern & Negation):** Expanded `_COMPLIANCE_PATTERN` to support `rating` and `assessment`, with explicit negation handling (`not compliant`, `failed to comply`, `non-compliant`).
- **Root Cause Fix 4 (Mass / Weight Metric Mapping):** Mapped `kg`, `g`, `tonne` units to canonical `weight` attribute, ensuring dimensional consistency between filing (5,000 kg) and ERP (5,000,000 g).
- **Result:** Successfully detects all 5 real-world conflicts (`production`, `revenue`, `executive`, `status`, `compliance`).

### 2. Extractor Generalization (>=30 New Tests)
- **Entity Disambiguation:** Prioritizes corporate organizations over person names in `_extract_primary_entity` (e.g., `Tata Motors Ltd` is primary corporate entity, not `Ratan Tata`).
- **Currency & Scale Symbols:** Comprehensive parsing for `US$`, `USD`, `€`, `EUR`, `£`, `GBP`, `¥`, `INR`, `₹`, `Rs.`, along with scale multipliers (`k`, `thousand`, `lakh`, `crore`, `million`, `mn`, `billion`, `bn`, `trillion`).
- **Leadership Phrasings:** Supported multiple grammatical constructions ("X serves as CEO", "X is the CEO", "X was appointed CEO", "Led by X", "Chief Executive Officer: X", "Sarah Jenkins, Managing Director").
- **Vocabulary & Negation:** Controlled vocabulary for compliance (`certified`, `approved`, `non-compliant`, `failed`) and operational status (`operational`, `shutdown`, `suspended`, `dormant`).
- **Tabular & Prose Formats:** Validated across wide tables, narrow tables, bullet points, and key-value forms.

### 3. OCR Confidence Threshold & Noise Rejection
- Added `ocr_confidence: float = 1.0` to `RawClaim` and `Claim`.
- Propagated word-level OCR confidence from Tesseract and PDF extractors.
- Claims with `ocr_confidence < 0.60` (configurable) are excluded from hard contradictions and marked `status="UNCERTAIN"` with `verdict="uncertain"`.
- Rejected ungrounded bare numbers lacking units and contextual keywords.

### 4. Evidence-Based Contradiction Confidence
- Eliminated all arbitrary/fake confidence formulas.
- Implemented 6-component weighted evidence breakdown:
  - `extraction`: `min(ocr_confidence) * min(extraction_confidence)`
  - `entity_match`: alignment score between matched entity names
  - `period_match`: exact match (1.0) vs overlapping intervals (0.85)
  - `unit_normalization`: base unit agreement vs cross-unit dimensional conversion
  - `source_reliability`: average reliability of conflicting sources
  - `value_divergence`: normalized discrepancy factor
- Stored in `confidence_breakdown` dict and summarized in human-readable `confidence_explanation`.

### 5. Duplicate and Intra-Document Inconsistency Module (`src/duplicates.py`)
- Created `src/duplicates.py` exposing `DuplicateReport` and `detect_duplicates()`.
- **Exact Duplicates:** Groups identical facts repeated across documents.
- **Near-Duplicates:** Identifies values within relative tolerance (default 5%) and textual paraphrases via token sort ratio.
- **Intra-Document Inconsistencies:** Automatically flags conflicting values or statuses occurring within the *very same* document.

### 6. Source Reliability Hook
- Added `set_source_reliability(source_id, score, reason)` on `GraphBuilder` and `ContradictionDetector`.
- Attached `source_reliability` and `source_reliability_reason` to `NODE_SOURCE` in the graph.
- Integrated source reliability directly into contradiction confidence scoring.

### 7. Teammate Integration Hooks
- Added `flags: list[str]` to `RawClaim` and `Claim` for teammate annotations.
- Added `verdict: str` to `ContradictionResult` supporting `"contradiction"`, `"consistent"`, `"uncertain"`, and `"insufficient_evidence"`.
- Tested adversarial prompt injection resistance: malicious instructions embedded in documents cannot override deterministic detector logic.

### 8. Configuration, Logging & Packaging
- Added `config/attribute_config.yaml` for per-attribute tolerances and confidence thresholds.
- Added `config/controlled_vocabulary.yaml` for compliance and status terms.
- Added `scripts/make_submission.py` producing a clean packaging ZIP archive (~400 KB) excluding `.venv/`, `__pycache__/`, `.pytest_cache/`, and output artifacts.
