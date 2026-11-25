"""
Contradiction Detection Engine.

Compares claims across documents and identifies genuine contradictions,
distinguishing them from rounding differences, unit dimensions, and missing data.

Supports:
- Dimension-based numerical comparisons (e.g. 5 kg == 5,000 g, ₹25 lakh == INR 25,00,000)
- Textual contradiction detection (status, compliance, executive, sentiment/polarity)
- Modality-aware partitioning (actual vs target vs estimate)
- Zero winner bias: preserves all conflicting claims with complete source references
- Exact temporal interval overlap checks
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from .claim_builder import Claim
from .normalizer import dates_overlap

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result structures
# ---------------------------------------------------------------------------

@dataclass
class ContradictionResult:
    """Represents a detected contradiction or consistency evaluation between claims."""
    contradiction_id: str
    entity: str
    entity_normalized: str
    attribute: str
    status: str            # "CONTRADICTION", "CONSISTENT", "UNCERTAIN"
    conflicting_claims: list[Claim]
    explanation: str
    confidence: float      # 0.0 – 1.0
    numerical_range: Optional[tuple[float, float]] = None
    tolerance_used: float = 0.0
    contradiction_type: str = "numerical"  # numerical, textual, modality, temporal
    verdict: str = "contradiction"         # contradiction, consistent, uncertain, insufficient_evidence
    confidence_breakdown: dict[str, float] = field(default_factory=dict)
    confidence_explanation: str = ""


@dataclass
class DetectionReport:
    total_claims: int
    contradictions: list[ContradictionResult]
    consistent_groups: list[list[Claim]]
    uncertain_groups: list[list[Claim]]

    @property
    def contradiction_count(self) -> int:
        return len(self.contradictions)

    @property
    def consistent_count(self) -> int:
        return sum(len(g) for g in self.consistent_groups)

    @property
    def uncertain_count(self) -> int:
        return sum(len(g) for g in self.uncertain_groups)


# Opposing semantic pairs for textual contradiction detection
ANTONYM_PAIRS = [
    ({"operational", "active", "running", "in operation", "open", "functional", "online"},
     {"shutdown", "shut down", "suspended", "bankrupt", "in liquidation", "under liquidation", "dormant", "closed", "inactive", "offline"}),
    ({"compliant", "approved", "certified", "passed", "in compliance", "satisfactory", "licensed"},
     {"non-compliant", "failed", "revoked", "rejected", "unsatisfactory", "violation", "unlicensed", "breached"}),
    ({"yes", "true", "confirmed", "verified", "accurate", "valid"},
     {"no", "false", "denied", "unverified", "disputed", "inaccurate", "invalid"}),
    ({"increase", "growth", "profit", "gain", "surplus", "positive"},
     {"decrease", "decline", "loss", "deficit", "shortfall", "negative"}),
    ({"solvent", "financially stable", "profitable", "viable"},
     {"insolvent", "bankrupt", "unprofitable", "unviable", "in default"}),
]


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

class ContradictionDetector:
    """
    Deterministic contradiction detection engine.

    Rules:
    - Same entity_normalized + same attribute + overlapping date interval -> comparable group.
    - Groups are partitioned by modality (actual vs target vs estimate).
    - Numerical claims are compared in their normalized canonical dimension base units.
    - Differences within tolerance_pct are marked CONSISTENT (accounting for rounding).
    - Differences exceeding tolerance_pct are flagged as CONTRADICTION.
    - Textual claims use semantic opposition and name disambiguation.
    - Preserves all conflicting statements without picking arbitrary winners.
    """

    def __init__(
        self,
        numerical_tolerance_pct: float = 2.0,
        text_similarity_threshold: float = 0.6,
        ocr_confidence_threshold: float = 0.6,
    ):
        self.numerical_tolerance_pct = numerical_tolerance_pct
        self.text_similarity_threshold = text_similarity_threshold
        self.ocr_confidence_threshold = ocr_confidence_threshold
        self.source_reliabilities: dict[str, float] = {}
        self._counter = 0

    def set_source_reliability(self, source_id: str, score: float) -> None:
        """Register a source reliability score (0.0 to 1.0) for a given source filename."""
        self.source_reliabilities[source_id] = max(0.0, min(1.0, float(score)))

    @staticmethod
    def _canonical_attribute(attr: str) -> str:
        """Map synonyms and sub-roles to canonical comparison attributes."""
        a = attr.lower().strip()
        if a in ("ceo", "executive", "chief executive officer", "managing director", "chief executive", "leadership"):
            return "executive"
        if a in ("compliance", "compliance rating", "compliance status", "audit outcome", "certification"):
            return "compliance"
        if a in ("status", "operational status", "condition", "operation"):
            return "status"
        if a in ("production", "production output", "output"):
            return "production"
        if a in ("revenue", "declared revenue", "gross revenue", "sales", "turnover"):
            return "revenue"
        return a

    def _compute_confidence_and_breakdown(
        self,
        claims: list[Claim],
        divergence_score: float = 1.0,
    ) -> tuple[float, dict[str, float], str]:
        """Evidence-based contradiction confidence and breakdown."""
        ocr_scores = [getattr(c, "ocr_confidence", 1.0) for c in claims]
        extract_scores = [getattr(c, "confidence", 1.0) for c in claims]
        extraction = min(ocr_scores) * min(extract_scores)

        entity_scores = [1.0 if c.entity == c.entity_normalized else 0.95 for c in claims]
        entity_match = sum(entity_scores) / len(entity_scores) if entity_scores else 1.0

        dates = {c.date_normalized for c in claims if c.date_normalized}
        period_match = 1.0 if len(dates) <= 1 else 0.85

        units = {c.unit_normalized for c in claims if c.unit_normalized}
        dims = {c.dimension for c in claims if c.dimension}
        if len(units) <= 1:
            unit_norm = 1.0
        elif len(dims) <= 1:
            unit_norm = 0.90
        else:
            unit_norm = 0.50

        source_rel_scores = [self.source_reliabilities.get(c.source, 1.0) for c in claims]
        source_reliability = sum(source_rel_scores) / len(source_rel_scores) if source_rel_scores else 1.0

        total_confidence = round(
            0.25 * extraction +
            0.20 * entity_match +
            0.20 * period_match +
            0.15 * unit_norm +
            0.10 * source_reliability +
            0.10 * divergence_score,
            3
        )
        total_confidence = max(0.10, min(0.99, total_confidence))

        breakdown = {
            "extraction": round(extraction, 3),
            "entity_match": round(entity_match, 3),
            "period_match": round(period_match, 3),
            "unit_normalization": round(unit_norm, 3),
            "source_reliability": round(source_reliability, 3),
            "value_divergence": round(divergence_score, 3),
        }
        explanation = (
            f"Confidence: {total_confidence:.2f} (Extraction: {extraction:.2f}, "
            f"Entity: {entity_match:.2f}, Period: {period_match:.2f}, "
            f"Units: {unit_norm:.2f}, Source Reliability: {source_reliability:.2f}, "
            f"Divergence: {divergence_score:.2f})"
        )
        return total_confidence, breakdown, explanation

    def detect(self, claims: list[Claim]) -> DetectionReport:
        """Run contradiction detection on a list of claims."""
        if not claims:
            return DetectionReport(
                total_claims=0,
                contradictions=[],
                consistent_groups=[],
                uncertain_groups=[],
            )

        # Group claims by (entity_normalized, canonical_attribute)
        groups: dict[tuple[str, str], list[Claim]] = {}
        for claim in claims:
            key = (claim.entity_normalized.lower(), self._canonical_attribute(claim.attribute))
            groups.setdefault(key, []).append(claim)

        contradictions: list[ContradictionResult] = []
        consistent_groups: list[list[Claim]] = []
        uncertain_groups: list[list[Claim]] = []

        for (entity, attribute), group in groups.items():
            # Only compare if there are claims from different sources
            multi_source = len({c.source for c in group}) > 1
            if not multi_source:
                uncertain_groups.append(group)
                continue

            # Split by overlapping date intervals
            date_subgroups = self._split_by_date(group)

            for subgroup in date_subgroups:
                if len(subgroup) < 2:
                    continue

                # Partition by modality (actual vs target vs estimate)
                modality_partitions = self._partition_by_modality(subgroup)

                for part in modality_partitions:
                    if len(part) < 2:
                        continue

                    multi_src = len({c.source for c in part}) > 1
                    if not multi_src:
                        uncertain_groups.append(part)
                        continue

                    result = self._compare_group(part)
                    if result.status == "CONTRADICTION":
                        contradictions.append(result)
                    elif result.status == "CONSISTENT":
                        consistent_groups.append(part)
                    else:
                        uncertain_groups.append(part)

        logger.info(
            "Detection complete: %d contradictions, %d consistent groups, %d uncertain",
            len(contradictions),
            len(consistent_groups),
            len(uncertain_groups),
        )

        return DetectionReport(
            total_claims=len(claims),
            contradictions=contradictions,
            consistent_groups=consistent_groups,
            uncertain_groups=uncertain_groups,
        )

    def _split_by_date(self, claims: list[Claim]) -> list[list[Claim]]:
        """Group claims by overlapping date intervals."""
        dated = [c for c in claims if c.date_normalized]
        undated = [c for c in claims if not c.date_normalized]

        if not dated:
            return [claims]

        date_groups: list[list[Claim]] = []
        for claim in dated:
            placed = False
            for grp in date_groups:
                if any(dates_overlap(claim.date_normalized, g.date_normalized) for g in grp):
                    grp.append(claim)
                    placed = True
                    break
            if not placed:
                date_groups.append([claim])

        # Add undated claims to all groups (conservative approach)
        for grp in date_groups:
            grp.extend(undated)

        return date_groups if date_groups else [undated]

    def _partition_by_modality(self, claims: list[Claim]) -> list[list[Claim]]:
        """Separate actual values from targets and estimates."""
        by_mod: dict[str, list[Claim]] = {}
        for c in claims:
            by_mod.setdefault(c.modality, []).append(c)

        partitions = []
        for mod, mclaims in by_mod.items():
            if len(mclaims) >= 2 and len({c.source for c in mclaims}) > 1:
                partitions.append(mclaims)
        return partitions if partitions else [claims]

    def _compare_group(self, claims: list[Claim]) -> ContradictionResult:
        """Compare a group of same-entity, same-attribute, same-date claims."""
        self._counter += 1
        cid = f"CONTR-{self._counter:04d}"

        entity = claims[0].entity_normalized
        attribute = claims[0].attribute

        # Separate numeric and textual claims
        numeric_claims = [c for c in claims if c.value_normalized is not None and c.comparable]
        text_claims = [c for c in claims if c.value_normalized is None or isinstance(c.value, str)]

        if len(numeric_claims) >= 2:
            return self._compare_numeric(cid, entity, attribute, numeric_claims)
        elif len(text_claims) >= 2:
            return self._compare_text(cid, entity, attribute, text_claims)
        else:
            return ContradictionResult(
                contradiction_id=cid,
                entity=entity,
                entity_normalized=entity,
                attribute=attribute,
                status="UNCERTAIN",
                conflicting_claims=claims,
                explanation="Claims could not be compared (mixed text and numeric values).",
                confidence=0.3,
            )

    def _compare_numeric(
        self,
        cid: str,
        entity: str,
        attribute: str,
        numeric_claims: list[Claim],
    ) -> ContradictionResult:
        """
        Compare numeric claim values using dimensionally normalized base units.
        (e.g. 5 kg and 5000 g both have unit_normalized='g' and value_normalized=5000.0).
        """
        # Check dimensional compatibility
        dim_set = {c.dimension for c in numeric_claims if c.dimension}
        unit_set = {c.unit_normalized for c in numeric_claims if c.unit_normalized}

        if len(unit_set) > 1 and len(dim_set) > 1:
            explanation = (
                f"Claims use incompatible dimensions ({', '.join(dim_set)}: {', '.join(unit_set)}). "
                "Cannot compare without cross-dimensional conversion."
            )
            return ContradictionResult(
                contradiction_id=cid,
                entity=entity,
                entity_normalized=entity,
                attribute=attribute,
                status="UNCERTAIN",
                conflicting_claims=numeric_claims,
                explanation=explanation,
                confidence=0.4,
                contradiction_type="numerical",
            )

        values = [c.value_normalized for c in numeric_claims]
        min_val = min(values)
        max_val = max(values)

        if min_val == 0 and max_val == 0:
            conf, breakdown, conf_exp = self._compute_confidence_and_breakdown(numeric_claims, divergence_score=0.1)
            return ContradictionResult(
                contradiction_id=cid,
                entity=entity,
                entity_normalized=entity,
                attribute=attribute,
                status="CONSISTENT",
                conflicting_claims=numeric_claims,
                explanation="All sources report the same value (0).",
                confidence=1.0,
                numerical_range=(0.0, 0.0),
                contradiction_type="numerical",
                verdict="consistent",
                confidence_breakdown=breakdown,
                confidence_explanation=conf_exp,
            )

        # Percentage difference from mean
        mean_val = sum(values) / len(values)
        pct_diff = ((max_val - min_val) / abs(mean_val) * 100) if mean_val != 0 else 0.0

        if pct_diff <= self.numerical_tolerance_pct:
            explanation = (
                f"All sources report consistent values for '{attribute}' "
                f"(range: {min_val:,.2f} – {max_val:,.2f} {numeric_claims[0].unit_normalized}, "
                f"difference: {pct_diff:.2f}% ≤ tolerance {self.numerical_tolerance_pct}%)."
            )
            conf, breakdown, conf_exp = self._compute_confidence_and_breakdown(numeric_claims, divergence_score=0.1)
            return ContradictionResult(
                contradiction_id=cid,
                entity=entity,
                entity_normalized=entity,
                attribute=attribute,
                status="CONSISTENT",
                conflicting_claims=numeric_claims,
                explanation=explanation,
                confidence=0.98,
                numerical_range=(min_val, max_val),
                tolerance_used=self.numerical_tolerance_pct,
                contradiction_type="numerical",
                verdict="consistent",
                confidence_breakdown=breakdown,
                confidence_explanation=conf_exp,
            )
        else:
            # Check OCR confidence threshold: if any claim has low OCR confidence, mark as UNCERTAIN
            min_ocr = min(getattr(c, "ocr_confidence", 1.0) for c in numeric_claims)
            if min_ocr < self.ocr_confidence_threshold:
                conf, breakdown, conf_exp = self._compute_confidence_and_breakdown(numeric_claims, divergence_score=0.4)
                return ContradictionResult(
                    contradiction_id=cid,
                    entity=entity,
                    entity_normalized=entity,
                    attribute=attribute,
                    status="UNCERTAIN",
                    conflicting_claims=numeric_claims,
                    explanation=f"Potential discrepancy flagged as UNCERTAIN due to low OCR confidence ({min_ocr:.2f} < threshold {self.ocr_confidence_threshold}).",
                    confidence=conf,
                    numerical_range=(min_val, max_val),
                    tolerance_used=self.numerical_tolerance_pct,
                    contradiction_type="numerical",
                    verdict="uncertain",
                    confidence_breakdown=breakdown,
                    confidence_explanation=conf_exp,
                )

            sources_str = "; ".join(
                f"{c.source} ({c.page_or_sheet}): {c.value} {c.unit}"
                for c in numeric_claims
            )
            explanation = (
                f"CONTRADICTION DETECTED for '{entity}' – '{attribute}'. "
                f"Values differ by {pct_diff:.1f}% across sources. "
                f"Sources: {sources_str}. "
                f"No single value is assumed correct. All {len(numeric_claims)} values preserved."
            )
            divergence = min(1.0, max(0.5, pct_diff / 50.0))
            conf, breakdown, conf_exp = self._compute_confidence_and_breakdown(numeric_claims, divergence_score=divergence)
            return ContradictionResult(
                contradiction_id=cid,
                entity=entity,
                entity_normalized=entity,
                attribute=attribute,
                status="CONTRADICTION",
                conflicting_claims=numeric_claims,
                explanation=explanation,
                confidence=round(conf, 3),
                numerical_range=(min_val, max_val),
                tolerance_used=self.numerical_tolerance_pct,
                contradiction_type="numerical",
                verdict="contradiction",
                confidence_breakdown=breakdown,
                confidence_explanation=conf_exp,
            )

    def _compare_text(
        self,
        cid: str,
        entity: str,
        attribute: str,
        text_claims: list[Claim],
    ) -> ContradictionResult:
        """Compare textual claims using semantic polarity and exact string matching."""
        seen_values: dict[str, Claim] = {}
        for c in text_claims:
            val_clean = str(c.value).lower().strip()
            seen_values[val_clean] = c

        if len(seen_values) == 1:
            conf, breakdown, conf_exp = self._compute_confidence_and_breakdown(text_claims, divergence_score=0.1)
            return ContradictionResult(
                contradiction_id=cid,
                entity=entity,
                entity_normalized=entity,
                attribute=attribute,
                status="CONSISTENT",
                conflicting_claims=text_claims,
                explanation=f"All sources report the same textual value: '{list(seen_values.keys())[0]}'.",
                confidence=0.95,
                contradiction_type="textual",
                verdict="consistent",
                confidence_breakdown=breakdown,
                confidence_explanation=conf_exp,
            )

        # Check for semantic antonym/polarity contradiction
        values_set = set(seen_values.keys())
        is_semantic_contradiction = False
        for set_pos, set_neg in ANTONYM_PAIRS:
            if (values_set & set_pos) and (values_set & set_neg):
                is_semantic_contradiction = True
                break

        # For executive/director/auditor names: different names are an explicit contradiction
        leadership_attrs = (
            "ceo", "director", "auditor", "coo", "cfo", "manager",
            "executive", "chief executive officer", "managing director", "leadership",
        )
        if attribute.lower() in leadership_attrs:
            names = list(seen_values.keys())
            if len(names) > 1:
                distinct_people = False
                for i, n1 in enumerate(names):
                    for n2 in names[i + 1:]:
                        sim = _token_similarity(n1, n2)
                        if sim < 0.5:
                            distinct_people = True
                            break
                    if distinct_people:
                        break
                if distinct_people:
                    is_semantic_contradiction = True
                else:
                    conf, breakdown, conf_exp = self._compute_confidence_and_breakdown(text_claims, divergence_score=0.1)
                    return ContradictionResult(
                        contradiction_id=cid,
                        entity=entity,
                        entity_normalized=entity,
                        attribute=attribute,
                        status="CONSISTENT",
                        conflicting_claims=text_claims,
                        explanation=f"All sources report consistent leadership name: '{names[0]}'.",
                        confidence=0.95,
                        contradiction_type="textual",
                        verdict="consistent",
                        confidence_breakdown=breakdown,
                        confidence_explanation=conf_exp,
                    )

        # Check OCR confidence threshold: if any claim has low OCR confidence, mark as UNCERTAIN
        min_ocr = min(getattr(c, "ocr_confidence", 1.0) for c in text_claims)
        if min_ocr < self.ocr_confidence_threshold:
            conf, breakdown, conf_exp = self._compute_confidence_and_breakdown(text_claims, divergence_score=0.4)
            return ContradictionResult(
                contradiction_id=cid,
                entity=entity,
                entity_normalized=entity,
                attribute=attribute,
                status="UNCERTAIN",
                conflicting_claims=text_claims,
                explanation=f"Textual conflict flagged as UNCERTAIN due to low OCR confidence ({min_ocr:.2f} < threshold {self.ocr_confidence_threshold}).",
                confidence=conf,
                contradiction_type="textual",
                verdict="uncertain",
                confidence_breakdown=breakdown,
                confidence_explanation=conf_exp,
            )

        sources_str = "; ".join(
            f"{c.source}: '{c.value}'" for c in text_claims
        )

        if is_semantic_contradiction:
            explanation = (
                f"TEXTUAL CONTRADICTION DETECTED for '{entity}' – '{attribute}'. "
                f"Sources disagree on status or entity: {sources_str}."
            )
            conf, breakdown, conf_exp = self._compute_confidence_and_breakdown(text_claims, divergence_score=1.0)
            return ContradictionResult(
                contradiction_id=cid,
                entity=entity,
                entity_normalized=entity,
                attribute=attribute,
                status="CONTRADICTION",
                conflicting_claims=text_claims,
                explanation=explanation,
                confidence=round(conf, 3),
                contradiction_type="textual",
                verdict="contradiction",
                confidence_breakdown=breakdown,
                confidence_explanation=conf_exp,
            )
        else:
            # Check string token similarity
            values_list = list(seen_values.keys())
            sim = _token_similarity(values_list[0], values_list[1])
            if sim >= self.text_similarity_threshold:
                conf, breakdown, conf_exp = self._compute_confidence_and_breakdown(text_claims, divergence_score=0.2)
                return ContradictionResult(
                    contradiction_id=cid,
                    entity=entity,
                    entity_normalized=entity,
                    attribute=attribute,
                    status="CONSISTENT",
                    conflicting_claims=text_claims,
                    explanation=f"Sources report similar textual descriptions (similarity {sim:.0%}): {sources_str}.",
                    confidence=0.80,
                    contradiction_type="textual",
                    verdict="consistent",
                    confidence_breakdown=breakdown,
                    confidence_explanation=conf_exp,
                )
            else:
                conf, breakdown, conf_exp = self._compute_confidence_and_breakdown(text_claims, divergence_score=0.9)
                return ContradictionResult(
                    contradiction_id=cid,
                    entity=entity,
                    entity_normalized=entity,
                    attribute=attribute,
                    status="CONTRADICTION",
                    conflicting_claims=text_claims,
                    explanation=f"Conflicting textual statements detected: {sources_str}.",
                    confidence=round(conf, 3),
                    contradiction_type="textual",
                    verdict="contradiction",
                    confidence_breakdown=breakdown,
                    confidence_explanation=conf_exp,
                )


def _token_similarity(a: str, b: str) -> float:
    """Jaccard similarity on word tokens."""
    tokens_a = set(a.lower().split())
    tokens_b = set(b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)
