import re
from typing import Optional, Tuple, List, Dict, Any
from .models import ContentItem

COMMON_UNITS = [
    # Quantities & Pieces
    "units", "unit", "pieces", "items", "pcs", "count",
    # Mass & Weight
    "kg", "g", "mg", "lbs", "lb", "ton", "tons", "metric tons", "oz",
    # Distance & Length
    "km", "m", "cm", "mm", "miles", "mile", "ft", "in", "yd",
    # Energy, Power & Electricity
    "kwh", "wh", "mwh", "kw", "mw", "w", "v", "mv", "kv", "a", "ma", "mah", "ah", "ohm", "hz", "khz", "mhz", "ghz",
    # Thermal & Temperature
    "°c", "°f", "k", "celsius", "fahrenheit",
    # Digital & Computing
    "kb", "mb", "gb", "tb", "pb", "bps", "kbps", "mbps", "gbps",
    # Time & Rates
    "sec", "seconds", "second", "s", "min", "minutes", "minute", "hours", "hour", "hrs", "hr", "h", "days", "day", "years", "year", "rpm", "bpm",
    # Percentage & Ratios
    "%", "percent", "percentage", "ppm", "ppb",
    # Pressure & Mechanics
    "bar", "psi", "pa", "kpa", "mpa", "db", "dbm",
    # Volume & Fluids
    "l", "ml", "gal", "liters", "litres", "gallons", "cc",
    # Currency
    "$", "€", "£", "¥", "₹", "usd", "eur", "gbp", "inr", "jpy"
]

NUM_PATTERN = r"(?P<val>(?:[±\+−\-~≈]\s*)?\d+(?:,\d{3})*(?:\.\d+)?)"

def extract_metric_from_text(text: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Extracts (claim, value, unit) from an input sentence or text line.
    Preserves words, cleans auxiliary filler, handles currencies and symbols,
    and never invents missing values.
    """
    cleaned = text.strip()
    if not cleaned:
        return "", None, None

    # Strip leading bullet/list markers e.g. "1. ", "• ", "- ", "* "
    list_marker_match = re.match(r"^(?:(?:\d+[\.\)])|[-•*])\s*(.+)$", cleaned)
    if list_marker_match:
        cleaned = list_marker_match.group(1).strip()

    # Pattern 1: Explicit Key-Value syntax (Key: Value or Key = Value)
    kv_match = re.search(r"^([^:=]+)[:=]\s*(.+)$", cleaned)
    if kv_match:
        key = kv_match.group(1).strip()
        val_part = kv_match.group(2).strip()

        # Handle inner formula/symbol like: ΔT = 45 °C or α ≤ 1.25
        inner_kv = re.search(r"^([^:=≤≥<>]+)[:=≤≥<>]\s*(.+)$", val_part)
        sub_key = None
        if inner_kv:
            sub_key = inner_kv.group(1).strip()
            val_part = inner_kv.group(2).strip()

        # Check if val_part contains currency or numbers with units
        num_unit_match = re.search(
            rf"^(?:(?P<pre_unit>[\$€£¥₹])\s*)?{NUM_PATTERN}\s*(?P<post_unit>[a-zA-Z%°/]+(?:\s*[a-zA-Z0-9]+)?)?$",
            val_part,
            re.IGNORECASE
        )
        if num_unit_match:
            value = num_unit_match.group("val").replace(",", "").strip()
            pre_unit = num_unit_match.group("pre_unit")
            post_unit = num_unit_match.group("post_unit")
            unit = pre_unit if pre_unit else (post_unit.strip() if post_unit else None)
            if unit and unit.lower() in ["°c", "°f"]:
                unit = unit.lower()
            combined_key = f"{key} ({sub_key})" if sub_key else key
            return combined_key, value, unit
        else:
            combined_key = f"{key} ({sub_key})" if sub_key else key
            return combined_key, val_part, None

    # Pattern 1b: Subject is/was/are/were Value (e.g. "Status is Active", "Limit was 85")
    is_match = re.search(r"^([^:=]+?)\s+\b(is|was|are|were)\b\s+([A-Za-z0-9_-]+)\.?$", cleaned, re.IGNORECASE)
    if is_match:
        subject = is_match.group(1).strip()
        val = is_match.group(3).strip()
        claim = _clean_claim_words(subject) or subject
        return claim, val, None

    # Pattern 2: Natural sentence with recognized unit
    for unit_candidate in COMMON_UNITS:
        # Currency prefix e.g. $1,200,000 or €50
        if unit_candidate in ["$", "€", "£", "¥", "₹"]:
            curr_match = re.search(rf"(\{unit_candidate})\s*{NUM_PATTERN}", cleaned)
            if curr_match:
                val = curr_match.group("val").replace(",", "").strip()
                # Extract claim by removing the currency token
                claim_raw = re.sub(rf"\{unit_candidate}\s*{NUM_PATTERN}", "", cleaned).strip()
                claim = _clean_claim_words(claim_raw) or cleaned
                return claim, val, unit_candidate

        # Postfix unit with word boundary where applicable
        b_start = r"\b" if unit_candidate[0].isalnum() else ""
        b_end = r"\b" if unit_candidate[-1].isalnum() else ""
        unit_regex = rf"{NUM_PATTERN}\s*(?P<u_found>{b_start}{re.escape(unit_candidate)}{b_end})"
        match = re.search(unit_regex, cleaned, re.IGNORECASE)
        if match:
            val = match.group("val").replace(",", "").strip()
            unit = match.group("u_found")
            claim_raw = re.sub(unit_regex, "", cleaned, flags=re.IGNORECASE).strip()
            claim = _clean_claim_words(claim_raw) or cleaned
            return claim, val, unit

    # Pattern 3: Standalone number with isolated word boundary
    isolated_num_match = re.search(rf"\b{NUM_PATTERN}\b", cleaned)
    if isolated_num_match:
        # Check if the number is an identifier/code like Q3, v2, 4K, 2024-05
        span_start, span_end = isolated_num_match.span()
        before_char = cleaned[span_start - 1] if span_start > 0 else " "
        after_char = cleaned[span_end] if span_end < len(cleaned) else " "
        
        # If part of alphanumeric token or date hyphen, treat as textual claim
        if before_char in "-_/:" or after_char in "-_/:":
            return cleaned, None, None
            
        val = isolated_num_match.group("val").replace(",", "").strip()
        claim_raw = (cleaned[:span_start] + cleaned[span_end:]).strip()
        claim = _clean_claim_words(claim_raw)
        if claim and len(claim) >= 2:
            return claim, val, None

    # Fallback: General textual assertion
    return cleaned, None, None


def _clean_claim_words(raw_claim: str) -> str:
    """
    Safely strips trailing auxiliary connector words without damaging valid English words.
    Uses regex word boundaries instead of character-based string stripping.
    """
    if not raw_claim:
        return ""
    # Strip trailing auxiliary verbs using word boundaries
    cleaned = re.sub(r"\b(was|is|at|reached|of|were|are|to|equals?|in|by)\b\s*$", "", raw_claim, flags=re.IGNORECASE).strip()
    # Strip leading auxiliary connectors
    cleaned = re.sub(r"^\b(the|that|and|or)\b\s*", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned.strip(" .:,;=-–—")


def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into clean, cohesive sentences and lines.
    Protects abbreviations, numbered lists, and decimal numbers from being split.
    """
    if not text:
        return []

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # Protect common abbreviations
    protected = normalized
    abbrevs = ["e.g.", "i.e.", "etc.", "vs.", "fig.", "dr.", "mr.", "ms.", "approx.", "no.", "vol.", "dept."]
    for abb in abbrevs:
        pattern = re.compile(re.escape(abb), re.IGNORECASE)
        protected = pattern.sub(abb.replace(".", "<DOT>"), protected)

    # Protect decimal numbers (e.g. 12.50)
    protected = re.sub(r"(\d+)\.(\d+)", r"\1<DECIMAL>\2", protected)

    # Protect numbered lists (e.g. 1. 2.)
    protected = re.sub(r"(?:^|\n)\s*(\d+)\.\s+", r"\n\1<NUMDOT> ", protected)

    extracted_items: List[str] = []
    lines = [l.strip() for l in protected.split("\n") if l.strip()]

    for line in lines:
        # Split on sentence end (. ! ?) only when followed by space and capital letter
        sub_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", line)
        for part in sub_sentences:
            restored = (
                part.replace("<DOT>", ".")
                .replace("<DECIMAL>", ".")
                .replace("<NUMDOT>", ".")
                .strip()
            )
            if restored and len(restored) > 1:
                extracted_items.append(restored)

    return extracted_items


def deduplicate_content_items(items: List[ContentItem]) -> List[ContentItem]:
    """
    Removes redundant identical content items while maintaining original document order.
    """
    seen = set()
    deduped: List[ContentItem] = []
    for item in items:
        # Key on claim, value, unit, page, sheet, row, column
        key = (
            item.claim.strip().lower(),
            str(item.value).strip().lower() if item.value is not None else None,
            item.unit.strip().lower() if item.unit is not None else None,
            item.page,
            item.sheet,
            item.row,
            item.column
        )
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped
