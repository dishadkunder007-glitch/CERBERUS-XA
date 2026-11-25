"""
Entity Matching – uses RapidFuzz to group similar entity names while preventing false merges.

Features:
- Corporate suffix normalization (Ltd, Inc, Corp, Industries, Plant, Co)
- Initials and abbreviation handling (e.g. "A.B.C. Industries" -> "ABC Industries")
- Strict distinctive token verification: prevents false matches between different companies
  (e.g. "Apple Inc." vs "Orange Inc.", "ABC Industries" vs "XYZ Industries")
- Configurable similarity threshold (for flagging) and merge threshold (for unifying)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EntityGroup:
    """A group of entity names that likely refer to the same real-world entity."""
    canonical: str                   # chosen representative name
    aliases: list[str] = field(default_factory=list)
    entity_type: str = "MISC"


GENERIC_CORPORATE_WORDS = {
    "industries", "industry", "corporation", "corp", "limited", "ltd",
    "company", "co", "incorporated", "inc", "enterprises", "enterprise",
    "technologies", "tech", "technology", "solutions", "group", "plant",
    "facility", "manufacturing", "manufacturing plant", "services", "holdings",
    "llc", "plc", "pvt", "private", "associates", "team", "the",
}


def _normalize_name_for_similarity(name: str) -> str:
    """Normalize common corporate suffixes and initials to improve fuzzy matching."""
    s = name.lower()

    # Normalize initials with dots: "a.b.c." -> "abc", "i.b.m." -> "ibm"
    s = re.sub(r'\b([a-z])\.(?=[a-z]\b|\s|$)', r'\1', s)
    s = re.sub(r'[\.,;:]', ' ', s)

    # Normalize suffixes
    s = re.sub(r'\b(manufacturing plant|plant|facility)\b', '', s)
    s = re.sub(r'\b(industries|industry)\b', 'industry', s)
    s = re.sub(r'\b(corporation|corp)\b', 'corp', s)
    s = re.sub(r'\b(limited|ltd)\b', 'ltd', s)
    s = re.sub(r'\b(company|co)\b', 'co', s)
    s = re.sub(r'\b(incorporated|inc)\b', 'inc', s)

    return re.sub(r'\s+', ' ', s).strip()


def _get_distinctive_tokens(name: str) -> set[str]:
    """Extract tokens that distinguish one entity from another (excluding generic corporate words)."""
    clean = _normalize_name_for_similarity(name)
    tokens = set(clean.split())
    distinctive = {t for t in tokens if t not in GENERIC_CORPORATE_WORDS and len(t) > 1}
    return distinctive if distinctive else tokens


def _compute_similarity(name_a: str, name_b: str) -> float:
    """
    Compute similarity between two entity names.
    Applies strict safeguards: if the distinctive tokens are completely different,
    the entities are never considered identical.
    """
    if not name_a or not name_b:
        return 0.0

    # Exact match after lowercase strip
    if name_a.strip().lower() == name_b.strip().lower():
        return 100.0

    # Initials and corporate suffix normalization
    norm_a = _normalize_name_for_similarity(name_a)
    norm_b = _normalize_name_for_similarity(name_b)

    # Identical after normalizing abbreviations/initials (e.g. A.B.C. Industries vs ABC Industries, I.B.M. vs IBM Corp)
    clean_a = re.sub(r'[\.,;:]', '', name_a).strip().lower()
    clean_b = re.sub(r'[\.,;:]', '', name_b).strip().lower()
    # Suffix difference (Ltd, Corp, Inc, Plant, Manufacturing) or abbreviation dot merges at 100.0
    suffix_words = [".", "corp", "corporation", "ltd", "limited", "inc", "plant", "facility", "manufacturing", "manufacturing plant"]
    core_pattern = r'\b(?:' + '|'.join(re.escape(w) for w in suffix_words) + r')\b'
    core_a = re.sub(r'\s+', ' ', re.sub(core_pattern, '', norm_a)).strip()
    core_b = re.sub(r'\s+', ' ', re.sub(core_pattern, '', norm_b)).strip()
    has_suffix = any(w in name_a.lower() for w in suffix_words) or any(w in name_b.lower() for w in suffix_words)
    if (clean_a == clean_b or norm_a == norm_b or core_a == core_b) and len(core_a) > 2 and has_suffix:
        return 100.0

    # Check distinctive core tokens (prevent Apple Inc vs Orange Inc, ABC vs XYZ)
    tokens_a = _get_distinctive_tokens(name_a)
    tokens_b = _get_distinctive_tokens(name_b)

    if tokens_a and tokens_b:
        has_overlap = bool(tokens_a & tokens_b)
        if not has_overlap:
            joined_a = "".join(sorted(tokens_a))
            joined_b = "".join(sorted(tokens_b))
            if joined_a != joined_b and not any(a in b or b in a for a in tokens_a for b in tokens_b):
                return 0.0

    from rapidfuzz import fuzz

    raw_score = float(fuzz.token_set_ratio(name_a, name_b))
    norm_score = float(fuzz.token_set_ratio(norm_a, norm_b))

    # Balanced weighting: allows variants (Industries vs Industry) to score ~88.5
    # (merging at 85.0 while flagging as possible match at 92.0)
    final_score = 0.75 * raw_score + 0.25 * norm_score
    return round(final_score, 1)


def match_entities(
    entity_names: list[str],
    similarity_threshold: float = 82.0,
    merge_threshold: float = 92.0,
) -> dict[str, str]:
    """
    Group similar entity names using RapidFuzz with false-positive prevention.

    Args:
        entity_names: list of raw entity name strings.
        similarity_threshold: minimum score to flag as POSSIBLE_MATCH (not merged).
        merge_threshold: minimum score to treat as the same entity (merged).

    Returns:
        A dict mapping each entity name -> canonical (representative) name.
    """
    try:
        from rapidfuzz import fuzz
    except ImportError:
        logger.error("rapidfuzz not installed. Returning identity mapping.")
        return {n: n for n in entity_names}

    unique_names = [n for n in dict.fromkeys(entity_names) if n and n != "Unknown"]
    canonical_map: dict[str, str] = {n: n for n in entity_names}

    if not unique_names:
        return canonical_map

    # Union-Find for grouping
    parent: dict[str, str] = {n: n for n in unique_names}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str):
        ra, rb = find(a), find(b)
        if ra != rb:
            # Choose canonical: prefer longer, more descriptive name
            if len(rb) >= len(ra):
                parent[ra] = rb
            else:
                parent[rb] = ra

    for i, name_a in enumerate(unique_names):
        for name_b in unique_names[i + 1:]:
            score = _compute_similarity(name_a, name_b)
            if score >= merge_threshold:
                union(name_a, name_b)
                logger.debug("Merged '%s' <-> '%s' (score=%.1f)", name_a, name_b, score)
            elif score >= similarity_threshold:
                logger.info("Possible match (not merged): '%s' <-> '%s' (score=%.1f)", name_a, name_b, score)

    for name in unique_names:
        canonical_map[name] = find(name)

    return canonical_map


def build_entity_groups(
    entity_names: list[str],
    entity_types: Optional[dict[str, str]] = None,
    similarity_threshold: float = 82.0,
    merge_threshold: float = 92.0,
) -> list[EntityGroup]:
    """Build EntityGroup objects from raw entity names."""
    canonical_map = match_entities(entity_names, similarity_threshold, merge_threshold)

    groups: dict[str, EntityGroup] = {}
    for original, canonical in canonical_map.items():
        if canonical not in groups:
            etype = (entity_types or {}).get(canonical, "ORG")
            groups[canonical] = EntityGroup(
                canonical=canonical,
                aliases=[],
                entity_type=etype,
            )
        if original != canonical:
            groups[canonical].aliases.append(original)

    return list(groups.values())


def get_possible_matches(
    entity_names: list[str],
    similarity_threshold: float = 70.0,
    merge_threshold: float = 92.0,
) -> list[tuple[str, str, float]]:
    """Return pairs of entity names that are similar but NOT merged."""
    unique = list(dict.fromkeys(entity_names))
    results = []
    for i, na in enumerate(unique):
        for nb in unique[i + 1:]:
            score = _compute_similarity(na, nb)
            if similarity_threshold <= score < merge_threshold:
                results.append((na, nb, score))
    return results
