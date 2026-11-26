"""
End-to-End Pipeline & FastAPI Endpoint Integration Tests
"""

import pytest
from pydantic import ValidationError
from backend.reasoning.service import (
    ReasoningPipeline,
    health_check,
    verify_evidence,
    evaluate_reliability,
)
from backend.reasoning.schemas import (
    ReasoningRequest,
    EvidenceItem,
    EvidenceMetadata,
    Claim,
    ConclusionType,
)


def test_health_check_endpoint():
    data = health_check()
    assert data["status"] == "healthy"
    assert "Member 4" in data["module"]
    assert data["mode"] == "offline-first-deterministic"
    assert data["ollama_model"] == "qwen2.5:7b-instruct"


def test_full_pipeline_verification():
    req = ReasoningRequest(
        question="What is the certified payload capacity of drone model Alpha-7?",
        claims=[
            Claim(
                id="CLM-DRONE-01",
                statement="Alpha-7 drone payload capacity is certified at 15.5 kg.",
                entity="Alpha-7",
                property="payload_capacity",
                value=15.5,
                unit="kg",
                evidence_ids=["EV-SPEC-01"],
                polarity=True,
            )
        ],
        evidence_items=[
            EvidenceItem(
                id="EV-SPEC-01",
                content="Official flight certification sheet: Alpha-7 drone payload capacity certified at 15.5 kg maximum takeoff weight.",
                modality="document",
                directness="primary",
                metadata=EvidenceMetadata(
                    source_id="FAA-TYPE-CERT-2023",
                    filename="alpha7_type_certificate.pdf",
                    page_number=3,
                    section="Specifications",
                    author="Federal Aviation Administration",
                    checksum_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    extraction_confidence=0.99,
                ),
            )
        ],
    )

    # Test via FastAPI endpoint function
    res = verify_evidence(req)

    assert res.conclusion_type == ConclusionType.SUPPORTED
    assert res.is_insufficient_evidence is False
    assert res.confidence_score > 0.70
    assert len(res.citations) == 1
    assert "FAA-TYPE-CERT-2023" in res.citations[0].source_id
    assert "alpha7_type_certificate.pdf" in res.citations[0].filename
    assert len(res.facts) > 0
    assert "EV-SPEC-01" in res.supporting_evidence_ids
    assert res.reasoning_mode == "deterministic"


def test_offline_ollama_graceful_fallback():
    """
    Test that when enable_ollama=True and Ollama server is unreachable,
    the pipeline seamlessly falls back to deterministic reasoning without crashing.
    """
    pipeline = ReasoningPipeline()
    req = ReasoningRequest(
        question="What is the operating temperature of the sensor?",
        claims=[
            Claim(
                id="CLM-01",
                statement="Sensor operating temperature range is -40C to 85C.",
                evidence_ids=["EV-01"],
            )
        ],
        evidence_items=[
            EvidenceItem(
                id="EV-01",
                content="Sensor operating temperature range is -40C to 85C.",
                metadata=EvidenceMetadata(source_id="SENSOR-DATASHEET", page_number=2),
            )
        ],
        enable_ollama=True,
        ollama_endpoint="http://127.0.0.1:1",  # port 1 refused immediately
    )

    # Must NOT raise exception; must fall back to deterministic
    res = pipeline.verify(req)
    assert res.conclusion_type == ConclusionType.SUPPORTED
    assert res.reasoning_mode == "deterministic"
    assert any("fell back to deterministic" in log for log in res.audit_trail)


def test_evaluate_reliability_endpoint():
    req = ReasoningRequest(
        question="Dummy query",
        evidence_items=[
            EvidenceItem(
                id="EV-TEST-REL",
                content="Some test content for reliability evaluation.",
                metadata=EvidenceMetadata(
                    source_id="TEST-SYS",
                    filename="test.txt",
                ),
            )
        ],
    )
    data = evaluate_reliability(req)
    assert "evidence_reliability" in data
    assert "EV-TEST-REL" in data["evidence_reliability"]
    assert data["evidence_reliability"]["EV-TEST-REL"].overall_score > 0.0


def test_adversarial_and_empty_inputs():
    # Empty question should fail validation (min_length=1)
    with pytest.raises(ValidationError):
        ReasoningRequest(
            question="",
            evidence_items=[],
        )

    # Valid question with empty evidence list should return insufficient_evidence
    empty_ev_req = ReasoningRequest(
        question="Can pigs fly according to official aviation records?",
        evidence_items=[],
    )
    res = verify_evidence(empty_ev_req)
    assert res.conclusion_type == ConclusionType.INSUFFICIENT_EVIDENCE
    assert res.is_insufficient_evidence is True
    assert res.confidence_score == 0.0

