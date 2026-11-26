"""
Tests for extraction modules.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


# ---------------------------------------------------------------------------
# TXT Extractor
# ---------------------------------------------------------------------------

class TestTxtExtractor:
    def test_basic_extraction(self, tmp_path):
        from src.extractors.txt_extractor import extract_txt
        f = tmp_path / "test.txt"
        f.write_text("ABC Industries produced 5000 units in January 2026.", encoding="utf-8")
        result = extract_txt(f)
        assert result["error"] is None
        assert len(result["pages"]) == 1
        assert "5000" in result["pages"][0]["text"]

    def test_empty_file(self, tmp_path):
        from src.extractors.txt_extractor import extract_txt
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        result = extract_txt(f)
        assert result["error"] is not None

    def test_nonexistent_file(self, tmp_path):
        from src.extractors.txt_extractor import extract_txt
        result = extract_txt(tmp_path / "nonexistent.txt")
        assert result["error"] is not None

    def test_latin1_encoding(self, tmp_path):
        from src.extractors.txt_extractor import extract_txt
        f = tmp_path / "latin.txt"
        f.write_bytes("Revenue grew by 10% in fiscal year 2025.".encode("latin-1"))
        result = extract_txt(f)
        assert result["error"] is None
        assert "Revenue" in result["pages"][0]["text"]


# ---------------------------------------------------------------------------
# CSV Extractor
# ---------------------------------------------------------------------------

class TestCsvExtractor:
    def test_basic_csv(self, tmp_path):
        from src.extractors.csv_extractor import extract_csv
        f = tmp_path / "data.csv"
        f.write_text("Company,Metric,Value\nABC Corp,Revenue,5000000\n", encoding="utf-8")
        result = extract_csv(f)
        assert result["error"] is None
        assert len(result["sheets"]) == 1
        assert "ABC Corp" in result["sheets"][0]["text"]

    def test_empty_csv(self, tmp_path):
        from src.extractors.csv_extractor import extract_csv
        f = tmp_path / "empty.csv"
        f.write_text("", encoding="utf-8")
        result = extract_csv(f)
        assert result["error"] is not None

    def test_csv_has_rows(self, tmp_path):
        from src.extractors.csv_extractor import extract_csv
        f = tmp_path / "rows.csv"
        lines = ["Entity,Value,Unit", "ABC Co,5000,units", "ABC Co,3000,units"]
        f.write_text("\n".join(lines), encoding="utf-8")
        result = extract_csv(f)
        assert result["error"] is None
        assert len(result["sheets"][0]["rows"]) == 3  # header + 2 data rows


# ---------------------------------------------------------------------------
# Excel Extractor
# ---------------------------------------------------------------------------

class TestExcelExtractor:
    def test_basic_excel(self, tmp_path):
        try:
            import openpyxl
        except ImportError:
            pytest.skip("openpyxl not installed")

        from src.extractors.excel_extractor import extract_excel

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report"
        ws.append(["Company", "Metric", "Value"])
        ws.append(["ABC Corp", "Production", 5000])
        wb.save(str(tmp_path / "test.xlsx"))

        result = extract_excel(tmp_path / "test.xlsx")
        assert result["error"] is None
        assert len(result["sheets"]) == 1
        assert "ABC Corp" in result["sheets"][0]["text"]

    def test_empty_excel(self, tmp_path):
        try:
            import openpyxl
        except ImportError:
            pytest.skip("openpyxl not installed")
        from src.extractors.excel_extractor import extract_excel
        wb = openpyxl.Workbook()
        wb.save(str(tmp_path / "empty.xlsx"))
        result = extract_excel(tmp_path / "empty.xlsx")
        # Empty sheets should still have no error (just empty sheets)
        assert isinstance(result["sheets"], list)


# ---------------------------------------------------------------------------
# Document Loader
# ---------------------------------------------------------------------------

class TestDocumentLoader:
    def test_unsupported_format(self, tmp_path):
        from src.extractors.document_loader import load_document
        f = tmp_path / "file.xyz"
        f.write_text("hello")
        result = load_document(f)
        assert result["error"] is not None
        assert result["type"] == "unknown"

    def test_nonexistent_file(self, tmp_path):
        from src.extractors.document_loader import load_document
        result = load_document(tmp_path / "ghost.pdf")
        assert result["error"] is not None

    def test_txt_via_loader(self, tmp_path):
        from src.extractors.document_loader import load_document
        f = tmp_path / "data.txt"
        f.write_text("ABC Corp produced 5000 units.", encoding="utf-8")
        result = load_document(f)
        assert result["error"] is None
        assert "5000" in result["full_text"]

    def test_multiple_documents(self, tmp_path):
        from src.extractors.document_loader import load_multiple_documents
        files = []
        for i, text in enumerate(["ABC Corp revenue 5000.", "XYZ Ltd profit 3000."]):
            f = tmp_path / f"doc{i}.txt"
            f.write_text(text, encoding="utf-8")
            files.append(f)
        docs = load_multiple_documents(files)
        assert len(docs) == 2
        assert all(d["error"] is None for d in docs)
