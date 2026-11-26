"""
Tests for graph builder and report generator.
"""

import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.claim_builder import Claim, _make_claim_id
from src.contradiction_detector import ContradictionResult


def _make_claim(entity="ABC Corp", attribute="production", value=5000, source="test.pdf"):
    return Claim(
        claim_id=_make_claim_id(entity, attribute, source, value),
        entity=entity, entity_normalized=entity, entity_type="ORG",
        attribute=attribute, value=value, value_normalized=float(value),
        unit="units", unit_normalized="units",
        date_str="2026", date_normalized="2026",
        source=source, page_or_sheet="Page 1",
        original_text=f"{entity} {attribute} {value}",
        confidence=0.9, comparable=True,
    )


def _make_contradiction(claims, cid="CONTR-0001"):
    return ContradictionResult(
        contradiction_id=cid,
        entity=claims[0].entity_normalized,
        entity_normalized=claims[0].entity_normalized,
        attribute=claims[0].attribute,
        status="CONTRADICTION",
        conflicting_claims=claims,
        explanation="Test contradiction.",
        confidence=0.95,
    )


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

class TestGraphBuilder:
    def test_builds_nodes(self):
        from src.graph_builder import GraphBuilder
        claims = [
            _make_claim(source="a.pdf"),
            _make_claim(value=3000, source="b.pdf"),
        ]
        gb = GraphBuilder()
        G = gb.build(claims, [])
        assert G.number_of_nodes() > 0

    def test_entity_source_nodes_present(self):
        from src.graph_builder import GraphBuilder
        claims = [_make_claim(source="report.pdf")]
        gb = GraphBuilder()
        G = gb.build(claims, [])
        node_labels = [G.nodes[n].get("node_type") for n in G.nodes]
        assert "entity" in node_labels
        assert "source" in node_labels
        assert "claim" in node_labels

    def test_contradiction_edge_added(self):
        from src.graph_builder import GraphBuilder, EDGE_CONTRADICTS
        claims = [
            _make_claim(source="a.pdf"),
            _make_claim(value=3000, source="b.pdf"),
        ]
        contradiction = _make_contradiction(claims)
        gb = GraphBuilder()
        G = gb.build(claims, [contradiction])
        edge_types = [d.get("edge_type") for _, _, d in G.edges(data=True)]
        assert EDGE_CONTRADICTS in edge_types

    def test_to_json_serializable(self):
        from src.graph_builder import GraphBuilder
        claims = [_make_claim()]
        gb = GraphBuilder()
        gb.build(claims, [])
        data = gb.to_json()
        # Must be JSON serializable
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

    def test_to_graphml(self, tmp_path):
        from src.graph_builder import GraphBuilder
        claims = [_make_claim()]
        gb = GraphBuilder()
        gb.build(claims, [])
        path = tmp_path / "graph.graphml"
        gb.to_graphml(path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_plotly_data_structure(self):
        from src.graph_builder import GraphBuilder
        claims = [_make_claim()]
        gb = GraphBuilder()
        gb.build(claims, [])
        pdata = gb.get_plotly_data()
        assert "node_traces" in pdata
        assert "edge_traces" in pdata
        assert "layout" in pdata


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------

class TestReportGenerator:
    def _make_report(self):
        from src.contradiction_detector import DetectionReport
        claims = [
            _make_claim(source="a.pdf"),
            _make_claim(value=3000, source="b.pdf"),
        ]
        contradiction = _make_contradiction(claims)
        return DetectionReport(
            total_claims=2,
            contradictions=[contradiction],
            consistent_groups=[],
            uncertain_groups=[],
        ), [_make_claim(source="a.pdf")]

    def test_json_report(self):
        from src.report_generator import generate_json_report
        report, claims = self._make_report()
        json_str = generate_json_report(report, claims)
        data = json.loads(json_str)
        assert data["summary"]["contradictions"] == 1
        assert len(data["contradictions"]) == 1
        assert "conflicting_claims" in data["contradictions"][0]

    def test_csv_report(self):
        from src.report_generator import generate_csv_report
        report, _ = self._make_report()
        csv_str = generate_csv_report(report)
        assert "CONTR-0001" in csv_str
        assert "CONTRADICTION" in csv_str

    def test_pdf_report(self, tmp_path):
        from src.report_generator import generate_pdf_report
        try:
            import reportlab
        except ImportError:
            pytest.skip("reportlab not installed")
        report, claims = self._make_report()
        path = tmp_path / "report.pdf"
        result = generate_pdf_report(report, claims, path)
        if result:  # reportlab available
            assert Path(result).exists()

    def test_json_report_saved(self, tmp_path):
        from src.report_generator import generate_json_report
        report, claims = self._make_report()
        output = tmp_path / "report.json"
        generate_json_report(report, claims, output)
        assert output.exists()
        data = json.loads(output.read_text())
        assert "summary" in data

    def test_csv_report_saved(self, tmp_path):
        from src.report_generator import generate_csv_report
        report, _ = self._make_report()
        output = tmp_path / "report.csv"
        generate_csv_report(report, output)
        assert output.exists()
