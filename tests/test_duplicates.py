"""
Tests for Duplicate and Intra-document Inconsistency Detection (src/duplicates.py).
"""

import pytest
from src.claim_builder import Claim
from src.duplicates import detect_duplicates, DuplicateReport


class TestDuplicateDetection:
    """Tests for exact duplicates, near-duplicates, and intra-document contradictions."""

    def test_exact_duplicate_claims_detected(self):
        claims = [
            Claim(
                claim_id="C-1", entity="ABC Industries", entity_normalized="ABC Industries",
                entity_type="ORG", attribute="revenue", value=2500000.0,
                value_normalized=2500000.0, unit="INR", unit_normalized="INR",
                date_str="2026", date_normalized="2026", source="filing.txt",
                page_or_sheet="P1", original_text="Revenue: INR 25,00,000",
                confidence=0.95, comparable=True,
            ),
            Claim(
                claim_id="C-2", entity="ABC Industries", entity_normalized="ABC Industries",
                entity_type="ORG", attribute="revenue", value=2500000.0,
                value_normalized=2500000.0, unit="INR", unit_normalized="INR",
                date_str="2026", date_normalized="2026", source="press.txt",
                page_or_sheet="P1", original_text="Revenue was INR 25,00,000",
                confidence=0.95, comparable=True,
            ),
        ]
        report = detect_duplicates([], claims)
        assert report.total_duplicate_groups == 1
        dup = report.duplicate_groups[0]
        assert dup["entity"] == "abc industries"
        assert dup["attribute"] == "revenue"
        assert dup["value"] == 2500000.0
        assert set(dup["claim_ids"]) == {"C-1", "C-2"}

    def test_near_duplicate_numerical_values(self):
        """Values within 5% relative difference should be flagged as near-duplicates."""
        claims = [
            Claim(
                claim_id="C-1", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="production", value=5000.0,
                value_normalized=5000.0, unit="units", unit_normalized="units",
                date_str="2026", date_normalized="2026", source="doc1.txt",
                page_or_sheet="P1", original_text="5,000 units produced",
                confidence=0.95, comparable=True,
            ),
            Claim(
                claim_id="C-2", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="production", value=5050.0,
                value_normalized=5050.0, unit="units", unit_normalized="units",
                date_str="2026", date_normalized="2026", source="doc2.txt",
                page_or_sheet="P1", original_text="5,050 units manufactured",
                confidence=0.95, comparable=True,
            ),
        ]
        report = detect_duplicates([], claims, value_similarity_threshold=0.05)
        assert report.total_near_duplicates >= 1
        nd = report.near_duplicate_claims[0]
        assert nd["similarity"] >= 0.98

    def test_near_duplicate_textual_statements(self):
        """Paraphrased textual claims should be detected as near-duplicates."""
        claims = [
            Claim(
                claim_id="C-1", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="strategy", value="Focus on sustainable solar manufacturing in 2026",
                value_normalized=None, unit="", unit_normalized="",
                date_str="2026", date_normalized="2026", source="doc1.txt",
                page_or_sheet="P1", original_text="Focus on sustainable solar manufacturing in 2026",
                confidence=0.9, comparable=True,
            ),
            Claim(
                claim_id="C-2", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="strategy", value="Focus on sustainable solar manufacturing for 2026",
                value_normalized=None, unit="", unit_normalized="",
                date_str="2026", date_normalized="2026", source="doc2.txt",
                page_or_sheet="P1", original_text="Focus on sustainable solar manufacturing for 2026",
                confidence=0.9, comparable=True,
            ),
        ]
        report = detect_duplicates([], claims, text_similarity_threshold=0.85)
        assert report.total_near_duplicates >= 1

    def test_intra_document_inconsistency_numerical(self):
        """Conflicting numbers in the SAME document must be flagged as internal inconsistency."""
        claims = [
            Claim(
                claim_id="C-1", entity="Zenith Corp", entity_normalized="Zenith Corp",
                entity_type="ORG", attribute="production", value=4000.0,
                value_normalized=4000.0, unit="units", unit_normalized="units",
                date_str="2026", date_normalized="2026", source="internal_report.pdf",
                page_or_sheet="Page 1", original_text="Production output: 4,000 units",
                confidence=0.95, comparable=True,
            ),
            Claim(
                claim_id="C-2", entity="Zenith Corp", entity_normalized="Zenith Corp",
                entity_type="ORG", attribute="production", value=6000.0,
                value_normalized=6000.0, unit="units", unit_normalized="units",
                date_str="2026", date_normalized="2026", source="internal_report.pdf",
                page_or_sheet="Page 12", original_text="Total production reached 6,000 units",
                confidence=0.95, comparable=True,
            ),
        ]
        report = detect_duplicates([], claims)
        assert report.total_intra_document_inconsistencies == 1
        incons = report.inconsistent_within_document[0]
        assert incons["source"] == "internal_report.pdf"
        assert "4000.0 units" in incons["values"]
        assert "6000.0 units" in incons["values"]

    def test_intra_document_inconsistency_textual(self):
        """Conflicting text status in the SAME document must be flagged."""
        claims = [
            Claim(
                claim_id="C-1", entity="Zenith Corp", entity_normalized="Zenith Corp",
                entity_type="ORG", attribute="status", value="operational",
                value_normalized=None, unit="", unit_normalized="",
                date_str="2026", date_normalized="2026", source="audit.txt",
                page_or_sheet="Page 1", original_text="Facility is operational",
                confidence=0.9, comparable=True,
            ),
            Claim(
                claim_id="C-2", entity="Zenith Corp", entity_normalized="Zenith Corp",
                entity_type="ORG", attribute="status", value="shutdown",
                value_normalized=None, unit="", unit_normalized="",
                date_str="2026", date_normalized="2026", source="audit.txt",
                page_or_sheet="Page 4", original_text="Plant shutdown confirmed",
                confidence=0.9, comparable=True,
            ),
        ]
        report = detect_duplicates([], claims)
        assert report.total_intra_document_inconsistencies == 1

    def test_no_false_duplicates_different_entities(self):
        """Claims for different entities are never duplicates even if values are identical."""
        claims = [
            Claim(
                claim_id="C-1", entity="Company A", entity_normalized="Company A",
                entity_type="ORG", attribute="revenue", value=100.0,
                value_normalized=100.0, unit="USD", unit_normalized="USD",
                date_str="2026", date_normalized="2026", source="doc1.txt",
                page_or_sheet="P1", original_text="Rev 100",
                confidence=0.9, comparable=True,
            ),
            Claim(
                claim_id="C-2", entity="Company B", entity_normalized="Company B",
                entity_type="ORG", attribute="revenue", value=100.0,
                value_normalized=100.0, unit="USD", unit_normalized="USD",
                date_str="2026", date_normalized="2026", source="doc2.txt",
                page_or_sheet="P1", original_text="Rev 100",
                confidence=0.9, comparable=True,
            ),
        ]
        report = detect_duplicates([], claims)
        assert report.total_duplicate_groups == 0

    def test_no_false_duplicates_different_dates(self):
        """Claims for different dates are not duplicates."""
        claims = [
            Claim(
                claim_id="C-1", entity="Company A", entity_normalized="Company A",
                entity_type="ORG", attribute="revenue", value=100.0,
                value_normalized=100.0, unit="USD", unit_normalized="USD",
                date_str="2025", date_normalized="2025", source="doc1.txt",
                page_or_sheet="P1", original_text="Rev 100 in 2025",
                confidence=0.9, comparable=True,
            ),
            Claim(
                claim_id="C-2", entity="Company A", entity_normalized="Company A",
                entity_type="ORG", attribute="revenue", value=100.0,
                value_normalized=100.0, unit="USD", unit_normalized="USD",
                date_str="2026", date_normalized="2026", source="doc2.txt",
                page_or_sheet="P1", original_text="Rev 100 in 2026",
                confidence=0.9, comparable=True,
            ),
        ]
        report = detect_duplicates([], claims)
        assert report.total_duplicate_groups == 0

    def test_empty_claims_duplicate_report(self):
        report = detect_duplicates([], [])
        assert report.total_duplicate_groups == 0
        assert report.total_near_duplicates == 0
        assert report.total_intra_document_inconsistencies == 0
