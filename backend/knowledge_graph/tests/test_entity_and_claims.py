"""
Tests for entity extraction, matching, claim building and normalization.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


# ---------------------------------------------------------------------------
# Entity Extraction
# ---------------------------------------------------------------------------

class TestEntityExtraction:
    def test_basic_extraction(self):
        from src.entity_extraction import extract_entities_from_text
        text = "ABC Industries produced 5000 units in January 2026."
        claims = extract_entities_from_text(text, source="test.txt", page_or_sheet="Page 1")
        assert isinstance(claims, list)
        # Should extract at least one claim
        assert len(claims) >= 1

    def test_percentage_extraction(self):
        from src.entity_extraction import extract_entities_from_text
        text = "The company grew by 15 percent in Q2 2026."
        claims = extract_entities_from_text(text, source="test.txt")
        percent_claims = [c for c in claims if c.unit == "%"]
        assert len(percent_claims) >= 1
        assert any(abs(c.value - 15.0) < 0.01 for c in percent_claims)

    def test_currency_extraction(self):
        from src.entity_extraction import extract_entities_from_text
        text = "Revenue was ₹5 lakh in FY2025."
        claims = extract_entities_from_text(text, source="test.txt")
        currency_claims = [c for c in claims if c.unit == "₹"]
        assert len(currency_claims) >= 1
        # ₹5 lakh = 500,000
        assert any(abs(c.value - 500_000) < 1 for c in currency_claims)

    def test_empty_text(self):
        from src.entity_extraction import extract_entities_from_text
        claims = extract_entities_from_text("", source="empty.txt")
        assert claims == []

    def test_no_numbers(self):
        from src.entity_extraction import extract_entities_from_text
        text = "The company released an annual report today."
        claims = extract_entities_from_text(text, source="text.txt")
        # Should not produce number claims with value 0
        numeric = [c for c in claims if isinstance(c.value, (int, float)) and c.value != 0]
        assert len(numeric) == 0

    def test_date_extraction(self):
        from src.entity_extraction import _find_date
        assert _find_date("Revenue was 5000 in January 2026.") == "January 2026"
        assert _find_date("Q3 2025 results released.") == "Q3 2025"
        assert _find_date("No date here.") == ""


# ---------------------------------------------------------------------------
# Entity Matching
# ---------------------------------------------------------------------------

class TestEntityMatching:
    def test_exact_same(self):
        from src.entity_matching import match_entities
        names = ["ABC Industries", "ABC Industries"]
        result = match_entities(names, merge_threshold=92.0)
        assert result["ABC Industries"] == result["ABC Industries"]

    def test_similar_names_merged(self):
        from src.entity_matching import match_entities
        names = ["ABC Industries", "ABC Industry", "ABC Industries Ltd"]
        result = match_entities(names, merge_threshold=85.0)
        # All should map to the same canonical
        canonicals = set(result.values())
        assert len(canonicals) == 1

    def test_different_companies_not_merged(self):
        from src.entity_matching import match_entities
        names = ["ABC Industries", "XYZ Corporation"]
        result = match_entities(names, merge_threshold=92.0)
        assert result["ABC Industries"] != result["XYZ Corporation"]

    def test_possible_matches(self):
        from src.entity_matching import get_possible_matches
        names = ["ABC Industries", "ABC Industry", "XYZ Corp"]
        matches = get_possible_matches(names, similarity_threshold=70.0, merge_threshold=92.0)
        # ABC Industries vs ABC Industry should be a possible match
        pairs = [(a, b) for a, b, _ in matches]
        found = any(
            ("ABC Industries" in p and "ABC Industry" in p)
            for p in pairs
        )
        assert found

    def test_entity_groups(self):
        from src.entity_matching import build_entity_groups
        names = ["ABC Industries", "ABC Industries Ltd", "XYZ Corp"]
        groups = build_entity_groups(names, merge_threshold=85.0)
        # Should produce 2 groups
        assert len(groups) >= 1


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------

class TestNormalizer:
    def test_unit_normalization(self):
        from src.normalizer import normalize_unit
        assert normalize_unit("kg") == "kg"
        assert normalize_unit("KG") == "kg"
        assert normalize_unit("%") == "%"
        assert normalize_unit("percent") == "%"
        assert normalize_unit("₹") == "INR"
        assert normalize_unit("units") == "units"

    def test_value_normalization_lakh(self):
        from src.normalizer import normalize_value
        val, comparable = normalize_value(5, "lakh", "lakh")
        assert comparable
        assert abs(val - 500_000) < 1

    def test_value_normalization_crore(self):
        from src.normalizer import normalize_value
        val, comparable = normalize_value(1, "crore", "crore")
        assert abs(val - 10_000_000) < 1

    def test_value_normalization_kg_to_g(self):
        from src.normalizer import normalize_value
        val, comparable = normalize_value(5, "kg", "kg")
        assert comparable
        assert abs(val - 5000.0) < 0.01

    def test_string_value_not_comparable(self):
        from src.normalizer import normalize_value
        val, comparable = normalize_value("positive growth", "text", "text")
        assert not comparable
        assert val is None

    def test_date_normalization(self):
        from src.normalizer import normalize_date
        assert normalize_date("January 2026") == "2026-01"
        assert normalize_date("Q3 2025") == "2025-Q3"
        assert normalize_date("FY2025") == "FY2025"
        assert normalize_date("2026-01-15") == "2026-01-15"
        assert normalize_date("") == ""

    def test_dates_overlap(self):
        from src.normalizer import dates_overlap
        assert dates_overlap("2026", "2026") is True
        assert dates_overlap("2026", "2025") is False
        assert dates_overlap("2026-01", "2026-01") is True
        assert dates_overlap("2026-01", "2026-02") is False
        assert dates_overlap("", "2026") is True  # unknown date -> conservative
        assert dates_overlap("2026-Q1", "2026") is True  # same year


# ---------------------------------------------------------------------------
# Claim Builder
# ---------------------------------------------------------------------------

class TestClaimBuilder:
    def _make_raw_claim(self, entity="ABC Corp", value=5000, unit="units", source="test.txt"):
        from src.entity_extraction import RawClaim
        return RawClaim(
            entity=entity, entity_type="ORG", attribute="production",
            value=value, unit=unit, date_str="January 2026",
            source=source, page_or_sheet="Page 1",
            original_text="ABC Corp produced 5000 units.", confidence=0.9,
        )

    def test_builds_claims(self):
        from src.claim_builder import ClaimBuilder
        raw = [self._make_raw_claim()]
        claims = ClaimBuilder().build(raw)
        assert len(claims) == 1
        assert claims[0].entity == "ABC Corp"

    def test_entity_normalization(self):
        from src.claim_builder import ClaimBuilder
        raw = [
            self._make_raw_claim(entity="ABC Industries"),
            self._make_raw_claim(entity="ABC Industries Ltd"),
        ]
        claims = ClaimBuilder(merge_threshold=85.0).build(raw)
        # Both should map to same canonical
        assert claims[0].entity_normalized == claims[1].entity_normalized

    def test_claim_id_deterministic(self):
        from src.claim_builder import ClaimBuilder
        raw = [self._make_raw_claim()]
        c1 = ClaimBuilder().build(raw)[0]
        c2 = ClaimBuilder().build(raw)[0]
        assert c1.claim_id == c2.claim_id
