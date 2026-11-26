"""
Claim Builder – converts raw extracted claims into structured, normalized Claim objects
and assigns unique, deterministic IDs, applying entity matching to unify similar names.
"""

import hashlib
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from .entity_extraction import RawClaim, classify_entity_type
from .entity_matching import match_entities
from .normalizer import (
    normalize_unit,
    normalize_value,
    normalize_date,
    get_canonical_unit,
    get_unit_dimension,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

@dataclass
class Claim:
    claim_id: str
    entity: str                      # original entity name from text
    entity_normalized: str           # canonical name after fuzzy matching
    entity_type: str
    attribute: str
    value: Any                       # numeric (float/int) or string
    value_normalized: float | None   # float in canonical dimension base unit if numeric, else None
    unit: str                        # raw unit
    unit_normalized: str             # canonical base unit (e.g. 'g', 'm', 'INR', 'USD', '%', 'units')
    date_str: str                    # raw date string
    date_normalized: str             # ISO-compatible e.g. "2026-01", "2026-Q1", "FY2025-26", "2026"
    source: str                      # filename
    page_or_sheet: str               # "Page 1" or "Sheet1"
    original_text: str               # excerpt
    confidence: float
    comparable: bool = True          # False if unit mismatch or invalid
    modality: str = "actual"         # actual, target, estimate, quoted
    dimension: str = ""              # mass, length, volume, currency_INR, percentage, count, etc.
    person: str = ""                 # associated person entity if any
    ocr_confidence: float = 1.0
    flags: list[str] = field(default_factory=list)


def _make_claim_id(
    entity: str,
    attribute: str,
    source: str,
    value: Any = None,
    page_or_sheet: str = "",
    unit: str = "",
    date_str: str = "",
    modality: str = "actual",
    *args,
    **kwargs,
) -> str:
    """Generate a deterministic, unique claim ID to avoid graph collisions."""
    key = f"{entity}|{attribute}|{source}|{page_or_sheet}|{value}|{unit}|{date_str}|{modality}"
    return "C-" + hashlib.md5(key.encode("utf-8")).hexdigest()[:10].upper()


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

class ClaimBuilder:
    """
    Converts RawClaim objects into normalized Claim objects.
    Applies entity matching to group corporate variants.
    """

    def __init__(
        self,
        merge_threshold: float = 92.0,
        similarity_threshold: float = 82.0,
    ):
        self.merge_threshold = merge_threshold
        self.similarity_threshold = similarity_threshold
        self._canonical_map: dict[str, str] = {}

    def build(self, raw_claims: list[RawClaim]) -> list[Claim]:
        """Convert raw claims to normalized Claim objects."""
        if not raw_claims:
            return []

        # Build entity canonical map
        all_entity_names = [rc.entity for rc in raw_claims if rc.entity]
        self._canonical_map = match_entities(
            all_entity_names,
            similarity_threshold=self.similarity_threshold,
            merge_threshold=self.merge_threshold,
        )

        claims: list[Claim] = []
        for rc in raw_claims:
            try:
                claim = self._build_one(rc)
                if claim is not None:
                    claims.append(claim)
            except Exception as exc:
                logger.warning("Failed to build claim from raw: %s — %s", rc, exc)

        logger.info("Built %d claims from %d raw claims.", len(claims), len(raw_claims))
        return claims

    def _build_one(self, rc: RawClaim) -> Optional[Claim]:
        """Build a single Claim from a RawClaim."""
        entity_norm = self._canonical_map.get(rc.entity, rc.entity)
        if not entity_norm:
            entity_norm = "Unknown"

        unit_norm = normalize_unit(rc.unit)
        canonical_unit = get_canonical_unit(unit_norm)
        dimension = get_unit_dimension(unit_norm)

        # Monetary scale words (lakh, crore) with financial attributes become INR
        if rc.unit.lower() in ("lakh", "lac", "lakhs", "crore", "cr", "crores") or unit_norm in ("lakh", "crore"):
            if rc.attribute in ("revenue", "profit", "cost", "turnover", "debt", "capex", "investment"):
                canonical_unit = "INR"
                dimension = "currency_INR"

        # Normalize value
        if isinstance(rc.value, (int, float)):
            value_norm, comparable = normalize_value(rc.value, rc.unit, unit_norm)
        else:
            # String / qualitative claim
            value_norm = None
            comparable = True

        date_norm = normalize_date(rc.date_str)

        attr = rc.attribute
        if attr.lower() in ("ceo", "chief executive officer", "chief executive", "managing director"):
            attr = "executive"

        claim_id = _make_claim_id(
            entity_norm,
            attr,
            rc.source,
            rc.page_or_sheet,
            rc.value,
            rc.unit,
            rc.date_str,
            rc.modality,
        )

        return Claim(
            claim_id=claim_id,
            entity=rc.entity,
            entity_normalized=entity_norm,
            entity_type=classify_entity_type(entity_norm) or rc.entity_type,
            attribute=attr,
            value=rc.value,
            value_normalized=value_norm,
            unit=rc.unit,
            unit_normalized=canonical_unit,
            date_str=rc.date_str,
            date_normalized=date_norm,
            source=rc.source,
            page_or_sheet=rc.page_or_sheet,
            original_text=rc.original_text,
            confidence=rc.confidence,
            comparable=comparable,
            modality=rc.modality,
            dimension=dimension,
            person=rc.person,
            ocr_confidence=getattr(rc, "ocr_confidence", 1.0),
            flags=list(getattr(rc, "flags", [])),
        )

    def to_dicts(self, claims: list[Claim]) -> list[dict]:
        return [asdict(c) for c in claims]
