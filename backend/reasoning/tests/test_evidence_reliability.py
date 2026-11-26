"""
Comprehensive Unit Tests for Component 1: Evidence Reliability Evaluator
Covering:
- Reliable traceable evidence
- Untraceable evidence
- Direct and indirect evidence
- Corroborated and uncorroborated evidence
- Duplicate sources (duplicates excluded from independent confirmation)
- Missing metadata
- Contradictory evidence
- Empty evidence handling
- Invalid scores and validation
- Weight validation (sum to 100% / 1.0)
- Unassessed criteria support
- Structured output verification
"""

import pytest
from pydantic import ValidationError
from backend.reasoning.schemas import (
    Claim,
    EvidenceItem,
    EvidenceMetadata,
    EvidenceModality,
    DirectnessLevel,
    ReliabilityRating,
    ReliabilityLabel,
    ReliabilityScorerConfig,
    CriterionScore,
    EvidenceReliabilityResult,
)
from backend.reasoning.evidence_reliability import EvidenceReliabilityEvaluator


@pytest.fixture
def evaluator():
    return EvidenceReliabilityEvaluator()


# 1. Reliable traceable evidence
def test_reliable_traceable_evidence(evaluator):
    item = EvidenceItem(
        id="EV-TRACE-01",
        content="Official audited annual filing: Net profits for FY2023 were $4.2B USD.",
        modality=EvidenceModality.DOCUMENT,
        directness=DirectnessLevel.PRIMARY,
        metadata=EvidenceMetadata(
            source_id="SEC-ARCHIVE-991",
            filename="annual_filing_2023.pdf",
            page_number=14,
            section="Financial Highlights",
            author="Office of the Auditor",
            organization="SEC",
            checksum_hash="sha256:4a5b6c7d8e9f0123456789abcdef",
            creation_date="2024-01-15T00:00:00Z",
            modification_date="2024-01-15T12:00:00Z",
            extraction_confidence=0.99,
        ),
    )

    result = evaluator.evaluate_item(item)
    assert isinstance(result, EvidenceReliabilityResult)
    assert result.evidence_id == "EV-TRACE-01"
    assert result.reliability_score >= 75.0
    assert result.reliability_label == ReliabilityLabel.HIGH
    assert result.criteria_scores["provenance"].score >= 90.0
    assert result.criteria_scores["directness"].score == 100.0
    assert len(result.limitations) >= 3


# 2. Untraceable evidence
def test_untraceable_evidence(evaluator):
    item = EvidenceItem(
        id="EV-UNTRACE-01",
        content="Anonymous tip claimed profits were overstated.",
        modality=EvidenceModality.OTHER,
        directness=DirectnessLevel.UNVERIFIED,
        metadata=EvidenceMetadata(
            source_id="",  # missing source
            filename="",
        ),
    )

    result = evaluator.evaluate_item(item)
    assert result.reliability_score < 50.0
    assert result.reliability_label == ReliabilityLabel.LOW
    assert result.criteria_scores["provenance"].score <= 20.0
    assert "Identifiable source_id is absent." in result.missing_information
    # Safeguard check: unknown source is NOT automatically marked false
    assert not any("false" in r.lower() for r in result.reasons)


# 3. Direct and indirect evidence
def test_direct_vs_indirect_evidence(evaluator):
    claim = Claim(
        id="CLM-01",
        statement="Target vessel arrived at Port of Rotterdam on June 12.",
        entity="Target Vessel",
        property="arrival_port",
        value="Port of Rotterdam",
    )

    direct_ev = EvidenceItem(
        id="EV-DIR-01",
        content="Port of Rotterdam automated AIS docking log: Target Vessel moored at Berth 4 on June 12.",
        directness=DirectnessLevel.PRIMARY,
        metadata=EvidenceMetadata(source_id="PORT-AIS-SYS", filename="ais_logs.csv", record_id="REC-994"),
    )
    claim.evidence_ids = [direct_ev.id]

    indirect_ev = EvidenceItem(
        id="EV-INDIR-01",
        content="General shipping industry commentary on European trade traffic trends during June.",
        directness=DirectnessLevel.HEARSAY,
        metadata=EvidenceMetadata(source_id="BLOG-PORTAL"),
    )

    res_direct = evaluator.evaluate_item(direct_ev, all_claims=[claim])
    res_indirect = evaluator.evaluate_item(indirect_ev, all_claims=[claim])

    assert res_direct.criteria_scores["directness"].score >= 90.0
    assert res_indirect.criteria_scores["directness"].score <= 40.0
    assert res_direct.reliability_score > res_indirect.reliability_score


# 4. Corroborated and uncorroborated evidence
def test_corroborated_vs_uncorroborated_evidence(evaluator):
    ev1 = EvidenceItem(
        id="EV-CORROB-1",
        content="Sensor A recorded radiation spike at 14:02 UTC.",
        metadata=EvidenceMetadata(source_id="SENSOR-SYSTEM-A", record_id="REC-1"),
    )
    ev2 = EvidenceItem(
        id="EV-CORROB-2",
        content="Sensor B recorded radiation spike at 14:02 UTC.",
        metadata=EvidenceMetadata(source_id="SENSOR-SYSTEM-B", record_id="REC-2"),
    )
    claim = Claim(id="C-1", statement="Radiation spike at 14:02 UTC.", evidence_ids=["EV-CORROB-1", "EV-CORROB-2"])

    results = evaluator.evaluate_all([ev1, ev2], claims=[claim])
    assert results["EV-CORROB-1"].criteria_scores["corroboration"].score >= 75.0

    # Uncorroborated standalone item
    res_standalone = evaluator.evaluate_item(ev1, all_items=[ev1])
    assert res_standalone.criteria_scores["corroboration"].score == 40.0
    assert "Standalone evidence item" in res_standalone.criteria_scores["corroboration"].explanation


# 5. Duplicate sources (Crucial Safeguard: Do not count duplicate copies as independent confirmation)
def test_duplicate_sources_excluded_from_corroboration(evaluator):
    """
    Test that duplicate evidence copies (identical text or hash) do NOT inflate corroboration!
    """
    ev_original = EvidenceItem(
        id="EV-ORIG",
        content="Intercept transcript: Operation Bluebird confirmed for 0600 hours.",
        metadata=EvidenceMetadata(
            source_id="INTEL-FEED-A",
            checksum_hash="hash-exact-match-12345",
        ),
    )
    # Duplicate copy 1: identical text and identical hash from another node
    ev_duplicate_1 = EvidenceItem(
        id="EV-DUP-1",
        content="Intercept transcript: Operation Bluebird confirmed for 0600 hours.",
        metadata=EvidenceMetadata(
            source_id="INTEL-MIRROR-B",
            checksum_hash="hash-exact-match-12345",
        ),
    )
    # Duplicate copy 2: exact same text
    ev_duplicate_2 = EvidenceItem(
        id="EV-DUP-2",
        content="Intercept transcript: Operation Bluebird confirmed for 0600 hours.",
        metadata=EvidenceMetadata(
            source_id="INTEL-MIRROR-C",
        ),
    )

    claim = Claim(
        id="CLM-OP",
        statement="Operation Bluebird confirmed for 0600 hours.",
        evidence_ids=["EV-ORIG", "EV-DUP-1", "EV-DUP-2"],
    )

    all_items = [ev_original, ev_duplicate_1, ev_duplicate_2]
    results = evaluator.evaluate_all(all_items, claims=[claim])

    res = results["EV-ORIG"]
    # Because all others are duplicates, independent corroboration must NOT be 100!
    assert res.criteria_scores["corroboration"].score == 40.0
    assert any("duplicate" in l.lower() for l in res.limitations)
    assert "duplicate" in res.criteria_scores["corroboration"].explanation.lower()


# 6. Missing metadata
def test_missing_metadata_safeguard(evaluator):
    item = EvidenceItem(
        id="EV-SPARSE",
        content="Text without rich metadata attributes.",
        metadata=EvidenceMetadata(source_id="SOURCE-X"),
    )
    res = evaluator.evaluate_item(item)
    assert len(res.missing_information) > 0
    # Missing information must NOT mean fabricated evidence
    assert not any("fabricated" in r.lower() for r in res.reasons)
    assert not any("fake" in r.lower() for r in res.reasons)


# 7. Contradictory evidence
def test_contradictory_evidence_impact(evaluator):
    ev1 = EvidenceItem(id="EV-POS", content="Target status confirmed active.", metadata=EvidenceMetadata(source_id="S1"))
    claim_pos = Claim(id="C1", statement="Target status active.", entity="Target", property="status", polarity=True, evidence_ids=["EV-POS"])
    claim_neg = Claim(id="C2", statement="Target status inactive.", entity="Target", property="status", polarity=False, evidence_ids=["EV-OTHER"])

    res = evaluator.evaluate_item(ev1, all_claims=[claim_pos, claim_neg])
    # Consistency score must drop due to contradiction
    assert res.criteria_scores["consistency"].score <= 65.0
    assert "contradictory" in res.criteria_scores["consistency"].explanation.lower()
    # But safeguard: score is not zero!
    assert res.criteria_scores["consistency"].score > 0.0


# 8. Empty evidence
def test_empty_evidence_raises_error(evaluator):
    item = EvidenceItem(
        id="EV-EMPTY",
        content="   ",  # whitespace only
        metadata=EvidenceMetadata(source_id="SRC"),
    )
    with pytest.raises(ValueError, match="content cannot be empty"):
        evaluator.evaluate_item(item)


# 9. Invalid scores
def test_criterion_score_validation():
    # Valid criterion score
    c = CriterionScore(name="provenance", score=85.0, weight=0.25, explanation="Valid")
    assert c.score == 85.0

    # Score > 100 should raise ValidationError
    with pytest.raises(ValidationError):
        CriterionScore(name="provenance", score=105.0, weight=0.25, explanation="Invalid")

    # Score < 0 should raise ValidationError
    with pytest.raises(ValidationError):
        CriterionScore(name="provenance", score=-5.0, weight=0.25, explanation="Invalid")


# 10. Weight validation
def test_weight_validation():
    # Valid config with fractions summing to 1.0
    cfg1 = ReliabilityScorerConfig(
        provenance_weight=0.25,
        directness_weight=0.25,
        corroboration_weight=0.20,
        consistency_weight=0.15,
        completeness_weight=0.15,
    )
    assert abs(cfg1.provenance_weight - 0.25) < 1e-4

    # Valid config with percentages summing to 100%
    cfg2 = ReliabilityScorerConfig(
        provenance_weight=25.0,
        directness_weight=25.0,
        corroboration_weight=20.0,
        consistency_weight=15.0,
        completeness_weight=15.0,
    )
    assert abs(cfg2.provenance_weight - 0.25) < 1e-4

    # Invalid config: weights sum to 0.70 (not 1.0 / 100%)
    with pytest.raises(ValueError, match="Criteria weights must sum to 1.0"):
        ReliabilityScorerConfig(
            provenance_weight=0.10,
            directness_weight=0.10,
            corroboration_weight=0.10,
            consistency_weight=0.20,
            completeness_weight=0.20,
        )


# 11. Unassessed criteria support
def test_unassessed_criteria_support(evaluator):
    item = EvidenceItem(
        id="EV-UNASSESSED",
        content="Sensor test log sample data.",
        metadata=EvidenceMetadata(source_id="SYS-A"),
    )

    # Mark corroboration and completeness as unassessed
    res = evaluator.evaluate_item(
        item=item,
        unassessed_criteria={"corroboration", "completeness"},
    )

    assert res.criteria_scores["corroboration"].is_assessed is False
    assert res.criteria_scores["corroboration"].score is None
    assert res.criteria_scores["completeness"].is_assessed is False
    assert res.criteria_scores["completeness"].score is None

    # Score must be re-normalized over the assessed criteria
    assert res.reliability_score > 0.0
    assert any("re-normalized" in l for l in res.limitations)


# 12. Modality neutrality check
def test_modality_neutrality(evaluator):
    meta = EvidenceMetadata(source_id="ARCHIVE-01", filename="file.bin", page_number=1)
    content = "Entity Alpha operation verified."

    scores = []
    for mod in [EvidenceModality.DOCUMENT, EvidenceModality.IMAGE, EvidenceModality.TABLE, EvidenceModality.RECORD]:
        ev = EvidenceItem(id=f"EV-{mod.value}", content=content, modality=mod, metadata=meta)
        res = evaluator.evaluate_item(ev)
        scores.append(res.reliability_score)

    # Modality alone does NOT alter score
    assert len(set(scores)) == 1

