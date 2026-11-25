"""
CERBERUS-XA: AI Reasoning & Evidence Verification Module (Member 4)
Conflict Preponderance Threshold & Hardened Margin Boundary Tests

Threshold Requirements:
- Authoritative Winner: average reliability >= PREPONDERANCE_HIGH_THRESHOLD (0.70)
- Low/Unverified Loser: average reliability <= PREPONDERANCE_LOW_THRESHOLD (0.50)
- Decisive Score Margin: abs(avg_a - avg_b) >= PREPONDERANCE_MIN_SCORE_GAP (0.25)
"""

import pytest
from backend.reasoning.conflict_analyzer import ConflictAnalyzer
from backend.reasoning.schemas import (
    Claim,
    EvidenceReliabilityResult,
    ReliabilityLabel,
)


@pytest.fixture
def analyzer():
    return ConflictAnalyzer()


def _make_mock_reliability(evidence_id: str, score: float) -> EvidenceReliabilityResult:
    return EvidenceReliabilityResult(
        evidence_id=evidence_id,
        reliability_score=round(score * 100.0, 1),
        reliability_label=ReliabilityLabel.HIGH if score >= 0.70 else (ReliabilityLabel.LOW if score <= 0.50 else ReliabilityLabel.MODERATE),
        criteria_scores={},
        overall_score=score,
    )


def test_boundary_case_083_vs_045_resolved(analyzer):
    """
    Case 1: 0.83 vs 0.45 -> Resolved for Claim A.
    Rationale: 0.83 >= 0.70, 0.45 <= 0.50, and score gap is 0.38 >= 0.25.
    High-reliability official source decisively overrides low-reliability/unsigned source.
    """
    claim_a = Claim(id="CLM-A", statement="Alpha-7 UAV payload is 15.5 kg.", entity="Alpha-7 UAV", property="payload", value=15.5, unit="kg", evidence_ids=["EV-A"])
    claim_b = Claim(id="CLM-B", statement="Alpha-7 UAV payload is 22.0 kg.", entity="Alpha-7 UAV", property="payload", value=22.0, unit="kg", evidence_ids=["EV-B"])

    rel_map = {
        "EV-A": _make_mock_reliability("EV-A", 0.83),
        "EV-B": _make_mock_reliability("EV-B", 0.45),
    }

    res_text, is_resolved, reason = analyzer._attempt_evidence_weight_resolution(claim_a, claim_b, rel_map)
    assert is_resolved is True
    assert "Resolved in favor of Claim CLM-A" in res_text
    assert "High-reliability" in reason


def test_boundary_case_070_vs_065_conflicted(analyzer):
    """
    Case 2: 0.70 vs 0.65 -> CONFLICTED / Unresolved.
    Rationale: Gap is only 0.05. Neither is low/unreliable (0.65 > 0.50). Too close to call.
    """
    claim_a = Claim(id="CLM-A", statement="Alpha-7 UAV payload is 15.5 kg.", entity="Alpha-7 UAV", property="payload", value=15.5, unit="kg", evidence_ids=["EV-A"])
    claim_b = Claim(id="CLM-B", statement="Alpha-7 UAV payload is 16.2 kg.", entity="Alpha-7 UAV", property="payload", value=16.2, unit="kg", evidence_ids=["EV-B"])

    rel_map = {
        "EV-A": _make_mock_reliability("EV-A", 0.70),
        "EV-B": _make_mock_reliability("EV-B", 0.65),
    }

    res_text, is_resolved, reason = analyzer._attempt_evidence_weight_resolution(claim_a, claim_b, rel_map)
    assert is_resolved is False
    assert "Unresolved conflict" in res_text
    assert "comparable or non-dispositive" in reason


def test_boundary_case_060_vs_060_conflicted(analyzer):
    """
    Case 3: 0.60 vs 0.60 -> CONFLICTED / Unresolved.
    Rationale: Identical reliability scores. Absolute deadlock with no preponderance.
    """
    claim_a = Claim(id="CLM-A", statement="Alpha-7 UAV payload is 15.5 kg.", entity="Alpha-7 UAV", property="payload", value=15.5, unit="kg", evidence_ids=["EV-A"])
    claim_b = Claim(id="CLM-B", statement="Alpha-7 UAV payload is 18.0 kg.", entity="Alpha-7 UAV", property="payload", value=18.0, unit="kg", evidence_ids=["EV-B"])

    rel_map = {
        "EV-A": _make_mock_reliability("EV-A", 0.60),
        "EV-B": _make_mock_reliability("EV-B", 0.60),
    }

    res_text, is_resolved, reason = analyzer._attempt_evidence_weight_resolution(claim_a, claim_b, rel_map)
    assert is_resolved is False
    assert "Unresolved conflict" in res_text
    assert "comparable or non-dispositive" in reason


def test_boundary_case_051_vs_049_conflicted(analyzer):
    """
    Case 4: 0.51 vs 0.49 -> CONFLICTED / Unresolved.
    Rationale: 0.51 vs 0.49 is a 0.02 gap between two mediocre sources. Neither source
    meets the High-reliability threshold (0.51 < 0.70), so Claim A cannot override Claim B.
    """
    claim_a = Claim(id="CLM-A", statement="Alpha-7 UAV payload is 15.5 kg.", entity="Alpha-7 UAV", property="payload", value=15.5, unit="kg", evidence_ids=["EV-A"])
    claim_b = Claim(id="CLM-B", statement="Alpha-7 UAV payload is 19.5 kg.", entity="Alpha-7 UAV", property="payload", value=19.5, unit="kg", evidence_ids=["EV-B"])

    rel_map = {
        "EV-A": _make_mock_reliability("EV-A", 0.51),
        "EV-B": _make_mock_reliability("EV-B", 0.49),
    }

    res_text, is_resolved, reason = analyzer._attempt_evidence_weight_resolution(claim_a, claim_b, rel_map)
    assert is_resolved is False
    assert "Unresolved conflict" in res_text
    assert "comparable or non-dispositive" in reason


def test_hardened_boundary_070_vs_050_conflicted_gap_too_narrow(analyzer):
    """
    Case 5 (PART A.3): 0.70 vs 0.50 -> CONFLICTED.
    Rationale: While 0.70 meets high threshold (>=0.70) and 0.50 meets low threshold (<=0.50),
    the score gap is only 0.20, which is below the mandatory PREPONDERANCE_MIN_SCORE_GAP (0.25).
    A razor-thin margin cannot safely resolve a factual contradiction.
    """
    claim_a = Claim(id="CLM-A", statement="Speed is 100 km/h.", entity="Drone", property="speed", value=100.0, evidence_ids=["EV-A"])
    claim_b = Claim(id="CLM-B", statement="Speed is 140 km/h.", entity="Drone", property="speed", value=140.0, evidence_ids=["EV-B"])

    rel_map = {
        "EV-A": _make_mock_reliability("EV-A", 0.70),
        "EV-B": _make_mock_reliability("EV-B", 0.50),
    }

    res_text, is_resolved, reason = analyzer._attempt_evidence_weight_resolution(claim_a, claim_b, rel_map)
    assert is_resolved is False
    assert "Unresolved conflict" in res_text
    assert "gap: 0.20 < 0.25" in reason


def test_hardened_boundary_080_vs_050_resolved(analyzer):
    """
    Case 6 (PART A.3): 0.80 vs 0.50 -> Resolved for Claim A.
    Rationale: 0.80 >= 0.70, 0.50 <= 0.50, and score gap is 0.30 >= 0.25.
    Conclusive preponderance achieved.
    """
    claim_a = Claim(id="CLM-A", statement="Speed is 100 km/h.", entity="Drone", property="speed", value=100.0, evidence_ids=["EV-A"])
    claim_b = Claim(id="CLM-B", statement="Speed is 140 km/h.", entity="Drone", property="speed", value=140.0, evidence_ids=["EV-B"])

    rel_map = {
        "EV-A": _make_mock_reliability("EV-A", 0.80),
        "EV-B": _make_mock_reliability("EV-B", 0.50),
    }

    res_text, is_resolved, reason = analyzer._attempt_evidence_weight_resolution(claim_a, claim_b, rel_map)
    assert is_resolved is True
    assert "Resolved in favor of Claim CLM-A" in res_text
    assert "gap 0.30 >= 0.25" in reason


def test_hardened_boundary_069_vs_040_conflicted_below_high_threshold(analyzer):
    """
    Case 7 (PART A.3): 0.69 vs 0.40 -> CONFLICTED.
    Rationale: While score gap is 0.29 (>= 0.25) and loser is 0.40 (<= 0.50),
    winner score 0.69 is below PREPONDERANCE_HIGH_THRESHOLD (0.70).
    A source lacking authoritative reliability cannot break a deadlock.
    """
    claim_a = Claim(id="CLM-A", statement="Speed is 100 km/h.", entity="Drone", property="speed", value=100.0, evidence_ids=["EV-A"])
    claim_b = Claim(id="CLM-B", statement="Speed is 140 km/h.", entity="Drone", property="speed", value=140.0, evidence_ids=["EV-B"])

    rel_map = {
        "EV-A": _make_mock_reliability("EV-A", 0.69),
        "EV-B": _make_mock_reliability("EV-B", 0.40),
    }

    res_text, is_resolved, reason = analyzer._attempt_evidence_weight_resolution(claim_a, claim_b, rel_map)
    assert is_resolved is False
    assert "Unresolved conflict" in res_text
    assert "threshold unmet" in reason
