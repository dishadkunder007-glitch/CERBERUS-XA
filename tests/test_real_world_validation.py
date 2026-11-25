"""
Tests reproducing current failures for new requirements.
1. All 5 conflicts in data/real_world_validation/
2. Extractor generalization
3. OCR confidence threshold
4. Evidence-based contradiction confidence breakdown
5. Duplicate detection module
6. Source reliability hook
7. Teammate hooks (flags, verdict, injection resistance)
"""

import pytest
from pathlib import Path

from src.extractors.document_loader import load_multiple_documents
from src.entity_extraction import (
    extract_entities_from_document,
    extract_entities_from_text,
    RawClaim,
)
from src.claim_builder import ClaimBuilder, Claim
from src.contradiction_detector import ContradictionDetector, ContradictionResult


class TestRealWorldAllFiveConflicts:
    """Problem 1: Real-world validation must detect all 5 conflicts."""

    def test_all_five_conflicts_detected(self):
        val_dir = Path("data/real_world_validation")
        assert val_dir.exists(), "real_world_validation directory must exist"

        files = [
            val_dir / "audit_q1.txt",
            val_dir / "filing_q1.txt",
            val_dir / "erp_q1.csv",
            val_dir / "corp_governance.txt",
        ]
        docs = load_multiple_documents(files)
        raw_claims = []
        for doc in docs:
            raw_claims.extend(extract_entities_from_document(doc))

        builder = ClaimBuilder()
        claims = builder.build(raw_claims)
        detector = ContradictionDetector()
        report = detector.detect(claims)

        # We must detect all 5 conflicting attributes:
        # 1. production (4,000 vs 5,000)
        # 2. revenue (20,00,000 vs 25,00,000)
        # 3. executive / ceo (Robert Vance vs Sarah Jenkins)
        # 4. status (shutdown vs operational)
        # 5. compliance (non-compliant vs certified)
        attrs = {c.attribute.lower() for c in report.contradictions}
        
        # Check canonicalized or raw names
        has_production = "production" in attrs
        has_revenue = "revenue" in attrs
        has_exec = any(a in attrs for a in ("executive", "ceo", "leadership"))
        has_status = any(a in attrs for a in ("status", "operational status"))
        has_compliance = any(a in attrs for a in ("compliance", "compliance rating"))

        assert has_production, f"Missing production contradiction in {attrs}"
        assert has_revenue, f"Missing revenue contradiction in {attrs}"
        assert has_exec, f"Missing executive/ceo contradiction in {attrs}"
        assert has_status, f"Missing status contradiction in {attrs}"
        assert has_compliance, f"Missing compliance contradiction in {attrs}"
        assert report.contradiction_count >= 5, f"Expected >= 5 contradictions, got {report.contradiction_count}"
