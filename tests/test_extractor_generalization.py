"""
Comprehensive Extractor Generalization Test Suite (>=30 tests).
Covers Problem 2:
- Entity-type disambiguation (e.g. Tata Motors vs Ratan Tata)
- Currency variations (US$, EUR, GBP, JPY, INR, scale multipliers)
- Leadership phrasings across plain prose, key-value, bullets
- Compliance negation and controlled vocabulary
- Operational status antonyms and phrasings
- Tables, bullets, and key-value formats
- Approximations and modalities
"""

import pytest
from src.entity_extraction import (
    extract_entities_from_text,
    _extract_primary_entity,
    classify_entity_type,
    RawClaim,
)
from src.claim_builder import ClaimBuilder
from src.contradiction_detector import ContradictionDetector


class TestEntityDisambiguation:
    """Disambiguate corporate entities from person names."""

    def test_tata_motors_not_ratan_tata(self):
        text = (
            "Tata Motors Ltd Annual Performance Review\n"
            "Executive: Ratan Tata serves as Chairman Emeritus.\n"
            "Total units produced: 45,000 in 2026.\n"
        )
        primary = _extract_primary_entity(text)
        assert "Tata Motors" in primary
        assert "Ratan Tata" not in primary

    def test_person_name_with_company_header(self):
        text = (
            "Company: Zenith Dynamics Corp\n"
            "Sarah Jenkins delivered the keynote.\n"
            "Revenue reached USD 5,000,000 in 2026.\n"
        )
        primary = _extract_primary_entity(text)
        assert primary == "Zenith Dynamics Corp"

    def test_classify_entity_type_person(self):
        assert classify_entity_type("Sarah Jenkins") == "PERSON"
        assert classify_entity_type("Robert Vance") == "PERSON"
        assert classify_entity_type("Dr. John Smith") == "PERSON"

    def test_classify_entity_type_org(self):
        assert classify_entity_type("KPMG Verification Services") == "ORGANIZATION"
        assert classify_entity_type("Apex Dynamics Corp") == "ORGANIZATION"
        assert classify_entity_type("Zenith Holdings Group") == "ORGANIZATION"


class TestCurrencyAndScaleVariations:
    """Currency symbols, scale multipliers, and formats."""

    def test_us_dollar_prefix(self):
        text = "Acme Corp earned US$5,000,000 in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == 5000000.0
        assert "USD" in claims[0].unit

    def test_euro_symbol(self):
        text = "Bavaria Motoren reported net profit of €450,000 in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == 450000.0
        assert "EUR" in claims[0].unit

    def test_british_pound_symbol(self):
        text = "London Rail capex of £2.5 million in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == 2500000.0
        assert "GBP" in claims[0].unit

    def test_inr_rupee_symbol(self):
        text = "Bharat Tech revenue of ₹25 lakh in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == 2500000.0

    def test_million_scale_word(self):
        text = "Solaris Corp produced 12 million units in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == 12000000.0

    def test_billion_scale_word(self):
        text = "Global Logistics turnover of 3.2 billion USD in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == 3200000000.0

    def test_crore_scale_word(self):
        text = "Reliance Infra gross revenue of 15 crore in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == 150000000.0

    def test_thousand_k_multiplier(self):
        text = "Heavy Machinery produced 450k units in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == 450000.0


class TestLeadershipPhrasings:
    """Leadership extraction across varied sentence structures."""

    def test_ceo_colon_format(self):
        text = "CEO: Sarah Jenkins"
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == "Sarah Jenkins"

    def test_executive_colon_format(self):
        text = "Executive: Robert Vance"
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == "Robert Vance"

    def test_serves_as_ceo_prose(self):
        text = "Robert Vance serves as CEO of ABC Industries in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == "Robert Vance"

    def test_was_appointed_ceo(self):
        text = "Sarah Jenkins was appointed as Chief Executive Officer in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].value == "Sarah Jenkins"

    def test_led_by_format(self):
        text = "ABC Industries Ltd is led by Sarah Jenkins."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert "Sarah Jenkins" in claims[0].value

    def test_comma_title_format(self):
        text = "Robert Vance, Chief Executive Officer, presented the findings."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert "Robert Vance" in claims[0].value


class TestComplianceNegationAndVocabulary:
    """Compliance extraction handling negation and controlled vocabulary."""

    def test_compliance_non_compliant(self):
        text = "Compliance Rating: non-compliant."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert any(c.attribute == "compliance" and c.value == "non-compliant" for c in claims)

    def test_compliance_certified(self):
        text = "Compliance Rating: certified."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert any(c.attribute == "compliance" and c.value == "certified" for c in claims)

    def test_not_compliant_negation(self):
        text = "The facility was not compliant with environmental rules in 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert any(c.attribute == "compliance" and c.value == "non-compliant" for c in claims)

    def test_failed_compliance_audit(self):
        text = "Audit outcome: failed compliance inspection."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert any(c.attribute == "compliance" and c.value == "non-compliant" for c in claims)

    def test_fully_compliant(self):
        text = "The plant operations were fully compliant during Q1 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert any(c.attribute == "compliance" and c.value == "compliant" for c in claims)


class TestOperationalStatusVariations:
    """Operational status phrasings."""

    def test_shutdown_status(self):
        text = "Operational Status: shutdown due to maintenance."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert any(c.attribute == "status" and c.value == "shutdown" for c in claims)

    def test_operational_status_active(self):
        text = "Facility status is operational and active."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert any(c.attribute == "status" and c.value == "operational" for c in claims)

    def test_suspended_operations(self):
        text = "Operations were suspended in January 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert any(c.attribute == "status" and c.value == "suspended" for c in claims)

    def test_dormant_plant(self):
        text = "Condition: dormant facility."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert any(c.attribute == "status" and c.value == "dormant" for c in claims)


class TestBulletPointsAndKeyValues:
    """Bullet points and key-value formatted documents."""

    def test_bullet_point_production(self):
        text = (
            "Company: Apex Industries\n"
            "- Production output verified at 4,000 units in Q1 2026.\n"
            "- Declared revenue confirmed as INR 20,00,000.\n"
        )
        claims = extract_entities_from_text(text, source="doc.txt")
        attrs = {c.attribute for c in claims}
        assert "production" in attrs
        assert "revenue" in attrs

    def test_key_value_pairs(self):
        text = (
            "Company: Apex Industries\n"
            "Production: 5,000 units\n"
            "Workforce Count: 450 employees\n"
        )
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 2
        p_claim = next(c for c in claims if c.attribute == "production")
        assert p_claim.value == 5000.0
        w_claim = next(c for c in claims if c.attribute == "employees")
        assert w_claim.value == 450.0

    def test_mass_material_processed(self):
        text = "Total Material Processed: 5,000 kg during Q1 2026."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert len(claims) == 1
        assert claims[0].attribute == "weight"
        assert claims[0].unit == "kg"
        assert claims[0].value == 5000.0


class TestApproximationsAndModalities:
    """Modality tagging."""

    def test_target_modality(self):
        text = "Target production set at 10,000 units."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert claims[0].modality == "target"

    def test_estimate_modality(self):
        text = "Estimated total cost of 2,000,000 USD."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert claims[0].modality == "estimate"

    def test_approximate_modality(self):
        text = "Approximate workforce of 300 employees."
        claims = extract_entities_from_text(text, source="doc.txt")
        assert claims[0].modality == "estimate"
