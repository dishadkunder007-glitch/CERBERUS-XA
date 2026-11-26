"""
CERBERUS-XA: AI Reasoning & Evidence Verification Module (Member 4)
Adapter Tests for Assumed Upstream Payloads (Member 2 & Member 3)

NOTE: Upstream code for Member 2 (backend/processor/) and Member 3 (backend/knowledge_graph/)
is not available in this workspace. These tests verify the defensive adapter against
SYNTHETIC ASSUMED payloads and error paths, NOT real upstream code samples.

Tests:
1. Normalization of assumed Member 2 (Processor) chunk and claim alias variations.
2. Normalization of assumed Member 3 (Knowledge Graph) edge/triple alias variations.
3. Loud failure (AdapterError) on missing required fields for evidence items.
4. Loud failure (AdapterError) on missing required fields for claims.
5. Loud failure (AdapterError) on missing required fields for knowledge graph edges.
6. Loud failure (AdapterError) on empty question string.
7. End-to-end pipeline verification using repo's sample request file (backend/reasoning/sample_request.json).
"""

import json
import os
import sys
from pathlib import Path
import pytest

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.reasoning.adapter import InterMemberAdapter, AdapterError
from backend.reasoning.schemas import EvidenceModality, DirectnessLevel, ReasoningStatus
from backend.reasoning.service import ReasoningPipeline


@pytest.fixture
def adapter():
    return InterMemberAdapter()


@pytest.fixture
def pipeline():
    return ReasoningPipeline()


def test_adapt_processor_assumed_field_variations(adapter):
    """
    Verifies that assumed Member 2 Processor output field naming variations
    are cleanly normalized into Member 4 EvidenceItem models.
    """
    synthetic_chunks = [
        {
            "chunk_id": "CHK-001",
            "text": "Alpha-7 UAV maximum payload capacity verified at 15.5 kg during flight test.",
            "source_type": "pdf",
            "directness": "direct",
            "metadata": {
                "source": "FAA-TCDS",
                "file_name": "alpha7_type_cert.pdf",
                "page": 4,
                "chapter": "Specifications",
                "sha256": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
                "ocr_confidence": 0.98,
                "author": "Federal Aviation Administration",
            },
        },
        {
            "doc_id": "CHK-002",
            "extracted_text": "Scanned bench test report confirms 15.5 kg ballast endurance.",
            "file_type": "scan",
            "directness": "raw",
            "metadata": {
                "source_name": "BENCH-TEST",
                "page_no": 1,
            },
        },
    ]

    items = adapter.adapt_processor_evidence(synthetic_chunks)
    assert len(items) == 2

    # Item 1 field normalization assertions
    item1 = items[0]
    assert item1.id == "CHK-001"  # chunk_id -> id
    assert "15.5 kg" in item1.content  # text -> content
    assert item1.modality == EvidenceModality.DOCUMENT  # pdf -> DOCUMENT
    assert item1.directness == DirectnessLevel.PRIMARY  # direct -> PRIMARY
    assert item1.metadata.source_id == "FAA-TCDS"  # source -> source_id
    assert item1.metadata.filename == "alpha7_type_cert.pdf"  # file_name -> filename
    assert item1.metadata.page_number == 4  # page -> page_number
    assert item1.metadata.section == "Specifications"  # chapter -> section
    assert item1.metadata.checksum_hash == "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
    assert item1.metadata.extraction_confidence == 0.98

    # Item 2 field normalization assertions
    item2 = items[1]
    assert item2.id == "CHK-002"  # doc_id -> id
    assert item2.modality == EvidenceModality.SCAN  # scan -> SCAN
    assert item2.metadata.source_id == "BENCH-TEST"  # source_name -> source_id
    assert item2.metadata.page_number == 1  # page_no -> page_number


def test_adapt_knowledge_graph_assumed_triples(adapter):
    """
    Verifies that assumed Member 3 Knowledge Graph triples (head/predicate/tail or source/relation/target)
    are cleanly converted into KGRelationship and supplementary Claim models.
    """
    synthetic_kg_output = {
        "nodes": [
            {"id": "Alpha-7 UAV", "type": "AIRCRAFT"},
            {"id": "15.5 kg", "type": "QUANTITY"},
        ],
        "edges": [
            {
                "head": "Alpha-7 UAV",
                "predicate": "has_payload_capacity",
                "tail": "15.5 kg",
                "weight": 0.95,
                "citations": ["CHK-001"],
            },
            {
                "source": "Alpha-7 UAV",
                "relation": "manufactured_by",
                "target": "AeroDynamics Corp",
                "confidence": 1.0,
                "evidence_ids": ["CHK-002"],
            },
        ],
    }

    rels, derived_claims = adapter.adapt_knowledge_graph(synthetic_kg_output)

    assert len(rels) == 2
    assert len(derived_claims) == 2

    # Relationship 1 (head/predicate/tail)
    r1 = rels[0]
    assert r1.source_entity == "Alpha-7 UAV"
    assert r1.relation == "has_payload_capacity"
    assert r1.target_entity == "15.5 kg"
    assert r1.confidence == 0.95
    assert r1.evidence_ids == ["CHK-001"]

    # Derived Claim 1
    c1 = derived_claims[0]
    assert c1.entity == "Alpha-7 UAV"
    assert c1.property == "has_payload_capacity"
    assert c1.value == "15.5 kg"
    assert c1.evidence_ids == ["CHK-001"]


def test_loud_failure_on_missing_evidence_required_fields(adapter):
    """
    Adapter must raise AdapterError with item index and present keys when
    mandatory fields (id, content, modality) cannot be resolved from aliases.
    """
    # Missing ID alias
    with pytest.raises(AdapterError) as exc_id:
        adapter.adapt_processor_evidence([{"text": "Sample text", "modality": "pdf"}])
    assert "missing required identifier alias" in str(exc_id.value)
    assert "index 0" in str(exc_id.value)
    assert "text" in str(exc_id.value)

    # Missing Content alias
    with pytest.raises(AdapterError) as exc_content:
        adapter.adapt_processor_evidence([{"id": "EV-01", "modality": "pdf"}])
    assert "missing required text content alias" in str(exc_content.value)
    assert "index 0" in str(exc_content.value)

    # Missing Modality alias
    with pytest.raises(AdapterError) as exc_mod:
        adapter.adapt_processor_evidence([{"id": "EV-01", "text": "Valid text"}])
    assert "missing required modality alias" in str(exc_mod.value)
    assert "index 0" in str(exc_mod.value)


def test_loud_failure_on_missing_claim_required_fields(adapter):
    """
    Adapter must raise AdapterError when statement alias is missing from claim payload.
    """
    with pytest.raises(AdapterError) as exc:
        adapter.adapt_processor_claims([{"id": "CLM-01", "entity": "Drone", "value": 15.5}])
    assert "missing required statement alias" in str(exc.value)
    assert "index 0" in str(exc.value)


def test_loud_failure_on_missing_kg_required_fields(adapter):
    """
    Adapter must raise AdapterError when source, relation, or target aliases are missing.
    """
    # Missing target
    with pytest.raises(AdapterError) as exc_tgt:
        adapter.adapt_knowledge_graph([{"source": "Drone", "relation": "operates_at"}])
    assert "missing required target entity alias" in str(exc_tgt.value)

    # Missing relation
    with pytest.raises(AdapterError) as exc_rel:
        adapter.adapt_knowledge_graph([{"source": "Drone", "target": "Base"}])
    assert "missing required relationship alias" in str(exc_rel.value)

    # Missing source
    with pytest.raises(AdapterError) as exc_src:
        adapter.adapt_knowledge_graph([{"relation": "connects", "target": "Base"}])
    assert "missing required source entity alias" in str(exc_src.value)


def test_loud_failure_on_empty_question(adapter):
    """
    build_reasoning_request must reject empty or whitespace questions with AdapterError.
    """
    with pytest.raises(AdapterError) as exc:
        adapter.build_reasoning_request(question="   ")
    assert "non-empty question string" in str(exc.value)


def test_end_to_end_reasoning_with_repo_sample(adapter, pipeline):
    """
    Verifies that the adapter correctly integrates with ReasoningPipeline using
    the repository sample file (backend/reasoning/sample_request.json).
    """
    sample_request_path = root_dir / "backend" / "reasoning" / "sample_request.json"
    assert sample_request_path.exists(), "Sample file backend/reasoning/sample_request.json missing."

    with open(sample_request_path, "r", encoding="utf-8") as f:
        sample_json = json.load(f)

    # Ingest using assumed processor dictionary format
    assumed_processor = {
        "documents": sample_json.get("evidence_items", []),
        "claims": sample_json.get("claims", []),
    }

    assumed_kg = {
        "edges": [
            {
                "head": "Project Cerberus",
                "predicate": "certified_payload_capacity",
                "tail": "15.5 kg",
                "citations": ["EV-01"],
            }
        ]
    }

    req = adapter.build_reasoning_request(
        question=sample_json.get("question", "What is the payload capacity?"),
        processor_output=assumed_processor,
        kg_output=assumed_kg,
        enable_ollama=False,
    )

    assert req.question == sample_json.get("question")
    assert len(req.evidence_items) == len(sample_json.get("evidence_items", []))
    assert len(req.claims) >= len(sample_json.get("claims", []))
    assert len(req.kg_relationships) == 1

    # Execute full verification pipeline
    response = pipeline.verify(req)

    assert response.status in (
        ReasoningStatus.ANSWERED,
        ReasoningStatus.CONFLICTED,
        ReasoningStatus.PARTIALLY_ANSWERED,
    )
    assert len(response.citations) > 0
    assert response.confidence > 0.0
