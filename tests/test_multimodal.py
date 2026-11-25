import io
import asyncio
from pathlib import Path
import pytest
from fastapi import UploadFile, HTTPException
from starlette.requests import Request
import pandas as pd
import pymupdf

from multimodal_processor.models import (
    StandardExtractionResult,
    BatchExtractionResult,
    ContentItem,
    BatchProcessRequest,
    BatchFileItem,
    SingleFileProcessRequest
)
from multimodal_processor.processor import (
    process_file_data,
    process_file_path,
    process_pdf,
    process_image,
    process_excel,
    process_csv
)
from multimodal_processor.api import (
    app,
    health_check,
    process_file_endpoint,
    process_file_json,
    process_batch_endpoint,
    process_batch_json,
    root_redirect,
    docs_slash_redirect,
    redoc_slash_redirect,
    MAX_FILE_SIZE_BYTES
)
from multimodal_processor.utils import (
    extract_metric_from_text,
    split_into_sentences,
    deduplicate_content_items
)

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "multimodal_processor" / "samples"

# ============================================================================
# 1. Claim Segmentation & Extraction Quality Tests
# ============================================================================

def test_claim_word_preservation_no_truncation():
    """Verify that auxiliary verb stripping does not truncate real words ending in s/t/a/w."""
    test_cases = [
        ("Limit was 85", "Limit", "85", None),
        ("Weight was 45 kg", "Weight", "45", "kg"),
        ("Status is Active", "Status", "Active", None),
        ("Cost was $500", "Cost", "500", "$"),
        ("Basis reached 12 %", "Basis", "12", "%"),
    ]
    for raw_text, exp_claim, exp_val, exp_unit in test_cases:
        claim, val, unit = extract_metric_from_text(raw_text)
        assert claim == exp_claim, f"Expected claim '{exp_claim}', got '{claim}'"
        assert val == exp_val, f"Expected value '{exp_val}', got '{val}'"
        assert unit == exp_unit, f"Expected unit '{exp_unit}', got '{unit}'"

def test_deduplication_of_claims():
    """Verify deduplication removes exact duplicates while preserving distinct items."""
    items = [
        ContentItem(claim="Production quantity", value="5000", unit="units", page=1),
        ContentItem(claim="Production quantity", value="5000", unit="units", page=1),  # duplicate
        ContentItem(claim="Production quantity", value="5000", unit="units", page=2),  # different page
        ContentItem(claim="Revenue", value="1000", unit="$", page=1),
    ]
    deduped = deduplicate_content_items(items)
    assert len(deduped) == 3
    assert deduped[0].page == 1
    assert deduped[1].page == 2
    assert deduped[2].claim == "Revenue"

def test_sentence_splitting_with_abbreviations_and_lists():
    """Verify sentence splitter protects abbreviations, decimals, and numbered items."""
    text = (
        "Operating limit was 85.5 °C. e.g. 100 units were tested.\n"
        "1. First sensor was active.\n"
        "2. Second sensor was standby."
    )
    sentences = split_into_sentences(text)
    assert len(sentences) >= 3
    assert any("85.5 °C" in s for s in sentences)
    assert any("First sensor" in s for s in sentences)

# ============================================================================
# 2. PDF Processing Tests (Digitally Generated, Scanned, Math, Tables)
# ============================================================================

def test_pdf_processing():
    """Verify normal multi-page PDF text extraction and page references."""
    pdf_path = SAMPLES_DIR / "sample_report.pdf"
    assert pdf_path.exists(), "Sample PDF must exist"
    
    data = pdf_path.read_bytes()
    res = process_pdf(data, filename=pdf_path.name)
    
    assert isinstance(res, StandardExtractionResult)
    assert res.source == "sample_report.pdf"
    assert res.source_type == "document"
    assert res.metadata["format"] == "pdf"
    assert res.metadata["total_pages"] == 2
    assert len(res.content) > 0
    
    claims = [c.claim for c in res.content]
    units = [c.unit for c in res.content if c.unit]
    pages = [c.page for c in res.content if c.page]
    
    assert any("Production quantity" in c for c in claims)
    assert "units" in units
    assert 1 in pages
    assert 2 in pages

def test_pdf_mathematical_symbols_and_special_characters():
    """Verify extraction of mathematical symbols, equations, and greek letters in PDF."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Thermal & Mechanical Stress Analysis", fontsize=16)
    page.insert_text((50, 110), "Delta temperature: ΔT = 45 °C", fontsize=12)
    page.insert_text((50, 140), "Tolerance limit: ±0.05 mm", fontsize=12)
    page.insert_text((50, 170), "Stress coefficient: α ≤ 1.25", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()

    res = process_pdf(pdf_bytes, filename="math_report.pdf")
    assert res.source_type == "document"
    claims_text = " ".join(c.claim for c in res.content)
    assert "ΔT" in claims_text or "Delta temperature" in claims_text
    assert any(c.unit in ["°c", "mm"] for c in res.content if c.unit)

def test_scanned_pdf_detection_and_ocr():
    """Verify detection of image-only / scanned PDF pages and OCR extraction."""
    scanned_path = SAMPLES_DIR / "sample_scanned.pdf"
    assert scanned_path.exists(), "Sample scanned PDF must exist"
    
    data = scanned_path.read_bytes()
    res = process_pdf(data, filename=scanned_path.name)
    
    assert isinstance(res, StandardExtractionResult)
    assert res.source_type == "document"
    assert res.metadata["is_scanned"] is True
    assert res.metadata["total_pages"] == 1
    assert res.metadata.get("ocr_applied") is True
    assert len(res.content) > 0
    assert any(c.page == 1 for c in res.content)
    assert any(c.confidence is not None for c in res.content)

# ============================================================================
# 3. Image Processing Tests (PNG, JPG, JPEG, OCR & Metadata)
# ============================================================================

def test_ocr_engine_direct():
    """Directly test OCR engine availability, initialization, and text recognition."""
    from multimodal_processor.ocr_engine import is_ocr_available, perform_ocr, get_active_ocr_engine_name
    assert is_ocr_available() is True
    assert "RapidOCR" in get_active_ocr_engine_name() or "Tesseract" in get_active_ocr_engine_name()

    img_path = SAMPLES_DIR / "sample_chart.png"
    text, conf, details = perform_ocr(img_path.read_bytes())
    assert text != ""
    assert conf is not None and conf > 0.5
    assert len(details) > 0

def test_image_processing_png():
    """Verify PNG image decoding, dimensions, OCR extraction, and confidence scores."""
    img_path = SAMPLES_DIR / "sample_chart.png"
    assert img_path.exists(), "Sample PNG must exist"
    
    data = img_path.read_bytes()
    res = process_image(data, filename=img_path.name)
    
    assert isinstance(res, StandardExtractionResult)
    assert res.source_type == "image"
    assert res.metadata["format"] == "png"
    assert res.metadata["dimensions"]["width"] == 600
    assert res.metadata["dimensions"]["height"] == 300
    assert res.metadata.get("ocr_applied") is True
    assert res.metadata.get("overall_confidence") is not None
    assert len(res.content) > 0
    assert any("Maximum speed" in c.claim for c in res.content)

def test_image_processing_jpg():
    """Verify JPG image OCR and metadata handling."""
    img_path = SAMPLES_DIR / "sample_receipt.jpg"
    assert img_path.exists(), "Sample JPG must exist"
    
    data = img_path.read_bytes()
    res = process_image(data, filename=img_path.name)
    
    assert isinstance(res, StandardExtractionResult)
    assert res.source_type == "image"
    assert res.metadata["format"] == "jpg"
    assert res.metadata.get("ocr_applied") is True
    assert len(res.content) > 0

def test_image_processing_jpeg():
    """Verify JPEG image extension handling and OCR via unified dispatcher."""
    img_path = SAMPLES_DIR / "sample_photo.jpeg"
    assert img_path.exists(), "Sample JPEG must exist"
    
    data = img_path.read_bytes()
    res = process_file_data(data, filename=img_path.name)
    
    assert isinstance(res, StandardExtractionResult)
    assert res.source_type == "image"
    assert res.metadata["format"] == "jpeg"
    assert res.metadata["dimensions"]["width"] == 600
    assert res.metadata.get("ocr_applied") is True
    assert len(res.content) > 0

# ============================================================================
# 4. Excel Processing Tests (XLSX, Legacy XLS, Dates, Formulas)
# ============================================================================

def test_excel_processing_xlsx():
    """Verify multi-sheet XLSX table extraction without inventing missing values."""
    xlsx_path = SAMPLES_DIR / "sample_metrics.xlsx"
    assert xlsx_path.exists(), "Sample Excel must exist"
    
    data = xlsx_path.read_bytes()
    res = process_excel(data, filename=xlsx_path.name)
    
    assert isinstance(res, StandardExtractionResult)
    assert res.source_type == "table"
    assert res.metadata["format"] == "xlsx"
    assert "Turbine_Performance" in res.metadata["sheets"]
    assert "Financial_Summary" in res.metadata["sheets"]
    assert len(res.content) > 0
    
    item = next(c for c in res.content if c.sheet == "Turbine_Performance" and c.column == "Power Output")
    assert item.value == "450"
    assert item.unit == "kw"
    assert item.row == 1

    # Missing value check: Row 3 has null Efficiency
    eff_row_3 = [c for c in res.content if c.sheet == "Turbine_Performance" and c.column == "Efficiency" and c.row == 3]
    assert len(eff_row_3) == 0, "Missing values must never be hallucinated"

def test_excel_dates_and_clean_rows():
    """Verify Excel extraction handles date timestamps cleanly without noise."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df = pd.DataFrame([
            {"Event": "Commissioning", "Timestamp": pd.Timestamp("2024-06-15 00:00:00"), "Count": 10},
            {"Event": "Inspection", "Timestamp": pd.Timestamp("2024-06-16 14:30:00"), "Count": 15},
            {"Event": None, "Timestamp": None, "Count": None}  # completely empty row to drop
        ])
        df.to_excel(writer, sheet_name="Timeline", index=False)
    buf.seek(0)

    res = process_excel(buf.read(), filename="timeline.xlsx")
    assert res.source_type == "table"
    date_item = next(c for c in res.content if c.claim == "Timestamp" and c.row == 1)
    assert "2024-06-15" in date_item.value

def test_excel_processing_legacy_xls():
    """Verify legacy .xls file extraction using xlrd engine."""
    xls_path = SAMPLES_DIR / "sample_legacy.xls"
    if not xls_path.exists():
        pytest.skip("sample_legacy.xls not generated in this environment")
    
    data = xls_path.read_bytes()
    res = process_excel(data, filename=xls_path.name)
    
    assert isinstance(res, StandardExtractionResult)
    assert res.source_type == "table"
    assert res.metadata["format"] == "xls"
    assert "Factory_Output" in res.metadata["sheets"]
    assert len(res.content) > 0
    
    item = next(c for c in res.content if c.column == "Capacity" and c.row == 1)
    assert item.value == "1200"
    assert item.unit == "units"

# ============================================================================
# 5. CSV Processing Tests (Normal, Semicolon, Quoted, Malformed)
# ============================================================================

def test_csv_processing_normal():
    """Verify CSV parsing with unit detection and missing values handling."""
    csv_path = SAMPLES_DIR / "sample_inventory.csv"
    assert csv_path.exists(), "Sample CSV must exist"
    
    data = csv_path.read_bytes()
    res = process_csv(data, filename=csv_path.name)
    
    assert isinstance(res, StandardExtractionResult)
    assert res.source_type == "table"
    assert res.metadata["format"] == "csv"
    assert res.metadata["total_rows"] == 4
    assert res.metadata["total_columns"] == 5
    
    qty_item = next(c for c in res.content if c.column == "Quantity" and c.row == 1)
    assert qty_item.value == "250"
    assert qty_item.unit == "units"
    
    # Missing value check: ITEM-003 row 3 has no quantity
    row_3_qty = [c for c in res.content if c.column == "Quantity" and c.row == 3]
    assert len(row_3_qty) == 0

def test_csv_semicolon_and_quoted_text():
    """Verify CSV with semicolon delimiter and quoted text containing commas."""
    content = (
        'Product ID;Product Name;Price ($);Description\n'
        'P-101;"Valve, High Pressure";150.00;"Heavy duty, industrial"\n'
        'P-102;"Sensor, Thermal";45.00;"Compact type"\n'
    ).encode("utf-8")

    res = process_csv(content, filename="products_semicolon.csv")
    assert res.source_type == "table"
    assert res.metadata["total_rows"] == 2
    name_item = next(c for c in res.content if c.claim == "Product Name" and c.row == 1)
    assert "Valve, High Pressure" in name_item.value

def test_csv_processing_malformed():
    """Verify malformed CSV with ragged lines is handled cleanly without crashing."""
    csv_path = SAMPLES_DIR / "sample_malformed.csv"
    if not csv_path.exists():
        pytest.skip("sample_malformed.csv not found")
        
    data = csv_path.read_bytes()
    res = process_csv(data, filename=csv_path.name)
    assert isinstance(res, StandardExtractionResult)
    assert res.source_type == "table"
    assert len(res.content) > 0

# ============================================================================
# 6. Robustness, Corrupted Files & Edge Cases
# ============================================================================

def test_unsupported_file_format():
    """Verify unsupported extensions return standardized JSON with error metadata."""
    res = process_file_data(b"fake executable", filename="malware.exe")
    assert res.source_type == "unknown"
    assert "Unsupported file format" in res.metadata["error"]
    assert len(res.content) == 0

def test_empty_files_graceful():
    """Verify empty file buffers across modalities return safe responses without crashing."""
    for fname in ["empty.pdf", "empty.csv", "empty.xlsx", "empty.png"]:
        res = process_file_data(b"", filename=fname)
        assert len(res.content) == 0
        assert "error" in res.metadata

def test_corrupted_pdf_graceful():
    """Verify corrupted PDF bytes are handled gracefully."""
    res = process_file_data(b"not a valid pdf header", filename="corrupt.pdf")
    assert "Corrupted or invalid PDF" in res.metadata["error"]
    assert len(res.content) == 0

def test_corrupted_image_graceful():
    """Verify corrupted image bytes return structured error."""
    res = process_file_data(b"broken image bytes", filename="corrupt.png")
    assert "error" in res.metadata
    assert len(res.content) == 0

def test_large_file_handling():
    """Verify handling of larger multi-row CSV datasets."""
    large_csv = "RowID,Metric,Value (kW)\n" + "\n".join(f"{i},Sensor_{i},{100 + i}" for i in range(1000))
    res = process_csv(large_csv.encode("utf-8"), filename="large_sensors.csv")
    assert res.metadata["total_rows"] == 1000
    assert len(res.content) == 3000

# ============================================================================
# 7. FastAPI Service Endpoints & Integration Tests
# ============================================================================

def test_api_health_endpoint():
    """Verify GET /health response structure, OCR engine availability, and supported formats."""
    data = health_check()
    assert data["status"] == "healthy"
    assert ".pdf" in data["supported_formats"]
    assert ".xlsx" in data["supported_formats"]
    assert ".xls" in data["supported_formats"]
    assert ".csv" in data["supported_formats"]
    assert data["ocr_engine_available"] is True
    assert "ocr_engine" in data
    assert data["ocr_engine"] != "None (Unavailable)"

def test_api_process_file_endpoint():
    """Verify POST /process-file returns valid StandardExtractionResult."""
    csv_path = SAMPLES_DIR / "sample_inventory.csv"
    upload = UploadFile(filename=csv_path.name, file=io.BytesIO(csv_path.read_bytes()))
    res = process_file_endpoint(file=upload)
    assert res.source == "sample_inventory.csv"
    assert res.source_type == "table"
    assert len(res.content) > 0

def test_api_process_file_size_limit_check():
    """Verify POST /process-file raises 413 if upload exceeds size limit."""
    huge_data = io.BytesIO(b"x" * (MAX_FILE_SIZE_BYTES + 1024))
    upload = UploadFile(filename="oversized.pdf", file=huge_data)
    with pytest.raises(HTTPException) as excinfo:
        process_file_endpoint(file=upload)
    assert excinfo.value.status_code == 413

def test_api_process_batch_endpoint():
    """Verify POST /process-batch processes multiple heterogeneous files."""
    csv_path = SAMPLES_DIR / "sample_inventory.csv"
    pdf_path = SAMPLES_DIR / "sample_report.pdf"
    
    f1 = UploadFile(filename=csv_path.name, file=io.BytesIO(csv_path.read_bytes()))
    f2 = UploadFile(filename=pdf_path.name, file=io.BytesIO(pdf_path.read_bytes()))
    data = process_batch_endpoint(files=[f1, f2])
    assert data.total_files == 2
    assert data.successful == 2
    assert data.failed == 0
    assert len(data.results) == 2

def test_api_process_batch_partial_failure_isolation():
    """Verify that an error in one batch file does NOT corrupt valid files."""
    pdf_path = SAMPLES_DIR / "sample_report.pdf"
    valid_file = UploadFile(filename=pdf_path.name, file=io.BytesIO(pdf_path.read_bytes()))
    broken_file = UploadFile(filename="invalid.exe", file=io.BytesIO(b"bad binary"))
    
    data = process_batch_endpoint(files=[valid_file, broken_file])
    assert data.total_files == 2
    assert data.successful == 1
    assert data.failed == 1
    assert len(data.errors) == 1
    assert data.errors[0]["filename"] == "invalid.exe"
    # Ensure valid file result was preserved intact
    assert data.results[0].source == "sample_report.pdf"
    assert data.results[0].source_type == "document"

# ============================================================================
# 8. Swagger Documentation, OpenAPI Schema & JSON Processing Verification
# ============================================================================

def test_api_process_batch_json_with_file_paths():
    """Verify POST /process_batch processes files specified as JSON file paths."""
    csv_path = SAMPLES_DIR / "sample_inventory.csv"
    pdf_path = SAMPLES_DIR / "sample_report.pdf"
    
    req = BatchProcessRequest(files=[str(csv_path), str(pdf_path)])
    data = process_batch_json(payload=req)
    assert data.total_files == 2
    assert data.successful == 2
    assert data.failed == 0
    assert len(data.results) == 2
    assert data.results[0].source == "sample_inventory.csv"
    assert data.results[1].source == "sample_report.pdf"

def test_api_process_batch_json_with_inline_content():
    """Verify POST /process_batch processes inline text / base64 content via JSON."""
    item = BatchFileItem(
        filename="inline_production.csv",
        content="Metric,Value,Unit\nTurbine_Output,500,kW\nEfficiency,92,%"
    )
    req = BatchProcessRequest(files=[item])
    data = process_batch_json(payload=req)
    assert data.total_files == 1
    assert data.successful == 1
    assert data.failed == 0
    assert len(data.results[0].content) >= 2
    values = [c.value for c in data.results[0].content]
    assert "Turbine_Output" in values

def test_api_process_batch_json_validation_errors():
    """Verify Pydantic validation rejects missing fields or invalid structures with 422."""
    from pydantic import ValidationError

    # Missing files / empty payload
    with pytest.raises(ValidationError) as excinfo:
        BatchProcessRequest.model_validate({})
    assert "At least one file item" in str(excinfo.value)

    # Empty list
    with pytest.raises(ValidationError) as excinfo:
        BatchProcessRequest.model_validate({"files": []})
    assert "At least one file item" in str(excinfo.value)

    # Incorrect data type (string instead of list)
    with pytest.raises(ValidationError) as excinfo:
        BatchProcessRequest.model_validate({"files": "not_a_list"})
    assert "Input should be a valid list" in str(excinfo.value)

def test_api_process_file_json_endpoint():
    """Verify POST /process_file handles single file references via JSON."""
    csv_path = SAMPLES_DIR / "sample_inventory.csv"
    req = SingleFileProcessRequest(file_path=str(csv_path))
    res = process_file_json(payload=req)
    assert res.source == "sample_inventory.csv"
    assert res.source_type == "table"
    assert len(res.content) > 0

    # Validation: empty request raises ValidationError
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SingleFileProcessRequest.model_validate({})

def test_openapi_schema_endpoint():
    """Verify that /openapi.json contains valid OpenAPI 3.1 specification with both endpoints."""
    schema = app.openapi()
    assert schema["info"]["title"] == "CERBERUS-XA Multimodal Data Processing API"
    assert "/process-file" in schema["paths"]
    assert "/process_file" in schema["paths"]
    assert "/process-batch" in schema["paths"]
    assert "/process_batch" in schema["paths"]
    assert "/health" in schema["paths"]

def test_swagger_and_redoc_endpoints():
    """Verify that /docs and /redoc routes are properly registered."""
    routes = {r.path: r for r in app.routes}
    assert "/docs" in routes, "/docs route must be registered"
    assert "/redoc" in routes, "/redoc route must be registered"
    assert "/openapi.json" in routes, "/openapi.json route must be registered"

def test_documentation_redirects():
    """Verify root / and trailing slash redirects lead cleanly to /docs."""
    r_root = root_redirect()
    assert r_root.status_code == 307
    assert r_root.headers["location"] == "/docs"

    r_docs = docs_slash_redirect()
    assert r_docs.status_code == 307
    assert r_docs.headers["location"] == "/docs"

    r_redoc = redoc_slash_redirect()
    assert r_redoc.status_code == 307
    assert r_redoc.headers["location"] == "/redoc"
