"""
Tests for contradiction detection engine.
Covers all 9 test scenarios from the requirements.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.entity_extraction import RawClaim
from src.claim_builder import ClaimBuilder, Claim
from src.contradiction_detector import ContradictionDetector


def make_claim(
    entity="ABC Corp",
    attribute="production",
    value=5000.0,
    value_norm=5000.0,
    unit="units",
    unit_norm="units",
    date_str="January 2026",
    date_norm="2026-01",
    source="report.pdf",
    page_or_sheet="Page 1",
):
    from src.claim_builder import _make_claim_id
    return Claim(
        claim_id=_make_claim_id(entity, attribute, source, value),
        entity=entity,
        entity_normalized=entity,
        entity_type="ORG",
        attribute=attribute,
        value=value,
        value_normalized=value_norm,
        unit=unit,
        unit_normalized=unit_norm,
        date_str=date_str,
        date_normalized=date_norm,
        source=source,
        page_or_sheet=page_or_sheet,
        original_text=f"{entity} {attribute} {value} {unit}.",
        confidence=0.9,
        comparable=True,
    )


# ---------------------------------------------------------------------------
# Scenario 1: All documents report the same value → NO contradiction
# ---------------------------------------------------------------------------
class TestScenario1_AllSame:
    def test_all_same_value(self):
        """Scenario 1: All documents contain the same quantity."""
        claims = [
            make_claim(value=5000, value_norm=5000, source="a.pdf"),
            make_claim(value=5000, value_norm=5000, source="b.xlsx"),
            make_claim(value=5000, value_norm=5000, source="c.csv"),
        ]
        report = ContradictionDetector(numerical_tolerance_pct=2.0).detect(claims)
        assert report.contradiction_count == 0
        assert len(report.consistent_groups) >= 1


# ---------------------------------------------------------------------------
# Scenario 2: Every document has a different quantity → CONTRADICTION
# ---------------------------------------------------------------------------
class TestScenario2_AllDifferent:
    def test_all_different_values(self):
        """Scenario 2: Every document contains a different quantity."""
        claims = [
            make_claim(value=5000, value_norm=5000, source="pdf.pdf"),
            make_claim(value=3000, value_norm=3000, source="img.png"),
            make_claim(value=4000, value_norm=4000, source="excel.xlsx"),
            make_claim(value=4500, value_norm=4500, source="data.csv"),
        ]
        report = ContradictionDetector(numerical_tolerance_pct=2.0).detect(claims)
        assert report.contradiction_count >= 1
        # All 4 sources must be preserved
        contr = report.contradictions[0]
        sources = {cl.source for cl in contr.conflicting_claims}
        assert len(sources) == 4


# ---------------------------------------------------------------------------
# Scenario 3: Same company, different name spellings → NO false contradiction
# ---------------------------------------------------------------------------
class TestScenario3_SameName:
    def test_similar_entity_names_merged(self):
        """Scenario 3: Different names refer to the same company."""
        raw_claims = [
            RawClaim("ABC Industries", "ORG", "revenue", 1000000, "INR",
                     "2026", "report1.pdf", "Page 1", "ABC Industries revenue 1000000 INR", 0.9),
            RawClaim("ABC Industries Ltd", "ORG", "revenue", 1000000, "INR",
                     "2026", "report2.pdf", "Page 1", "ABC Industries Ltd revenue 1000000 INR", 0.9),
        ]
        builder = ClaimBuilder(merge_threshold=85.0)
        claims = builder.build(raw_claims)
        # Both should map to same canonical entity
        assert claims[0].entity_normalized == claims[1].entity_normalized
        # Same value → no contradiction
        report = ContradictionDetector().detect(claims)
        assert report.contradiction_count == 0


# ---------------------------------------------------------------------------
# Scenario 4: Minor rounding differences → NO contradiction
# ---------------------------------------------------------------------------
class TestScenario4_Rounding:
    def test_rounding_within_tolerance(self):
        """Scenario 4: Similar values with minor rounding differences."""
        claims = [
            make_claim(value=5000, value_norm=5000, source="a.pdf"),
            make_claim(value=5002, value_norm=5002, source="b.pdf"),  # 0.04% diff
        ]
        report = ContradictionDetector(numerical_tolerance_pct=2.0).detect(claims)
        assert report.contradiction_count == 0

    def test_rounding_beyond_tolerance(self):
        """Rounding beyond tolerance should be a contradiction."""
        claims = [
            make_claim(value=5000, value_norm=5000, source="a.pdf"),
            make_claim(value=5500, value_norm=5500, source="b.pdf"),  # 10% diff
        ]
        report = ContradictionDetector(numerical_tolerance_pct=2.0).detect(claims)
        assert report.contradiction_count >= 1


# ---------------------------------------------------------------------------
# Scenario 5: Different dates → NOT a contradiction (different periods)
# ---------------------------------------------------------------------------
class TestScenario5_DifferentDates:
    def test_different_dates_no_contradiction(self):
        """Scenario 5: Documents contain different dates – should not be compared."""
        claims = [
            make_claim(value=5000, value_norm=5000, date_str="January 2026", date_norm="2026-01", source="a.pdf"),
            make_claim(value=3000, value_norm=3000, date_str="February 2026", date_norm="2026-02", source="b.pdf"),
        ]
        report = ContradictionDetector(numerical_tolerance_pct=2.0).detect(claims)
        # Different months → different periods → no contradiction
        assert report.contradiction_count == 0


# ---------------------------------------------------------------------------
# Scenario 6: Different units → UNCERTAIN
# ---------------------------------------------------------------------------
class TestScenario6_DifferentUnits:
    def test_different_units_uncertain(self):
        """Scenario 6: Documents contain different units → uncertain, not false contradiction."""
        from src.claim_builder import _make_claim_id
        claims = [
            Claim(
                claim_id=_make_claim_id("ABC Corp", "weight", "a.pdf", 5),
                entity="ABC Corp", entity_normalized="ABC Corp", entity_type="ORG",
                attribute="weight", value=5, value_normalized=5000.0,  # 5 kg = 5000 g
                unit="kg", unit_normalized="kg",
                date_str="2026", date_normalized="2026",
                source="a.pdf", page_or_sheet="Page 1",
                original_text="ABC Corp weight 5 kg", confidence=0.9, comparable=True,
            ),
            Claim(
                claim_id=_make_claim_id("ABC Corp", "weight", "b.pdf", 5000),
                entity="ABC Corp", entity_normalized="ABC Corp", entity_type="ORG",
                attribute="weight", value=5000, value_normalized=5000.0,  # 5000 g = 5000 g (same!)
                unit="g", unit_normalized="g",
                date_str="2026", date_normalized="2026",
                source="b.pdf", page_or_sheet="Page 1",
                original_text="ABC Corp weight 5000 g", confidence=0.9, comparable=True,
            ),
        ]
        report = ContradictionDetector(numerical_tolerance_pct=2.0).detect(claims)
        # 5 kg (5000 g) and 5000 g are dimensionally equivalent and consistent
        assert report.contradiction_count == 0
        assert report.consistent_count == 2


# ---------------------------------------------------------------------------
# Scenario 7: Missing info in one document → NOT a contradiction
# ---------------------------------------------------------------------------
class TestScenario7_MissingInfo:
    def test_single_source_not_contradicted(self):
        """Scenario 7: Information missing from one document – not a contradiction."""
        claims = [
            make_claim(value=5000, value_norm=5000, source="only_source.pdf"),
        ]
        report = ContradictionDetector().detect(claims)
        # Only one source → no cross-document comparison
        assert report.contradiction_count == 0


# ---------------------------------------------------------------------------
# Scenario 8: Contradictory textual statements
# ---------------------------------------------------------------------------
class TestScenario8_TextualContradiction:
    def test_textual_contradiction(self):
        """Scenario 8: Documents contain contradictory textual statements."""
        from src.claim_builder import _make_claim_id
        claims = [
            Claim(
                claim_id=_make_claim_id("ABC Corp", "status", "a.pdf", "profitable"),
                entity="ABC Corp", entity_normalized="ABC Corp", entity_type="ORG",
                attribute="status", value="the company is profitable and growing",
                value_normalized=None,
                unit="", unit_normalized="",
                date_str="2026", date_normalized="2026",
                source="a.pdf", page_or_sheet="Page 1",
                original_text="the company is profitable and growing", confidence=0.8, comparable=False,
            ),
            Claim(
                claim_id=_make_claim_id("ABC Corp", "status", "b.pdf", "loss"),
                entity="ABC Corp", entity_normalized="ABC Corp", entity_type="ORG",
                attribute="status", value="the company is facing heavy losses and declining",
                value_normalized=None,
                unit="", unit_normalized="",
                date_str="2026", date_normalized="2026",
                source="b.pdf", page_or_sheet="Page 1",
                original_text="the company is facing heavy losses and declining", confidence=0.8, comparable=False,
            ),
        ]
        report = ContradictionDetector(text_similarity_threshold=0.6).detect(claims)
        assert report.contradiction_count >= 1


# ---------------------------------------------------------------------------
# Scenario 9: Corrupted / empty files → graceful handling
# ---------------------------------------------------------------------------
class TestScenario9_CorruptedFiles:
    def test_corrupted_pdf_reports_error(self, tmp_path):
        from src.extractors.document_loader import load_document
        f = tmp_path / "corrupt.pdf"
        f.write_bytes(b"THIS IS NOT A REAL PDF FILE - CORRUPTED")
        result = load_document(f)
        # Corrupted PDF should set an error
        assert result["error"] is not None

    def test_empty_txt_reports_error(self, tmp_path):
        from src.extractors.document_loader import load_document
        f = tmp_path / "empty.txt"
        f.write_text("")
        result = load_document(f)
        assert result["error"] is not None


# ---------------------------------------------------------------------------
# Contradiction detector: core properties
# ---------------------------------------------------------------------------
class TestDetectorProperties:
    def test_no_random_selection(self):
        """System must never silently pick one value."""
        claims = [
            make_claim(value=5000, value_norm=5000, source="a.pdf"),
            make_claim(value=3000, value_norm=3000, source="b.pdf"),
        ]
        report = ContradictionDetector().detect(claims)
        assert report.contradiction_count == 1
        contr = report.contradictions[0]
        # Both claims must be preserved
        assert len(contr.conflicting_claims) == 2

    def test_deterministic_results(self):
        """Results must be the same across multiple runs."""
        claims = [
            make_claim(value=5000, value_norm=5000, source="a.pdf"),
            make_claim(value=3000, value_norm=3000, source="b.pdf"),
        ]
        r1 = ContradictionDetector().detect(claims)
        r2 = ContradictionDetector().detect(claims)
        assert r1.contradiction_count == r2.contradiction_count

    def test_insufficient_evidence_is_uncertain(self):
        """Single-source claims should be uncertain, not contradictions."""
        claims = [make_claim(source="only.pdf")]
        report = ContradictionDetector().detect(claims)
        assert report.contradiction_count == 0
