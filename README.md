# 🛡️ CERBERUX-XA: AI-Powered Contradiction Detection System

A complete, production-grade AI system that ingests multimodal documents from disparate sources (**PDF, PNG/JPG OCR, Excel XLSX, CSV, TXT**), extracts structured claims using spaCy NER and high-precision NLP rules, normalizes entities, dimensions, and temporal intervals, extracts entity governance relationships, and **deterministically identifies contradictions** — preserving all conflicting values and source provenance with zero arbitrary winner selection.

---

## 🌟 Key Architecture & Capabilities

### 1. Robust Multimodal Ingestion & Advanced OCR
- **PDF Extraction**: Native PyMuPDF text and table extraction with graceful fallback when Tesseract is not installed.
- **Image OCR Preprocessing**: Image upscaling (bicubic interpolation for low-DPI scans), grayscale conversion, contrast enhancement, adaptive binarization, and multi-PSM fallback (`--psm 6` -> `--psm 3` -> `--psm 11`) with word-level confidence scoring and empty-text warnings.
- **Spreadsheets & CSV**: Supports both narrow/long format (`[Entity, Metric, Value, Unit, Period]`) and wide matrix formats (`[Entity, Metric, 2024, 2025, 2026]` or `[Entity, Date, Revenue, Profit, Production, Employees]`).
- **Plain Text**: Supports UTF-8, Latin-1, and CP1252 encodings.

### 2. High-Precision Entity & Fact Extraction
- **Indian Number Formats**: Accurately parses Indian comma notation (`INR 25,00,000`, `5,00,000`, `Rs. 1,50,00,000`, lakh, crore) alongside standard international notation without digit truncation.
- **Single Claim Guarantee**: Exact span deduplication prevents duplicate claims for the same numerical fact.
- **Dynamic Attribute Windowing**: Attributes are extracted from the immediate clause window, preventing multi-clause sentence confusion (e.g. distinguishing `85% capacity` from `INR 50,00,000 revenue` in the same sentence).
- **Modality Classification**: Distinguishes `actual` facts from `target`, `estimate`, and `quoted` statements.
- **Zero Hard-Coded Fallback**: Uses `"Unknown"` when an entity cannot be determined.

### 3. Entity Classification & Governance Relationships
- **Strict Entity Classification**:
  - `KPMG`, `PwC`, `Deloitte`, `EY`, and other auditing firms are classified strictly as **ORGANIZATION** (never `PERSON`).
  - `ABC Industries` and corporate entities are classified as **ORGANIZATION**.
  - `Sarah Jenkins` and `Robert Vance` are classified as **PERSON**.
  - **No Quantity Nodes for Names**: Quantity nodes (`QTY:...`) are strictly reserved for genuine numeric quantities and measurements; person and organization names never generate quantity nodes.
- **Entity-to-Entity & Person-to-Entity Relationships**:
  - `audited_by`: Connects organizations to auditing firms (e.g. `ABC Industries` $\xrightarrow{\text{audited\_by}}$ `KPMG`).
  - `executive_of`: Connects persons to their organizations (e.g. `Sarah Jenkins` $\xrightarrow{\text{executive\_of}}$ `ABC Industries`).
  - `subsidiary_of`: Connects subsidiary companies to their parent corporations.
  - `owned_by`: Connects companies to their parent owners and holding groups.

### 4. Dimensional & Temporal Interval Normalization
- **Dimensional Equivalence**: Values are normalized into canonical dimension base units:
  - `mass`: base unit `g` (`5 kg` == `5,000 g`)
  - `length`: base unit `m` (`1 km` == `1,000 m`)
  - `volume`: base unit `mL` (`1 L` == `1,000 mL`)
  - `currency`: ISO canonical code (`₹25 lakh` == `INR 25,00,000`)
- **Interval-Based Temporal Overlap**: Rigorous interval arithmetic for:
  - Calendar Months (`2026-01`)
  - Quarters (`2026-Q1` spans Jan–Mar; does NOT overlap with Q2)
  - Financial Years (`FY2025-26` spans April 2025 to March 2026)
  - Calendar Years (`2026` spans Jan–Dec)

### 5. Deterministic Contradiction Detection Engine
- Detects **Numerical Contradictions** (configurable tolerance, e.g. 2%).
- Detects **Textual Contradictions**:
  - Semantic antonyms (`operational` vs `shutdown`, `compliant` vs `non-compliant`).
  - Conflicting leadership names for identical organizations and periods (`CEO: Sarah Jenkins` vs `CEO: Robert Vance`).
- **Evidence-Based Contradiction Confidence**: Six-component granular breakdown (`extraction`, `entity_match`, `period_match`, `unit_normalization`, `source_reliability`, `value_divergence`) plus human-readable explanation.
- **OCR Confidence Gating**: Claims with OCR confidence below threshold (default 0.60) routed to `status="UNCERTAIN"` and `verdict="uncertain"`, never generating contradiction edges.
- **Duplicate & Inconsistency Detection** (`src/duplicates.py`):
  - Exact duplicates (same entity, attribute, period, normalized value).
  - Near-duplicates (minor scalar variation <= 1%).
  - Intra-document inconsistencies (conflicting claims within the same source document).
- Flags **Uncertainty** when evidence is single-source, OCR quality is poor, or dimensions are incompatible.
- **Zero Winner Bias**: Displays all conflicting values with full source references.

### 6. Enriched Knowledge & Conflict Graph (NetworkX)
- **Node Types**: `entity`, `person`, `date`, `quantity`, `claim`, `source`.
- **Edge Types**:
  - Structural: `has_claim`, `from_source`, `has_date`, `has_quantity`, `attributed_to`.
  - Relational: `contradicts` (red), `consistent_with` (green), `uncertain_with` (amber).
  - Governance: `audited_by`, `executive_of`, `subsidiary_of`, `owned_by`.
- **Source Reliability Modulation**: `set_source_reliability(source_id, score, reason)` hook modulates node attributes and downweights confidence for lower-trust sources.
- **Strict Logic Safeguards**:
  - `contradicts` edges are added **ONLY** between claim pairs whose values genuinely disagree.
  - Identical values **NEVER** receive a `contradicts` edge.
  - Claims that agree receive `consistent_with` edges.
- **Interactive Visualization**: Full Plotly network graph with export to **JSON** and **GraphML**.

### 7. Streamlit Executive Dashboard (7 Complete Tabs)
1. 📊 **Executive Overview**: 5 KPI metric cards (Documents, Claims, Contradictions, Duplicates, Graph Nodes), status breakdown chart, high-priority contradiction alert banners, 1-click sample dataset runner.
2. 📁 **Document Ingestion & Processing**: Multi-file drag-and-drop, format validation, and quick-load sample data.
3. 📋 **Extracted Claims & Attributes**: Searchable and filterable claim table with CSV export.
4. ⚡ **Contradiction Analysis**: Side-by-side evidence inspection preserving all sources with evidence breakdown metrics and human-readable reasoning.
5. 🕸️ **Knowledge & Conflict Graph**: Interactive Plotly graph and exports (JSON & GraphML).
6. 🔍 **Source Traceability & Provenance**: Complete provenance inspector mapping each claim to source, page, excerpt, and conflict status.
7. 📄 **Reports & Audit Export**: One-click download of PDF, CSV, and JSON audit reports.

---

## 🚀 Execution & Usage

### 1. Launch the Streamlit Web Application

```powershell
Set-Location "c:\Users\HARSHITA G\OneDrive\Desktop\CERBERUX-XA\contradiction-detection"
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501
```
Then open your browser at: **`http://localhost:8501`**

### 2. Run the Command-Line Pipeline

```powershell
Set-Location "c:\Users\HARSHITA G\OneDrive\Desktop\CERBERUX-XA\contradiction-detection"
.\.venv\Scripts\python.exe main.py data/sample_docs/sample_report.pdf data/sample_docs/sample_chart_receipt.png data/sample_docs/erp_production.xlsx data/sample_docs/erp_warehouse.csv data/sample_docs/external_audit.txt --output reports
```

### 3. Run the Packaging Script for Submission

```powershell
Set-Location "c:\Users\HARSHITA G\OneDrive\Desktop\CERBERUX-XA\contradiction-detection"
.\.venv\Scripts\python.exe scripts/make_submission.py
```
Generates a clean submission package `cerberux_xa_submission.zip` (~122 KB compressed, ~378 KB uncompressed) containing all source code, configs, test suites, and sample data while strictly excluding `.venv/`, `__pycache__/`, `.pytest_cache/`, and temporary artifacts.

### 4. Run the Automated Test Suite

```powershell
Set-Location "c:\Users\HARSHITA G\OneDrive\Desktop\CERBERUX-XA\contradiction-detection"
.\.venv\Scripts\python.exe -m pytest -v
```

---

## 🧪 Verification & Test Results

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.2.2, pluggy-1.7.0
rootdir: C:\Users\HARSHITA G\OneDrive\Desktop\CERBERUX-XA\contradiction-detection
plugins: cov-5.0.0
collected 161 items

tests/test_advanced_contradiction_and_graph.py ...............           [  9%]
tests/test_audit_requirements.py ...........................             [ 26%]
tests/test_contradiction_detector.py ..............                      [ 34%]
tests/test_duplicates.py ........                                        [ 39%]
tests/test_entity_and_claims.py .....................                    [ 52%]
tests/test_extractor_generalization.py ................................. [ 73%]
tests/test_extractors.py .............                                   [ 81%]
tests/test_graph_and_reports.py ...........                              [ 88%]
tests/test_integration.py ....                                           [ 90%]
tests/test_ocr_and_confidence.py .......                                 [ 95%]
tests/test_real_world_validation.py .                                    [ 95%]
tests/test_source_reliability_and_hooks.py .......                       [100%]

====================== 161 passed, 5 warnings in 12.54s =======================
```

---

## 📦 Fresh Setup from Scratch (Clean Environment)

To reproduce or deploy this project in a fresh Python 3.11.9 environment:

```powershell
# 1. Create a fresh virtual environment
python -m venv .venv

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install locked dependencies
pip install -r requirements.txt

# 5. Download spaCy English model
python -m spacy download en_core_web_sm

# 6. Verify full test suite
python -m pytest -v
```

**Clean Packaging Size (excluding `.venv`, caches, and git):** `~122 KB` zip (`~378 KB` uncompressed across 59 files).
