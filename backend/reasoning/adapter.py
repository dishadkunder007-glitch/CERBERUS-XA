"""
CERBERUS-XA: AI Reasoning & Evidence Verification Module (Member 4)
Inter-Member Integration Adapter

STATUS: UNVERIFIED / ASSUMED
Upstream code for Member 2 (backend/processor/) and Member 3 (backend/knowledge_graph/)
is not committed or available in this repository. All key mappings in this file are
ASSUMED based on typical pipeline conventions, NOT verified against actual implementations.

=============================================================================
ASSUMED_UPSTREAM_SCHEMA
=============================================================================
1. Member 2 (Processor) Evidence Item:
   - Required aliases:
     * id: 'id', 'chunk_id', 'evidence_id', 'doc_id'
     * content: 'content', 'text', 'extracted_text', 'body', 'raw_text', 'snippet'
     * modality: 'modality', 'source_type', 'file_type'
   - Optional aliases (logs warning if missing, uses safe default):
     * source_id: 'source_id', 'source', 'source_name' (default: "UNKNOWN_PROCESSOR_SRC")
     * filename: 'filename', 'file_name', 'doc_name' (default: None)
     * page_number: 'page_number', 'page', 'page_no' (default: None)
     * directness: 'directness' (default: "primary")
     * extraction_confidence: 'extraction_confidence', 'ocr_confidence', 'confidence' (default: 1.0)

2. Member 2 (Processor) Claims:
   - Required aliases:
     * statement: 'statement', 'text', 'claim', 'assertion'
   - Optional aliases:
     * id: 'id', 'claim_id' (default: auto-generated CLM-PROC-xxx)
     * entity: 'entity', 'subject' (default: None)
     * property: 'property', 'predicate', 'attribute' (default: None)
     * value: 'value', 'object' (default: None)
     * unit: 'unit', 'dimension' (default: None)
     * evidence_ids: 'evidence_ids', 'evidence_id', 'sources' (default: [])
     * confidence: 'confidence', 'score' (default: 1.0)
     * polarity: 'polarity' (default: True, with heuristic negation check)

3. Member 3 (Knowledge Graph) Triples / Edges:
   - Required aliases:
     * source: 'source_entity', 'source', 'head', 'subject', 'from'
     * relation: 'relation', 'predicate', 'edge', 'type', 'rel'
     * target: 'target_entity', 'target', 'tail', 'object', 'to'
   - Optional aliases:
     * confidence: 'confidence', 'weight', 'score' (default: 1.0)
     * evidence_ids: 'evidence_ids', 'citations', 'source_ids' (default: [])
     * provenance: 'provenance' (default: "Member3_KnowledgeGraph")
=============================================================================
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from .schemas import (
    Claim,
    DirectnessLevel,
    EvidenceItem,
    EvidenceMetadata,
    EvidenceModality,
    KGRelationship,
    ReasoningRequest,
)

logger = logging.getLogger("cerberus_xa.reasoning.adapter")


class AdapterError(ValueError):
    """Raised when an assumed upstream schema payload lacks mandatory required fields."""
    pass


class InterMemberAdapter:
    """
    Translates ASSUMED upstream payloads from Member 2 (Processor) and Member 3 (Knowledge Graph)
    into validated Member 4 domain models.
    Fails loudly with AdapterError if mandatory fields are missing.
    """

    # -------------------------------------------------------------------------
    # Modality and Directness Mapping Rules (ASSUMED)
    # -------------------------------------------------------------------------
    MODALITY_MAP: Dict[str, EvidenceModality] = {
        "document": EvidenceModality.DOCUMENT,
        "doc": EvidenceModality.DOCUMENT,
        "pdf": EvidenceModality.DOCUMENT,
        "text": EvidenceModality.DOCUMENT,
        "txt": EvidenceModality.DOCUMENT,
        "image": EvidenceModality.IMAGE,
        "img": EvidenceModality.IMAGE,
        "ocr": EvidenceModality.IMAGE,
        "scan": EvidenceModality.SCAN,
        "scanned": EvidenceModality.SCAN,
        "table": EvidenceModality.TABLE,
        "csv": EvidenceModality.TABLE,
        "tsv": EvidenceModality.TABLE,
        "excel": EvidenceModality.TABLE,
        "structured": EvidenceModality.STRUCTURED,
        "json": EvidenceModality.STRUCTURED,
        "record": EvidenceModality.RECORD,
        "database": EvidenceModality.RECORD,
        "audio": EvidenceModality.AUDIO,
        "transcript": EvidenceModality.AUDIO,
    }

    DIRECTNESS_MAP: Dict[str, DirectnessLevel] = {
        "primary": DirectnessLevel.PRIMARY,
        "direct": DirectnessLevel.PRIMARY,
        "raw": DirectnessLevel.PRIMARY,
        "secondary": DirectnessLevel.SECONDARY,
        "indirect": DirectnessLevel.SECONDARY,
        "derived": DirectnessLevel.DERIVED,
        "inferred": DirectnessLevel.DERIVED,
        "hearsay": DirectnessLevel.HEARSAY,
        "unverified": DirectnessLevel.UNVERIFIED,
        "unconfirmed": DirectnessLevel.UNVERIFIED,
    }

    # -------------------------------------------------------------------------
    # Member 2 (Processor) Adaptation
    # -------------------------------------------------------------------------
    def adapt_processor_evidence(
        self,
        raw_items: List[Dict[str, Any]],
    ) -> List[EvidenceItem]:
        """
        Converts assumed Member 2 document chunks into Member 4 EvidenceItem models.
        Raises AdapterError if id, content, or modality cannot be resolved from aliases.
        """
        if not isinstance(raw_items, list):
            raise AdapterError(f"Expected a list of evidence items, got {type(raw_items).__name__}")

        adapted: List[EvidenceItem] = []

        for idx, item in enumerate(raw_items):
            if not isinstance(item, dict):
                raise AdapterError(f"Evidence item at index {idx} must be a dictionary, got {type(item).__name__}")

            present_keys = list(item.keys())

            # 1. Required: Evidence ID
            ev_id = (
                item.get("id")
                or item.get("chunk_id")
                or item.get("evidence_id")
                or item.get("doc_id")
            )
            if not ev_id or not str(ev_id).strip():
                raise AdapterError(
                    f"Evidence item at index {idx} is missing required identifier alias "
                    f"('id' / 'chunk_id' / 'evidence_id' / 'doc_id'). Present keys: {present_keys}"
                )

            # 2. Required: Content / Text
            content = (
                item.get("content")
                or item.get("text")
                or item.get("extracted_text")
                or item.get("body")
                or item.get("raw_text")
                or item.get("snippet")
            )
            if content is None or not str(content).strip():
                raise AdapterError(
                    f"Evidence item at index {idx} is missing required text content alias "
                    f"('content' / 'text' / 'extracted_text' / 'body' / 'raw_text' / 'snippet'). Present keys: {present_keys}"
                )
            content = str(content).strip()

            # 3. Required: Modality
            raw_mod = (
                item.get("modality")
                or item.get("source_type")
                or item.get("file_type")
            )
            if not raw_mod or not str(raw_mod).strip():
                raise AdapterError(
                    f"Evidence item at index {idx} is missing required modality alias "
                    f"('modality' / 'source_type' / 'file_type'). Present keys: {present_keys}"
                )
            mod_str = str(raw_mod).strip().lower()
            if mod_str not in self.MODALITY_MAP:
                logger.warning(
                    "Evidence item %s has unrecognized modality '%s'; defaulting to EvidenceModality.OTHER",
                    ev_id, raw_mod,
                )
            modality = self.MODALITY_MAP.get(mod_str, EvidenceModality.OTHER)

            # 4. Optional: Directness (with warning on default)
            raw_dir = item.get("directness")
            if not raw_dir:
                logger.warning("Evidence item %s missing 'directness'; defaulting to 'primary'", ev_id)
                directness = DirectnessLevel.PRIMARY
            else:
                dir_str = str(raw_dir).strip().lower()
                directness = self.DIRECTNESS_MAP.get(dir_str, DirectnessLevel.PRIMARY)

            # 5. Extract and Normalize Metadata
            raw_meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}

            source_id = (
                raw_meta.get("source_id")
                or item.get("source_id")
                or raw_meta.get("source")
                or item.get("source")
                or raw_meta.get("source_name")
            )
            if not source_id:
                logger.warning("Evidence item %s missing 'source_id' metadata; defaulting to 'UNKNOWN_PROCESSOR_SRC'", ev_id)
                source_id = "UNKNOWN_PROCESSOR_SRC"

            filename = raw_meta.get("filename") or item.get("filename") or raw_meta.get("file_name") or item.get("file_name")
            file_type = raw_meta.get("file_type") or item.get("file_type") or raw_meta.get("mime_type")

            # Page number normalization
            page_val = (
                raw_meta.get("page_number")
                or raw_meta.get("page")
                or raw_meta.get("page_no")
                or item.get("page_number")
                or item.get("page")
                or item.get("page_no")
            )
            page_number = None
            if page_val is not None:
                try:
                    page_number = int(page_val)
                except (ValueError, TypeError):
                    logger.warning("Evidence item %s has non-integer page '%s'; ignoring", ev_id, page_val)
                    page_number = None

            section = raw_meta.get("section") or raw_meta.get("chapter") or raw_meta.get("header")
            table_name = raw_meta.get("table_name") or raw_meta.get("table")
            row_id = str(raw_meta.get("row_id") or raw_meta.get("row") or "") or None
            image_id = str(raw_meta.get("image_id") or raw_meta.get("figure_id") or "") or None
            author = raw_meta.get("author") or raw_meta.get("organization")
            checksum_hash = raw_meta.get("checksum_hash") or raw_meta.get("hash") or raw_meta.get("sha256")

            # Extraction confidence
            conf_val = raw_meta.get("extraction_confidence") or raw_meta.get("ocr_confidence") or item.get("confidence")
            extraction_conf = 1.0
            if conf_val is not None:
                try:
                    extraction_conf = float(conf_val)
                except (ValueError, TypeError):
                    extraction_conf = 1.0

            metadata = EvidenceMetadata(
                source_id=str(source_id),
                filename=str(filename) if filename else None,
                file_type=str(file_type) if file_type else None,
                page_number=page_number,
                section=str(section) if section else None,
                table_name=str(table_name) if table_name else None,
                row_id=row_id,
                image_id=image_id,
                author=str(author) if author else None,
                checksum_hash=str(checksum_hash) if checksum_hash else None,
                extraction_confidence=extraction_conf,
            )

            adapted.append(
                EvidenceItem(
                    id=str(ev_id),
                    content=content,
                    modality=modality,
                    directness=directness,
                    metadata=metadata,
                )
            )

        return adapted

    def adapt_processor_claims(
        self,
        raw_claims: List[Dict[str, Any]],
    ) -> List[Claim]:
        """
        Converts assumed Member 2 extracted proposition claims into Member 4 Claim models.
        Raises AdapterError if statement alias is missing.
        """
        if not isinstance(raw_claims, list):
            raise AdapterError(f"Expected a list of claims, got {type(raw_claims).__name__}")

        adapted: List[Claim] = []

        for idx, item in enumerate(raw_claims):
            if not isinstance(item, dict):
                raise AdapterError(f"Claim item at index {idx} must be a dictionary, got {type(item).__name__}")

            present_keys = list(item.keys())

            # Required: Statement
            statement = item.get("statement") or item.get("text") or item.get("claim") or item.get("assertion")
            if not statement or not str(statement).strip():
                raise AdapterError(
                    f"Claim item at index {idx} is missing required statement alias "
                    f"('statement' / 'text' / 'claim' / 'assertion'). Present keys: {present_keys}"
                )

            claim_id = item.get("id") or item.get("claim_id")
            if not claim_id:
                logger.warning("Claim item at index %d missing id; generating auto-id", idx)
                claim_id = f"CLM-PROC-{idx + 1:03d}"

            entity = item.get("entity") or item.get("subject")
            prop = item.get("property") or item.get("predicate") or item.get("attribute")
            val = item.get("value") or item.get("object")
            unit = item.get("unit") or item.get("dimension")

            ev_ids = item.get("evidence_ids") or item.get("evidence_id") or item.get("sources") or []
            if isinstance(ev_ids, str):
                ev_ids = [ev_ids]

            confidence = float(item.get("confidence") or item.get("score") or 1.0)
            polarity = bool(item.get("polarity", True))

            if polarity and re.search(r"\b(not|never|denied|false|disproved|prohibited|failed)\b", str(statement).lower()):
                if "polarity" not in item:
                    polarity = False

            adapted.append(
                Claim(
                    id=str(claim_id),
                    statement=str(statement).strip(),
                    entity=str(entity) if entity else None,
                    property=str(prop) if prop else None,
                    value=val,
                    unit=str(unit) if unit else None,
                    timestamp=item.get("timestamp") or item.get("date"),
                    time_period=item.get("time_period") or item.get("period"),
                    scope=item.get("scope"),
                    evidence_ids=[str(e) for e in ev_ids],
                    confidence=confidence,
                    polarity=polarity,
                )
            )

        return adapted

    # -------------------------------------------------------------------------
    # Member 3 (Knowledge Graph) Adaptation
    # -------------------------------------------------------------------------
    def adapt_knowledge_graph(
        self,
        kg_output: Union[Dict[str, Any], List[Dict[str, Any]]],
    ) -> Tuple[List[KGRelationship], List[Claim]]:
        """
        Converts assumed Member 3 knowledge graph outputs into KGRelationship models and claims.
        Raises AdapterError if source, relation, or target entity aliases are missing.
        """
        relationships: List[KGRelationship] = []
        derived_claims: List[Claim] = []

        raw_edges: List[Dict[str, Any]] = []
        if isinstance(kg_output, list):
            raw_edges = kg_output
        elif isinstance(kg_output, dict):
            raw_edges = kg_output.get("edges") or kg_output.get("relationships") or kg_output.get("triples") or []
        else:
            raise AdapterError(f"Knowledge graph output must be a dict or list, got {type(kg_output).__name__}")

        for idx, edge in enumerate(raw_edges):
            if not isinstance(edge, dict):
                raise AdapterError(f"Knowledge graph edge at index {idx} must be a dictionary, got {type(edge).__name__}")

            present_keys = list(edge.keys())

            # Required: Source entity
            src = (
                edge.get("source_entity")
                or edge.get("source")
                or edge.get("head")
                or edge.get("subject")
                or edge.get("from")
            )
            if not src or not str(src).strip():
                raise AdapterError(
                    f"Knowledge graph edge at index {idx} is missing required source entity alias "
                    f"('source_entity' / 'source' / 'head' / 'subject' / 'from'). Present keys: {present_keys}"
                )

            # Required: Relation
            rel = (
                edge.get("relation")
                or edge.get("predicate")
                or edge.get("edge")
                or edge.get("type")
                or edge.get("rel")
            )
            if not rel or not str(rel).strip():
                raise AdapterError(
                    f"Knowledge graph edge at index {idx} is missing required relationship alias "
                    f"('relation' / 'predicate' / 'edge' / 'type' / 'rel'). Present keys: {present_keys}"
                )

            # Required: Target entity
            tgt = (
                edge.get("target_entity")
                or edge.get("target")
                or edge.get("tail")
                or edge.get("object")
                or edge.get("to")
            )
            if not tgt or not str(tgt).strip():
                raise AdapterError(
                    f"Knowledge graph edge at index {idx} is missing required target entity alias "
                    f"('target_entity' / 'target' / 'tail' / 'object' / 'to'). Present keys: {present_keys}"
                )

            conf = float(edge.get("confidence") or edge.get("weight") or edge.get("score") or 1.0)

            ev_ids = edge.get("evidence_ids") or edge.get("citations") or edge.get("source_ids") or []
            if isinstance(ev_ids, str):
                ev_ids = [ev_ids]

            kg_rel = KGRelationship(
                source_entity=str(src).strip(),
                relation=str(rel).strip(),
                target_entity=str(tgt).strip(),
                confidence=conf,
                evidence_ids=[str(e) for e in ev_ids],
                provenance=str(edge.get("provenance") or "Member3_KnowledgeGraph"),
                properties=edge.get("properties") if isinstance(edge.get("properties"), dict) else {},
            )
            relationships.append(kg_rel)

            claim_id = f"CLM-KG-{idx + 1:03d}"
            statement = f"{src} {rel} {tgt}."
            derived_claims.append(
                Claim(
                    id=claim_id,
                    statement=statement,
                    entity=str(src).strip(),
                    property=str(rel).strip(),
                    value=str(tgt).strip(),
                    evidence_ids=[str(e) for e in ev_ids],
                    confidence=conf,
                    polarity=True,
                )
            )

        return relationships, derived_claims

    # -------------------------------------------------------------------------
    # Unified Request Builder
    # -------------------------------------------------------------------------
    def build_reasoning_request(
        self,
        question: str,
        processor_output: Optional[Dict[str, Any]] = None,
        kg_output: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        enable_ollama: bool = False,
        context: Optional[str] = None,
    ) -> ReasoningRequest:
        """
        Aggregates assumed Member 2 and Member 3 payloads into a validated ReasoningRequest.
        Fails with AdapterError if question is empty or if any mandatory field is missing.
        """
        if not question or not question.strip():
            raise AdapterError("ReasoningRequest requires a non-empty question string.")

        evidence_items: List[EvidenceItem] = []
        claims: List[Claim] = []
        kg_relationships: List[KGRelationship] = []

        if processor_output and isinstance(processor_output, dict):
            raw_docs = processor_output.get("documents") or processor_output.get("chunks") or processor_output.get("evidence_items")
            if raw_docs is not None:
                evidence_items.extend(self.adapt_processor_evidence(raw_docs))

            raw_claims = processor_output.get("claims") or processor_output.get("extracted_claims")
            if raw_claims is not None:
                claims.extend(self.adapt_processor_claims(raw_claims))

        if kg_output is not None:
            rels, derived_claims = self.adapt_knowledge_graph(kg_output)
            kg_relationships.extend(rels)
            claims.extend(derived_claims)

        return ReasoningRequest(
            question=question.strip(),
            claims=claims,
            evidence_items=evidence_items,
            kg_relationships=kg_relationships,
            context=context,
            enable_ollama=enable_ollama,
        )
