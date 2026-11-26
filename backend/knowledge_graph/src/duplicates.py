"""
Duplicates and Inconsistencies Detection Engine.

Detects:
1. Exact duplicates across documents (same entity, attribute, period, unit, value).
2. Near-duplicate claims (very close values or textual paraphrasing).
3. Intra-document inconsistencies (conflicts within the very same document).
"""

import logging
from dataclasses import dataclass, field
from typing import Any
from rapidfuzz import fuzz

from .claim_builder import Claim
from .normalizer import dates_overlap

logger = logging.getLogger(__name__)


@dataclass
class DuplicateReport:
    """Report detailing duplicate claims, near-duplicates, and intra-document inconsistencies."""
    duplicate_groups: list[dict[str, Any]] = field(default_factory=list)
    near_duplicate_claims: list[dict[str, Any]] = field(default_factory=list)
    inconsistent_within_document: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_duplicate_groups(self) -> int:
        return len(self.duplicate_groups)

    @property
    def total_near_duplicates(self) -> int:
        return len(self.near_duplicate_claims)

    @property
    def total_intra_document_inconsistencies(self) -> int:
        return len(self.inconsistent_within_document)


def detect_duplicates(
    documents: list[dict],
    claims: list[Claim],
    text_similarity_threshold: float = 0.90,
    value_similarity_threshold: float = 0.05,
) -> DuplicateReport:
    """
    Detect exact duplicates, near-duplicates, and intra-document contradictions.

    Args:
        documents: loaded document objects
        claims: normalized claims list
        text_similarity_threshold: ratio for text fuzz matching (default 0.90)
        value_similarity_threshold: relative fractional diff for near duplicates (default 0.05 or 5%)

    Returns:
        DuplicateReport
    """
    report = DuplicateReport()
    if not claims:
        return report

    # 1. Intra-document Inconsistencies
    # Group claims by source document, entity, attribute, and overlapping date
    by_source: dict[str, list[Claim]] = {}
    for c in claims:
        by_source.setdefault(c.source, []).append(c)

    for source_name, src_claims in by_source.items():
        # Compare claims within this document
        for i, ca in enumerate(src_claims):
            for cb in src_claims[i + 1:]:
                if ca.entity_normalized.lower() != cb.entity_normalized.lower():
                    continue
                if ca.attribute.lower() != cb.attribute.lower():
                    continue
                if not dates_overlap(ca.date_normalized or ca.date_str, cb.date_normalized or cb.date_str):
                    continue
                if ca.modality != cb.modality:
                    continue

                # Compare values
                if ca.value_normalized is not None and cb.value_normalized is not None:
                    mean_val = (abs(ca.value_normalized) + abs(cb.value_normalized)) / 2.0
                    if mean_val > 0:
                        diff_ratio = abs(ca.value_normalized - cb.value_normalized) / mean_val
                        if diff_ratio > 0.02:  # Over 2% difference within same document
                            report.inconsistent_within_document.append({
                                "claim_ids": [ca.claim_id, cb.claim_id],
                                "source": source_name,
                                "attribute": ca.attribute,
                                "values": [f"{ca.value} {ca.unit}", f"{cb.value} {cb.unit}"],
                                "reason": (
                                    f"Internal contradiction in '{source_name}': "
                                    f"{ca.page_or_sheet} states {ca.value} {ca.unit} but "
                                    f"{cb.page_or_sheet} states {cb.value} {cb.unit} "
                                    f"for {ca.attribute} ({diff_ratio * 100:.1f}% divergence)."
                                ),
                            })
                else:
                    sa = str(ca.value).lower().strip()
                    sb = str(cb.value).lower().strip()
                    if sa != sb and sa and sb:
                        report.inconsistent_within_document.append({
                            "claim_ids": [ca.claim_id, cb.claim_id],
                            "source": source_name,
                            "attribute": ca.attribute,
                            "values": [ca.value, cb.value],
                            "reason": (
                                f"Internal textual disagreement in '{source_name}': "
                                f"{ca.page_or_sheet} states '{ca.value}' but "
                                f"{cb.page_or_sheet} states '{cb.value}' for {ca.attribute}."
                            ),
                        })

    # 2. Exact Duplicates & Near Duplicates across all claims
    # Group claims by (entity_normalized, attribute, date_normalized, modality)
    fact_groups: dict[tuple[str, str, str, str], list[Claim]] = {}
    for c in claims:
        key = (
            c.entity_normalized.lower(),
            c.attribute.lower(),
            c.date_normalized or c.date_str,
            c.modality,
        )
        fact_groups.setdefault(key, []).append(c)

    for (ent, attr, dt, mod), grp in fact_groups.items():
        if len(grp) < 2:
            continue

        # Check for exact matches
        exact_subgroups: dict[str, list[Claim]] = {}
        for c in grp:
            v_key = f"{c.value_normalized}:{c.unit_normalized}" if c.value_normalized is not None else str(c.value).strip().lower()
            exact_subgroups.setdefault(v_key, []).append(c)

        for v_key, exact_list in exact_subgroups.items():
            if len(exact_list) >= 2:
                report.duplicate_groups.append({
                    "entity": ent,
                    "attribute": attr,
                    "date": dt,
                    "value": exact_list[0].value,
                    "unit": exact_list[0].unit,
                    "claim_ids": [c.claim_id for c in exact_list],
                    "sources": [c.source for c in exact_list],
                    "similarity": 1.0,
                    "reason": f"Exact duplicate fact across {len(exact_list)} sources.",
                })

        # Check for near duplicates (different claims but within value_similarity_threshold or text fuzzy similarity)
        for i, ca in enumerate(grp):
            for cb in grp[i + 1:]:
                # If exact duplicate, already handled
                if ca.value_normalized is not None and cb.value_normalized is not None:
                    if ca.value_normalized == cb.value_normalized:
                        continue
                    mean_val = (abs(ca.value_normalized) + abs(cb.value_normalized)) / 2.0
                    if mean_val > 0:
                        diff_pct = abs(ca.value_normalized - cb.value_normalized) / mean_val
                        if 0 < diff_pct <= value_similarity_threshold:
                            report.near_duplicate_claims.append({
                                "claim_ids": [ca.claim_id, cb.claim_id],
                                "entity": ent,
                                "attribute": attr,
                                "similarity": round(1.0 - diff_pct, 4),
                                "values": [f"{ca.value} {ca.unit}", f"{cb.value} {cb.unit}"],
                                "sources": [ca.source, cb.source],
                                "source_spans": [ca.original_text, cb.original_text],
                                "reason": f"Near-duplicate value within {diff_pct * 100:.1f}% relative difference.",
                            })
                else:
                    sa = str(ca.value).strip()
                    sb = str(cb.value).strip()
                    if sa and sb and sa.lower() != sb.lower():
                        sim = fuzz.token_sort_ratio(sa, sb) / 100.0
                        if sim >= text_similarity_threshold:
                            report.near_duplicate_claims.append({
                                "claim_ids": [ca.claim_id, cb.claim_id],
                                "entity": ent,
                                "attribute": attr,
                                "similarity": round(sim, 4),
                                "values": [sa, sb],
                                "sources": [ca.source, cb.source],
                                "source_spans": [ca.original_text, cb.original_text],
                                "reason": f"Near-duplicate textual statement (token sort similarity {sim:.0%}).",
                            })

    logger.info(
        "Duplicate detection complete: %d duplicate groups, %d near-duplicates, %d intra-doc inconsistencies",
        len(report.duplicate_groups),
        len(report.near_duplicate_claims),
        len(report.inconsistent_within_document),
    )
    return report
