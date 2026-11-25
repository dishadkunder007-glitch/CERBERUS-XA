"""
CERBERUS-X: AI Reasoning & Evidence Verification Module
Component 2: Conflict Analyzer

Analyzes claims and evidence for:
- Agreement
- Direct Contradiction
- Partial Contradiction
- Unresolved Conflict
- No Overlap

Evaluates timestamps, context, units of measurement, entity identity, and claim scopes.
Crucial Rule: Never force a resolution if the evidence cannot resolve it.
"""

from __future__ import annotations
import math
import re
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from dateutil import parser as date_parser

from .schemas import (
    Claim,
    ConflictPair,
    ConflictType,
    EvidenceItem,
    ReliabilityBreakdown,
    EvidenceReliabilityResult,
    ReliabilityRating,
)


class ConflictAnalyzer:
    """
    Robust deterministic conflict detection and resolution evaluator.
    Examines semantic polarity, entity binding, numerical & unit compatibility,
    temporal progressions, and scope boundaries.
    """

    # Common unit conversions to base SI or standard unit
    UNIT_CONVERSIONS = {
        # Distance (to meters)
        "km": ("m", 1000.0),
        "kilometer": ("m", 1000.0),
        "kilometers": ("m", 1000.0),
        "m": ("m", 1.0),
        "meter": ("m", 1.0),
        "meters": ("m", 1.0),
        "cm": ("m", 0.01),
        "mile": ("m", 1609.34),
        "miles": ("m", 1609.34),
        "ft": ("m", 0.3048),
        "feet": ("m", 0.3048),
        # Mass (to grams)
        "kg": ("g", 1000.0),
        "kilogram": ("g", 1000.0),
        "g": ("g", 1.0),
        "gram": ("g", 1.0),
        "lb": ("g", 453.592),
        "lbs": ("g", 453.592),
        # Multipliers
        "k": ("1", 1000.0),
        "thousand": ("1", 1000.0),
        "m_mult": ("1", 1000000.0),
        "million": ("1", 1000000.0),
        "b": ("1", 1000000000.0),
        "billion": ("1", 1000000000.0),
    }

    def analyze_claims(
        self,
        claims: List[Claim],
        evidence_items: Optional[List[EvidenceItem]] = None,
        reliability_map: Optional[Dict[str, Union[ReliabilityBreakdown, EvidenceReliabilityResult]]] = None,
    ) -> List[ConflictPair]:
        """Pairwise conflict evaluation across all claims."""
        conflicts: List[ConflictPair] = []
        n = len(claims)
        if n < 2:
            return conflicts

        ev_map = {ev.id: ev for ev in (evidence_items or [])}

        for i in range(n):
            for j in range(i + 1, n):
                claim_a = claims[i]
                claim_b = claims[j]

                result = self._evaluate_claim_pair(claim_a, claim_b, ev_map, reliability_map or {})
                if result and result.conflict_type != ConflictType.NO_OVERLAP:
                    conflicts.append(result)

        return conflicts

    def _evaluate_claim_pair(
        self,
        claim_a: Claim,
        claim_b: Claim,
        ev_map: Dict[str, EvidenceItem],
        reliability_map: Dict[str, Union[ReliabilityBreakdown, EvidenceReliabilityResult]],
    ) -> Optional[ConflictPair]:
        # 1. Check entity identity overlap
        entities_overlap = self._check_entity_overlap(claim_a, claim_b)
        properties_overlap = self._check_property_overlap(claim_a, claim_b)

        # If entities are completely different and not mentioned in statements, skip
        if not entities_overlap and not self._check_textual_subject_overlap(claim_a.statement, claim_b.statement):
            return ConflictPair(
                claim_a_id=claim_a.id,
                claim_b_id=claim_b.id,
                conflict_type=ConflictType.NO_OVERLAP,
                description="Claims refer to different entities or unrelated subjects.",
            )

        # 2. Check Temporal Differentiation
        time_differs, temporal_msg = self._evaluate_temporal_context(claim_a, claim_b)

        # 3. Check Scope Differentiation (e.g. Geographic or Domain)
        scope_differs, scope_msg = self._evaluate_scope_context(claim_a, claim_b)

        # 4. Check Quantitative / Unit Divergence
        is_num, units_match, values_compatible, unit_msg = self._evaluate_quantitative_context(claim_a, claim_b)

        # 5. Check Polarity (affirmation vs negation)
        polarity_conflict = (claim_a.polarity != claim_b.polarity)

        # Case A: Polarities contradict on the same property/subject
        if polarity_conflict and (properties_overlap or self._check_statement_contradiction(claim_a.statement, claim_b.statement)):
            if time_differs:
                # E.g. was true in 2020, but not true in 2024
                return ConflictPair(
                    claim_a_id=claim_a.id,
                    claim_b_id=claim_b.id,
                    conflict_type=ConflictType.PARTIAL_CONTRADICTION,
                    description=f"Apparent polarity inversion explained by temporal progression: {temporal_msg}",
                    conflicting_attributes=["polarity", "timestamp"],
                    temporal_resolution=temporal_msg,
                    is_resolved=True,
                    resolution_reason="Resolved via temporal transition (state changed over time).",
                )
            elif scope_differs:
                return ConflictPair(
                    claim_a_id=claim_a.id,
                    claim_b_id=claim_b.id,
                    conflict_type=ConflictType.PARTIAL_CONTRADICTION,
                    description=f"Polarity difference bounded by distinct scopes: {scope_msg}",
                    conflicting_attributes=["polarity", "scope"],
                    scope_resolution=scope_msg,
                    is_resolved=True,
                    resolution_reason="Resolved via domain/scope boundary differentiation.",
                )
            else:
                # Direct irreconcilable contradiction
                res_attempt, is_res, res_reason = self._attempt_evidence_weight_resolution(
                    claim_a, claim_b, reliability_map
                )
                return ConflictPair(
                    claim_a_id=claim_a.id,
                    claim_b_id=claim_b.id,
                    conflict_type=ConflictType.UNRESOLVED_CONFLICT if not is_res else ConflictType.CONTRADICTION,
                    description=f"Direct polarity contradiction on same subject: Claim {claim_a.id} asserts positive whereas Claim {claim_b.id} asserts negative.",
                    conflicting_attributes=["polarity", "statement"],
                    is_resolved=is_res,
                    resolution_reason=res_reason,
                )

        # Case B: Quantitative comparison
        if is_num:
            if values_compatible:
                return ConflictPair(
                    claim_a_id=claim_a.id,
                    claim_b_id=claim_b.id,
                    conflict_type=ConflictType.AGREEMENT,
                    description=f"Quantitative values agree ({unit_msg}).",
                    unit_resolution=unit_msg,
                    is_resolved=True,
                    resolution_reason="Values match when converted to standardized units.",
                )
            else:
                # If numerical values differ, ensure they actually refer to the same property
                if not properties_overlap and claim_a.property and claim_b.property:
                    # Distinct properties (e.g. payload_capacity vs ballast_mounting, or wingspan vs height)
                    return ConflictPair(
                        claim_a_id=claim_a.id,
                        claim_b_id=claim_b.id,
                        conflict_type=ConflictType.NO_OVERLAP,
                        description=f"Claims describe distinct quantitative properties: '{claim_a.property}' vs '{claim_b.property}'.",
                    )

                # Quantitative values genuinely disagree on the same property
                if time_differs:
                    return ConflictPair(
                        claim_a_id=claim_a.id,
                        claim_b_id=claim_b.id,
                        conflict_type=ConflictType.PARTIAL_CONTRADICTION,
                        description=f"Numerical values differ across different time periods: {temporal_msg}.",
                        conflicting_attributes=["value", "timestamp"],
                        temporal_resolution=temporal_msg,
                        is_resolved=True,
                        resolution_reason="Different reporting periods account for value variation.",
                    )
                elif scope_differs:
                    return ConflictPair(
                        claim_a_id=claim_a.id,
                        claim_b_id=claim_b.id,
                        conflict_type=ConflictType.PARTIAL_CONTRADICTION,
                        description=f"Numerical values differ across distinct scopes: {scope_msg}.",
                        conflicting_attributes=["value", "scope"],
                        scope_resolution=scope_msg,
                        is_resolved=True,
                        resolution_reason="Different observational scopes account for numerical variance.",
                    )
                else:
                    # Same entity, property, time, and scope, but truly different numbers
                    res_attempt, is_res, res_reason = self._attempt_evidence_weight_resolution(
                        claim_a, claim_b, reliability_map
                    )
                    return ConflictPair(
                        claim_a_id=claim_a.id,
                        claim_b_id=claim_b.id,
                        conflict_type=ConflictType.UNRESOLVED_CONFLICT if not is_res else ConflictType.CONTRADICTION,
                        description=f"Numerical discrepancy for property '{claim_a.property or 'value'}': {claim_a.value} {claim_a.unit or ''} vs {claim_b.value} {claim_b.unit or ''}.",
                        conflicting_attributes=["value", "unit"],
                        unit_resolution=unit_msg,
                        is_resolved=is_res,
                        resolution_reason=res_reason,
                    )

        # Case C: Qualitative / Value mismatch
        if properties_overlap and claim_a.value is not None and claim_b.value is not None:
            if str(claim_a.value).strip().lower() == str(claim_b.value).strip().lower():
                return ConflictPair(
                    claim_a_id=claim_a.id,
                    claim_b_id=claim_b.id,
                    conflict_type=ConflictType.AGREEMENT,
                    description=f"Claims agree on property '{claim_a.property}' with value '{claim_a.value}'.",
                    is_resolved=True,
                    resolution_reason="Identical asserted property values.",
                )
            else:
                if time_differs:
                    return ConflictPair(
                        claim_a_id=claim_a.id,
                        claim_b_id=claim_b.id,
                        conflict_type=ConflictType.PARTIAL_CONTRADICTION,
                        description=f"Differing property values across time periods: {temporal_msg}",
                        temporal_resolution=temporal_msg,
                        is_resolved=True,
                        resolution_reason="Values represent different temporal snapshots.",
                    )
                res_attempt, is_res, res_reason = self._attempt_evidence_weight_resolution(
                    claim_a, claim_b, reliability_map
                )
                return ConflictPair(
                    claim_a_id=claim_a.id,
                    claim_b_id=claim_b.id,
                    conflict_type=ConflictType.UNRESOLVED_CONFLICT if not is_res else ConflictType.CONTRADICTION,
                    description=f"Conflicting value for property '{claim_a.property}': '{claim_a.value}' vs '{claim_b.value}'.",
                    conflicting_attributes=["property", "value"],
                    is_resolved=is_res,
                    resolution_reason=res_reason,
                )

        # Case D: Textual statement direct semantic contradiction check
        if self._check_statement_contradiction(claim_a.statement, claim_b.statement):
            res_attempt, is_res, res_reason = self._attempt_evidence_weight_resolution(
                claim_a, claim_b, reliability_map
            )
            return ConflictPair(
                claim_a_id=claim_a.id,
                claim_b_id=claim_b.id,
                conflict_type=ConflictType.UNRESOLVED_CONFLICT if not is_res else ConflictType.CONTRADICTION,
                description="Statements express mutually exclusive factual assertions.",
                conflicting_attributes=["statement"],
                is_resolved=is_res,
                resolution_reason=res_reason,
            )

        # Default fallback: Agreement if high textual similarity, else No Overlap
        if self._compute_text_similarity(claim_a.statement, claim_b.statement) > 0.65:
            return ConflictPair(
                claim_a_id=claim_a.id,
                claim_b_id=claim_b.id,
                conflict_type=ConflictType.AGREEMENT,
                description="Statements affirm substantively corroborating facts.",
                is_resolved=True,
                resolution_reason="High semantic and factual alignment.",
            )

        return ConflictPair(
            claim_a_id=claim_a.id,
            claim_b_id=claim_b.id,
            conflict_type=ConflictType.NO_OVERLAP,
            description="No substantial factual overlap or divergence detected.",
        )

    def _check_entity_overlap(self, a: Claim, b: Claim) -> bool:
        if a.entity and b.entity:
            ea = a.entity.strip().lower()
            eb = b.entity.strip().lower()
            return ea == eb or ea in eb or eb in ea
        return False

    def _check_property_overlap(self, a: Claim, b: Claim) -> bool:
        if a.property and b.property:
            pa = a.property.strip().lower()
            pb = b.property.strip().lower()
            return pa == pb or pa in pb or pb in pa
        return False

    def _check_textual_subject_overlap(self, text_a: str, text_b: str) -> bool:
        words_a = {w.lower() for w in re.findall(r"\b[A-Za-z0-9_-]{3,}\b", text_a)}
        words_b = {w.lower() for w in re.findall(r"\b[A-Za-z0-9_-]{3,}\b", text_b)}
        stopwords = {"the", "and", "for", "with", "that", "this", "from", "were", "been", "have", "said", "reported"}
        meaningful_a = words_a - stopwords
        meaningful_b = words_b - stopwords
        overlap = meaningful_a.intersection(meaningful_b)
        return len(overlap) >= 2

    def _evaluate_temporal_context(self, a: Claim, b: Claim) -> Tuple[bool, Optional[str]]:
        # Compare time_period string first
        if a.time_period and b.time_period and a.time_period.strip().lower() != b.time_period.strip().lower():
            return True, f"Claim A period '{a.time_period}' vs Claim B period '{b.time_period}'"

        # Compare timestamps
        t_a = self._parse_date(a.timestamp)
        t_b = self._parse_date(b.timestamp)
        if t_a and t_b:
            diff_seconds = abs((t_a - t_b).total_seconds())
            if diff_seconds > 86400:  # More than 1 day difference
                return True, f"Claim A date '{t_a.date()}' vs Claim B date '{t_b.date()}'"

        return False, None

    def _evaluate_scope_context(self, a: Claim, b: Claim) -> Tuple[bool, Optional[str]]:
        if a.scope and b.scope:
            if a.scope.strip().lower() != b.scope.strip().lower():
                return True, f"Claim A scope '{a.scope}' vs Claim B scope '{b.scope}'"
        elif (a.scope and not b.scope) or (b.scope and not a.scope):
            scope_present = a.scope if a.scope else b.scope
            unscoped_id = b.id if a.scope else a.id
            return True, f"Claim has regional/domain scope '{scope_present}' whereas Claim {unscoped_id} is global/unbounded"
        return False, None

    def _extract_unit(self, claim: Claim) -> str:
        if claim.unit and claim.unit.strip():
            return self._normalize_unit_str(claim.unit)
        if claim.value is not None:
            m = re.search(r"[-+]?\d*\.?\d+\s*([a-zA-Z/%$€£]+)", str(claim.value))
            if m:
                return self._normalize_unit_str(m.group(1))
        if claim.statement:
            m = re.search(r"[-+]?\d*\.?\d+\s*([a-zA-Z/%$€£]+)", claim.statement)
            if m:
                return self._normalize_unit_str(m.group(1))
        return ""

    @staticmethod
    def _normalize_unit_str(unit_str: str) -> str:
        u = unit_str.strip().lower().rstrip(".,")
        # Common plurals and abbreviations
        if u in ("kilograms", "kilogram", "kgs"):
            return "kg"
        if u in ("grams", "gram"):
            return "g"
        if u in ("kilometers", "kilometer", "kms"):
            return "km"
        if u in ("meters", "meter"):
            return "m"
        if u in ("centimeters", "centimeter"):
            return "cm"
        if u in ("seconds", "second", "sec"):
            return "s"
        if u in ("hours", "hour", "hrs", "hr"):
            return "h"
        if u in ("percent", "percentage"):
            return "%"
        return u

    def _evaluate_quantitative_context(self, a: Claim, b: Claim) -> Tuple[bool, bool, bool, str]:
        num_a = self._extract_number(a.value)
        num_b = self._extract_number(b.value)

        if num_a is None or num_b is None:
            return False, False, False, "Non-quantitative values"

        unit_a = self._extract_unit(a)
        unit_b = self._extract_unit(b)

        # Tolerance check with relative + absolute tolerance
        rel_tol = 1e-4
        abs_tol = 1e-4

        # Case 1: Same unit or both empty
        if unit_a == unit_b:
            match = math.isclose(num_a, num_b, rel_tol=rel_tol, abs_tol=abs_tol)
            return True, True, match, f"Units identical ('{unit_a or 'scalar'}'): {num_a} vs {num_b}"

        # Case 2: One unit is empty/unspecified, but scalar numbers are identical
        if not unit_a or not unit_b:
            match = math.isclose(num_a, num_b, rel_tol=rel_tol, abs_tol=abs_tol)
            specified_unit = unit_a or unit_b
            return True, True, match, f"Scalar numerical comparison (unit: '{specified_unit}'): {num_a} vs {num_b}"

        # Case 3: Convert unit A and B if known
        norm_a, factor_a = self.UNIT_CONVERSIONS.get(unit_a, (unit_a, 1.0))
        norm_b, factor_b = self.UNIT_CONVERSIONS.get(unit_b, (unit_b, 1.0))

        if norm_a == norm_b and norm_a:
            std_val_a = num_a * factor_a
            std_val_b = num_b * factor_b
            match = math.isclose(std_val_a, std_val_b, rel_tol=1e-3, abs_tol=1e-3)
            return True, True, match, f"Converted to standard {norm_a}: {std_val_a:.4g} vs {std_val_b:.4g}"

        # Case 4: Distinct incompatible units
        return True, False, False, f"Incompatible units '{unit_a}' vs '{unit_b}'"

    # =========================================================================
    # Preponderance Resolution Constants & Threshold Rationale
    # =========================================================================
    # 1. PREPONDERANCE_HIGH_THRESHOLD: Winning evidence must meet or exceed 0.70
    #    to be treated as an authoritative, verified source capable of overriding a conflict.
    # 2. PREPONDERANCE_LOW_THRESHOLD: Losing evidence must not exceed 0.50
    #    (representing unverified, unsigned, or low-reliability assertions).
    # 3. PREPONDERANCE_MIN_SCORE_GAP: A decisive gap of at least 0.25 between the two
    #    average reliability scores is required. This prevents razor-thin boundary victories
    #    (e.g., 0.70 vs 0.50 only has a 0.20 gap, which is too close to break a factual deadlock).
    PREPONDERANCE_HIGH_THRESHOLD: float = 0.70
    PREPONDERANCE_LOW_THRESHOLD: float = 0.50
    PREPONDERANCE_MIN_SCORE_GAP: float = 0.25

    def _attempt_evidence_weight_resolution(
        self,
        a: Claim,
        b: Claim,
        reliability_map: Dict[str, Union[ReliabilityBreakdown, EvidenceReliabilityResult]],
    ) -> Tuple[str, bool, str]:
        """
        Evaluates whether evidence reliability conclusively breaks the deadlock.
        Rule: Never force a resolution if the evidence cannot resolve it.
        Requires high authority (>= 0.70), low/unreliable counter-evidence (<= 0.50),
        and a minimum score margin of at least 0.25. Otherwise preserves UNRESOLVED_CONFLICT.
        """
        if not a.evidence_ids or not b.evidence_ids or not reliability_map:
            return "No resolution", False, "Evidence metadata insufficient to resolve conflict definitively."

        scores_a = [reliability_map[eid].overall_score for eid in a.evidence_ids if eid in reliability_map]
        scores_b = [reliability_map[eid].overall_score for eid in b.evidence_ids if eid in reliability_map]

        if not scores_a or not scores_b:
            return "No resolution", False, "Reliability data missing for one or both claim evidence sets."

        avg_a = sum(scores_a) / len(scores_a)
        avg_b = sum(scores_b) / len(scores_b)
        score_gap = abs(avg_a - avg_b)

        # Strict criteria: high authority, low opposition, and minimum gap
        if (
            avg_a >= self.PREPONDERANCE_HIGH_THRESHOLD
            and avg_b <= self.PREPONDERANCE_LOW_THRESHOLD
            and score_gap >= self.PREPONDERANCE_MIN_SCORE_GAP
        ):
            return (
                f"Resolved in favor of Claim {a.id}",
                True,
                f"Resolved: Claim {a.id} supported by High-reliability evidence (score {avg_a:.2f}) vs Low-reliability/Unsigned Claim {b.id} (score {avg_b:.2f}, gap {score_gap:.2f} >= {self.PREPONDERANCE_MIN_SCORE_GAP}).",
            )
        elif (
            avg_b >= self.PREPONDERANCE_HIGH_THRESHOLD
            and avg_a <= self.PREPONDERANCE_LOW_THRESHOLD
            and score_gap >= self.PREPONDERANCE_MIN_SCORE_GAP
        ):
            return (
                f"Resolved in favor of Claim {b.id}",
                True,
                f"Resolved: Claim {b.id} supported by High-reliability evidence (score {avg_b:.2f}) vs Low-reliability/Unsigned Claim {a.id} (score {avg_a:.2f}, gap {score_gap:.2f} >= {self.PREPONDERANCE_MIN_SCORE_GAP}).",
            )
        else:
            return (
                "Unresolved conflict",
                False,
                f"Cannot force resolution: Both sources possess comparable or non-dispositive reliability (Claim A: {avg_a:.2f}, Claim B: {avg_b:.2f}, gap: {score_gap:.2f} < {self.PREPONDERANCE_MIN_SCORE_GAP} or threshold unmet).",
            )

    def _check_statement_contradiction(self, s1: str, s2: str) -> bool:
        t1 = s1.lower()
        t2 = s2.lower()
        neg_patterns = [
            (r"\bwas\b", r"\bwas not\b"),
            (r"\bis\b", r"\bis not\b"),
            (r"\bdid\b", r"\bdid not\b"),
            (r"\bhas\b", r"\bhas not\b"),
            (r"\bactive\b", r"\binactive\b"),
            (r"\bapproved\b", r"\brejected\b"),
            (r"\btrue\b", r"\bfalse\b"),
            (r"\bvalid\b", r"\binvalid\b"),
            (r"\bconfirmed\b", r"\bdenied\b"),
        ]
        for pos, neg in neg_patterns:
            if (re.search(pos, t1) and re.search(neg, t2)) or (re.search(pos, t2) and re.search(neg, t1)):
                return True
        return False

    def _compute_text_similarity(self, s1: str, s2: str) -> float:
        w1 = set(re.findall(r"\b\w{3,}\b", s1.lower()))
        w2 = set(re.findall(r"\b\w{3,}\b", s2.lower()))
        if not w1 or not w2:
            return 0.0
        return len(w1.intersection(w2)) / max(len(w1), len(w2))

    @staticmethod
    def _extract_number(val: Any) -> Optional[float]:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        try:
            s = str(val).replace(",", "").strip()
            match = re.search(r"[-+]?\d*\.?\d+", s)
            if match:
                return float(match.group(0))
        except Exception:
            pass
        return None

    @staticmethod
    def _parse_date(date_val: Optional[Union[datetime, str]]) -> Optional[datetime]:
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val
        try:
            return date_parser.parse(str(date_val))
        except Exception:
            return None
