"""
CERBERUS-XA — Member 4: AI Reasoning & Evidence Verification Module
Interactive End-to-End Demonstration Script

Demonstrates:
1. Multi-modal evidence reliability scoring (0-100 score across 5 weighted dimensions).
2. Multi-dimensional conflict analysis (unit conversion, temporal differentiation, deadlocks).
3. Suspicious evidence indicator detection with ethical audit safeguards.
4. 7-stage deterministic conflict-aware deliberation engine.
5. Zero-fabrication citation and traceability generation across all supported source types.
6. Optional local Ollama LLM integration with mandatory deterministic fallback.

Usage:
    python backend/reasoning/demo_member4.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.reasoning.schemas import (
    Claim,
    DirectnessLevel,
    EvidenceItem,
    EvidenceMetadata,
    EvidenceModality,
    KGRelationship,
    ReasoningRequest,
)
from backend.reasoning.service import ReasoningPipeline


def run_demo():
    print("=" * 80)
    print("  CERBERUS-XA — Member 4: AI Reasoning & Evidence Verification Demo")
    print("=" * 80)

    # 1. Prepare realistic multimodal test dataset
    print("\n[Stage 0] Constructing Multimodal Evidence & Claim Manifest...")

    evidence_items = [
        EvidenceItem(
            id="EV-PDF-01",
            content="Official FAA Type Certification Data Sheet No. A7-2024: Alpha-7 UAV certified payload capacity is 15.5 kg at MTOW.",
            modality=EvidenceModality.DOCUMENT,
            directness=DirectnessLevel.PRIMARY,
            metadata=EvidenceMetadata(
                source_id="FAA-TCDS-ARCHIVE",
                filename="alpha7_tcds_spec.pdf",
                file_type="application/pdf",
                page_number=4,
                section="Technical Specifications",
                author="Federal Aviation Administration",
                checksum_hash="sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
            ),
        ),
        EvidenceItem(
            id="EV-CSV-02",
            content="Flight test telemetry record indicates payload carried was 15,500 grams with stable avionics.",
            modality=EvidenceModality.DOCUMENT,
            directness=DirectnessLevel.PRIMARY,
            metadata=EvidenceMetadata(
                source_id="FLIGHT-OPS-DB",
                filename="telemetry_test_series.csv",
                file_type="text/csv",
                row_id="ROW-FLT-8821",
                author="Flight Test Engineering Team",
            ),
        ),
        EvidenceItem(
            id="EV-DRAFT-03",
            content="Informal engineering forum posting claiming payload limit was downgraded to 12.0 kg due to motor heating.",
            modality=EvidenceModality.DOCUMENT,
            directness=DirectnessLevel.HEARSAY,
            metadata=EvidenceMetadata(
                source_id="COMMUNITY-FORUM",
                filename="internal_discussion_thread.html",
                # Missing page number and author intentionally to demonstrate audit indicators
            ),
        ),
        EvidenceItem(
            id="EV-IMG-04",
            content="High-resolution test bay camera capture showing Alpha-7 mounted with 15.5 kg test ballast during pre-flight.",
            modality=EvidenceModality.IMAGE,
            directness=DirectnessLevel.PRIMARY,
            metadata=EvidenceMetadata(
                source_id="TEST-BAY-CAMERA",
                filename="ballast_mount_test.png",
                image_id="IMG-BAY4-BALLAST",
                author="Avionics Lab QA",
            ),
        ),
    ]

    claims = [
        Claim(
            id="CLM-01",
            statement="Alpha-7 UAV certified payload capacity is 15.5 kg.",
            entity="Alpha-7 UAV",
            property="payload_capacity",
            value="15.5",
            unit="kg",
            evidence_ids=["EV-PDF-01", "EV-CSV-02"],
            polarity=True,
        ),
        Claim(
            id="CLM-02",
            statement="Alpha-7 UAV payload capacity was downgraded to 12.0 kg due to motor heating.",
            entity="Alpha-7 UAV",
            property="payload_capacity",
            value="12.0",
            unit="kg",
            evidence_ids=["EV-DRAFT-03"],
            polarity=False,
        ),
        Claim(
            id="CLM-03",
            statement="Pre-flight ballast verification confirms physical 15.5 kg mounting capability.",
            entity="Alpha-7 UAV",
            property="ballast_mounting",
            value="15.5 kg",
            evidence_ids=["EV-IMG-04"],
            polarity=True,
        ),
    ]

    kg_relationships = [
        KGRelationship(
            source_entity="Alpha-7 UAV",
            relation="certified_under",
            target_entity="FAA-TCDS-ARCHIVE",
            evidence_ids=["EV-PDF-01"],
            confidence=0.99,
        )
    ]

    request = ReasoningRequest(
        question="What is the certified payload capacity of the Alpha-7 UAV, and are claims of a downgrade substantiated?",
        claims=claims,
        evidence_items=evidence_items,
        kg_relationships=kg_relationships,
        enable_ollama=False,  # Demonstrating deterministic baseline reasoning
    )

    print(f"  - Total Evidence Items : {len(evidence_items)}")
    print(f"  - Extracted Claims     : {len(claims)}")
    print(f"  - Target Query         : '{request.question}'")

    # 2. Execute Reasoning Pipeline
    print("\n[Stage 1] Initializing Member 4 ReasoningPipeline...")
    pipeline = ReasoningPipeline()

    print("[Stage 2] Executing Verification & Conflict-Aware Reasoning Pipeline...")
    response = pipeline.verify(request)

    # 3. Present Results
    print("\n" + "=" * 80)
    print("  VERIFICATION DELIBERATION RESULTS")
    print("=" * 80)
    print(f"Status           : {response.status.value}")
    print(f"Conclusion Type  : {response.conclusion_type.value.upper()}")
    print(f"Confidence Score : {response.confidence * 100:.1f}% ({response.confidence:.2f})")
    print(f"Confidence Basis : {response.confidence_explanation}")
    print(f"Reasoning Mode   : {response.reasoning_mode}")

    print("\n--- Answer ---")
    print(response.answer)

    print("\n--- Summary ---")
    print(response.summary)

    print("\n--- Grounded Claims & Epistemic Status ---")
    for fact in response.facts:
        print(f"  {fact}")

    print("\n--- Inferences & Epistemic Limitations ---")
    for inf in response.inferences:
        print(f"  [*] {inf}")
    for lim in response.limitations:
        print(f"  [!] {lim}")

    print("\n--- Identified Conflicts & Resolutions ---")
    if response.conflicts:
        for c in response.conflicts:
            status = "RESOLVED" if c.is_resolved else "UNRESOLVED DEADLOCK"
            print(f"  [-] ({status}) {c.conflict_type.value}: {c.description}")
            if c.resolution_reason:
                print(f"      Resolution: {c.resolution_reason}")
    else:
        print("  None detected.")

    print("\n--- Suspicion Indicators (Non-Prejudicial Audit Signals) ---")
    if response.suspicion_indicators:
        for ind in response.suspicion_indicators:
            print(f"  [?] [{ind.severity.value}] {ind.title}: {ind.explanation}")
            print(f"      Recommended Action: {ind.recommended_verification_action}")
    else:
        print("  No significant suspicion indicators detected.")

    print("\n--- Traceable Citations (Zero Fabrication Guarantee) ---")
    for cit in response.citations:
        print(f"  {cit.formatted_citation}")

    print("\n--- Claim-Level Structured Citations ---")
    for cc in response.claim_citations:
        print(f"  Claim [{cc.claim_id}] (Polarity={cc.polarity}): {cc.statement}")
        for c_item in cc.citations:
            loc = c_item.formatted_citation
            print(f"    -> {loc}")
        if cc.missing_metadata:
            print(f"    -> Missing Info: {', '.join(cc.missing_metadata)}")

    print("\n" + "=" * 80)
    print("  DEMO COMPLETED SUCCESSFULLY — 100% OFFLINE, LOCAL & DETERMINISTIC")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
