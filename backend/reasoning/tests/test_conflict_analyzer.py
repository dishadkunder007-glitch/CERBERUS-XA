"""
Unit Tests for Component 2: Conflict Analyzer
"""

import pytest
from backend.reasoning.schemas import (
    Claim,
    ConflictType,
    EvidenceItem,
    EvidenceMetadata,
    ReliabilityBreakdown,
    ReliabilityRating,
)
from backend.reasoning.conflict_analyzer import ConflictAnalyzer


@pytest.fixture
def analyzer():
    return ConflictAnalyzer()


def test_agreement_on_values(analyzer):
    c1 = Claim(
        id="CLM-01",
        statement="ACME Corp reported revenue of 50M USD.",
        entity="ACME Corp",
        property="revenue",
        value=50000000,
        unit="USD",
        time_period="2023",
    )
    c2 = Claim(
        id="CLM-02",
        statement="Audit confirms ACME Corp generated 50M USD in revenue.",
        entity="ACME Corp",
        property="revenue",
        value=50000000,
        unit="USD",
        time_period="2023",
    )

    conflicts = analyzer.analyze_claims([c1, c2])
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.AGREEMENT
    assert conflicts[0].is_resolved is True


def test_unit_conversion_agreement(analyzer):
    # 5 km vs 5000 meters
    c1 = Claim(
        id="CLM-01",
        statement="Pipeline length is 5 km.",
        entity="Pipeline",
        property="length",
        value=5.0,
        unit="km",
    )
    c2 = Claim(
        id="CLM-02",
        statement="Pipeline measures 5000 meters.",
        entity="Pipeline",
        property="length",
        value=5000.0,
        unit="m",
    )

    conflicts = analyzer.analyze_claims([c1, c2])
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.AGREEMENT
    assert "Converted to standard m" in conflicts[0].unit_resolution


def test_temporal_differentiation_partial_conflict(analyzer):
    # CEO changed over time
    c1 = Claim(
        id="CLM-01",
        statement="Alice is the CEO of CyberNet.",
        entity="CyberNet",
        property="CEO",
        value="Alice",
        time_period="2019",
        timestamp="2019-01-01T00:00:00Z",
    )
    c2 = Claim(
        id="CLM-02",
        statement="Bob is the CEO of CyberNet.",
        entity="CyberNet",
        property="CEO",
        value="Bob",
        time_period="2024",
        timestamp="2024-01-01T00:00:00Z",
    )

    conflicts = analyzer.analyze_claims([c1, c2])
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.PARTIAL_CONTRADICTION
    assert conflicts[0].is_resolved is True
    assert "temporal" in conflicts[0].resolution_reason.lower()


def test_scope_differentiation(analyzer):
    c1 = Claim(
        id="CLM-01",
        statement="Sales were 10M in North America.",
        entity="TechCo",
        property="sales",
        value=10000000,
        scope="North America",
    )
    c2 = Claim(
        id="CLM-02",
        statement="Sales were 45M globally.",
        entity="TechCo",
        property="sales",
        value=45000000,
        scope="Global",
    )

    conflicts = analyzer.analyze_claims([c1, c2])
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.PARTIAL_CONTRADICTION
    assert conflicts[0].is_resolved is True
    assert "scope" in conflicts[0].resolution_reason.lower()


def test_unresolved_conflict_when_evidence_cannot_resolve(analyzer):
    """
    Requirement: 'Never force a resolution if the evidence cannot resolve it.'
    Both claims have comparable reliability scores -> must remain UNRESOLVED_CONFLICT.
    """
    c1 = Claim(
        id="CLM-01",
        statement="Transaction balance was 100,000 USD.",
        entity="Account-90",
        property="balance",
        value=100000,
        unit="USD",
        time_period="2023-12-31",
        evidence_ids=["EV-1"],
    )
    c2 = Claim(
        id="CLM-02",
        statement="Transaction balance was 250,000 USD.",
        entity="Account-90",
        property="balance",
        value=250000,
        unit="USD",
        time_period="2023-12-31",
        evidence_ids=["EV-2"],
    )

    # Both have moderate reliability (0.65 vs 0.60)
    rel_map = {
        "EV-1": ReliabilityBreakdown(
            traceability_score=0.7, directness_score=0.7, corroboration_score=0.5,
            consistency_score=0.8, completeness_score=0.6, overall_score=0.65,
            rating=ReliabilityRating.MEDIUM, reasons=[]
        ),
        "EV-2": ReliabilityBreakdown(
            traceability_score=0.6, directness_score=0.7, corroboration_score=0.5,
            consistency_score=0.7, completeness_score=0.6, overall_score=0.60,
            rating=ReliabilityRating.MEDIUM, reasons=[]
        ),
    }

    conflicts = analyzer.analyze_claims([c1, c2], reliability_map=rel_map)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.UNRESOLVED_CONFLICT
    assert conflicts[0].is_resolved is False
    assert "cannot force resolution" in conflicts[0].resolution_reason.lower()

