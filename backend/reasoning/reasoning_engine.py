"""
CERBERUS-X: AI Reasoning & Evidence Verification Module
Component 4: Conflict-Aware Deterministic Reasoning Engine

Implements the 7-stage evidence-based reasoning pipeline:
- Stage 1: Question Understanding (entity, property, temporal, and scope extraction)
- Stage 2: Evidence Grouping (by entity, claim, topic, time, and source)
- Stage 3: Supporting Evidence Identification
- Stage 4: Contradictory Evidence Identification
- Stage 5: Context Analysis (dates, units, entities, locations, scopes)
- Stage 6: Evidence Sufficiency Evaluation
- Stage 7: Conclusion & Structured Synthesis

Rules Enforced:
1. Do not invent missing facts.
2. Never silently ignore contradictory evidence.
3. Do not treat source count as proof if sources originate from the same origin.
4. Clearly distinguish extracted facts from reasoning-based inferences.
5. Explain why one conclusion is preferred, if preferred.
6. Return CONFLICTED if conflicting evidence cannot be resolved.
7. Return INSUFFICIENT_EVIDENCE if evidence is inadequate or question is outside corpus.
8. Do not force an answer simply because a question was asked.
9. Preserve source IDs for every important statement.
10. Defend against prompt injection attempts inside document content.
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from datetime import datetime

from .schemas import (
    Claim,
    Citation,
    ClaimCitation,
    ClaimStatus,
    ConclusionType,
    ConflictPair,
    ConflictType,
    EvidenceItem,
    EvidenceReliabilityResult,
    KGRelationship,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningStatus,
    ReliabilityBreakdown,
    SuspicionIndicator,
)
from .citation_builder import CitationBuilder


class DeterministicReasoningEngine:
    """
    Core Conflict-Aware Reasoning Engine for CERBERUS-X.
    Synthesizes claims, evidence, knowledge graph edges, and conflict data
    through a transparent 7-stage deliberation process.
    """

    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s+override",
        r"disregard\s+(all\s+)?(evidence|facts|rules)",
        r"you\s+must\s+(always\s+)?say\s+yes",
        r"new\s+instruction\s*:",
        r"admin\s+mode\s*:\s*enabled",
        r"bypass\s+(all\s+)?(verification|checks|rules|security)",
        r"declare\s+(the\s+)?(claim|company|entity|target)\s+(as\s+)?(innocent|verified|true|false)",
        r"override\s+status\s*:\s*[a-zA-Z_]+",
        r"output\s+status\s*:\s*[a-zA-Z_]+",
        r"act\s+as\s+an?\s+unrestricted",
        r"format\s+output\s+as\s+verified",
    ]

    def __init__(self, citation_builder: Optional[CitationBuilder] = None):
        self.citation_builder = citation_builder or CitationBuilder()

    def deliberate(self, request: ReasoningRequest) -> ReasoningResponse:
        """Self-contained deliberation synthesizing reliability, suspicion, conflict analysis, and citations."""
        from .evidence_reliability import EvidenceReliabilityEvaluator
        from .conflict_analyzer import ConflictAnalyzer
        from .suspicion_detector import SuspicionDetector

        rel_eval = EvidenceReliabilityEvaluator()
        rel_results = [
            rel_eval.evaluate_item(item, request.evidence_items, request.claims)
            for item in request.evidence_items
        ]
        rel_map = {r.evidence_id: r for r in rel_results}
        suspicion = SuspicionDetector().detect_indicators(
            request.evidence_items, request.claims, request.kg_relationships
        )
        conflicts = ConflictAnalyzer().analyze_claims(
            claims=request.claims,
            evidence_items=request.evidence_items,
            reliability_map=rel_map,
        )
        citations = self.citation_builder.build_citations_for_evidence(
            evidence_items=request.evidence_items
        )
        return self.reason(
            request=request,
            reliability_map=rel_map,
            conflicts=conflicts,
            suspicion_indicators=suspicion,
            citations=citations,
        )

    def reason(
        self,
        request: ReasoningRequest,
        reliability_map: Dict[str, Union[ReliabilityBreakdown, EvidenceReliabilityResult]],
        conflicts: List[ConflictPair],
        suspicion_indicators: List[SuspicionIndicator],
        citations: List[Citation],
    ) -> ReasoningResponse:
        reasoning_steps: List[str] = []
        assumptions: List[str] = []
        limitations: List[str] = []
        audit_trail: List[str] = ["Initiated 7-stage conflict-aware reasoning engine."]

        # Sanitize / Audit prompt injection inside evidence content
        self._audit_prompt_injection(request.evidence_items, limitations, reasoning_steps, audit_trail)

        # ---------------------------------------------------------------------
        # STAGE 1: Question Understanding
        # ---------------------------------------------------------------------
        q_meta = self._stage1_understand_question(request.question)
        reasoning_steps.append(
            f"Stage 1 (Question Understanding): Identified target entity='{q_meta['target_entity'] or 'Unspecified'}', "
            f"property='{q_meta['target_property'] or 'General'}', time_constraint='{q_meta['time_constraint'] or 'Unbounded'}', "
            f"query_type='{q_meta['query_type']}'."
        )

        # ---------------------------------------------------------------------
        # STAGE 2: Evidence Grouping (Entity, Claim, Topic, Time, Source)
        # ---------------------------------------------------------------------
        evidence_by_id = {ev.id: ev for ev in request.evidence_items}
        groupings = self._stage2_group_evidence(request, reliability_map)
        reasoning_steps.append(
            f"Stage 2 (Evidence Grouping): Grouped {len(request.evidence_items)} evidence item(s) across "
            f"{len(groupings['by_entity'])} entities, {len(groupings['by_source'])} distinct sources, "
            f"and {len(groupings['by_time'])} temporal snapshots."
        )

        # Rule 3 Check: Are multiple sources actually co-originating duplicates?
        co_origin_notes = groupings["co_origin_notes"]
        if co_origin_notes:
            limitations.extend(co_origin_notes)
            reasoning_steps.append(
                f"Stage 2 (Provenance Origin Check): {len(co_origin_notes)} potential single-origin / duplicate cluster(s) detected. "
                "Co-originating items discounted from independent confirmation counts."
            )

        # ---------------------------------------------------------------------
        # STAGE 3: Supporting Evidence Identification
        # ---------------------------------------------------------------------
        supporting_claims, supporting_ev_ids, supported_facts = self._stage3_identify_supporting(
            request, q_meta, reliability_map, groupings, conflicts
        )
        reasoning_steps.append(
            f"Stage 3 (Supporting Evidence): Identified {len(supporting_claims)} supporting claim(s) backed by "
            f"{len(supporting_ev_ids)} evidence item(s) ({', '.join(sorted(supporting_ev_ids)) if supporting_ev_ids else 'None'})."
        )

        # ---------------------------------------------------------------------
        # STAGE 4: Contradictory Evidence Identification
        # ---------------------------------------------------------------------
        opposing_claims, opposing_ev_ids, opposing_facts = self._stage4_identify_contradictory(
            request, q_meta, reliability_map, conflicts
        )
        reasoning_steps.append(
            f"Stage 4 (Contradictory Evidence): Identified {len(opposing_claims)} opposing claim(s) backed by "
            f"{len(opposing_ev_ids)} evidence item(s) ({', '.join(sorted(opposing_ev_ids)) if opposing_ev_ids else 'None'})."
        )

        # ---------------------------------------------------------------------
        # STAGE 5: Context Analysis (Dates, Units, Entity, Location, Scopes)
        # ---------------------------------------------------------------------
        context_resolutions, unresolved_conflicts = self._stage5_context_analysis(
            supporting_claims, opposing_claims, conflicts, groupings
        )
        for cres in context_resolutions:
            reasoning_steps.append(f"Stage 5 (Context Analysis): {cres}")

        # ---------------------------------------------------------------------
        # STAGE 6: Evidence Sufficiency Evaluation
        # ---------------------------------------------------------------------
        is_sufficient, partial_flag, sufficiency_msg = self._stage6_evaluate_sufficiency(
            request=request,
            q_meta=q_meta,
            supporting_ids=supporting_ev_ids,
            opposing_ids=opposing_ev_ids,
            reliability_map=reliability_map,
            assumptions=assumptions,
            limitations=limitations,
        )
        reasoning_steps.append(f"Stage 6 (Evidence Sufficiency): {sufficiency_msg}")

        # ---------------------------------------------------------------------
        # STAGE 7: Conclusion & Synthesis
        # ---------------------------------------------------------------------
        status, confidence, answer, summary, confidence_explanation = self._stage7_derive_conclusion(
            request=request,
            q_meta=q_meta,
            is_sufficient=is_sufficient,
            partial_flag=partial_flag,
            supporting_claims=supporting_claims,
            opposing_claims=opposing_claims,
            supporting_ev_ids=supporting_ev_ids,
            opposing_ev_ids=opposing_ev_ids,
            unresolved_conflicts=unresolved_conflicts,
            evidence_by_id=evidence_by_id,
            reliability_map=reliability_map,
            reasoning_steps=reasoning_steps,
            limitations=limitations,
        )
        reasoning_steps.append(
            f"Stage 7 (Conclusion): Reached terminal status '{status.value}' with calibrated confidence {confidence:.2f}."
        )

        # Map to ConclusionType for backward compatibility
        status_to_conclusion = {
            ReasoningStatus.ANSWERED: ConclusionType.SUPPORTED if not opposing_ev_ids else ConclusionType.INCONCLUSIVE,
            ReasoningStatus.PARTIALLY_ANSWERED: ConclusionType.INCONCLUSIVE,
            ReasoningStatus.CONFLICTED: ConclusionType.CONFLICTING,
            ReasoningStatus.INSUFFICIENT_EVIDENCE: ConclusionType.INSUFFICIENT_EVIDENCE,
        }
        conclusion_type = status_to_conclusion.get(status, ConclusionType.INSUFFICIENT_EVIDENCE)
        is_insufficient = (status == ReasoningStatus.INSUFFICIENT_EVIDENCE)

        # Extract structured facts, inferences, unknowns with transparent claim classification
        facts, inferences, unknowns = self._format_epistemic_categories(
            request=request,
            status=status,
            unresolved_conflicts=unresolved_conflicts,
            supporting_claims=supporting_claims,
            opposing_claims=opposing_claims,
            evidence_by_id=evidence_by_id,
            reliability_map=reliability_map,
            q_meta=q_meta,
            conflicts=conflicts,
        )

        # Filter citations to only referenced evidence items
        referenced_ids = set(supporting_ev_ids).union(opposing_ev_ids)
        if not referenced_ids and request.evidence_items:
            # If no items directly linked but evidence exists, provide citations for reviewed items
            referenced_ids = {ev.id for ev in request.evidence_items}

        relevant_citations = [c for c in citations if c.evidence_id in referenced_ids]

        # Build claim-level citations with invalid reference detection & deduplication
        claim_citations = self.citation_builder.build_claim_citations(
            claims=request.claims,
            evidence_items=request.evidence_items,
        )

        return ReasoningResponse(
            question=request.question,
            status=status,
            conclusion_type=conclusion_type,
            answer=answer,
            summary=summary,
            supporting_claims=supporting_claims,
            opposing_claims=opposing_claims,
            unresolved_conflicts=unresolved_conflicts,
            reasoning_steps=reasoning_steps,
            assumptions=assumptions,
            limitations=limitations,
            confidence=round(confidence, 4),
            confidence_score=round(confidence, 4),
            confidence_explanation=confidence_explanation,
            is_insufficient_evidence=is_insufficient,
            facts=facts,
            inferences=inferences,
            unknowns=unknowns,
            supporting_evidence_ids=sorted(supporting_ev_ids),
            opposing_evidence_ids=sorted(opposing_ev_ids),
            evidence_reliability=reliability_map,
            conflicts=conflicts,
            suspicion_indicators=suspicion_indicators,
            citations=relevant_citations,
            claim_citations=claim_citations,
            reasoning_mode="deterministic",
            audit_trail=audit_trail,
        )

    # -------------------------------------------------------------------------
    # Stage 1: Question Understanding
    # -------------------------------------------------------------------------
    def _stage1_understand_question(self, question: str) -> Dict[str, Any]:
        q_lower = question.lower()
        tokens = set(re.findall(r"\b[A-Za-z0-9_-]{2,}\b", q_lower))

        # 1. Target Entity Extraction (capitalized tokens or multi-word entities)
        cap_matches = re.findall(r"\b[A-Z][a-zA-Z0-9_-]+(?:\s+[A-Z][a-zA-Z0-9_-]+)*\b", question)
        question_words = {"where", "what", "when", "why", "who", "how", "did", "does", "is", "was", "can", "could", "should", "would", "which"}
        non_q_matches = [m for m in cap_matches if m.lower() not in question_words]
        target_entity = non_q_matches[0] if non_q_matches else (cap_matches[0] if cap_matches else None)

        # 2. Target Property Extraction
        property_keywords = {
            "revenue": ["revenue", "sales", "earnings", "gross", "turnover", "income"],
            "payload_capacity": ["payload", "capacity", "takeoff weight", "load"],
            "location": ["where", "located", "location", "headquarters", "city", "port"],
            "status": ["status", "active", "inactive", "operational", "condition"],
            "date": ["when", "date", "year", "month", "time"],
            "temperature": ["temperature", "heat", "thermal", "degrees", "celsius"],
            "cost": ["cost", "price", "budget", "expenditure", "funding"],
            "ceo": ["ceo", "director", "chief executive", "leader", "president"],
            "cause": ["why", "cause", "reason", "breach", "violate", "violation"],
        }
        target_property = None
        for prop, kws in property_keywords.items():
            if any(kw in q_lower for kw in kws):
                target_property = prop
                break

        # 3. Temporal Constraints
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", question)
        quarter_match = re.search(r"\b(Q[1-4]|FY\s*\d{2,4})\b", question, re.IGNORECASE)
        date_match = re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b", q_lower)

        time_constraint = None
        if quarter_match:
            time_constraint = quarter_match.group(0).upper()
        elif year_match:
            time_constraint = year_match.group(0)
        elif date_match:
            time_constraint = date_match.group(0).title()

        # 4. Scope constraint
        scope = None
        if "north america" in q_lower:
            scope = "North America"
        elif "global" in q_lower or "worldwide" in q_lower:
            scope = "Global"
        elif "europe" in q_lower:
            scope = "Europe"

        # 5. Query type
        if q_lower.startswith(("is ", "was ", "did ", "does ", "can ", "has ", "will ", "were ")):
            query_type = "CONFIRMATION_BOOLEAN"
        elif any(w in q_lower for w in ["how much", "how many", "what amount", "capacity", "cost", "budget"]):
            query_type = "QUANTITATIVE"
        elif any(w in q_lower for w in ["where", "which location"]):
            query_type = "LOCATION"
        elif any(w in q_lower for w in ["when", "what date", "what time"]):
            query_type = "TEMPORAL"
        else:
            query_type = "ATTRIBUTE_LOOKUP"

        return {
            "question": question,
            "target_entity": target_entity,
            "target_property": target_property,
            "time_constraint": time_constraint,
            "scope": scope,
            "query_type": query_type,
            "tokens": tokens,
        }

    # -------------------------------------------------------------------------
    # Stage 2: Evidence Grouping (Entity, Claim, Topic, Time, Source)
    # -------------------------------------------------------------------------
    def _stage2_group_evidence(
        self,
        request: ReasoningRequest,
        reliability_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        by_entity: Dict[str, List[str]] = {}
        by_claim: Dict[str, List[str]] = {}
        by_topic: Dict[str, List[str]] = {}
        by_time: Dict[str, List[str]] = {}
        by_source: Dict[str, List[str]] = {}
        co_origin_notes: List[str] = []

        # Map claims to evidence
        for claim in request.claims:
            by_claim[claim.id] = claim.evidence_ids
            if claim.entity:
                by_entity.setdefault(claim.entity.strip().lower(), []).extend(claim.evidence_ids)
            if claim.time_period:
                by_time.setdefault(claim.time_period.strip().lower(), []).extend(claim.evidence_ids)
            if claim.property:
                by_topic.setdefault(claim.property.strip().lower(), []).extend(claim.evidence_ids)

        # Map KG relationships
        for kg in request.kg_relationships:
            by_entity.setdefault(kg.source_entity.strip().lower(), []).extend(kg.evidence_ids)
            by_entity.setdefault(kg.target_entity.strip().lower(), []).extend(kg.evidence_ids)
            by_topic.setdefault(kg.relation.strip().lower(), []).extend(kg.evidence_ids)

        # Group evidence items by source and check for duplicate/co-origin items
        source_clusters: Dict[str, List[str]] = {}
        hash_clusters: Dict[str, List[str]] = {}
        content_clusters: Dict[str, List[str]] = {}

        for ev in request.evidence_items:
            src = (ev.metadata.source_id or "UNKNOWN").strip().lower()
            by_source.setdefault(src, []).append(ev.id)
            source_clusters.setdefault(src, []).append(ev.id)

            # Hash check
            h = (ev.metadata.checksum_hash or "").strip().lower()
            if h:
                hash_clusters.setdefault(h, []).append(ev.id)

            # Text content exact match check
            norm_content = re.sub(r"\s+", " ", ev.content.strip().lower())
            content_clusters.setdefault(norm_content, []).append(ev.id)

            # Time grouping from evidence metadata
            if ev.metadata.timestamp:
                by_time.setdefault(str(ev.metadata.timestamp), []).append(ev.id)

        # Detect co-origin clusters (multiple items sharing identical origin or content)
        for src, ev_list in source_clusters.items():
            if len(ev_list) >= 2 and src != "unknown":
                co_origin_notes.append(
                    f"Evidence items {ev_list} originate from the same source system ('{src}'). Treated as single-origin evidence cluster."
                )

        for h, ev_list in hash_clusters.items():
            if len(ev_list) >= 2:
                co_origin_notes.append(
                    f"Evidence items {ev_list} share cryptographic hash '{h}'. Verified as duplicate copies."
                )

        for content_str, ev_list in content_clusters.items():
            if len(ev_list) >= 2 and len(content_str) > 20:
                co_origin_notes.append(
                    f"Evidence items {ev_list} share verbatim identical text content. Multiple copies do not count as independent confirmation."
                )

        return {
            "by_entity": by_entity,
            "by_claim": by_claim,
            "by_topic": by_topic,
            "by_time": by_time,
            "by_source": by_source,
            "co_origin_notes": list(set(co_origin_notes)),
        }

    # -------------------------------------------------------------------------
    # Stage 3: Supporting Evidence Identification
    # -------------------------------------------------------------------------
    def _stage3_identify_supporting(
        self,
        request: ReasoningRequest,
        q_meta: Dict[str, Any],
        reliability_map: Dict[str, Any],
        groupings: Dict[str, Any],
        conflicts: Optional[List[ConflictPair]] = None,
    ) -> Tuple[List[Claim], Set[str], List[str]]:
        supporting_claims: List[Claim] = []
        supporting_ev_ids: Set[str] = set()
        supported_facts: List[str] = []
        q_tokens = q_meta["tokens"]

        # Identify claims that lost in resolved conflicts (overridden by higher reliability)
        losing_claim_ids: Set[str] = set()
        if conflicts:
            for conflict in conflicts:
                if conflict.is_resolved and conflict.resolution_reason:
                    m = re.search(r"(?:in favor of Claim|Resolved:\s*Claim)\s+([A-Za-z0-9_-]+)", conflict.resolution_reason)
                    if m:
                        winning_id = m.group(1)
                        losing_id = conflict.claim_b_id if winning_id == conflict.claim_a_id else conflict.claim_a_id
                        losing_claim_ids.add(losing_id)

        # 1. Match from claims
        for claim in request.claims:
            if not claim.polarity or claim.id in losing_claim_ids:
                continue

            # Check entity and semantic match
            claim_tokens = set(re.findall(r"\b[A-Za-z0-9_-]{2,}\b", claim.statement.lower()))
            overlap = q_tokens.intersection(claim_tokens)

            is_entity_match = False
            if q_meta["target_entity"] and claim.entity:
                if (
                    q_meta["target_entity"].lower() in claim.entity.lower()
                    or claim.entity.lower() in q_meta["target_entity"].lower()
                ):
                    is_entity_match = True

            # If token overlap or entity matches, assess as supporting
            if is_entity_match or len(overlap) >= 2:
                supporting_claims.append(claim)
                for eid in claim.evidence_ids:
                    # Check reliability threshold
                    score = self._get_overall_score(reliability_map.get(eid))
                    if score >= request.min_reliability_threshold:
                        supporting_ev_ids.add(eid)
                supported_facts.append(
                    f"Extracted Fact: {claim.statement} (Citing: {', '.join(claim.evidence_ids) or 'Unlinked'})"
                )

        # 2. Match from Knowledge Graph Relationships
        for kg in request.kg_relationships:
            kg_tokens = {kg.source_entity.lower(), kg.relation.lower(), kg.target_entity.lower()}
            if q_meta["target_entity"] and q_meta["target_entity"].lower() in kg.source_entity.lower():
                supported_facts.append(
                    f"KG Triple: ({kg.source_entity}) -[{kg.relation}]-> ({kg.target_entity}) [Confidence: {kg.confidence:.2f}]"
                )
                supporting_ev_ids.update(kg.evidence_ids)

        # 3. Direct evidence content token overlap fallback
        if not supporting_claims and not supported_facts:
            for ev in request.evidence_items:
                ev_tokens = set(re.findall(r"\b[A-Za-z0-9_-]{2,}\b", ev.content.lower()))
                overlap = q_tokens.intersection(ev_tokens)
                if len(overlap) >= 2:
                    # Check for explicit negation in evidence
                    if not re.search(r"\b(not|never|denied|false|rejected|disproved)\b", ev.content.lower()):
                        score = self._get_overall_score(reliability_map.get(ev.id))
                        if score >= request.min_reliability_threshold:
                            supporting_ev_ids.add(ev.id)
                            supported_facts.append(
                                f"Direct Evidence: Excerpt in {ev.id} affirms query subjects ({', '.join(overlap)})."
                            )

        return supporting_claims, supporting_ev_ids, supported_facts

    # -------------------------------------------------------------------------
    # Stage 4: Contradictory Evidence Identification
    # -------------------------------------------------------------------------
    def _stage4_identify_contradictory(
        self,
        request: ReasoningRequest,
        q_meta: Dict[str, Any],
        reliability_map: Dict[str, Any],
        conflicts: List[ConflictPair],
    ) -> Tuple[List[Claim], Set[str], List[str]]:
        opposing_claims: List[Claim] = []
        opposing_ev_ids: Set[str] = set()
        opposing_facts: List[str] = []
        q_tokens = q_meta["tokens"]

        # 1. Claims with negative polarity on same subject
        for claim in request.claims:
            claim_tokens = set(re.findall(r"\b[A-Za-z0-9_-]{2,}\b", claim.statement.lower()))
            overlap = q_tokens.intersection(claim_tokens)

            if len(overlap) >= 2:
                if not claim.polarity:
                    opposing_claims.append(claim)
                    for eid in claim.evidence_ids:
                        score = self._get_overall_score(reliability_map.get(eid))
                        if score >= request.min_reliability_threshold:
                            opposing_ev_ids.add(eid)
                    opposing_facts.append(
                        f"Contradictory Claim: {claim.statement} (Negation cited by: {', '.join(claim.evidence_ids)})"
                    )

        # 2. Check conflicts list from Conflict Analyzer
        for conflict in conflicts:
            if conflict.conflict_type in (ConflictType.CONTRADICTION, ConflictType.UNRESOLVED_CONFLICT):
                if not conflict.is_resolved:
                    claim_b = next((c for c in request.claims if c.id == conflict.claim_b_id), None)
                    if claim_b and claim_b not in opposing_claims:
                        opposing_claims.append(claim_b)
                        for eid in claim_b.evidence_ids:
                            opposing_ev_ids.add(eid)
                        opposing_facts.append(
                            f"Contradictory Evidence in {conflict.claim_b_id}: {conflict.description}"
                        )
                else:
                    # Conflict was resolved by evidence reliability weighting (e.g. High-reliability wins)
                    opposing_facts.append(
                        f"Resolved Contradiction: {conflict.description} ({conflict.resolution_reason})"
                    )

        # 3. Direct evidence content negative assertions
        if not opposing_claims and not opposing_facts:
            for ev in request.evidence_items:
                ev_tokens = set(re.findall(r"\b[A-Za-z0-9_-]{2,}\b", ev.content.lower()))
                overlap = q_tokens.intersection(ev_tokens)
                if len(overlap) >= 2:
                    if re.search(r"\b(was not|did not|never|refuted|denied|false|disproved|prohibited)\b", ev.content.lower()):
                        score = self._get_overall_score(reliability_map.get(ev.id))
                        if score >= request.min_reliability_threshold:
                            opposing_ev_ids.add(ev.id)
                            opposing_facts.append(
                                f"Direct Counter-Evidence: Excerpt in {ev.id} explicitly refutes query proposition."
                            )

        return opposing_claims, opposing_ev_ids, opposing_facts

    # -------------------------------------------------------------------------
    # Stage 5: Context Analysis (Dates, Units, Entity, Location, Scopes)
    # -------------------------------------------------------------------------
    def _stage5_context_analysis(
        self,
        supporting_claims: List[Claim],
        opposing_claims: List[Claim],
        conflicts: List[ConflictPair],
        groupings: Dict[str, Any],
    ) -> Tuple[List[str], List[ConflictPair]]:
        resolutions: List[str] = []
        unresolved: List[ConflictPair] = []

        for conflict in conflicts:
            if conflict.conflict_type in (ConflictType.CONTRADICTION, ConflictType.UNRESOLVED_CONFLICT):
                if conflict.is_resolved:
                    resolutions.append(
                        f"Resolved discrepancy between {conflict.claim_a_id} and {conflict.claim_b_id}: {conflict.resolution_reason}"
                    )
                else:
                    unresolved.append(conflict)
                    resolutions.append(
                        f"Unresolved factual deadlock between {conflict.claim_a_id} and {conflict.claim_b_id}: {conflict.description}"
                    )
            elif conflict.conflict_type == ConflictType.PARTIAL_CONTRADICTION:
                temporal_flag = ""
                if conflict.temporal_resolution:
                    temporal_flag = " Newer record flagged as current; historical record retained (not dropped) for longitudinal context."
                resolutions.append(
                    f"Contextual divergence accounted for: {conflict.description} ({conflict.resolution_reason or 'Distinct scopes/times'}).{temporal_flag}"
                )

        # Temporal Context Check
        time_keys = list(groupings["by_time"].keys())
        if len(time_keys) >= 2:
            resolutions.append(
                f"Multi-temporal data detected across time periods: {', '.join(time_keys[:3])}. Statements reflect distinct temporal windows."
            )

        return resolutions, unresolved

    # -------------------------------------------------------------------------
    # Stage 6: Evidence Sufficiency Evaluation
    # -------------------------------------------------------------------------
    def _stage6_evaluate_sufficiency(
        self,
        request: ReasoningRequest,
        q_meta: Dict[str, Any],
        supporting_ids: Set[str],
        opposing_ids: Set[str],
        reliability_map: Dict[str, Any],
        assumptions: List[str],
        limitations: List[str],
    ) -> Tuple[bool, bool, str]:
        # Condition A: Zero evidence provided
        if not request.evidence_items:
            return False, False, "Zero evidence items provided; completely insufficient evidence to answer."

        # Condition B: Question entirely outside supplied evidence corpus
        q_tokens = q_meta["tokens"]
        corpus_tokens: Set[str] = set()
        for ev in request.evidence_items:
            corpus_tokens.update(re.findall(r"\b[A-Za-z0-9_-]{2,}\b", ev.content.lower()))

        meaningful_q_tokens = {t for t in q_tokens if len(t) > 3 and t not in {"what", "when", "where", "which", "does", "with", "from"}}
        overlap = meaningful_q_tokens.intersection(corpus_tokens)

        if not overlap:
            limitations.append(
                f"Question subject '{request.question}' is completely absent from the supplied evidence corpus."
            )
            return False, False, "The question lies outside the supplied evidence corpus. No matching entities or properties found."

        # Condition C: Only unreliable hearsay evidence available
        usable_evs = [
            eid for eid, res in reliability_map.items()
            if self._get_overall_score(res) >= request.min_reliability_threshold
        ]
        if not usable_evs:
            limitations.append(
                f"All provided evidence items fell below the minimum reliability threshold ({request.min_reliability_threshold})."
            )
            return False, False, "Available evidence lacks verified provenance or exceeds unreliability thresholds."

        # Condition D: Partial Answer (query asks for multi-part attribute or entity where only subset is documented)
        if q_meta["query_type"] == "QUANTITATIVE" and not any(re.search(r"\d+", ev.content) for ev in request.evidence_items):
            assumptions.append("Question requested quantitative metrics, but only qualitative text was documented.")
            return True, True, "Qualitative evidence is present, but exact quantitative metrics requested are absent (Partial Answer)."

        # Condition E: Supporting or opposing evidence is present
        if supporting_ids or opposing_ids:
            return True, False, f"Sufficient relevant evidence identified ({len(supporting_ids)} supporting, {len(opposing_ids)} opposing)."

        # Fallback
        return False, False, "Evidence is insufficient to substantiate a definitive response to the inquiry."

    # -------------------------------------------------------------------------
    # Stage 7: Conclusion & Synthesis
    # -------------------------------------------------------------------------
    def _stage7_derive_conclusion(
        self,
        request: ReasoningRequest,
        q_meta: Dict[str, Any],
        is_sufficient: bool,
        partial_flag: bool,
        supporting_claims: List[Claim],
        opposing_claims: List[Claim],
        supporting_ev_ids: Set[str],
        opposing_ev_ids: Set[str],
        unresolved_conflicts: List[ConflictPair],
        evidence_by_id: Dict[str, EvidenceItem],
        reliability_map: Dict[str, Any],
        reasoning_steps: List[str],
        limitations: List[str],
    ) -> Tuple[ReasoningStatus, float, str, str, str]:
        # Rule 7: If evidence is inadequate, return INSUFFICIENT_EVIDENCE
        if not is_sufficient:
            status = ReasoningStatus.INSUFFICIENT_EVIDENCE
            confidence = 0.0
            explanation = "Confidence 0.00: Insufficient evidence in corpus to substantiate or address the query proposition."
            answer = (
                f"Insufficient evidence to conclude on: '{request.question}'. "
                "The supplied evidence corpus does not contain sufficient verified, reliable facts to answer."
            )
            summary = (
                f"Abstention triggered: {len(request.evidence_items)} evidence item(s) reviewed, but no reliable, "
                "substantive link to the question proposition could be established."
            )
            return status, confidence, answer, summary, explanation

        # Rule 6: If conflicting evidence cannot be resolved, return CONFLICTED
        if unresolved_conflicts:
            status = ReasoningStatus.CONFLICTED
            scores_supp = [self._get_overall_score(reliability_map.get(eid)) for eid in supporting_ev_ids if eid in reliability_map]
            scores_opp = [self._get_overall_score(reliability_map.get(eid)) for eid in opposing_ev_ids if eid in reliability_map]
            avg_supp = sum(scores_supp) / len(scores_supp) if scores_supp else 0.70
            avg_opp = sum(scores_opp) / len(scores_opp) if scores_opp else 0.70
            penalty = min(0.20, 0.05 * len(unresolved_conflicts))
            raw_conf = max(0.15, min(0.40, (avg_supp * 0.40) - penalty))
            confidence = round(raw_conf, 4)
            explanation = (
                f"Confidence strictly limited to {confidence:.2f} due to {len(unresolved_conflicts)} active unresolved "
                f"contradiction(s). Base supporting reliability ({avg_supp:.2f}) penalized by opposing evidence ({avg_opp:.2f}). "
                "Epistemic assessment reflecting evidentiary deadlock, not statistical probability of truth."
            )
            conflict_details = "; ".join(f"[{c.claim_a_id} vs {c.claim_b_id}: {c.description}]" for c in unresolved_conflicts[:2])
            answer = (
                f"Conflicted evidence: A definitive answer to '{request.question}' cannot be established due to "
                f"unresolved contradictions between sources: {conflict_details}."
            )
            summary = (
                f"Evaluation halted on unresolved conflict. Contradictory evidence was detected across independent records. "
                "Adjudication cannot be forced without secondary ground truth."
            )
            return status, confidence, answer, summary, explanation

        # Partial Answer Condition
        if partial_flag:
            status = ReasoningStatus.PARTIALLY_ANSWERED
            scores_supp = [self._get_overall_score(reliability_map.get(eid)) for eid in supporting_ev_ids if eid in reliability_map]
            avg_supp = sum(scores_supp) / len(scores_supp) if scores_supp else 0.70
            confidence = round(min(0.60, max(0.20, avg_supp * 0.65)), 4)
            explanation = (
                f"Confidence capped at {confidence:.2f}: Contextual evidence exists (base reliability {avg_supp:.2f}), "
                "but specific quantitative parameters or attributes are missing from records."
            )
            cited_srcs = [evidence_by_id[eid].metadata.source_id for eid in supporting_ev_ids if eid in evidence_by_id]
            answer = (
                f"Partially answered: Reliable evidence provides contextual background on '{request.question}', "
                f"but does not fully satisfy all specific parameters (Sources: {', '.join(filter(None, cited_srcs)) or 'Unspecified'})."
            )
            summary = (
                "Partial answer derived: Core entity verified, but requested quantitative or specific attributes are missing from records."
            )
            return status, confidence, answer, summary, explanation

        # Direct Contradiction / Opposing Only
        if opposing_ev_ids and not supporting_ev_ids:
            status = ReasoningStatus.ANSWERED
            scores = [self._get_overall_score(reliability_map.get(eid)) for eid in opposing_ev_ids if eid in reliability_map]
            avg_rel = sum(scores) / len(scores) if scores else 0.80
            count_factor = min(1.0, 0.75 + (0.08 * len(opposing_ev_ids)))
            confidence = round(min(0.95, max(0.50, avg_rel * count_factor)), 4)
            explanation = (
                f"Confidence {confidence:.2f} derived deterministically: Conclusive refutation across {len(opposing_ev_ids)} "
                f"verified item(s) with average reliability {avg_rel:.2f}."
            )
            cited_srcs = [evidence_by_id[eid].metadata.source_id for eid in opposing_ev_ids if eid in evidence_by_id]
            answer = (
                f"Refuted: Reliable evidence contradicts the proposition in '{request.question}' "
                f"(Sources: {', '.join(filter(None, cited_srcs)) or ', '.join(opposing_ev_ids)})."
            )
            summary = (
                f"Evidence conclusively denies or refutes the query proposition across {len(opposing_ev_ids)} verified item(s)."
            )
            return status, confidence, answer, summary, explanation

        # Supported Answer
        if supporting_ev_ids and not opposing_ev_ids:
            status = ReasoningStatus.ANSWERED
            distinct_sources = {
                (evidence_by_id[eid].metadata.source_id or eid).strip().lower()
                for eid in supporting_ev_ids if eid in evidence_by_id
            }
            indep_count = len(distinct_sources)
            scores = [self._get_overall_score(reliability_map.get(eid)) for eid in supporting_ev_ids if eid in reliability_map]
            avg_rel = sum(scores) / len(scores) if scores else 0.85

            if indep_count >= 3:
                corrob_mult = 1.00
                corrob_desc = "3+ independent sources (1.00)"
            elif indep_count == 2:
                corrob_mult = 0.95
                corrob_desc = "2 independent sources (0.95)"
            else:
                corrob_mult = 0.85
                corrob_desc = "single source (0.85)"

            relevance = 1.00 if q_meta.get("target_entity") else 0.90
            raw = avg_rel * corrob_mult * relevance
            confidence = round(min(0.98, max(0.50, raw)), 4)
            explanation = (
                f"Confidence {confidence:.2f} computed deterministically: Base reliability ({avg_rel:.2f}) x "
                f"{corrob_desc} x Query relevance ({relevance:.2f}). No active contradictions. "
                "Epistemic assessment, not statistical probability."
            )

            cited_srcs = [
                f"{evidence_by_id[eid].metadata.source_id or eid}"
                for eid in supporting_ev_ids if eid in evidence_by_id
            ]

            concrete_values = [
                str(c.value) for c in supporting_claims
                if c.value is not None and str(c.value).strip()
            ]
            val_summary = f" Verified result: {', '.join(dict.fromkeys(concrete_values))}." if concrete_values else ""

            answer = (
                f"Answered: Verified evidence confirms the proposition in '{request.question}'.{val_summary} "
                f"Supported by: {', '.join(cited_srcs)}."
            )
            summary = (
                f"Conclusion reached with {confidence:.0%} confidence: Verified across {indep_count} independent source(s) "
                f"({', '.join(sorted(distinct_sources))}). No active contradictions detected."
            )
            return status, confidence, answer, summary, explanation

        # Both supporting and opposing present (without formal ConflictPair deadlock)
        status = ReasoningStatus.CONFLICTED
        confidence = 0.35
        explanation = "Confidence limited to 0.35 due to mutual factual tension between affirmative and negative statements."
        answer = (
            f"Conflicted evidence for '{request.question}': Opposing assertions exist between supporting items "
            f"({', '.join(sorted(supporting_ev_ids))}) and counter-items ({', '.join(sorted(opposing_ev_ids))})."
        )
        summary = "Evidence exhibits mutual factual tension between affirmative and negative statements."
        return status, confidence, answer, summary, explanation

    # -------------------------------------------------------------------------
    # Helpers & Security Defenses
    # -------------------------------------------------------------------------
    def _audit_prompt_injection(
        self,
        items: List[EvidenceItem],
        limitations: List[str],
        steps: List[str],
        audit_trail: Optional[List[str]] = None,
    ) -> None:
        """
        Safeguard against prompt injection inside document content.
        Ensures document instructions are strictly treated as inert data strings, not commands.
        """
        for item in items:
            for pattern in self.PROMPT_INJECTION_PATTERNS:
                if re.search(pattern, item.content, re.IGNORECASE):
                    limitations.append(
                        f"Security notice: Evidence item '{item.id}' contains suspicious directive pattern ('{pattern}'). "
                        "Content was parsed strictly as untrusted data; instruction overrides were ignored."
                    )
                    steps.append(
                        f"Security Defense: Neutralized potential prompt injection directive in item '{item.id}'."
                    )
                    if audit_trail is not None:
                        audit_trail.append(
                            f"Security Defense: Flagged potential prompt injection in evidence '{item.id}'; instruction overrides neutralized."
                        )
                    break

    def _format_epistemic_categories(
        self,
        request: ReasoningRequest,
        status: ReasoningStatus,
        unresolved_conflicts: List[ConflictPair],
        supporting_claims: List[Claim],
        opposing_claims: List[Claim],
        evidence_by_id: Dict[str, EvidenceItem],
        reliability_map: Dict[str, Any],
        q_meta: Dict[str, Any],
        conflicts: Optional[List[ConflictPair]] = None,
    ) -> Tuple[List[str], List[str], List[str]]:
        facts: List[str] = []
        inferences: List[str] = []
        unknowns: List[str] = []

        disputed_claim_ids = set()
        for conf in unresolved_conflicts:
            disputed_claim_ids.add(conf.claim_a_id)
            disputed_claim_ids.add(conf.claim_b_id)
        for opp in opposing_claims:
            disputed_claim_ids.add(opp.id)
        if conflicts:
            for conf in conflicts:
                if conf.is_resolved and conf.resolution_reason:
                    m = re.search(r"(?:in favor of Claim|Resolved:\s*Claim)\s+([A-Za-z0-9_-]+)", conf.resolution_reason)
                    if m:
                        winning_id = m.group(1)
                        losing_id = conf.claim_b_id if winning_id == conf.claim_a_id else conf.claim_a_id
                        disputed_claim_ids.add(losing_id)

        for claim in request.claims:
            if claim.id in disputed_claim_ids:
                label = ClaimStatus.DISPUTED.value
                facts.append(f"[{label}] {claim.statement} (Disputed by contradictory records; Citing: {', '.join(claim.evidence_ids) or 'Unlinked'})")
            elif not claim.evidence_ids:
                label = ClaimStatus.EXTRACTED_CLAIM.value
                facts.append(f"[{label}] {claim.statement} (Extracted assertion lacking linked evidence)")
            else:
                ev_items = [evidence_by_id[eid] for eid in claim.evidence_ids if eid in evidence_by_id]
                if not ev_items:
                    label = ClaimStatus.UNVERIFIED_CLAIM.value
                    facts.append(f"[{label}] {claim.statement} (Referenced evidence items missing from manifest)")
                else:
                    scores = [self._get_overall_score(reliability_map.get(eid)) for eid in claim.evidence_ids if eid in reliability_map]
                    avg_score = sum(scores) / len(scores) if scores else 0.0
                    if avg_score < request.min_reliability_threshold:
                        label = ClaimStatus.UNVERIFIED_CLAIM.value
                        facts.append(f"[{label}] {claim.statement} (Evidence reliability {avg_score:.2f} below threshold; Citing: {', '.join(claim.evidence_ids)})")
                    else:
                        distinct_sources = {
                            (ev.metadata.source_id or ev.id)
                            for ev in ev_items
                            if ev.metadata.source_id and ev.metadata.source_id != "UNKNOWN"
                        }
                        # ONLY assign "Verified Fact" when overall status is ANSWERED, corroborated, and NO active contradictions
                        if status == ReasoningStatus.ANSWERED and not unresolved_conflicts and (len(distinct_sources) >= 2 or avg_score >= 0.85):
                            label = ClaimStatus.VERIFIED_FACT.value
                            facts.append(f"[{label}] {claim.statement} (Verified by reliable records from {', '.join(distinct_sources) or 'Primary Source'})")
                        elif len(distinct_sources) >= 2:
                            label = ClaimStatus.CORROBORATED.value
                            facts.append(f"[{label}] {claim.statement} (Corroborated across {len(distinct_sources)} independent sources: {', '.join(distinct_sources)})")
                        else:
                            label = ClaimStatus.EVIDENCE_SUPPORTED.value
                            facts.append(f"[{label}] {claim.statement} (Supported by reliable evidence from '{list(distinct_sources)[0] if distinct_sources else 'Primary'}'; Citing: {', '.join(claim.evidence_ids)})")

        # Knowledge Graph edges
        for kg in request.kg_relationships:
            facts.append(f"[KG Relationship] ({kg.source_entity}) -[{kg.relation}]-> ({kg.target_entity}) [Confidence: {kg.confidence:.2f}]")

        if status == ReasoningStatus.ANSWERED:
            inferences.append(
                f"Factual convergence: Reliable evidence directly substantiates query proposition regarding '{q_meta['target_entity'] or 'entity'}'."
            )
        elif status == ReasoningStatus.PARTIALLY_ANSWERED:
            inferences.append("Partial inference: Contextual facts confirm general activity, but parameters lack granularity.")
            unknowns.append("Granular quantitative metrics or complete temporal logs remain unverified.")
        elif status == ReasoningStatus.CONFLICTED:
            inferences.append("Adjudication deadlock: Opposing sources possess non-dispositive or divergent authority.")
            unknowns.append("Definitive primary source adjudication needed to resolve conflicting records.")
        elif status == ReasoningStatus.INSUFFICIENT_EVIDENCE:
            unknowns.append("Factual grounding is missing for the core proposition in the user question.")

        return facts, inferences, unknowns

    @staticmethod
    def _get_overall_score(res: Optional[Union[ReliabilityBreakdown, EvidenceReliabilityResult]]) -> float:
        if res is None:
            return 1.0  # default permissive if unassessed
        if hasattr(res, "overall_score"):
            return getattr(res, "overall_score")
        if hasattr(res, "reliability_score"):
            return getattr(res, "reliability_score") / 100.0
        return 1.0
