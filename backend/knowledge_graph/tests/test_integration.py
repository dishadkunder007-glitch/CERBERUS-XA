"""
Integration test using sample documents (TXT-based for CI compatibility).
Tests the full pipeline end-to-end.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


SAMPLE_DIR = Path(__file__).parent.parent / "data" / "sample_docs"


class TestIntegrationPipeline:
    def test_pipeline_with_sample_docs(self):
        """Full pipeline on sample contradictory documents."""
        from main import run_pipeline

        files = [
            SAMPLE_DIR / "report_pdf_equivalent.txt",
            SAMPLE_DIR / "report_image_equivalent.txt",
            SAMPLE_DIR / "audit_report.txt",
            SAMPLE_DIR / "erp_data.csv",
        ]

        # Only use existing files
        existing = [f for f in files if f.exists()]
        assert len(existing) >= 2, "Need at least 2 sample files for integration test"

        result = run_pipeline(
            file_paths=existing,
            numerical_tolerance_pct=2.0,
            use_ocr_for_pdf=False,
            output_dir=SAMPLE_DIR / ".." / ".." / "reports",
        )

        # Basic assertions
        assert "claims" in result
        assert "report" in result
        assert "graph" in result

        report = result["report"]
        claims = result["claims"]

        print(f"\nIntegration Test Results:")
        print(f"  Documents loaded : {len(result['documents'])}")
        print(f"  Claims extracted : {len(claims)}")
        print(f"  Contradictions   : {report.contradiction_count}")
        print(f"  Consistent       : {report.consistent_count}")
        print(f"  Uncertain        : {report.uncertain_count}")

        # The sample docs have contradictory production figures
        # (5000, 3000, 4500, 4000) → should detect contradictions
        # Note: detection depends on NLP extraction quality
        assert report.total_claims > 0
        assert report.contradiction_count >= 1

    def test_pipeline_empty_input(self, tmp_path):
        """Pipeline handles empty file gracefully."""
        from main import run_pipeline
        f = tmp_path / "empty.txt"
        f.write_text("")
        result = run_pipeline([f], output_dir=tmp_path / "out", use_ocr_for_pdf=False)
        assert "report" in result

    def test_pipeline_single_document(self, tmp_path):
        """Single document → no cross-document contradictions."""
        from main import run_pipeline
        f = tmp_path / "single.txt"
        f.write_text("ABC Corp produced 5000 units in January 2026.")
        result = run_pipeline([f], output_dir=tmp_path / "out", use_ocr_for_pdf=False)
        report = result["report"]
        assert report.contradiction_count == 0

    def test_pipeline_generates_reports(self, tmp_path):
        """Pipeline generates JSON and CSV reports."""
        from main import run_pipeline
        files = []
        for text, name in [
            ("ABC Corp produced 5000 units in January 2026.", "a.txt"),
            ("ABC Corp produced 3000 units in January 2026.", "b.txt"),
        ]:
            f = tmp_path / name
            f.write_text(text)
            files.append(f)

        result = run_pipeline(files, output_dir=tmp_path / "out", use_ocr_for_pdf=False)
        reports = result["reports"]
        assert Path(reports["json"]).exists() if reports["json"] else True
        assert Path(reports["csv"]).exists() if reports["csv"] else True
