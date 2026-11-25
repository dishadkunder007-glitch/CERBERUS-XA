"""
Tests for OCR Confidence Filtering, Noise Rejection, and Evidence-Based Confidence Breakdown.
Covers Problems 3 & 4.
"""

import pytest
from src.claim_builder import Claim, ClaimBuilder
from src.entity_extraction import extract_entities_from_text, RawClaim
from src.contradiction_detector import ContradictionDetector, ContradictionResult


class TestOCRConfidenceThreshold:
    """Problem 3: OCR confidence threshold filters noisy/low-confidence extractions."""

    def test_low_ocr_confidence_claim_flagged_uncertain(self):
        """Claims with OCR confidence < 0.60 must not trigger false CONTRADICTION; flagged as UNCERTAIN."""
        claims = [
            Claim(
                claim_id="C-CLEAN", entity="ABC Industries", entity_normalized="ABC Industries",
                entity_type="ORG", attribute="production", value=5000.0,
                value_normalized=5000.0, unit="units", unit_normalized="units",
                date_str="2026", date_normalized="2026", source="clean_filing.pdf",
                page_or_sheet="P1", original_text="Production: 5,000 units",
                confidence=0.95, comparable=True, ocr_confidence=1.0,
            ),
            Claim(
                claim_id="C-NOISY", entity="ABC Industries", entity_normalized="ABC Industries",
                entity_type="ORG", attribute="production", value=3.0,
                value_normalized=3.0, unit="units", unit_normalized="units",
                date_str="2026", date_normalized="2026", source="noisy_scan.png",
                page_or_sheet="P1", original_text="3.0 units",
                confidence=0.5, comparable=True, ocr_confidence=0.42,  # Low OCR confidence
            ),
        ]
        detector = ContradictionDetector(ocr_confidence_threshold=0.60)
        report = detector.detect(claims)

        # Must NOT be a hard contradiction
        assert report.contradiction_count == 0
        # Must be in uncertain groups or reported as uncertain
        assert report.uncertain_count >= 1

    def test_high_ocr_confidence_claim_evaluated_as_contradiction(self):
        """When both claims have OCR confidence >= 0.60, genuine differences are contradictions."""
        claims = [
            Claim(
                claim_id="C-1", entity="ABC Industries", entity_normalized="ABC Industries",
                entity_type="ORG", attribute="production", value=5000.0,
                value_normalized=5000.0, unit="units", unit_normalized="units",
                date_str="2026", date_normalized="2026", source="clean_filing.pdf",
                page_or_sheet="P1", original_text="Production: 5,000 units",
                confidence=0.95, comparable=True, ocr_confidence=0.92,
            ),
            Claim(
                claim_id="C-2", entity="ABC Industries", entity_normalized="ABC Industries",
                entity_type="ORG", attribute="production", value=4000.0,
                value_normalized=4000.0, unit="units", unit_normalized="units",
                date_str="2026", date_normalized="2026", source="audit_scan.png",
                page_or_sheet="P1", original_text="Verified production: 4,000 units",
                confidence=0.92, comparable=True, ocr_confidence=0.88,
            ),
        ]
        detector = ContradictionDetector(ocr_confidence_threshold=0.60)
        report = detector.detect(claims)
        assert report.contradiction_count == 1
        assert report.contradictions[0].status == "CONTRADICTION"

    def test_bare_address_number_not_extracted_as_claim(self):
        """Locations like 'Industrial Zone, Sector 4' must not generate production=4 claims."""
        text = "Location: Industrial Zone, Sector 4"
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 0, f"Expected 0 claims for location line, got {len(claims)}: {claims}"


class TestEvidenceBasedConfidenceBreakdown:
    """Problem 4: Evidence-based confidence breakdown dictionary and explanation."""

    def test_breakdown_contains_all_six_components(self):
        claims = [
            Claim(
                claim_id="C-1", entity="ABC Corp", entity_normalized="ABC Corp",
                entity_type="ORG", attribute="revenue", value=100.0,
                value_normalized=100.0, unit="USD", unit_normalized="USD",
                date_str="2026", date_normalized="2026", source="doc1.pdf",
                page_or_sheet="P1", original_text="Rev 100 USD",
                confidence=0.95, comparable=True, ocr_confidence=0.90,
            ),
            Claim(
                claim_id="C-2", entity="ABC Corp", entity_normalized="ABC Corp",
                entity_type="ORG", attribute="revenue", value=200.0,
                value_normalized=200.0, unit="USD", unit_normalized="USD",
                date_str="2026", date_normalized="2026", source="doc2.pdf",
                page_or_sheet="P1", original_text="Rev 200 USD",
                confidence=0.95, comparable=True, ocr_confidence=0.90,
            ),
        ]
        report = ContradictionDetector().detect(claims)
        assert report.contradiction_count == 1
        c = report.contradictions[0]

        expected_keys = {
            "extraction", "entity_match", "period_match",
            "unit_normalization", "source_reliability", "value_divergence"
        }
        assert set(c.confidence_breakdown.keys()) == expected_keys
        for k, v in c.confidence_breakdown.items():
            assert 0.0 <= v <= 1.0, f"Component {k} out of range: {v}"

        assert isinstance(c.confidence_explanation, str)
        assert len(c.confidence_explanation) > 10

    def test_confidence_monotonic_with_extraction_certainty(self):
        """Higher extraction certainty produces higher overall confidence."""
        def make_pair(extract_conf, ocr_conf):
            return [
                Claim(
                    claim_id="C-1", entity="ABC Corp", entity_normalized="ABC Corp",
                    entity_type="ORG", attribute="revenue", value=100.0,
                    value_normalized=100.0, unit="USD", unit_normalized="USD",
                    date_str="2026", date_normalized="2026", source="doc1.pdf",
                    page_or_sheet="P1", original_text="Rev 100",
                    confidence=extract_conf, comparable=True, ocr_confidence=ocr_conf,
                ),
                Claim(
                    claim_id="C-2", entity="ABC Corp", entity_normalized="ABC Corp",
                    entity_type="ORG", attribute="revenue", value=200.0,
                    value_normalized=200.0, unit="USD", unit_normalized="USD",
                    date_str="2026", date_normalized="2026", source="doc2.pdf",
                    page_or_sheet="P1", original_text="Rev 200",
                    confidence=extract_conf, comparable=True, ocr_confidence=ocr_conf,
                ),
            ]

        rep_low = ContradictionDetector().detect(make_pair(0.70, 0.70))
        rep_high = ContradictionDetector().detect(make_pair(0.98, 0.98))

        assert rep_high.contradictions[0].confidence > rep_low.contradictions[0].confidence

    def test_confidence_explanation_readable_text(self):
        claims = [
            Claim(
                claim_id="C-1", entity="ABC Corp", entity_normalized="ABC Corp",
                entity_type="ORG", attribute="revenue", value=100.0,
                value_normalized=100.0, unit="USD", unit_normalized="USD",
                date_str="2026", date_normalized="2026", source="doc1.pdf",
                page_or_sheet="P1", original_text="Rev 100",
                confidence=0.95, comparable=True, ocr_confidence=0.90,
            ),
            Claim(
                claim_id="C-2", entity="ABC Corp", entity_normalized="ABC Corp",
                entity_type="ORG", attribute="revenue", value=200.0,
                value_normalized=200.0, unit="USD", unit_normalized="USD",
                date_str="2026", date_normalized="2026", source="doc2.pdf",
                page_or_sheet="P1", original_text="Rev 200",
                confidence=0.95, comparable=True, ocr_confidence=0.90,
            ),
        ]
        c = ContradictionDetector().detect(claims).contradictions[0]
        assert "Extraction:" in c.confidence_explanation
        assert "Entity:" in c.confidence_explanation
        assert "Period:" in c.confidence_explanation

    def test_unseen_test_dataset_execution(self):
        """End-to-end execution on newly created data/unseen_tests/."""
        from pathlib import Path
        from src.extractors.document_loader import load_multiple_documents
        from src.entity_extraction import extract_entities_from_document
        
        unseen_dir = Path("data/unseen_tests")
        assert unseen_dir.exists()
        files = list(unseen_dir.glob("*.txt"))
        assert len(files) >= 2

        docs = load_multiple_documents(files)
        raw = []
        for d in docs:
            raw.extend(extract_entities_from_document(d))

        claims = ClaimBuilder().build(raw)
        report = ContradictionDetector().detect(claims)
        
        # TechNova production (80,000 vs 70,000), revenue (12M vs 10M), compliance (certified vs non-compliant)
        assert report.contradiction_count >= 2
        attrs = {c.attribute.lower() for c in report.contradictions}
        assert "production" in attrs or "revenue" in attrs
