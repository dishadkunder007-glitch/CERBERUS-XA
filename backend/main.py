"""
CERBERUS-XA — Unified Multi-Modal Intelligence Backend
Orchestrates:
  - Member 2: Multimodal Ingestion & Extraction (backend/multimodal)
  - Member 3: Knowledge Graph, Entity Resolution & Contradictions (backend/knowledge_graph)
  - Member 4: Conflict-Aware Reasoning & Traceable Citations (backend/reasoning)
"""

import sys
import os
import io
import csv
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
import pymupdf

# Ensure backend and knowledge_graph directories are in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
KG_DIR = BASE_DIR / "knowledge_graph"
if str(KG_DIR) not in sys.path:
    sys.path.insert(0, str(KG_DIR))

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

# Member 2: Multimodal Processing
from multimodal.processor import process_file_data
from multimodal.models import StandardExtractionResult, BatchExtractionResult
from multimodal.ocr_engine import is_ocr_available, get_active_ocr_engine_name

# Member 3: Knowledge Graph, Entity Resolution & Contradiction Detection
from src.claim_builder import ClaimBuilder, Claim as M3Claim
from src.entity_extraction import RawClaim
from src.contradiction_detector import ContradictionDetector, DetectionReport
from src.graph_builder import GraphBuilder
from src.duplicates import detect_duplicates

# Member 4: Reasoning & Verification
from reasoning.service import router as reasoning_router, pipeline as reasoning_pipeline
from reasoning.schemas import (
    ReasoningRequest,
    ReasoningResponse,
    EvidenceItem,
    EvidenceMetadata,
    EvidenceModality,
    DirectnessLevel,
    Claim as M4Claim,
    KGRelationship
)
from reasoning.adapter import InterMemberAdapter
from reasoning.suspicion_detector import SuspicionDetector

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cerberus_xa.unified_backend")

# Initialize FastAPI App
app = FastAPI(
    title="CERBERUS-XA Intelligence Engine API",
    description="Unified Multimodal Evidence Graph Construction & Conflict-Aware Reasoning Backend",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Member 4 Router
app.include_router(reasoning_router)

# ---------------------------------------------------------------------------
# Global In-Memory Pipeline State
# ---------------------------------------------------------------------------
class PipelineState:
    def __init__(self):
        self.evidence_files: List[Dict[str, Any]] = []
        self.raw_extractions: List[StandardExtractionResult] = []
        self.claims: List[Dict[str, Any]] = []
        self.m3_claims: List[M3Claim] = []
        self.graph_data: Dict[str, Any] = {"nodes": [], "links": []}
        self.conflicts: List[Dict[str, Any]] = []
        self.entity_resolutions: List[Dict[str, Any]] = []
        self.reliability_records: List[Dict[str, Any]] = []
        self.adversarial_alerts: List[Dict[str, Any]] = []
        self.investigation_history: List[Dict[str, Any]] = []
        self.audit_logs: List[Dict[str, Any]] = []
        self.adapter = InterMemberAdapter()
        self.suspicion_detector = SuspicionDetector()

state = PipelineState()

# Log initial state
state.audit_logs.append({
    "id": f"AUD-{int(time.time())}",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "action": "SYSTEM_INITIALIZE",
    "details": "CERBERUS-XA Unified Intelligence Engine online. All modules ready.",
    "user": "CERBERUS_CORE",
    "status": "SUCCESS"
})


# ---------------------------------------------------------------------------
# 1. Health & Status Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    """Unified system health check verifying all 3 backend subsystems."""
    ollama_status = reasoning_pipeline.llm_adapter.is_available()
    return {
        "status": "healthy",
        "system": "CERBERUS-XA Multimodal Intelligence Platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules": {
            "member_2_multimodal": {
                "status": "online",
                "ocr_available": is_ocr_available(),
                "ocr_engine": get_active_ocr_engine_name()
            },
            "member_3_knowledge_graph": {
                "status": "online",
                "graph_nodes": len(state.graph_data.get("nodes", [])),
                "graph_edges": len(state.graph_data.get("links", [])),
                "conflicts_detected": len(state.conflicts)
            },
            "member_4_reasoning": {
                "status": "online",
                "mode": "offline-first-deterministic",
                "ollama_available": ollama_status,
                "ollama_model": reasoning_pipeline.llm_adapter.default_model
            }
        },
        "evidence_count": len(state.evidence_files),
        "claims_count": len(state.claims)
    }


# ---------------------------------------------------------------------------
# 2. Multimodal Ingestion Pipeline (Member 2 -> Member 3 -> Member 4)
# ---------------------------------------------------------------------------
def _clean_text(val: str) -> str:
    """Normalizes whitespace and strips garbled OCR replacement characters."""
    if not val:
        return ""
    cleaned = val.replace("\ufffd", "-").replace("?", " ").strip()
    return " ".join(cleaned.split())


def _build_clean_graph_from_pipeline(
    extractions: List[StandardExtractionResult],
    m3_claims: List[M3Claim],
    detected_conflicts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Constructs a clean, deduplicated, frontend-ready Knowledge Graph from actual
    extracted evidence and Member 3 contradiction analysis.
    Returns empty nodes/links if no extractions exist (never invents fake data).
    """
    if not extractions:
        return {"nodes": [], "links": []}

    nodes_map: Dict[str, Dict[str, Any]] = {}
    links_list: List[Dict[str, Any]] = []
    seen_links = set()

    def add_node(nid: str, label: str, ntype: str, category: str, **extra):
        clean_lbl = _clean_text(label)
        if not clean_lbl:
            return
        if nid not in nodes_map:
            nodes_map[nid] = {
                "id": nid,
                "label": clean_lbl,
                "type": ntype,
                "node_type": category,
                "category": category,
                **extra,
            }

    def add_link(src_id: str, tgt_id: str, ltype: str, relation: str):
        if src_id == tgt_id or src_id not in nodes_map or tgt_id not in nodes_map:
            return
        key = (src_id, tgt_id, relation)
        if key not in seen_links:
            seen_links.add(key)
            links_list.append({
                "source": src_id,
                "target": tgt_id,
                "type": ltype,
                "edge_type": relation,
                "relation": relation,
            })

    # 1. Source (Evidence) nodes from actual uploaded files
    source_ids: List[str] = []
    for ext in extractions:
        src_name = ext.source
        sid = f"SRC:{src_name}"
        source_ids.append(sid)
        mod_label = "PDF Document" if ext.source_type == "document" else ("Scanned Image / OCR" if ext.source_type == "image" else "Structured Table")
        add_node(
            sid,
            src_name,
            "EVIDENCE",
            "source",
            modality=mod_label,
            source=src_name,
            details=f"{len(ext.content)} extracted assertion(s) from {src_name}",
        )

    # 2. Extract clean subject & attribute-value facts per source
    import re
    from rapidfuzz import fuzz

    subject_candidates: List[str] = []
    # Scan for explicit Model / Device / Entity declarations first
    for ext in extractions:
        for item in ext.content:
            c_txt = _clean_text(item.claim)
            v_txt = _clean_text(item.value or "")
            combined = f"{c_txt} {v_txt}".strip()
            low = combined.lower()
            if any(k in low for k in ["model", "device inspected", "laptop x", "entity"]):
                # Extract clean model name if present
                m = re.search(r"(laptop\s+x(?:\s*\(?lx[-\s]*16\)?)?)", combined, re.IGNORECASE)
                if m:
                    subject_candidates.append("Laptop X (LX-16)")
                elif v_txt and len(v_txt) < 40:
                    subject_candidates.append(v_txt)

    if not subject_candidates and m3_claims:
        for c in m3_claims:
            if c.entity_normalized and "." not in c.entity_normalized:
                subject_candidates.append(c.entity_normalized)

    primary_subject = subject_candidates[0] if subject_candidates else (
        extractions[0].source.rsplit(".", 1)[0] if extractions else "Primary Entity"
    )
    subj_id = f"ENT:{primary_subject.upper()}"
    add_node(subj_id, primary_subject, "ENTITY", "entity", details="Primary subject identified across uploaded evidence")

    # Extract key factual attributes & values (RAM, Storage, Processor, etc. or CSV columns)
    attr_value_sources: Dict[tuple, set] = {}  # (attr_label, value_label) -> {src_ids}
    for ext in extractions:
        sid = f"SRC:{ext.source}"
        for item in ext.content:
            raw_c = _clean_text(item.claim)
            raw_v = _clean_text(item.value or "")
            raw_u = _clean_text(item.unit or "")
            combined = f"{raw_c} {raw_v} {raw_u}".strip()
            low = combined.lower()

            # Skip boilerplate disclaimers/headers
            if any(skip in low for skip in ["not a real", "fictional", "specification sheet", "product specifications", "describes the inspected unit"]):
                continue

            # Detect RAM / Memory facts
            ram_match = re.search(r"(\d+\s*gb(?:\s*ddr\d+)?(?:\s*ram)?)", combined, re.IGNORECASE)
            if ("ram" in low or "memory" in low) and ram_match:
                val_norm = ram_match.group(1).strip()
                # Prefer canonical "16 GB DDR5" if DDR5 is mentioned anywhere for same GB
                if "ddr5" in low and "ddr5" not in val_norm.lower():
                    val_norm = f"{val_norm} DDR5"
                val_norm = re.sub(r"\s+ram$", "", val_norm, flags=re.IGNORECASE).strip()
                attr_value_sources.setdefault(("RAM", val_norm), set()).add(sid)
                continue

            # Detect Storage facts
            ssd_match = re.search(r"(\d+\s*(?:gb|tb)(?:\s*ssd|\s*nvme)?)", combined, re.IGNORECASE)
            if ("storage" in low or "ssd" in low or "nvme" in low) and ssd_match:
                val_norm = ssd_match.group(1).strip()
                attr_value_sources.setdefault(("Storage", val_norm), set()).add(sid)
                continue

            # Generic structured attribute: value
            if raw_v and raw_c and not any(k in raw_c.lower() for k in ["model", "device", "conclusion"]):
                val_full = f"{raw_v} {raw_u}".strip()
                if len(raw_c) <= 28 and len(val_full) <= 32:
                    attr_value_sources.setdefault((raw_c, val_full), set()).add(sid)

    # Merge equivalent values under the same attribute (e.g. "16 GB" and "16 GB DDR5" -> "16 GB DDR5")
    merged_facts: Dict[tuple, set] = {}
    for (attr, val), srcs in attr_value_sources.items():
        merged = False
        for (m_attr, m_val), m_srcs in list(merged_facts.items()):
            if attr.lower() == m_attr.lower():
                # Check if one value contains the other's numeric core or has high fuzzy similarity
                nums_a = re.findall(r"\d+", val)
                nums_b = re.findall(r"\d+", m_val)
                if nums_a and nums_a == nums_b or fuzz.token_set_ratio(val.lower(), m_val.lower()) >= 85:
                    preferred_val = m_val if len(m_val) >= len(val) else val
                    combined_srcs = m_srcs | srcs
                    del merged_facts[(m_attr, m_val)]
                    merged_facts[(m_attr, preferred_val)] = combined_srcs
                    merged = True
                    break
        if not merged:
            merged_facts[(attr, val)] = set(srcs)

    # Limit non-primary attribute clutter to keep graph clean & readable (prioritize multi-source & RAM/Storage)
    sorted_facts = sorted(
        merged_facts.items(),
        key=lambda kv: (len(kv[1]), kv[0][0].lower() in ("ram", "storage")),
        reverse=True,
    )[:6]

    for (attr, val), srcs in sorted_facts:
        attr_id = f"ATTR:{attr.upper()}"
        val_id = f"VAL:{val.upper()}"
        add_node(attr_id, attr, "ENTITY", "attribute", details=f"Property '{attr}' of {primary_subject}")
        add_node(val_id, val, "ENTITY", "quantity", details=f"Verified value '{val}' for {attr} (supported by {len(srcs)} source(s))")

        rel_name = f"has_{attr.replace(' ', '_')}"
        add_link(subj_id, attr_id, "RELATES", "has_property")
        add_link(subj_id, val_id, "SUPPORTS", rel_name)
        add_link(attr_id, val_id, "RELATES", "value")

        for sid in srcs:
            add_link(sid, val_id, "SUPPORTS", "supports")

    # 3. Real Contradictions OR Genuine Multi-Source Consistency
    if detected_conflicts:
        for idx, conf in enumerate(detected_conflicts):
            cid = f"CONF:{idx + 1}"
            add_node(
                cid,
                f"Conflict: {conf.get('attribute', 'Discrepancy')}",
                "CONFLICT",
                "conflict",
                details=conf.get("description", "Cross-source contradiction detected"),
            )
            for sname in conf.get("sources", []):
                add_link(f"SRC:{sname}", cid, "CONTRADICTS", "contradicts")
    elif len(source_ids) >= 2:
        cons_id = "CONSISTENCY:CONSISTENT"
        add_node(
            cons_id,
            "Evidence Consistency: Consistent",
            "ENTITY",
            "consistency",
            details=f"All {len(source_ids)} uploaded evidence sources agree with 0 contradictions detected.",
        )
        # Connect agreeing sources to each other and to the consistency node
        for i in range(len(source_ids)):
            add_link(source_ids[i], cons_id, "SUPPORTS", "supports")
            for j in range(i + 1, len(source_ids)):
                add_link(source_ids[i], source_ids[j], "SUPPORTS", "agrees_with")

    return {"nodes": list(nodes_map.values()), "links": links_list, "edges": links_list}


def _extract_canonical_records(extractions: List[StandardExtractionResult]) -> List[Dict[str, Any]]:
    """
    Extracts clean, row-aware and subject-aware canonical claim records from
    multimodal extractions. Prevents unrelated CSV rows from falsely conflicting
    and aligns cross-modal assertions (PDF/Image/CSV) on shared entity + attribute.
    """
    import re
    records: List[Dict[str, Any]] = []

    skip_phrases = [
        "not a real", "fictional", "specification sheet", "product specifications",
        "memory configuration", "this report describes", "disclaimer",
        "synthetic", "evidencedemo", "created for cerberus-xa", "page  of", "page 1 of"
    ]
    id_col_names = {"part", "part_id", "entity", "device", "model", "container_id", "item", "name", "product"}

    def _detect_subject(text: str, fallback: str) -> str:
        # Match part/model codes like P-4471, LX-16, CONT-EU-9011
        m_code = re.search(r"\b([A-Z]{1,5}-\d{2,6}(?:-\d{1,6})?)\b", text)
        if m_code and not m_code.group(1).startswith(("INV-", "BLR-")):
            return m_code.group(1).upper()
        m_laptop = re.search(r"(laptop\s+x(?:\s*\(?lx[-\s]*16\)?)?)", text, re.IGNORECASE)
        if m_laptop:
            return "Laptop X (LX-16)"
        return fallback

    def _normalize_attr(prop: str, val: str, unit: str) -> tuple:
        low_p = prop.lower()
        low_v = f"{val} {unit}".lower()
        if ("ram" in low_p or "memory" in low_p or "ram" in low_v) and ("gb" in low_v or "ddr" in low_v):
            m_ram = re.search(r"(\d+(?:\.\d+)?)\s*gb", low_v, re.IGNORECASE)
            if m_ram:
                return "ram_capacity", m_ram.group(1), "GB"
            return "ram_capacity", val, unit or "GB"
        if ("storage" in low_p or "ssd" in low_p or "nvme" in low_p) and ("gb" in low_v or "tb" in low_v):
            return "storage", val, unit or ""
        if any(k in low_p for k in ["qty", "quantity", "received", "shipped", "actuator", "units"]) and re.search(r"\b\d+(?:\.\d+)?\b", val):
            num_m = re.search(r"(\d+(?:\.\d+)?)", val)
            num_val = num_m.group(1) if num_m else val
            norm_unit = unit or "units"
            return "quantity", num_val, norm_unit
        return prop, val, unit

    for ext in extractions:
        src = ext.source
        src_type = ext.source_type
        doc_fallback_subj = src.rsplit(".", 1)[0]

        if src_type == "table":
            # Group items by row index so each row's columns share the row's subject entity
            rows_map: Dict[Any, List[ContentItem]] = {}
            for item in ext.content:
                rows_map.setdefault(item.row or 0, []).append(item)

            for row_idx, row_items in rows_map.items():
                row_subject = doc_fallback_subj
                context_parts = []
                for it in row_items:
                    col_low = (it.column or it.claim or "").strip().lower()
                    val_str = _clean_text(it.value or "")
                    if col_low in id_col_names and val_str:
                        row_subject = val_str
                    elif col_low in {"date", "warehouse", "location", "status"} and val_str:
                        context_parts.append(f"{col_low}: {val_str}")

                ctx_suffix = f" ({', '.join(context_parts)})" if context_parts else ""
                for it in row_items:
                    col_name = _clean_text(it.column or it.claim or "")
                    val_str = _clean_text(it.value or "")
                    unit_str = _clean_text(it.unit or "")
                    if not col_name or not val_str:
                        continue
                    if col_name.lower() in id_col_names or col_name.lower() == "row":
                        continue

                    norm_attr, norm_val, norm_unit = _normalize_attr(col_name, val_str, unit_str)
                    stmt = f"{row_subject} {col_name}: {norm_val} {norm_unit}".strip() + f"{ctx_suffix}."
                    records.append({
                        "entity": row_subject,
                        "attribute": norm_attr,
                        "raw_attribute": col_name,
                        "value": norm_val,
                        "unit": norm_unit,
                        "statement": stmt,
                        "source": src,
                        "source_type": src_type,
                        "location": f"Sheet '{it.sheet}' Row {row_idx}" if it.sheet else f"Row {row_idx}",
                        "confidence": float(it.confidence if it.confidence is not None else 0.95),
                    })
        else:
            # Document / Image: track active subject across lines (e.g. P-4471 or Laptop X)
            active_subj = doc_fallback_subj
            for it in ext.content:
                raw_c = _clean_text(it.claim or "")
                raw_v = _clean_text(it.value or "")
                raw_u = _clean_text(it.unit or "")
                if not raw_c:
                    continue
                combined_low = f"{raw_c} {raw_v}".lower()
                if any(sp in combined_low for sp in skip_phrases):
                    continue
                if not raw_v and not any(ch.isdigit() for ch in raw_c) and ":" not in raw_c:
                    if len(raw_c.split()) <= 3:
                        continue

                if raw_v:
                    prop_name = raw_c
                    val_str = raw_v
                elif ":" in raw_c:
                    p_left, p_right = raw_c.split(":", 1)
                    prop_name = p_left.strip()
                    val_str = p_right.strip()
                else:
                    prop_name = "observation"
                    val_str = raw_c

                # Update active subject if a part/model code appears
                detected = _detect_subject(f"{raw_c} {raw_v}", active_subj)
                if detected != active_subj:
                    active_subj = detected

                # Skip bare "Part: 4471" duplicate line if P-4471 is already captured
                if prop_name.lower() == "part" and re.fullmatch(r"\d+", val_str):
                    continue

                norm_attr, norm_val, norm_unit = _normalize_attr(prop_name, val_str, raw_u)
                stmt = f"{prop_name}: {val_str} {raw_u}".strip() + "." if prop_name != "observation" else val_str
                records.append({
                    "entity": detected,
                    "attribute": norm_attr,
                    "raw_attribute": prop_name,
                    "value": norm_val,
                    "unit": norm_unit,
                    "statement": stmt,
                    "source": src,
                    "source_type": src_type,
                    "location": f"Page {it.page}" if it.page else "File Record",
                    "confidence": float(it.confidence if it.confidence is not None else 0.95),
                })

    return records


def _rebuild_pipeline():
    """Rebuilds claims, knowledge graph, contradictions, and reliability scores from raw extractions."""
    if not state.raw_extractions:
        return

    # A. Collect raw extracted items into Member 3 claims format using canonical row/subject extraction
    canonical_records = _extract_canonical_records(state.raw_extractions)
    raw_claims_for_m3 = [
        RawClaim(
            entity=rec["entity"],
            entity_type="ORG",
            attribute=rec["attribute"],
            value=rec["value"],
            unit=rec["unit"],
            date_str="",
            source=rec["source"],
            page_or_sheet=rec["location"],
            original_text=rec["statement"],
            confidence=rec["confidence"],
            modality=rec["source_type"] or "actual",
            ocr_confidence=rec["confidence"],
        )
        for rec in canonical_records
    ]
    evidence_items_for_m4: List[EvidenceItem] = []

    for ext_idx, extraction in enumerate(state.raw_extractions):
        src = extraction.source
        src_type = extraction.source_type

        # Build full text from content items for doc-level analysis
        full_text_pieces = [
            f"{item.claim} {item.value or ''} {item.unit or ''}".strip()
            for item in extraction.content
        ]

        # Build Member 4 EvidenceItem
        modality_enum = EvidenceModality.DOCUMENT
        if src_type == "image":
            modality_enum = EvidenceModality.IMAGE
        elif src_type == "table":
            modality_enum = EvidenceModality.TABLE

        ev_id = f"EV-{ext_idx + 1:03d}"
        body_text = "\n".join(full_text_pieces) if full_text_pieces else f"Evidence content from {src}"
        
        evidence_items_for_m4.append(EvidenceItem(
            id=ev_id,
            source_id=src,
            content=body_text,
            modality=modality_enum,
            directness=DirectnessLevel.PRIMARY,
            metadata=EvidenceMetadata(
                source_id=src,
                filename=src,
                source_type=src_type,
                extraction_confidence=1.0
            )
        ))

    # B. Member 3: Build and normalize claims
    builder = ClaimBuilder(merge_threshold=90.0, similarity_threshold=80.0)
    m3_claims = builder.build(raw_claims_for_m3)
    state.m3_claims = m3_claims

    # Convert M3 claims for frontend display
    frontend_claims = []
    for c in m3_claims:
        frontend_claims.append({
            "id": c.claim_id,
            "entity": c.entity_normalized,
            "attribute": c.attribute,
            "value": c.value,
            "unit": c.unit,
            "source": c.source,
            "location": c.page_or_sheet,
            "confidence": round(c.confidence, 2),
            "modality": getattr(c, "modality", "document"),
            "date": c.date_str or "N/A"
        })
    state.claims = frontend_claims

    # C. Member 3: Detect Contradictions
    detector = ContradictionDetector(numerical_tolerance_pct=2.0)
    detection_report = detector.detect(m3_claims)

    detected_conflicts = []
    for c in detection_report.contradictions:
        sources = list(set([cl.source for cl in c.conflicting_claims]))
        vals = [f"{cl.value} {cl.unit or ''}".strip() for cl in c.conflicting_claims]
        detected_conflicts.append({
            "id": f"CONF-{len(detected_conflicts) + 1:03d}",
            "contradiction_id": c.contradiction_id,
            "entity": c.entity,
            "attribute": c.attribute,
            "severity": "CRITICAL" if c.status == "CONTRADICTION" else "HIGH",
            "status": c.status,
            "confidence": round(c.confidence, 2),
            "description": c.explanation or f"Contradiction detected for '{c.entity}' on attribute '{c.attribute}'.",
            "sources": sources,
            "values": vals,
            "resolutionStatus": "UNRESOLVED"
        })
    state.conflicts = detected_conflicts

    # D. Member 3: Construct Multi-Relational Knowledge Graph & normalize for UI
    graph_builder = GraphBuilder()
    graph_builder.build(m3_claims, detection_report)
    _ = graph_builder.to_json()
    state.graph_data = _build_clean_graph_from_pipeline(
        state.raw_extractions,
        m3_claims,
        detected_conflicts,
    )

    # E. Entity Resolutions
    entity_resolutions = []
    canonical_map = getattr(builder, "_canonical_map", {})
    if canonical_map:
        for alias_group, canonical in canonical_map.items():
            entity_resolutions.append({
                "id": f"ENT-RES-{len(entity_resolutions) + 1:03d}",
                "canonicalName": canonical,
                "alias": alias_group,
                "sources": list(set([c.source for c in m3_claims if c.entity_normalized == canonical])),
                "confidence": 0.95,
                "status": "RESOLVED"
            })
    if not entity_resolutions:
        unique_entities = list(set([c.entity_normalized for c in m3_claims]))
        for ent in unique_entities:
            entity_resolutions.append({
                "id": f"ENT-RES-{len(entity_resolutions) + 1:03d}",
                "canonicalName": ent,
                "alias": ent,
                "sources": list(set([c.source for c in m3_claims if c.entity_normalized == ent])),
                "confidence": 1.0,
                "status": "CANONICAL"
            })
    state.entity_resolutions = entity_resolutions

    # F. Member 4: Evaluate Source Reliability
    try:
        ev_source_map = {ev.id: ev.source_id for ev in evidence_items_for_m4}
        reliability_evals = reasoning_pipeline.evaluate_reliability(
            evidence_items=evidence_items_for_m4
        )
        state.reliability_records = [
            {
                "id": f"REL-{r.evidence_id}",
                "evidence_id": r.evidence_id,
                "source": ev_source_map.get(r.evidence_id, r.evidence_id),
                "reliability_score": round(r.overall_score, 2),
                "score_pct": round(r.reliability_score, 1),
                "is_reliable": r.overall_score >= 0.5,
                "classification": r.reliability_label.value if hasattr(r.reliability_label, 'value') else str(r.reliability_label),
                "rating": r.rating.value if hasattr(r.rating, 'value') else str(r.rating),
                "breakdown": {
                    k: round(v.score if isinstance(v.score, (int, float)) else 0.0, 2)
                    for k, v in r.criteria_scores.items()
                } if hasattr(r, 'criteria_scores') else {},
                "summary": r.reasons[0] if r.reasons else "Assessed across evidential provenance criteria."
            }
            for r in reliability_evals
        ]
    except Exception as e:
        logger.warning(f"Reliability scoring warning: {e}")

    # G. Member 4: Suspicion & Adversarial Indicator Detection
    try:
        indicators = state.suspicion_detector.detect_indicators(
            evidence_items=evidence_items_for_m4
        )
        state.adversarial_alerts = [
            {
                "id": f"ADV-{idx + 1:03d}",
                "severity": ind.severity.upper() if hasattr(ind, 'severity') else "HIGH",
                "category": ind.indicator_type if hasattr(ind, 'indicator_type') else "Metadata Inconsistency",
                "description": ind.description if hasattr(ind, 'description') else str(ind),
                "source": getattr(ind, 'source_id', 'Unknown'),
                "evidence_id": getattr(ind, 'evidence_id', 'EV-001'),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            for idx, ind in enumerate(indicators)
        ]
    except Exception as e:
        logger.warning(f"Suspicion detection warning: {e}")


def _map_modality_ui(source_type: str) -> str:
    st = (source_type or "").lower()
    if st == "table":
        return "STRUCTURED_DATA"
    if st in ("image", "scan", "ocr"):
        return "IMAGE_OCR"
    return "DOCUMENT"


@app.post("/process-file")
async def process_file_endpoint(file: UploadFile = File(...)):
    """Upload and process single evidence file through full pipeline."""
    content = await file.read()
    filename = file.filename or "uploaded_file"
    res = process_file_data(content, filename=filename)

    ev_id = f"EVID-{len(state.evidence_files) + 1:03d}"
    now_iso = datetime.now(timezone.utc).isoformat()
    state.raw_extractions.append(res)
    state.evidence_files.append({
        "id": ev_id,
        "name": filename,
        "filename": filename,
        "type": res.source_type.upper(),
        "modality": _map_modality_ui(res.source_type),
        "size": len(content),
        "status": "PROCESSED",
        "claimsExtracted": len(res.content),
        "extractedClaimsCount": len(res.content),
        "timestamp": now_iso,
        "uploadTime": now_iso,
    })

    _rebuild_pipeline()

    state.audit_logs.append({
        "id": f"AUD-{int(time.time())}",
        "timestamp": now_iso,
        "action": "EVIDENCE_INGEST_SINGLE",
        "details": f"Processed {filename}: {len(res.content)} assertions extracted.",
        "user": "ANALYST_01",
        "status": "SUCCESS"
    })

    return res


@app.post("/process-batch")
async def process_batch_endpoint(files: List[UploadFile] = File(...)):
    """Upload and process batch of multimodal evidence files through full pipeline."""
    results = []
    errors = []
    successful = 0
    failed = 0

    for f in files:
        fname = f.filename or "unknown"
        try:
            content = await f.read()
            res = process_file_data(content, filename=fname)
            if res.metadata.get("error"):
                failed += 1
                errors.append({"filename": fname, "error": res.metadata["error"]})
            else:
                successful += 1
                now_iso = datetime.now(timezone.utc).isoformat()
                state.raw_extractions.append(res)
                state.evidence_files.append({
                    "id": f"EVID-{len(state.evidence_files) + 1:03d}",
                    "name": fname,
                    "filename": fname,
                    "type": res.source_type.upper(),
                    "modality": _map_modality_ui(res.source_type),
                    "size": len(content),
                    "status": "PROCESSED",
                    "claimsExtracted": len(res.content),
                    "extractedClaimsCount": len(res.content),
                    "timestamp": now_iso,
                    "uploadTime": now_iso,
                })
            results.append(res)
        except Exception as e:
            failed += 1
            errors.append({"filename": fname, "error": str(e)})

    # Trigger end-to-end graph & conflict & reasoning compilation
    _rebuild_pipeline()

    state.audit_logs.append({
        "id": f"AUD-{int(time.time())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "EVIDENCE_INGEST_BATCH",
        "details": f"Batch ingest: {successful} successful, {failed} failed. Graph updated to {len(state.graph_data.get('nodes', []))} nodes.",
        "user": "ANALYST_01",
        "status": "SUCCESS" if failed == 0 else "PARTIAL_SUCCESS"
    })

    return {
        "total_files": len(files),
        "successful": successful,
        "failed": failed,
        "results": results,
        "errors": errors
    }


# ---------------------------------------------------------------------------
# 3. Data Query Endpoints (Consumed by React Frontend)
# ---------------------------------------------------------------------------
@app.get("/evidence")
def get_evidence_files():
    """Returns all currently ingested evidence files with reliability scores."""
    rel_by_source = {r.get("source"): r.get("reliability_score") for r in state.reliability_records}
    enriched = []
    for f in state.evidence_files:
        fname = f.get("filename") or f.get("name") or "unknown"
        item = dict(f)
        item["filename"] = fname
        item["modality"] = item.get("modality") or _map_modality_ui(item.get("type", "document"))
        item["extractedClaimsCount"] = item.get("extractedClaimsCount", item.get("claimsExtracted", 0))
        item["uploadTime"] = item.get("uploadTime") or item.get("timestamp")
        if fname in rel_by_source:
            item["reliabilityScore"] = rel_by_source[fname]
        enriched.append(item)
    return enriched


@app.delete("/evidence/{evidence_id}")
def delete_evidence_file(evidence_id: str):
    """Deletes a specific evidence file from the active vault and rebuilds the pipeline."""
    idx_to_remove = None
    removed_name = None
    for idx, f in enumerate(state.evidence_files):
        if f.get("id") == evidence_id:
            idx_to_remove = idx
            removed_name = f.get("filename") or f.get("name")
            break

    if idx_to_remove is None:
        raise HTTPException(status_code=404, detail=f"Evidence '{evidence_id}' not found.")

    state.evidence_files.pop(idx_to_remove)
    if idx_to_remove < len(state.raw_extractions):
        state.raw_extractions.pop(idx_to_remove)

    if state.raw_extractions:
        _rebuild_pipeline()
    else:
        state.claims.clear()
        state.m3_claims.clear()
        state.graph_data = {"nodes": [], "links": []}
        state.conflicts.clear()
        state.entity_resolutions.clear()
        state.reliability_records.clear()
        state.adversarial_alerts.clear()

    state.audit_logs.append({
        "id": f"AUD-{int(time.time())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "EVIDENCE_DELETED",
        "details": f"Removed '{removed_name}' ({evidence_id}) from active vault.",
        "user": "ANALYST_01",
        "status": "SUCCESS"
    })
    return {"status": "deleted", "id": evidence_id, "remaining": len(state.evidence_files)}
@app.get("/claims")
def get_claims(entity: Optional[str] = None):
    """Returns normalized extracted claims with provenance coordinates."""
    if entity:
        return [c for c in state.claims if entity.lower() in c.get("entity", "").lower()]
    return state.claims


@app.get("/graph")
def get_graph():
    """Returns the multi-relational Knowledge & Conflict Graph in NetworkX node-link format."""
    return state.graph_data


@app.get("/conflicts")
def get_conflicts():
    """Returns cross-modal contradiction analysis."""
    return state.conflicts


@app.get("/entity-resolution")
def get_entity_resolution():
    """Returns resolved entities, cross-source aliases, and fuzzy match confidences."""
    return state.entity_resolutions


@app.get("/reliability")
def get_reliability():
    """Returns 6-dimension provenance and reliability scores for ingested sources."""
    return state.reliability_records


@app.get("/adversarial")
def get_adversarial():
    """Returns adversarial manipulation red flags and metadata backdating alerts."""
    return state.adversarial_alerts


@app.get("/audit")
def get_audit():
    """Returns verifiable audit trail logs."""
    return state.audit_logs


# ---------------------------------------------------------------------------
# 4. Investigation & Conflict-Aware AI Reasoning (Member 4 Integration)
# ---------------------------------------------------------------------------
class InvestigationQueryPayload(BaseModel):
    question: str
    caseId: Optional[str] = "CASE-LIVE-001"
    evidenceIds: Optional[List[str]] = None
    enable_ollama: Optional[bool] = False

@app.post("/investigate")
def investigate_query(payload: InvestigationQueryPayload):
    """
    Submits hypothesis or forensic inquiry to Member 4's 7-Stage Deliberation Engine.
    Executes conflict-aware reasoning, constructs traceable citations, and saves to dossier.
    """
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="Investigation question cannot be empty.")

    # Build Member 4 EvidenceItems from state
    evidence_items_for_m4: List[EvidenceItem] = []
    for ext_idx, extraction in enumerate(state.raw_extractions):
        src = extraction.source
        src_type = extraction.source_type
        text_lines = [f"{item.claim}: {item.value or ''} {item.unit or ''}".strip() for item in extraction.content]
        body = "\n".join(text_lines) if text_lines else f"Evidence content from {src}"

        modality_enum = EvidenceModality.DOCUMENT
        if src_type == "image":
            modality_enum = EvidenceModality.IMAGE
        elif src_type == "table":
            modality_enum = EvidenceModality.TABLE

        evidence_items_for_m4.append(EvidenceItem(
            id=f"EV-{ext_idx + 1:03d}",
            source_id=src,
            content=body,
            modality=modality_enum,
            directness=DirectnessLevel.PRIMARY,
            metadata=EvidenceMetadata(
                source_id=src,
                filename=src,
                source_type=src_type,
                extraction_confidence=1.0
            )
        ))

    # Build clean, canonical Member 4 Claims using row-aware & subject-aware extraction
    ev_id_by_source = {ev.source_id: ev.id for ev in evidence_items_for_m4}
    canonical_records = _extract_canonical_records(state.raw_extractions)
    m4_claims: List[M4Claim] = []
    for idx, rec in enumerate(canonical_records):
        mapped_ev_id = ev_id_by_source.get(rec["source"], "EV-001")
        m4_claims.append(M4Claim(
            id=f"CLM-{idx + 1:03d}",
            statement=rec["statement"],
            entity=rec["entity"],
            property=rec["attribute"],
            value=str(rec["value"]),
            unit=rec["unit"] or None,
            evidence_ids=[mapped_ev_id],
            confidence=rec["confidence"],
            polarity=True,
        ))

    # Fallback to M3 claims if extraction filtering yielded none
    if not m4_claims:
        for idx, c in enumerate(state.m3_claims):
            mapped_ev_id = ev_id_by_source.get(c.source, "EV-001")
            m4_claims.append(M4Claim(
                id=f"CLM-{idx + 1:03d}",
                statement=f"{c.attribute}: {c.value} {c.unit or ''}.".strip(),
                entity=c.entity_normalized,
                property=c.attribute,
                value=str(c.value),
                unit=c.unit,
                evidence_ids=[mapped_ev_id],
                confidence=float(c.confidence),
                polarity=True
            ))

    # Filter claims & evidence by relevance to the user's question so unrelated vault files
    # do not inject false conflicts or force a constant 15% confidence.
    stop_tokens = {
        "what", "which", "where", "when", "does", "have", "that", "this", "with", "from",
        "reliable", "actual", "evidence", "valid", "please", "tell", "about", "there",
        "pdf", "jpg", "jpeg", "png", "csv", "xlsx", "xls", "scanned", "copy", "file",
        "files", "document", "documents", "report", "reports", "how", "and", "the", "are"
    }
    raw_q_words = [w.strip("?.,!\"'()[]/:;").lower() for w in payload.question.split()]
    q_tokens = {w for w in raw_q_words if len(w) >= 3 and w not in stop_tokens}

    ev_by_id = {ev.id: ev for ev in evidence_items_for_m4}
    scored_claims = []
    for clm in m4_claims:
        ev_src = ev_by_id[clm.evidence_ids[0]].source_id if clm.evidence_ids and clm.evidence_ids[0] in ev_by_id else ""
        haystack = f"{clm.entity or ''} {clm.statement} {clm.property or ''} {clm.value or ''} {ev_src}".lower()
        score = sum(1 for tok in q_tokens if tok in haystack)
        if score > 0:
            scored_claims.append((score, clm))

    scored_claims.sort(key=lambda x: x[0], reverse=True)
    if scored_claims:
        max_score = scored_claims[0][0]
        # Keep strongly relevant claims (at least 1 match, or >= max_score - 1 when multi-keyword)
        min_keep = max(1, max_score - 1) if max_score >= 2 else 1
        relevant_claims = [c for s, c in scored_claims if s >= min_keep]
        relevant_ev_ids = {eid for c in relevant_claims for eid in (c.evidence_ids or [])}
        relevant_evidence = [ev for ev in evidence_items_for_m4 if ev.id in relevant_ev_ids]
    else:
        relevant_claims = []
        relevant_evidence = []

    # Build Knowledge Graph Relationships relevant to the filtered evidence
    kg_relationships: List[KGRelationship] = []
    if relevant_claims:
        for edge in state.graph_data.get("links", []):
            kg_relationships.append(KGRelationship(
                source_entity=str(edge.get("source")),
                relation=str(edge.get("edge_type") or edge.get("relation") or "RELATES_TO"),
                target_entity=str(edge.get("target")),
                confidence=float(edge.get("confidence", 1.0)),
                evidence_ids=[]
            ))

    # Assemble reasoning request using question-relevant claims & evidence
    reasoning_req = ReasoningRequest(
        question=payload.question.strip(),
        claims=relevant_claims,
        evidence_items=relevant_evidence,
        kg_relationships=kg_relationships,
        enable_ollama=payload.enable_ollama or False
    )

    try:
        response: ReasoningResponse = reasoning_pipeline.verify(reasoning_req)
        resp_dict = response.model_dump()
    except Exception as e:
        logger.exception("Reasoning engine execution error")
        raise HTTPException(status_code=500, detail=f"Reasoning engine failed: {str(e)}")

    # Build structured mappings for ReportViewer without fabricating data
    raw_status = resp_dict.get("status", "INSUFFICIENT_EVIDENCE")
    status_label_map = {
        "ANSWERED": "Supported by evidence",
        "PARTIALLY_ANSWERED": "Partially supported",
        "CONFLICTED": "Conflicting evidence",
        "INSUFFICIENT_EVIDENCE": "Insufficient evidence",
    }
    final_verdict_label = status_label_map.get(raw_status, raw_status)
    conf_ratio = round(float(resp_dict.get("confidence", 0.0)), 4)
    raw_steps = resp_dict.get("reasoning_steps", [])

    # Citation & claim lookup by ID
    citations_list = resp_dict.get("citations", [])
    citation_by_ev = {c.get("evidence_id"): c for c in citations_list if isinstance(c, dict) and c.get("evidence_id")}
    ev_meta_map = {ev.id: ev for ev in evidence_items_for_m4}
    rel_map = {r.get("evidence_id"): r for r in state.reliability_records}
    claim_by_id = {c.id: c for c in m4_claims}

    # Map supporting_claims -> supportingEvidence (only from actual claims)
    supporting_evidence = []
    for clm in resp_dict.get("supporting_claims", []):
        stmt = (clm.get("statement") or "").strip()
        if not stmt:
            continue
        ev_ids = clm.get("evidence_ids") or []
        ev_id = ev_ids[0] if ev_ids else None
        cit = citation_by_ev.get(ev_id, {})
        ev_obj = ev_meta_map.get(ev_id)
        rel_obj = rel_map.get(ev_id, {})
        supporting_evidence.append({
            "source": cit.get("filename") or (ev_obj.source_id if ev_obj else "Pipeline Corpus"),
            "modality": cit.get("source_type") or (ev_obj.modality.value if ev_obj else "document"),
            "reliability": float(rel_obj.get("reliability_score", clm.get("confidence", 0.0))),
            "finding": stmt,
            "citationRef": cit.get("formatted_citation") or cit.get("location_locator") or (ev_id or ""),
        })

    # Map unresolved_conflicts & opposing_claims -> contradictingEvidence (using ConflictPair schema)
    contradicting_evidence = []
    for conf in resp_dict.get("unresolved_conflicts", []):
        clm_a_obj = claim_by_id.get(conf.get("claim_a_id"))
        clm_b_obj = claim_by_id.get(conf.get("claim_b_id"))
        claim_a_text = (clm_a_obj.statement if clm_a_obj else "").strip()
        claim_b_text = (clm_b_obj.statement if clm_b_obj else "").strip()
        desc_text = (conf.get("description") or conf.get("explanation") or "").strip()

        primary_claim = claim_a_text or desc_text
        refutes_text = claim_b_text or desc_text
        if not primary_claim and not refutes_text:
            continue

        ev_ids = (clm_a_obj.evidence_ids if clm_a_obj else []) or []
        ev_id = ev_ids[0] if ev_ids else None
        cit = citation_by_ev.get(ev_id, {})
        ev_obj = ev_meta_map.get(ev_id)
        raw_ctype = conf.get("conflict_type", "CONFLICT")
        ctype_str = raw_ctype.value if hasattr(raw_ctype, "value") else str(raw_ctype)

        contradicting_evidence.append({
            "source": cit.get("filename") or (ev_obj.source_id if ev_obj else ctype_str),
            "criticality": str(conf.get("severity", "HIGH")).upper(),
            "claim": primary_claim,
            "contradicts": refutes_text,
            "citationRef": cit.get("formatted_citation") or cit.get("location_locator") or (ev_id or ""),
        })
    if not contradicting_evidence:
        for clm in resp_dict.get("opposing_claims", []):
            stmt = (clm.get("statement") or "").strip()
            if not stmt:
                continue
            ev_ids = clm.get("evidence_ids") or []
            ev_id = ev_ids[0] if ev_ids else None
            cit = citation_by_ev.get(ev_id, {})
            contradicting_evidence.append({
                "source": cit.get("filename") or "Opposing Source",
                "criticality": "HIGH",
                "claim": stmt,
                "contradicts": payload.question,
                "citationRef": cit.get("formatted_citation") or cit.get("location_locator") or "",
            })

    # Map sourceReliability from actual evaluated records
    source_reliability = [
        {
            "sourceName": r.get("source", r.get("evidence_id", "Unknown")),
            "score": float(r.get("reliability_score", 0.0)),
            "authStatus": r.get("classification", "ASSESSED"),
            "reason": r.get("summary", ""),
        }
        for r in state.reliability_records
    ]

    # Extract exact matched facts from question-relevant claims
    matched_facts = []
    for clm in relevant_claims:
        src_name = ev_meta_map[clm.evidence_ids[0]].source_id if clm.evidence_ids and clm.evidence_ids[0] in ev_meta_map else "Uploaded File"
        matched_facts.append((src_name, clm.statement))

    # Deduplicate exact statement strings while preserving order
    unique_exact_answers = []
    seen_stmts = set()
    for src_name, stmt in matched_facts:
        norm = stmt.strip().rstrip(".")
        if norm.lower() not in seen_stmts:
            seen_stmts.add(norm.lower())
            unique_exact_answers.append((src_name, norm))

    # Build exact answer ONLY (no extra clutter or unrelated files)
    if raw_status == "INSUFFICIENT_EVIDENCE" or not unique_exact_answers:
        concise_summary = "Insufficient evidence in the uploaded documents to answer this question."
    elif raw_status == "CONFLICTED" and contradicting_evidence:
        conflict_pairs = [f"{c.get('claim', '')} vs {c.get('contradicts', '')}" for c in contradicting_evidence[:2]]
        concise_summary = f"Conflicting evidence found: {'; '.join(conflict_pairs)}."
    else:
        concise_summary = "; ".join([f"{stmt} ({src})" for src, stmt in unique_exact_answers[:3]]) + "."

    # Build small, readable reasoning lines strictly from the analyzed relevant documents
    relevant_sources = list(dict.fromkeys(src for src, _ in unique_exact_answers))
    if not unique_exact_answers:
        reasoning_explanation = [
            {
                "step": 1,
                "title": "Document Analysis",
                "detail": "No matching evidence was found in the uploaded documents for this question."
            }
        ]
    else:
        evidence_lines = " | ".join([f"[{src}] {stmt}" for src, stmt in unique_exact_answers[:3]])
        conflict_line = (
            f"Conflicting assertions detected between sources: {contradicting_evidence[0].get('claim', '')} vs {contradicting_evidence[0].get('contradicts', '')}."
            if contradicting_evidence
            else f"All relevant sources ({', '.join(relevant_sources)}) are consistent with zero contradictions on this question."
        )
        reasoning_explanation = [
            {
                "step": 1,
                "title": "Evidence Extracted",
                "detail": evidence_lines
            },
            {
                "step": 2,
                "title": "Conflict & Consistency Check",
                "detail": conflict_line
            },
            {
                "step": 3,
                "title": "Conclusion",
                "detail": f"{final_verdict_label} ({round(conf_ratio * 100, 1)}% confidence)."
            }
        ]

    # Format into frontend dossier report
    report_id = f"DOSSIER-{int(time.time())}"
    now_iso = datetime.now(timezone.utc).isoformat()
    dossier = {
        "reportId": report_id,
        "caseId": payload.caseId,
        "timestamp": now_iso,
        "generatedAt": now_iso,
        "question": payload.question,
        "investigationQuestion": payload.question,
        "verdict": raw_status,
        "finalVerdict": final_verdict_label,
        "conclusionType": resp_dict.get("conclusion_type"),
        "verdictConfidence": conf_ratio,
        "confidence": round(conf_ratio * 100, 1),
        "confidenceExplanation": resp_dict.get("confidence_explanation"),
        "summary": concise_summary,
        "summaryAnswer": concise_summary,
        "answer": concise_summary,
        "reasoningSteps": raw_steps,
        "reasoningExplanation": reasoning_explanation,
        "supportingEvidence": supporting_evidence,
        "contradictingEvidence": contradicting_evidence,
        "sourceReliability": source_reliability,
        "facts": resp_dict.get("facts", []),
        "inferences": resp_dict.get("inferences", []),
        "limitations": resp_dict.get("limitations", []),
        "assumptions": resp_dict.get("assumptions", []),
        "unresolvedConflicts": resp_dict.get("unresolved_conflicts", []),
        "citations": citations_list,
        "reasoningMode": resp_dict.get("reasoning_mode", "deterministic"),
        "llmAttempted": resp_dict.get("llm_attempted", False),
        "llmSynthesisUsed": resp_dict.get("llm_synthesis_used", False),
    }

    state.investigation_history.append(dossier)

    state.audit_logs.append({
        "id": f"AUD-{int(time.time())}",
        "timestamp": now_iso,
        "action": "AI_INVESTIGATION_VERDICT",
        "details": f"Inquiry '{payload.question[:45]}...' -> Verdict: {dossier['verdict']} ({dossier['confidence']}% confidence)",
        "user": "AI_REASONING_ENGINE",
        "status": "SUCCESS"
    })

    return dossier


@app.get("/investigations")
def get_investigations():
    """Returns completed live investigations formatted for Reports & Audit history."""
    formatted = []
    for d in reversed(state.investigation_history):
        raw_v = d.get("verdict", "INSUFFICIENT_EVIDENCE")
        if raw_v == "ANSWERED":
            status_str = "SUPPORTED"
        elif raw_v == "CONFLICTED":
            status_str = "CONFLICT_DETECTED"
        else:
            status_str = "INSUFFICIENT_EVIDENCE"

        lead_ent = state.entity_resolutions[0].get("canonicalName") if state.entity_resolutions else "Uploaded Corpus"
        formatted.append({
            "id": d.get("reportId"),
            "title": d.get("investigationQuestion") or d.get("question") or "Live Forensic Inquiry",
            "category": "Live Cross-Modal Inquiry",
            "status": status_str,
            "leadEntity": lead_ent,
            "evidenceCount": len(state.evidence_files),
            "claimsCount": len(state.claims),
            "verdict": d.get("finalVerdict") or raw_v,
            "confidence": d.get("verdictConfidence", 0.0),
            "timestamp": d.get("timestamp") or d.get("generatedAt"),
            "lastUpdated": d.get("timestamp") or d.get("generatedAt"),
            "dossier": d,
        })
    return formatted


@app.get("/investigation-report/{report_id}")
def get_investigation_report(report_id: str = "latest"):
    """Returns stored investigation dossier by reportId or the latest generated verdict."""
    if not state.investigation_history:
        return {"error": "No investigations run yet."}
    if report_id == "latest":
        return state.investigation_history[-1]
    for d in state.investigation_history:
        if d.get("reportId") == report_id:
            return d
    return state.investigation_history[-1]


# ---------------------------------------------------------------------------
# 4b. Report Export Endpoints (JSON, CSV, PDF)
# ---------------------------------------------------------------------------
def _build_csv_bytes(dossier: Dict[str, Any]) -> bytes:
    """Serializes an investigation dossier into a structured UTF-8 CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Section", "Field / Source", "Detail / Claim", "Confidence / Reliability", "Citation / Provenance"])

    conf_val = dossier.get("verdictConfidence")
    if conf_val is None:
        raw_c = dossier.get("confidence", 0.0)
        conf_val = raw_c / 100.0 if raw_c > 1 else raw_c
    conf_pct = f"{float(conf_val) * 100:.1f}%"

    writer.writerow(["METADATA", "Report ID", dossier.get("reportId", ""), "", ""])
    writer.writerow(["METADATA", "Case ID", dossier.get("caseId", ""), "", ""])
    writer.writerow(["METADATA", "Timestamp", dossier.get("timestamp") or dossier.get("generatedAt", ""), "", ""])
    writer.writerow(["METADATA", "Question", dossier.get("investigationQuestion") or dossier.get("question", ""), "", ""])
    writer.writerow(["METADATA", "Verdict", dossier.get("finalVerdict") or dossier.get("verdict", ""), conf_pct, ""])
    writer.writerow(["METADATA", "Summary", dossier.get("summaryAnswer") or dossier.get("summary", ""), "", ""])

    for sup in dossier.get("supportingEvidence", []):
        rel = sup.get("reliability", "")
        rel_str = f"{float(rel) * 100:.1f}%" if isinstance(rel, (int, float)) else str(rel)
        writer.writerow(["SUPPORTING", sup.get("source", ""), sup.get("finding", ""), rel_str, sup.get("citationRef", "")])

    for con in dossier.get("contradictingEvidence", []):
        claim_txt = str(con.get("claim") or "").strip()
        refutes_txt = str(con.get("contradicts") or "").strip()
        if not claim_txt and not refutes_txt:
            continue
        detail = f"{claim_txt} (Refutes: {refutes_txt})" if refutes_txt and refutes_txt != claim_txt else claim_txt
        writer.writerow(["CONTRADICTING", con.get("source", ""), detail, con.get("criticality", ""), con.get("citationRef", "")])

    for cit in dossier.get("citations", []):
        writer.writerow(["CITATION", cit.get("filename") or cit.get("source_id", ""), cit.get("formatted_citation", ""), cit.get("source_type", ""), cit.get("location_locator", "")])

    return output.getvalue().encode("utf-8")


def _build_pdf_bytes(dossier: Dict[str, Any]) -> bytes:
    """Renders an investigation dossier into a multi-page PDF using PyMuPDF."""
    doc = pymupdf.open()
    conf_val = dossier.get("verdictConfidence")
    if conf_val is None:
        raw_c = dossier.get("confidence", 0.0)
        conf_val = raw_c / 100.0 if raw_c > 1 else raw_c
    conf_pct = f"{float(conf_val) * 100:.1f}%"

    lines = [
        "CERBERUS-XA FORENSIC INTELLIGENCE DOSSIER",
        "=" * 60,
        f"Report ID : {dossier.get('reportId', 'N/A')}",
        f"Case ID   : {dossier.get('caseId', 'N/A')}",
        f"Generated : {dossier.get('timestamp') or dossier.get('generatedAt', 'N/A')}",
        "",
        "INVESTIGATION QUESTION:",
        str(dossier.get("investigationQuestion") or dossier.get("question", "N/A")),
        "",
        f"FINAL VERDICT : {dossier.get('finalVerdict') or dossier.get('verdict', 'N/A')}",
        f"CONFIDENCE    : {conf_pct}",
        "",
        "EXECUTIVE SUMMARY:",
        str(dossier.get("summaryAnswer") or dossier.get("summary", "N/A")),
        "",
    ]

    steps = dossier.get("reasoningExplanation") or []
    if steps:
        lines.append("REASONING EXPLANATION:")
        for st in steps[:25]:
            if isinstance(st, dict):
                lines.append(f"  {st.get('step', '')}. {st.get('title', '')}: {st.get('detail', '')}")
            else:
                lines.append(f"  - {st}")
        lines.append("")

    sup_list = dossier.get("supportingEvidence") or []
    lines.append(f"SUPPORTING EVIDENCE ({len(sup_list)}):")
    for sup in sup_list:
        lines.append(f"  - [{sup.get('modality', '')}] {sup.get('source', '')}: {sup.get('finding', '')} [{sup.get('citationRef', '')}]")
    lines.append("")

    con_list = dossier.get("contradictingEvidence") or []
    lines.append(f"CONTRADICTING EVIDENCE ({len(con_list)}):")
    for con in con_list:
        lines.append(f"  - [{con.get('criticality', '')}] {con.get('source', '')}: {con.get('claim', '')} (Refutes: {con.get('contradicts', '')})")
    lines.append("")

    cits = dossier.get("citations") or []
    if cits:
        lines.append(f"TRACEABLE CITATIONS ({len(cits)}):")
        for c in cits:
            lines.append(f"  {c.get('formatted_citation', str(c))}")

    # Paginate cleanly across A4 pages without blank pages
    margin = 45
    page_w, page_h = 595, 842
    max_lines_per_page = 42
    wrapped_lines: List[str] = []
    for ln in lines:
        if len(ln) <= 88:
            wrapped_lines.append(ln)
        else:
            words = ln.split(" ")
            cur = ""
            for w in words:
                if len(cur) + len(w) + 1 <= 88:
                    cur = f"{cur} {w}".strip()
                else:
                    wrapped_lines.append(cur)
                    cur = "  " + w
            if cur:
                wrapped_lines.append(cur)

    for idx in range(0, max(1, len(wrapped_lines)), max_lines_per_page):
        chunk = "\n".join(wrapped_lines[idx : idx + max_lines_per_page])
        if not chunk.strip():
            continue
        page = doc.new_page(width=page_w, height=page_h)
        page.insert_textbox(
            pymupdf.Rect(margin, margin, page_w - margin, page_h - margin),
            chunk,
            fontsize=9.5,
            fontname="helv",
        )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@app.get("/investigation-report/{report_id}/export")
def export_stored_report(report_id: str, format: str = Query("json", pattern="^(json|csv|pdf)$")):
    """Exports a stored investigation dossier in JSON, CSV, or PDF format."""
    if not state.investigation_history:
        raise HTTPException(status_code=404, detail="No investigation reports available to export.")

    target = None
    if report_id == "latest":
        target = state.investigation_history[-1]
    else:
        for d in state.investigation_history:
            if d.get("reportId") == report_id:
                target = d
                break
    if target is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    rid = target.get("reportId", report_id)
    if format == "json":
        content = json.dumps(target, indent=2, default=str).encode("utf-8")
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="CERBERUS_DOSSIER_{rid}.json"'},
        )
    if format == "csv":
        content = _build_csv_bytes(target)
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="CERBERUS_DOSSIER_{rid}.csv"'},
        )
    content = _build_pdf_bytes(target)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="CERBERUS_DOSSIER_{rid}.pdf"'},
    )


@app.post("/export-report")
def export_provided_report(
    dossier: Dict[str, Any] = Body(...),
    format: str = Query("json", pattern="^(json|csv|pdf)$"),
):
    """Exports the currently selected investigation dossier (live or demo) in JSON, CSV, or PDF."""
    if not dossier or not isinstance(dossier, dict):
        raise HTTPException(status_code=400, detail="Report payload is required for export.")

    rid = dossier.get("reportId") or f"DOSSIER-{int(time.time())}"
    if format == "json":
        content = json.dumps(dossier, indent=2, default=str).encode("utf-8")
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="CERBERUS_DOSSIER_{rid}.json"'},
        )
    if format == "csv":
        content = _build_csv_bytes(dossier)
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="CERBERUS_DOSSIER_{rid}.csv"'},
        )
    content = _build_pdf_bytes(dossier)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="CERBERUS_DOSSIER_{rid}.pdf"'},
    )


# ---------------------------------------------------------------------------
# 5. Preload Sample Benchmark Case (Optional Demo Seed)
# ---------------------------------------------------------------------------
@app.post("/reset")
def reset_pipeline_state():
    """Resets in-memory pipeline state for clean session or isolated fixture testing."""
    state.evidence_files.clear()
    state.raw_extractions.clear()
    state.claims.clear()
    state.m3_claims.clear()
    state.graph_data = {"nodes": [], "links": []}
    state.conflicts.clear()
    state.entity_resolutions.clear()
    state.reliability_records.clear()
    state.adversarial_alerts.clear()
    state.investigation_history.clear()
    return {"status": "reset", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/seed-benchmark")
def seed_benchmark_data():
    """Loads sample files from Member 2 & 3 samples to bootstrap active case state."""
    sample_files = [
        ("sample_report.pdf", "application/pdf"),
        ("sample_inventory.csv", "text/csv"),
        ("sample_metrics.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    ]
    samples_dir = BASE_DIR / "multimodal" / "samples"
    loaded = 0
    for sname, ctype in sample_files:
        p = samples_dir / sname
        if p.exists():
            data = p.read_bytes()
            res = process_file_data(data, filename=sname)
            state.raw_extractions.append(res)
            state.evidence_files.append({
                "id": f"EVID-{len(state.evidence_files) + 1:03d}",
                "name": sname,
                "type": res.source_type.upper(),
                "size": len(data),
                "status": "PROCESSED",
                "claimsExtracted": len(res.content),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            loaded += 1

    if loaded > 0:
        _rebuild_pipeline()

    return {
        "status": "success",
        "loaded_files": loaded,
        "claims": len(state.claims),
        "conflicts": len(state.conflicts),
        "nodes": len(state.graph_data.get("nodes", []))
    }
