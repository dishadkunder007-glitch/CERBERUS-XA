"""
Comprehensive Regression & Advanced Feature Test Suite for CERBERUX-XA.

Covers:
1. Contradiction graph logic: contradicts ONLY between genuine disagreements;
   identical values NEVER connected as contradictions; agreeing claims get consistent_with edges.
2. Entity-to-entity relationships: audited_by (KPMG -> ABC Industries),
   executive_of (Sarah Jenkins -> ABC Industries), subsidiary_of, owned_by.
3. Entity classification: KPMG and ABC Industries as ORGANIZATION (never PERSON);
   Sarah Jenkins and Robert Vance as PERSON; no quantity nodes for entity/person names.
4. Textual contradictions: executive/leadership conflicts, antonyms, semantic polarity.
5. Output defects: no explanation truncation (200/300 chars removed), no doubled carriage returns in CSV (\r\r\n).
6. Real-world validation on multimodal realistic documents.
"""

from pathlib import Path
import pytest
import networkx as nx

from src.claim_builder import Claim, ClaimBuilder
from src.contradiction_detector import ContradictionDetector, ContradictionResult, DetectionReport
from src.entity_extraction import (
    EntityRelationship,
    classify_entity_type,
    extract_entities_from_text,
    extract_relationships_from_text,
    RawClaim,
)
from src.graph_builder import (
    GraphBuilder,
    NODE_ENTITY,
    NODE_PERSON,
    NODE_QUANTITY,
    NODE_CLAIM,
    EDGE_CONTRADICTS,
    EDGE_CONSISTENT,
    EDGE_UNCERTAIN,
    EDGE_AUDITED_BY,
    EDGE_EXECUTIVE_OF,
    EDGE_SUBSIDIARY_OF,
    EDGE_OWNED_BY,
)
from src.report_generator import generate_csv_report, generate_json_report, generate_pdf_report


# ===========================================================================
# 1. Contradiction Graph Logic & Agreement Edges
# ===========================================================================

class TestContradictionGraphLogic:
    def test_identical_values_never_contradict(self):
        """
        When 3 claims exist (C1=5000, C2=4000, C3=5000):
        - C1 and C2 must be connected with EDGE_CONTRADICTS (5000 vs 4000).
        - C2 and C3 must be connected with EDGE_CONTRADICTS (4000 vs 5000).
        - C1 and C3 (both 5000) must NEVER be connected with EDGE_CONTRADICTS.
          They must be connected with EDGE_CONSISTENT.
        """
        claims = [
            Claim(
                claim_id="C-5000-A", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="production", value=5000.0,
                value_normalized=5000.0, unit="units", unit_normalized="units",
                date_str="Q1 2026", date_normalized="2026-Q1", source="filing.pdf",
                page_or_sheet="Page 1", original_text="Output 5,000 units",
                confidence=0.95, comparable=True, modality="actual", dimension="count",
            ),
            Claim(
                claim_id="C-4000-B", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="production", value=4000.0,
                value_normalized=4000.0, unit="units", unit_normalized="units",
                date_str="Q1 2026", date_normalized="2026-Q1", source="audit.pdf",
                page_or_sheet="Page 1", original_text="Output 4,000 units",
                confidence=0.95, comparable=True, modality="actual", dimension="count",
            ),
            Claim(
                claim_id="C-5000-C", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="production", value=5000.0,
                value_normalized=5000.0, unit="units", unit_normalized="units",
                date_str="Q1 2026", date_normalized="2026-Q1", source="warehouse.csv",
                page_or_sheet="Page 1", original_text="Output 5,000 units",
                confidence=0.95, comparable=True, modality="actual", dimension="count",
            ),
        ]

        detector = ContradictionDetector(numerical_tolerance_pct=2.0)
        report = detector.detect(claims)

        gb = GraphBuilder()
        G = gb.build(claims, report, numerical_tolerance_pct=2.0)

        # Inspect edges between C-5000-A and C-4000-B (must be contradicts)
        edges_ab = [d["edge_type"] for _, _, d in G.edges("C-5000-A", data=True) if _ == "C-5000-A"] + \
                   [d["edge_type"] for u, v, d in G.edges(data=True) if (u, v) in [("C-5000-A", "C-4000-B"), ("C-4000-B", "C-5000-A")]]
        assert EDGE_CONTRADICTS in edges_ab, "C1 (5000) and C2 (4000) must contradict"

        # Inspect edges between C-4000-B and C-5000-C (must be contradicts)
        edges_bc = [d["edge_type"] for u, v, d in G.edges(data=True) if (u, v) in [("C-4000-B", "C-5000-C"), ("C-5000-C", "C-4000-B")]]
        assert EDGE_CONTRADICTS in edges_bc, "C2 (4000) and C3 (5000) must contradict"

        # Inspect edges between C-5000-A and C-5000-C (both 5000)
        edges_ac = [d["edge_type"] for u, v, d in G.edges(data=True) if (u, v) in [("C-5000-A", "C-5000-C"), ("C-5000-C", "C-5000-A")]]
        assert EDGE_CONTRADICTS not in edges_ac, "Identical claims (5000 vs 5000) must NEVER be marked as contradictions"
        assert EDGE_CONSISTENT in edges_ac, "Identical claims (5000 vs 5000) must be marked consistent_with"

    def test_consistent_claims_receive_consistent_with_edge(self):
        """Claims within tolerance must receive EDGE_CONSISTENT edges."""
        claims = [
            Claim(
                claim_id="C-CONS-1", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="revenue", value=1000000.0,
                value_normalized=1000000.0, unit="INR", unit_normalized="INR",
                date_str="2026", date_normalized="2026", source="doc1.txt",
                page_or_sheet="Page 1", original_text="Revenue 1,000,000 INR",
                confidence=0.95, comparable=True, modality="actual", dimension="currency_INR",
            ),
            Claim(
                claim_id="C-CONS-2", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="revenue", value=1005000.0,  # 0.5% diff <= 2.0%
                value_normalized=1005000.0, unit="INR", unit_normalized="INR",
                date_str="2026", date_normalized="2026", source="doc2.txt",
                page_or_sheet="Page 1", original_text="Revenue 1,005,000 INR",
                confidence=0.95, comparable=True, modality="actual", dimension="currency_INR",
            ),
        ]
        detector = ContradictionDetector(numerical_tolerance_pct=2.0)
        report = detector.detect(claims)
        assert report.contradiction_count == 0
        assert report.consistent_count == 2

        gb = GraphBuilder()
        G = gb.build(claims, report)
        edge_types = [d["edge_type"] for u, v, d in G.edges(data=True) if (u, v) in [("C-CONS-1", "C-CONS-2"), ("C-CONS-2", "C-CONS-1")]]
        assert EDGE_CONSISTENT in edge_types
        assert EDGE_CONTRADICTS not in edge_types


# ===========================================================================
# 2. Entity Classification & Safeguards
# ===========================================================================

class TestEntityClassification:
    def test_kpmg_classified_as_organization(self):
        """KPMG must be classified as ORGANIZATION, never PERSON."""
        assert classify_entity_type("KPMG") == "ORGANIZATION"
        assert classify_entity_type("KPMG Verification Services") == "ORGANIZATION"
        assert classify_entity_type("PwC") == "ORGANIZATION"
        assert classify_entity_type("Deloitte") == "ORGANIZATION"
        assert classify_entity_type("Ernst & Young") == "ORGANIZATION"

    def test_abc_industries_classified_as_organization(self):
        """ABC Industries must be classified as ORGANIZATION."""
        assert classify_entity_type("ABC Industries") == "ORGANIZATION"
        assert classify_entity_type("ABC Industries Ltd") == "ORGANIZATION"
        assert classify_entity_type("ABC Industries Manufacturing Plant") == "ORGANIZATION"

    def test_sarah_and_robert_classified_as_person(self):
        """Sarah Jenkins and Robert Vance must be classified as PERSON."""
        assert classify_entity_type("Sarah Jenkins") == "PERSON"
        assert classify_entity_type("Robert Vance") == "PERSON"
        assert classify_entity_type("Dr. Sarah Jenkins") == "PERSON"

    def test_no_quantity_nodes_for_person_or_org_names(self):
        """
        Quantity nodes must ONLY be created for genuine numeric values.
        Text claims (CEO: Sarah Jenkins, Auditor: KPMG) must NOT create QTY:Sarah Jenkins or QTY:KPMG.
        """
        claims = [
            Claim(
                claim_id="C-EXEC-SJ", entity="ABC Industries", entity_normalized="ABC Industries",
                entity_type="ORG", attribute="ceo", value="Sarah Jenkins",
                value_normalized=None, unit="", unit_normalized="",
                date_str="2026", date_normalized="2026", source="doc.txt",
                page_or_sheet="Page 1", original_text="CEO: Sarah Jenkins",
                confidence=0.95, comparable=True, modality="actual", person="Sarah Jenkins",
            ),
            Claim(
                claim_id="C-AUDIT-KPMG", entity="ABC Industries", entity_normalized="ABC Industries",
                entity_type="ORG", attribute="auditor", value="KPMG Verification Services",
                value_normalized=None, unit="", unit_normalized="",
                date_str="2026", date_normalized="2026", source="doc.txt",
                page_or_sheet="Page 1", original_text="Auditor: KPMG Verification Services",
                confidence=0.95, comparable=True, modality="actual",
            ),
        ]
        gb = GraphBuilder()
        G = gb.build(claims)

        qty_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == NODE_QUANTITY]
        assert len(qty_nodes) == 0, f"No quantity nodes should exist for text claims, found: {qty_nodes}"
        assert not G.has_node("QTY:Sarah Jenkins")
        assert not G.has_node("QTY:KPMG Verification Services")


# ===========================================================================
# 3. Entity-to-Entity Relationships
# ===========================================================================

class TestEntityToEntityRelationships:
    def test_audited_by_relationship_extraction_and_connection(self):
        """KPMG must be connected to ABC Industries through audited_by relationship."""
        text = (
            "Entity: ABC Industries Ltd\n"
            "Auditor: KPMG Verification Services\n"
        )
        rels = extract_relationships_from_text(text, source="audit.txt")
        assert len(rels) >= 1
        audit_rel = next((r for r in rels if r.relation_type == "audited_by"), None)
        assert audit_rel is not None
        assert "ABC Industries" in audit_rel.source_entity
        assert "KPMG" in audit_rel.target_entity
        assert audit_rel.source_type == "ORGANIZATION"
        assert audit_rel.target_type == "ORGANIZATION"

        # Build graph and check edge
        gb = GraphBuilder()
        G = gb.build(claims=[], entity_relationships=rels)
        assert G.has_node(f"ENT:{audit_rel.source_entity}")
        assert G.has_node(f"ENT:{audit_rel.target_entity}")
        
        edges = G.get_edge_data(f"ENT:{audit_rel.source_entity}", f"ENT:{audit_rel.target_entity}")
        assert edges is not None
        edge_types = [data.get("edge_type") for data in edges.values()]
        assert EDGE_AUDITED_BY in edge_types

    def test_executive_of_relationship_extraction_and_connection(self):
        """Sarah Jenkins must be connected to ABC Industries through executive_of relationship."""
        text = (
            "Entity: ABC Industries Ltd\n"
            "CEO: Sarah Jenkins\n"
        )
        rels = extract_relationships_from_text(text, source="annual_report.txt")
        assert len(rels) >= 1
        exec_rel = next((r for r in rels if r.relation_type == "executive_of"), None)
        assert exec_rel is not None
        assert exec_rel.source_entity == "Sarah Jenkins"
        assert exec_rel.source_type == "PERSON"
        assert "ABC Industries" in exec_rel.target_entity

        # Build graph and check edge
        gb = GraphBuilder()
        G = gb.build(claims=[], entity_relationships=rels)
        assert G.has_node("PERSON:Sarah Jenkins")
        edges = G.get_edge_data("PERSON:Sarah Jenkins", f"ENT:{exec_rel.target_entity}")
        assert edges is not None
        edge_types = [data.get("edge_type") for data in edges.values()]
        assert EDGE_EXECUTIVE_OF in edge_types

    def test_subsidiary_and_owned_by_relationships(self):
        """Verify subsidiary_of and owned_by relationships."""
        text = (
            "ABC Industries Ltd is a subsidiary of Apex Dynamics Corp.\n"
            "Apex Dynamics Corp is owned by Zenith Holdings Group.\n"
        )
        rels = extract_relationships_from_text(text, source="corp_structure.txt")
        rel_types = {r.relation_type for r in rels}
        assert "subsidiary_of" in rel_types
        assert "owned_by" in rel_types


# ===========================================================================
# 4. Textual Contradictions: Leadership, Semantic & Antonyms
# ===========================================================================

class TestTextContradictions:
    def test_executive_name_conflict(self):
        """Executive attribute conflict between Sarah Jenkins and Robert Vance."""
        claims = [
            Claim(
                claim_id="C-EX-1", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="executive", value="Sarah Jenkins",
                value_normalized=None, unit="", unit_normalized="",
                date_str="2026", date_normalized="2026", source="filing.txt",
                page_or_sheet="Page 1", original_text="Executive: Sarah Jenkins",
                confidence=0.92, comparable=True, modality="actual", person="Sarah Jenkins",
            ),
            Claim(
                claim_id="C-EX-2", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="executive", value="Robert Vance",
                value_normalized=None, unit="", unit_normalized="",
                date_str="2026", date_normalized="2026", source="audit.txt",
                page_or_sheet="Page 1", original_text="Executive: Robert Vance",
                confidence=0.92, comparable=True, modality="actual", person="Robert Vance",
            ),
        ]
        report = ContradictionDetector().detect(claims)
        assert report.contradiction_count == 1
        assert report.contradictions[0].status == "CONTRADICTION"

    def test_matching_executive_names_are_consistent(self):
        """Same executive name across sources must be CONSISTENT."""
        claims = [
            Claim(
                claim_id="C-EX-SAME-1", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="executive", value="Sarah Jenkins",
                value_normalized=None, unit="", unit_normalized="",
                date_str="2026", date_normalized="2026", source="filing.txt",
                page_or_sheet="Page 1", original_text="Executive: Sarah Jenkins",
                confidence=0.92, comparable=True, modality="actual", person="Sarah Jenkins",
            ),
            Claim(
                claim_id="C-EX-SAME-2", entity="Apex Corp", entity_normalized="Apex Corp",
                entity_type="ORG", attribute="executive", value="Sarah Jenkins",
                value_normalized=None, unit="", unit_normalized="",
                date_str="2026", date_normalized="2026", source="press.txt",
                page_or_sheet="Page 1", original_text="Executive: Sarah Jenkins",
                confidence=0.92, comparable=True, modality="actual", person="Sarah Jenkins",
            ),
        ]
        report = ContradictionDetector().detect(claims)
        assert report.contradiction_count == 0
        assert report.consistent_count == 2

    def test_semantic_antonym_contradictions(self):
        """Operational vs Shutdown must be flagged as CONTRADICTION."""
        claims = [
            Claim(
                claim_id="C-ST-1", entity="ABC Industries", entity_normalized="ABC Industries",
                entity_type="ORG", attribute="status", value="operational",
                value_normalized=None, unit="", unit_normalized="",
                date_str="January 2026", date_normalized="2026-01", source="report.pdf",
                page_or_sheet="Page 1", original_text="Facility status: operational",
                confidence=0.90, comparable=True, modality="actual",
            ),
            Claim(
                claim_id="C-ST-2", entity="ABC Industries", entity_normalized="ABC Industries",
                entity_type="ORG", attribute="status", value="shutdown",
                value_normalized=None, unit="", unit_normalized="",
                date_str="January 2026", date_normalized="2026-01", source="inspection.txt",
                page_or_sheet="Page 1", original_text="Facility status: shutdown",
                confidence=0.90, comparable=True, modality="actual",
            ),
        ]
        report = ContradictionDetector().detect(claims)
        assert report.contradiction_count == 1
        assert report.contradictions[0].status == "CONTRADICTION"


# ===========================================================================
# 5. Output Defects: No Truncation, No Double CRLF
# ===========================================================================

class TestOutputDefects:
    def test_csv_line_endings_no_double_returns(self, tmp_path):
        """CSV export must never contain doubled carriage returns (\\r\\r\\n)."""
        claims = [
            Claim(
                claim_id="C-1", entity="Acme Corp", entity_normalized="Acme Corp",
                entity_type="ORG", attribute="revenue", value=100.0,
                value_normalized=100.0, unit="INR", unit_normalized="INR",
                date_str="2026", date_normalized="2026", source="d1.txt",
                page_or_sheet="P1", original_text="Rev 100",
                confidence=0.9, comparable=True,
            ),
            Claim(
                claim_id="C-2", entity="Acme Corp", entity_normalized="Acme Corp",
                entity_type="ORG", attribute="revenue", value=200.0,
                value_normalized=200.0, unit="INR", unit_normalized="INR",
                date_str="2026", date_normalized="2026", source="d2.txt",
                page_or_sheet="P1", original_text="Rev 200",
                confidence=0.9, comparable=True,
            ),
        ]
        report = ContradictionDetector().detect(claims)
        csv_file = tmp_path / "test_report.csv"
        generate_csv_report(report, csv_file)

        raw_bytes = csv_file.read_bytes()
        assert b"\r\r\n" not in raw_bytes, "CSV file contains doubled carriage returns (\\r\\r\\n)"

    def test_complete_explanations_preserved(self, tmp_path):
        """Explanations exceeding 200 characters must NOT be truncated."""
        long_explanation = (
            "CONTRADICTION DETECTED for 'Apex Dynamics Corp' – 'production'. "
            "Values differ significantly across multiple documents: "
            "Filing report indicates exactly 5000 units while the independent verification "
            "report completed by external auditors shows 4000 units for Q1 2026. "
            "This exceeds 200 characters and must be fully preserved across all exports and graph nodes."
        )
        assert len(long_explanation) > 250

        c_res = ContradictionResult(
            contradiction_id="CONTR-LONG",
            entity="Apex Dynamics Corp",
            entity_normalized="Apex Dynamics Corp",
            attribute="production",
            status="CONTRADICTION",
            conflicting_claims=[],
            explanation=long_explanation,
            confidence=0.95,
        )
        report = DetectionReport(
            total_claims=2,
            contradictions=[c_res],
            consistent_groups=[],
            uncertain_groups=[],
        )

        # JSON
        json_str = generate_json_report(report, [])
        assert long_explanation in json_str, "JSON report truncated explanation"

        # CSV
        csv_str = generate_csv_report(report)
        assert long_explanation in csv_str, "CSV report truncated explanation"


# ===========================================================================
# 6. Real-World Multi-Document Validation
# ===========================================================================

class TestRealWorldMultiDocumentValidation:
    def test_real_world_validation_pipeline(self, tmp_path):
        """Run complete pipeline on the realistic validation test documents."""
        from main import run_pipeline

        val_dir = Path("data/real_world_validation")
        assert val_dir.exists()
        files = list(val_dir.glob("*.*"))
        assert len(files) >= 4

        result = run_pipeline(
            file_paths=files,
            numerical_tolerance_pct=2.0,
            output_dir=tmp_path / "reports",
        )

        report = result["report"]
        assert report.total_claims > 0
        assert report.contradiction_count >= 1, "Must detect genuine contradictions"
        assert report.consistent_count >= 1, "Must preserve consistent facts"

        # Check graph
        graph = result["graph"]
        assert graph.number_of_nodes() > 10
        assert graph.number_of_edges() > 10

        # Check edge types in graph
        edge_types = {d.get("edge_type") for u, v, d in graph.edges(data=True)}
        assert EDGE_CONTRADICTS in edge_types
        assert EDGE_CONSISTENT in edge_types
        assert EDGE_AUDITED_BY in edge_types
        assert EDGE_EXECUTIVE_OF in edge_types
