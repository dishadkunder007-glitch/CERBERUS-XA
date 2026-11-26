# CERBERUS-XA — Multimodal Data Processing Module (Member 2)

> **High-Performance Local Evidence Extraction & Normalization Engine**  
> Part of the 24-hour hackathon project: **CERBERUS-XA — Multimodal Evidence Graph & Conflict-Aware Reasoning**.

---

## 📌 Overview

This module serves as the primary data ingestion and evidence extraction layer for CERBERUS-XA. It processes heterogenous multi-format files (**PDF**, **Scanned PDF**, **JPG**, **JPEG**, **PNG**, **XLSX**, **XLS**, and **CSV**) locally and normalizes all extracted assertions, metrics, and tabular rows into a **standardized JSON format** for downstream Knowledge Graph construction and Conflict-Aware Reasoning modules (Members 1, 3, etc.).

### ✨ Core Capabilities

- **Blazing Fast Local Execution**: Powered by PyMuPDF (C++ backend), vectorized Pandas, and RapidOCR (PaddleOCR ONNX engine), completing full test suites with zero cloud API dependencies.
- **Intelligent Scanned PDF Detection**: Automatically differentiates between native vector PDFs and scanned image PDFs, invoking OCR only when necessary.
- **Dual-Engine Image Preprocessing & OCR**: Uses OpenCV for noise reduction and contrast enhancement alongside RapidOCR (PaddleOCR ONNX) with Tesseract fallback. No external installers or admin rights needed!
- **Structural Integrity for Tables**: Extracts multi-sheet Excel files and CSVs while preserving row indexes, column headers, units, and never hallucinating or inventing missing values.
- **Strict Evidence Traceability**: Retains source filename, page number, sheet name, row index, column name, and extraction confidence.
- **Multiple Integration Modes**: Exposes both a REST API (FastAPI) and clean Python programmatic imports.

---

## 📐 Standardized JSON Output Schema

Every processed file produces a consistent structure matching the CERBERUS-XA evidence model:

```json
{
  "source": "report.pdf",
  "source_type": "document",
  "content": [
    {
      "claim": "Production quantity",
      "value": "5000",
      "unit": "units",
      "page": 1,
      "sheet": null,
      "row": null,
      "column": null,
      "confidence": null
    }
  ],
  "metadata": {
    "filename": "report.pdf",
    "format": "pdf",
    "file_size_bytes": 14205,
    "total_pages": 2,
    "is_scanned": false,
    "ocr_applied": false,
    "items_extracted": 1,
    "processing_time_ms": 12.4
  }
}
```

### Field Definitions

| Field | Type | Description |
|---|---|---|
| `source` | string | Filename or document identifier. |
| `source_type` | string | `"document"`, `"image"`, or `"table"`. |
| `content` | array | List of extracted standardized evidence objects. |
| `content[].claim` | string | Extracted textual assertion, header, or field name. |
| `content[].value` | string / null | Extracted value (normalized, never invented). |
| `content[].unit` | string / null | Measurement unit (e.g., `units`, `$`, `kW`, `%`, `°C`). |
| `content[].page` | integer / null | 1-based page number (for documents). |
| `content[].sheet` | string / null | Sheet name (for multi-sheet spreadsheets). |
| `content[].row` | integer / null | 1-based row index (for tabular datasets). |
| `content[].column` | string / null | Column name (for tabular datasets). |
| `content[].confidence` | float / null | OCR extraction confidence (0.0 to 1.0) where available. |
| `metadata` | object | Format details, performance metrics, and non-fatal warnings. |

---

## 🚀 Quickstart

### 1. Installation

```bash
pip install -r requirements.txt
```

*(Optional)* If OCR is required on your machine, install Tesseract OCR:
- **Windows**: `winget install --id UB-Mannheim.TesseractOCR` (or configure path via `TESSERACT_CMD` environment variable).
- **Linux/Ubuntu**: `sudo apt-get install tesseract-ocr`
- **macOS**: `brew install tesseract`

### 2. Run Test Suite

To verify all extractors independently (PDF, Scanned PDF, Images, Excel, CSV, Edge cases, API):

```bash
python -m pytest tests/test_multimodal.py -v
```

### 3. Launch FastAPI Server

```bash
uvicorn multimodal_processor.api:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🌐 REST API Endpoints

### 1. `GET /health`
Returns module status, supported formats, and OCR engine availability.

```bash
curl -X GET "http://localhost:8000/health"
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "module": "CERBERUS-XA Multimodal Data Processor",
  "version": "1.0.0",
  "supported_formats": [".pdf", ".jpg", ".jpeg", ".png", ".xlsx", ".xls", ".csv"],
  "ocr_engine_available": true,
  "timestamp": "2026-11-25T07:45:00.000000Z"
}
```

---

### 2. `POST /process_file` & `POST /process-file`
Extract evidence from a single file using **either** JSON payload or multipart form upload.

#### Option A: JSON Request
```bash
curl -X POST "http://localhost:8000/process_file" \
     -H "Content-Type: application/json" \
     -d '{
       "file_path": "multimodal_processor/samples/sample_report.pdf"
     }'
```
*Alternatively, pass base64 or inline data:*
```bash
curl -X POST "http://localhost:8000/process_file" \
     -H "Content-Type: application/json" \
     -d '{
       "filename": "metrics.csv",
       "content": "Metric,Value,Unit\nTurbine_Output,500,kW"
     }'
```

#### Option B: Multipart File Upload
```bash
curl -X POST "http://localhost:8000/process-file" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@multimodal_processor/samples/sample_report.pdf"
```

---

### 3. `POST /process_batch` & `POST /process-batch`
Process multiple multimodal files concurrently using **either** JSON payload or multipart file uploads.

#### Option A: JSON Request (`POST /process_batch`)
Accepts file paths on disk, inline text, or base64-encoded files:
```bash
curl -X POST "http://localhost:8000/process_batch" \
     -H "Content-Type: application/json" \
     -d '{
       "files": [
         "multimodal_processor/samples/sample_report.pdf",
         "multimodal_processor/samples/sample_inventory.csv"
       ]
     }'
```
*Or using detailed file objects:*
```bash
curl -X POST "http://localhost:8000/process_batch" \
     -H "Content-Type: application/json" \
     -d '{
       "files": [
         {
           "filename": "sample_chart.png",
           "file_path": "multimodal_processor/samples/sample_chart.png"
         },
         {
           "filename": "dynamic.csv",
           "content": "Claim,Value,Unit\nProduction,5000,units"
         }
       ]
     }'
```

#### Option B: Multipart File Upload (`POST /process-batch`)
```bash
curl -X POST "http://localhost:8000/process-batch" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@multimodal_processor/samples/sample_report.pdf" \
     -F "files=@multimodal_processor/samples/sample_inventory.csv"
```

**Consolidated Batch Response (200 OK):**
```json
{
  "total_files": 2,
  "successful": 2,
  "failed": 0,
  "results": [ ... ],
  "errors": []
}
```

---

## 🐍 Python Programmatic Usage (For CERBERUS-XA Teammates)

Other team members can directly import and call the extraction logic inside their Python modules:

```python
from multimodal_processor import process_file_path, process_file_data

# Process from file path
result = process_file_path("path/to/evidence.xlsx")
for item in result.content:
    print(f"[{item.sheet} R{item.row}] {item.claim}: {item.value} {item.unit or ''}")

# Process from in-memory bytes
with open("document.pdf", "rb") as f:
    result = process_file_data(f.read(), filename="document.pdf")
```

---

## 📂 Project Directory Layout

```
CERBERUS-XA/
├── conftest.py
├── requirements.txt
├── README.md
├── multimodal_processor/
│   ├── __init__.py            # Package exports
│   ├── config.py              # Configuration & path detection
│   ├── models.py              # Pydantic JSON schemas
│   ├── utils.py               # Metric & unit extraction helpers
│   ├── ocr_engine.py          # OpenCV preprocessing & Tesseract wrapper
│   ├── pdf_processor.py       # PyMuPDF text & scanned PDF handler
│   ├── image_processor.py     # JPG/PNG OpenCV + OCR pipeline
│   ├── table_processor.py     # Excel & CSV Pandas/OpenPyXL parser
│   ├── processor.py           # Unified dispatch router
│   ├── api.py                 # FastAPI service endpoints
│   ├── create_samples.py      # Sample test file generator
│   └── samples/               # Comprehensive test fixtures
│       ├── sample_report.pdf
│       ├── sample_scanned.pdf
│       ├── sample_chart.png
│       ├── sample_receipt.jpg
│       ├── sample_metrics.xlsx
│       └── sample_inventory.csv
└── tests/
    ├── __init__.py
    └── test_multimodal.py     # 33 comprehensive unit, JSON validation, and integration tests
```
