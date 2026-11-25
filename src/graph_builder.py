"""
Graph Builder – constructs an enriched NetworkX knowledge and conflict graph.

Nodes:
  - Entity nodes (Company / Organization)
  - Person nodes (Executives / Signatories)
  - Date / Period nodes (Months, Quarters, Financial Years)
  - Quantity nodes (Values and Units – strictly for numeric measurements)
  - Claim nodes (Centralized statement record)
  - Source document nodes (PDF, PNG, XLSX, CSV, TXT)

Edges:
  - entity -> claim (HAS_CLAIM)
  - claim -> source (FROM_SOURCE)
  - claim -> person (ATTRIBUTED_TO)
  - claim -> date (HAS_DATE)
  - claim -> quantity (HAS_QUANTITY)
  - claim <-> claim (CONTRADICTS / CONSISTENT_WITH / UNCERTAIN_WITH)
  - entity -> entity (AUDITED_BY / OWNED_BY / SUBSIDIARY_OF)
  - person -> entity (EXECUTIVE_OF / DIRECTOR_OF / CEO_OF)
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

import networkx as nx

from .claim_builder import Claim
from .contradiction_detector import ContradictionResult, DetectionReport, ANTONYM_PAIRS
from .entity_extraction import EntityRelationship, classify_entity_type

logger = logging.getLogger(__name__)

# Node type constants
NODE_ENTITY = "entity"
NODE_PERSON = "person"
NODE_DATE = "date"
NODE_QUANTITY = "quantity"
NODE_CLAIM = "claim"
NODE_SOURCE = "source"

# Edge type constants
EDGE_HAS_CLAIM = "has_claim"
EDGE_FROM_SOURCE = "from_source"
EDGE_CONTRADICTS = "contradicts"
EDGE_CONSISTENT = "consistent_with"
EDGE_UNCERTAIN = "uncertain_with"
EDGE_HAS_DATE = "has_date"
EDGE_HAS_QUANTITY = "has_quantity"
EDGE_ATTRIBUTED_TO = "attributed_to"
EDGE_AUDITED_BY = "audited_by"
EDGE_EXECUTIVE_OF = "executive_of"
EDGE_OWNED_BY = "owned_by"
EDGE_SUBSIDIARY_OF = "subsidiary_of"


class GraphBuilder:
    """Builds a multigraph connecting entities, people, dates, quantities, claims, and documents."""

    def __init__(self):
        self.G = nx.MultiDiGraph()
        self.source_reliabilities: dict[str, tuple[float, str]] = {}

    def set_source_reliability(self, source_id: str, score: float, reason: str = "") -> None:
        """Set reliability score (0.0 to 1.0) and optional reason for a source document."""
        self.source_reliabilities[source_id] = (max(0.0, min(1.0, float(score))), reason)

    def build(
        self,
        claims: list[Claim],
        contradictions: list[ContradictionResult] | Any = None,
        consistent_groups: Optional[list[list[Claim]]] = None,
        entity_relationships: Optional[list[EntityRelationship]] = None,
        numerical_tolerance_pct: float = 2.0,
    ) -> nx.MultiDiGraph:
        """
        Build the comprehensive multi-node knowledge and contradiction graph.
        Evaluates claim pairs so that:
        - contradicts edges are ONLY added between claims whose values genuinely disagree.
        - consistent_with edges are added between claims that agree.
        - identical values NEVER receive a contradicts edge.
        - entity-to-entity relationships (audited_by, executive_of, etc.) are explicitly connected.
        - quantity nodes are strictly created for numeric quantities, never for people or organizations.
        """
        self.G.clear()

        # Handle DetectionReport object passed directly
        if hasattr(contradictions, "contradictions"):
            if consistent_groups is None:
                consistent_groups = getattr(contradictions, "consistent_groups", [])
            contradictions = getattr(contradictions, "contradictions", [])
        elif contradictions is None:
            contradictions = []

        if consistent_groups is None:
            consistent_groups = []

        # 1. Add nodes and structural edges from claims
        for claim in claims:
            # Claim node
            claim_id = claim.claim_id
            if not self.G.has_node(claim_id):
                self.G.add_node(
                    claim_id,
                    label=f"{claim.attribute}={claim.value} {claim.unit}".strip(),
                    node_type=NODE_CLAIM,
                    attribute=claim.attribute,
                    value=str(claim.value),
                    unit=claim.unit,
                    date=claim.date_str,
                    source=claim.source,
                    page_or_sheet=claim.page_or_sheet,
                    confidence=claim.confidence,
                    modality=claim.modality,
                    ocr_confidence=getattr(claim, "ocr_confidence", 1.0),
                    flags=getattr(claim, "flags", []),
                )

            # Entity node (Company/Organization)
            entity_id = f"ENT:{claim.entity_normalized}"
            if not self.G.has_node(entity_id):
                self.G.add_node(
                    entity_id,
                    label=claim.entity_normalized,
                    node_type=NODE_ENTITY,
                    entity_type="ORGANIZATION",
                )
            self._add_edge_if_not_exists(entity_id, claim_id, EDGE_HAS_CLAIM)

            # Source document node with reliability metadata
            source_id = f"SRC:{claim.source}"
            rel_score, rel_reason = self.source_reliabilities.get(claim.source, (1.0, "Verified source"))
            if not self.G.has_node(source_id):
                self.G.add_node(
                    source_id,
                    label=claim.source,
                    node_type=NODE_SOURCE,
                    source_reliability=rel_score,
                    source_reliability_reason=rel_reason,
                )
            else:
                self.G.nodes[source_id]["source_reliability"] = rel_score
                self.G.nodes[source_id]["source_reliability_reason"] = rel_reason
            self._add_edge_if_not_exists(claim_id, source_id, EDGE_FROM_SOURCE)

            # Date node (Temporal provenance)
            if claim.date_normalized or claim.date_str:
                d_val = claim.date_normalized or claim.date_str
                date_id = f"DATE:{d_val}"
                if not self.G.has_node(date_id):
                    self.G.add_node(
                        date_id,
                        label=d_val,
                        node_type=NODE_DATE,
                    )
                self._add_edge_if_not_exists(claim_id, date_id, EDGE_HAS_DATE)

            # Quantity node (Value and Unit) – ONLY for genuine numeric measurements/quantities
            is_numeric = (
                claim.value_normalized is not None
                or (isinstance(claim.value, (int, float)) and not isinstance(claim.value, bool))
            )
            if is_numeric:
                q_label = f"{claim.value} {claim.unit}".strip()
                quantity_id = f"QTY:{q_label}"
                if not self.G.has_node(quantity_id):
                    self.G.add_node(
                        quantity_id,
                        label=q_label,
                        node_type=NODE_QUANTITY,
                        value=str(claim.value),
                        unit=claim.unit,
                    )
                self._add_edge_if_not_exists(claim_id, quantity_id, EDGE_HAS_QUANTITY)

            # Person node (only if an actual person is mentioned)
            if claim.person and classify_entity_type(claim.person) == "PERSON":
                person_id = f"PERSON:{claim.person}"
                if not self.G.has_node(person_id):
                    self.G.add_node(
                        person_id,
                        label=claim.person,
                        node_type=NODE_PERSON,
                        entity_type="PERSON",
                    )
                self._add_edge_if_not_exists(claim_id, person_id, EDGE_ATTRIBUTED_TO)

        # 2. Add relational edges from contradiction/consistency detection
        def _evaluate_pair(ca: Claim, cb: Claim) -> tuple[str, str]:
            """Determine edge type ('contradicts', 'consistent_with', 'uncertain_with') and explanation."""
            if ca.attribute.lower() != cb.attribute.lower():
                return None, ""

            # Numeric evaluation
            is_num_a = ca.value_normalized is not None or isinstance(ca.value, (int, float))
            is_num_b = cb.value_normalized is not None or isinstance(cb.value, (int, float))

            if is_num_a and is_num_b:
                va = ca.value_normalized if ca.value_normalized is not None else float(ca.value)
                vb = cb.value_normalized if cb.value_normalized is not None else float(cb.value)

                # Incompatible dimensions
                if ca.dimension and cb.dimension and ca.dimension != cb.dimension:
                    return EDGE_UNCERTAIN, f"Incompatible dimensions: {ca.dimension} vs {cb.dimension}"

                if va == vb:
                    return EDGE_CONSISTENT, f"Consistent values: both report {ca.value} {ca.unit}."

                mean_val = (abs(va) + abs(vb)) / 2.0
                pct_diff = (abs(va - vb) / mean_val * 100.0) if mean_val != 0 else 0.0

                if pct_diff <= numerical_tolerance_pct:
                    return EDGE_CONSISTENT, (
                        f"Consistent values within {numerical_tolerance_pct}% tolerance "
                        f"({pct_diff:.2f}% diff: {va} vs {vb})."
                    )
                else:
                    return EDGE_CONTRADICTS, (
                        f"Contradiction: {ca.source} reports {ca.value} {ca.unit} vs "
                        f"{cb.source} reports {cb.value} {cb.unit} "
                        f"(diff {pct_diff:.1f}% > {numerical_tolerance_pct}%)."
                    )

            # Textual evaluation
            sa = str(ca.value).strip().lower()
            sb = str(cb.value).strip().lower()

            if sa == sb:
                return EDGE_CONSISTENT, f"Consistent statements: both report '{ca.value}'."

            # Check antonyms
            is_antonym = False
            for pos_set, neg_set in ANTONYM_PAIRS:
                if (sa in pos_set and sb in neg_set) or (sa in neg_set and sb in pos_set):
                    is_antonym = True
                    break

            if is_antonym:
                return EDGE_CONTRADICTS, f"Semantic textual contradiction: '{ca.value}' vs '{cb.value}'."

            # Leadership name conflict
            if ca.attribute.lower() in ("ceo", "director", "auditor", "executive", "coo", "cfo", "manager"):
                return EDGE_CONTRADICTS, f"Conflicting leadership names: '{ca.value}' ({ca.source}) vs '{cb.value}' ({cb.source})."

            return EDGE_UNCERTAIN, f"Different textual descriptions: '{ca.value}' vs '{cb.value}'."

        # Add edges from contradictions
        for contradiction in contradictions:
            claim_ids = [c for c in contradiction.conflicting_claims if self.G.has_node(c.claim_id)]
            for i, ca in enumerate(claim_ids):
                for cb in claim_ids[i + 1:]:
                    etype, reason = _evaluate_pair(ca, cb)
                    if not etype:
                        etype = EDGE_CONTRADICTS if contradiction.status == "CONTRADICTION" else EDGE_CONSISTENT
                        reason = contradiction.explanation
                    self.G.add_edge(
                        ca.claim_id,
                        cb.claim_id,
                        edge_type=etype,
                        explanation=reason,
                        contradiction_id=contradiction.contradiction_id,
                        confidence=getattr(contradiction, "confidence", 1.0),
                        confidence_breakdown=getattr(contradiction, "confidence_breakdown", {}),
                        confidence_explanation=getattr(contradiction, "confidence_explanation", ""),
                        verdict=getattr(contradiction, "verdict", "contradiction"),
                    )

        # Add edges from consistent groups
        for grp in consistent_groups:
            c_nodes = [c for c in grp if self.G.has_node(c.claim_id)]
            for i, ca in enumerate(c_nodes):
                for cb in c_nodes[i + 1:]:
                    if not self._has_claim_rel_edge(ca.claim_id, cb.claim_id):
                        etype, reason = _evaluate_pair(ca, cb)
                        self.G.add_edge(
                            ca.claim_id,
                            cb.claim_id,
                            edge_type=etype or EDGE_CONSISTENT,
                            explanation=reason or f"Consistent: {ca.value} agrees with {cb.value}.",
                        )

        # 3. Add Entity-to-Entity and Person-to-Entity Relationships
        all_relationships = list(entity_relationships or [])

        # In addition, infer relationships from leadership and audit claims
        for claim in claims:
            if claim.attribute.lower() == "auditor" and claim.value:
                auditor_name = str(claim.value).strip()
                all_relationships.append(
                    EntityRelationship(
                        source_entity=claim.entity_normalized,
                        source_type="ORGANIZATION",
                        target_entity=auditor_name,
                        target_type="ORGANIZATION",
                        relation_type=EDGE_AUDITED_BY,
                        source_doc=claim.source,
                        page_or_sheet=claim.page_or_sheet,
                        evidence_text=claim.original_text,
                    )
                )
            elif claim.attribute.lower() in ("ceo", "executive", "director", "managing director", "coo", "cfo") and claim.value:
                person_name = str(claim.value).strip()
                if classify_entity_type(person_name) == "PERSON":
                    all_relationships.append(
                        EntityRelationship(
                            source_entity=person_name,
                            source_type="PERSON",
                            target_entity=claim.entity_normalized,
                            target_type="ORGANIZATION",
                            relation_type=EDGE_EXECUTIVE_OF,
                            source_doc=claim.source,
                            page_or_sheet=claim.page_or_sheet,
                            evidence_text=claim.original_text,
                        )
                    )

        for rel in all_relationships:
            # Source node
            if rel.source_type == "PERSON" or classify_entity_type(rel.source_entity) == "PERSON":
                src_id = f"PERSON:{rel.source_entity}"
                src_type = NODE_PERSON
            else:
                src_id = f"ENT:{rel.source_entity}"
                src_type = NODE_ENTITY

            if not self.G.has_node(src_id):
                self.G.add_node(src_id, label=rel.source_entity, node_type=src_type)

            # Target node
            if rel.target_type == "PERSON" or classify_entity_type(rel.target_entity) == "PERSON":
                tgt_id = f"PERSON:{rel.target_entity}"
                tgt_type = NODE_PERSON
            else:
                tgt_id = f"ENT:{rel.target_entity}"
                tgt_type = NODE_ENTITY

            if not self.G.has_node(tgt_id):
                self.G.add_node(tgt_id, label=rel.target_entity, node_type=tgt_type)

            self._add_edge_if_not_exists(
                src_id,
                tgt_id,
                edge_type=rel.relation_type,
                label=rel.relation_type,
                source=rel.source_doc,
                evidence=rel.evidence_text,
            )

        logger.info(
            "Graph built: %d nodes, %d edges",
            self.G.number_of_nodes(),
            self.G.number_of_edges(),
        )
        return self.G

    def _has_claim_rel_edge(self, u: str, v: str) -> bool:
        """Check if any relational edge already exists between two claims."""
        if self.G.has_edge(u, v):
            for _, edge_data in self.G[u][v].items():
                if edge_data.get("edge_type") in (EDGE_CONTRADICTS, EDGE_CONSISTENT, EDGE_UNCERTAIN):
                    return True
        if self.G.has_edge(v, u):
            for _, edge_data in self.G[v][u].items():
                if edge_data.get("edge_type") in (EDGE_CONTRADICTS, EDGE_CONSISTENT, EDGE_UNCERTAIN):
                    return True
        return False

    def _add_edge_if_not_exists(self, u: str, v: str, edge_type: str, **attrs):
        """Prevent adding duplicate structural or relational edges."""
        if self.G.has_edge(u, v):
            for _, edge_data in self.G[u][v].items():
                if edge_data.get("edge_type") == edge_type:
                    return
        self.G.add_edge(u, v, edge_type=edge_type, **attrs)

    def to_json(self, output_path: Optional[str | Path] = None) -> dict:
        """Export graph as a JSON-serialisable dict (node-link format)."""
        data = nx.node_link_data(self.G)
        if output_path:
            Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.info("Graph exported to JSON: %s", output_path)
        return data

    def to_graphml(self, output_path: str | Path) -> str:
        """Export graph to GraphML format, ensuring all node and edge attributes are GraphML-serializable."""
        output_path = Path(output_path)
        G_export = nx.MultiDiGraph()
        for node, data in self.G.nodes(data=True):
            clean_data = {}
            for k, v in data.items():
                if isinstance(v, (list, dict)):
                    clean_data[k] = json.dumps(v)
                else:
                    clean_data[k] = v
            G_export.add_node(node, **clean_data)

        for u, v, k, data in self.G.edges(data=True, keys=True):
            clean_data = {}
            for dk, dv in data.items():
                if isinstance(dv, (list, dict)):
                    clean_data[dk] = json.dumps(dv)
                else:
                    clean_data[dk] = dv
            G_export.add_edge(u, v, key=k, **clean_data)

        nx.write_graphml(G_export, str(output_path))
        logger.info("Graph exported to GraphML: %s", output_path)
        return str(output_path)

    def get_plotly_data(self) -> dict[str, Any]:
        """
        Return Plotly-compatible traces for interactive graph visualization.
        Provides distinct shapes and colors for all node types and typed edges.
        """
        try:
            pos = nx.spring_layout(self.G, seed=42, k=1.8, iterations=50)
        except Exception:
            pos = {n: (0.0, 0.0) for n in self.G.nodes()}

        type_config = {
            NODE_ENTITY:   {"color": "#58A6FF", "symbol": "circle", "size": 22, "name": "Company/Entity"},
            NODE_PERSON:   {"color": "#D2A8FF", "symbol": "diamond", "size": 18, "name": "Person"},
            NODE_DATE:     {"color": "#FFA657", "symbol": "hourglass", "size": 16, "name": "Date / Period"},
            NODE_QUANTITY: {"color": "#7EE787", "symbol": "triangle-up", "size": 16, "name": "Quantity"},
            NODE_CLAIM:    {"color": "#238636", "symbol": "square", "size": 14, "name": "Claim"},
            NODE_SOURCE:   {"color": "#F0883E", "symbol": "pentagon", "size": 18, "name": "Document Source"},
        }

        node_groups: dict[str, dict] = {
            ntype: {"x": [], "y": [], "text": [], "hovertext": []}
            for ntype in type_config
        }

        for node, data in self.G.nodes(data=True):
            ntype = data.get("node_type", NODE_CLAIM)
            if ntype not in node_groups:
                ntype = NODE_CLAIM

            x, y = pos.get(node, (0.0, 0.0))
            label = data.get("label", node)
            hover = f"<b>{label}</b><br>Type: {ntype.upper()}"
            if ntype == NODE_CLAIM:
                hover += (
                    f"<br>Attribute: {data.get('attribute', '')}"
                    f"<br>Value: {data.get('value', '')} {data.get('unit', '')}"
                    f"<br>Date: {data.get('date', '')}"
                    f"<br>Source: {data.get('source', '')}"
                    f"<br>Modality: {data.get('modality', 'actual')}"
                )

            node_groups[ntype]["x"].append(x)
            node_groups[ntype]["y"].append(y)
            node_groups[ntype]["text"].append(label[:22] + "…" if len(label) > 22 else label)
            node_groups[ntype]["hovertext"].append(hover)

        # Node traces
        node_traces = []
        for ntype, cfg in type_config.items():
            grp = node_groups[ntype]
            if not grp["x"]:
                continue
            trace = {
                "x": grp["x"],
                "y": grp["y"],
                "text": grp["text"],
                "hovertext": grp["hovertext"],
                "hoverinfo": "text",
                "mode": "markers+text",
                "textposition": "top center",
                "name": cfg["name"],
                "marker": {
                    "size": cfg["size"],
                    "color": cfg["color"],
                    "symbol": cfg["symbol"],
                    "line": {"color": "#161B22", "width": 1.5},
                },
                "textfont": {"color": "#E6EDF3", "size": 10},
            }
            node_traces.append(trace)

        # Edge traces grouped by edge type
        edge_colors = {
            EDGE_CONTRADICTS:   "#FF5252",
            EDGE_CONSISTENT:    "#2ECC71",
            EDGE_UNCERTAIN:     "#F39C12",
            EDGE_AUDITED_BY:    "#00D2D3",
            EDGE_EXECUTIVE_OF:  "#A55EEA",
            EDGE_OWNED_BY:      "#45AAF2",
            EDGE_SUBSIDIARY_OF: "#26DE81",
            EDGE_HAS_CLAIM:     "#30363D",
            EDGE_FROM_SOURCE:   "#484F58",
            EDGE_HAS_DATE:      "#8B949E",
            EDGE_HAS_QUANTITY:  "#58A6FF",
            EDGE_ATTRIBUTED_TO: "#BC8CFF",
        }

        edge_groups: dict[str, dict] = {
            etype: {"x": [], "y": []} for etype in edge_colors
        }

        for u, v, data in self.G.edges(data=True):
            etype = data.get("edge_type", EDGE_HAS_CLAIM)
            if etype not in edge_groups:
                etype = EDGE_HAS_CLAIM
            x0, y0 = pos.get(u, (0.0, 0.0))
            x1, y1 = pos.get(v, (0.0, 0.0))
            edge_groups[etype]["x"].extend([x0, x1, None])
            edge_groups[etype]["y"].extend([y0, y1, None])

        edge_traces = []
        for etype, grp in edge_groups.items():
            if not grp["x"]:
                continue
            color = edge_colors.get(etype, "#30363D")
            width = 3.0 if etype in (EDGE_CONTRADICTS, EDGE_AUDITED_BY, EDGE_EXECUTIVE_OF) else (2.0 if etype in (EDGE_CONSISTENT, EDGE_UNCERTAIN) else 1.0)
            edge_traces.append({
                "x": grp["x"],
                "y": grp["y"],
                "line": {"width": width, "color": color},
                "hoverinfo": "none",
                "mode": "lines",
                "name": etype.replace("_", " ").title(),
                "showlegend": (etype in (
                    EDGE_CONTRADICTS, EDGE_CONSISTENT, EDGE_UNCERTAIN,
                    EDGE_AUDITED_BY, EDGE_EXECUTIVE_OF, EDGE_OWNED_BY, EDGE_SUBSIDIARY_OF
                )),
            })

        layout = {
            "title": "Knowledge & Conflict Graph",
            "showlegend": True,
            "hovermode": "closest",
            "margin": {"b": 20, "l": 20, "r": 20, "t": 40},
            "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
            "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
            "paper_bgcolor": "#0E1117",
            "plot_bgcolor": "#0E1117",
            "legend": {"font": {"color": "#F0F6FC"}},
        }

        return {
            "node_traces": node_traces,
            "edge_traces": edge_traces,
            "layout": layout,
        }
