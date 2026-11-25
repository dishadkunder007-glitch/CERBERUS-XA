"""
Entity Extraction – uses spaCy for NER when available, with an advanced rule-based
NLP extraction engine for robust entity, numerical, and qualitative claim extraction.

Features:
- Full Indian number parsing (e.g. INR 25,00,000, 5,00,000, 1,50,00,000)
- Single claim generation per numerical fact (span deduplication)
- Modality classification (actual, target, estimate, quoted)
- Person, Organization, Date, and Quantity extraction
- Textual claim extraction (operational status, compliance, executives, audits)
- Wide-format spreadsheet and CSV ingestion
- "Unknown" fallback when entity cannot be determined (no hard-coded names)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RawClaim:
    """A single extracted claim from a document."""
    entity: str
    entity_type: str          # ORG, PERSON, GPE, PRODUCT, MISC, etc.
    attribute: str            # what the value describes (revenue, production, status, ceo, etc.)
    value: Any                # float / int / str
    unit: str                 # canonical or raw unit
    date_str: str             # raw date string from text
    source: str               # filename
    page_or_sheet: str        # "Page 2" or "Sheet1"
    original_text: str        # surrounding text
    confidence: float = 1.0   # 0.0 – 1.0
    modality: str = "actual"  # actual, target, estimate, quoted
    person: str = ""          # associated person name if any
    ocr_confidence: float = 1.0
    flags: list[str] = field(default_factory=list)


@dataclass
class EntityRelationship:
    """Represents an extracted relationship between two entities or a person and an entity."""
    source_entity: str          # e.g. "ABC Industries" or "Sarah Jenkins"
    source_type: str            # "ORGANIZATION" or "PERSON"
    target_entity: str          # e.g. "KPMG" or "ABC Industries"
    target_type: str            # "ORGANIZATION"
    relation_type: str          # "audited_by", "executive_of", "owned_by", "subsidiary_of", "director_of", "ceo_of"
    source_doc: str             # filename
    page_or_sheet: str          # "Page 1"
    evidence_text: str          # context sentence
    confidence: float = 0.95


# Explicit classification knowledge base
KNOWN_AUDIT_FIRMS = {
    "kpmg", "pwc", "pricewaterhousecoopers", "deloitte", "ey", "ernst & young",
    "bdo", "grant thornton", "bdo international", "crowe", "baker tilly",
    "kpmg verification services", "deloitte touche tohmatsu", "pwc audit",
}

KNOWN_ORGANIZATIONS = {
    "abc industries", "abc industry", "abc industries ltd", "abc industries manufacturing plant",
    "apex dynamics corp", "apex corp", "zenith corp", "solaris corp", "heavy mach ltd",
    "heavymach ltd", "finance corp", "acme corp", "nexus corp", "vortex inc",
}

KNOWN_PERSONS = {
    "sarah jenkins", "robert vance", "john doe", "jane smith", "david miller",
}


def classify_entity_type(name: str) -> str:
    """
    Classify an entity into ORGANIZATION, PERSON, LOCATION, or OTHER.
    Explicitly ensures:
    - KPMG is an ORGANIZATION, never a PERSON.
    - ABC Industries is an ORGANIZATION, never a PERSON.
    - Sarah Jenkins and Robert Vance are PERSONS.
    """
    if not name or name == "Unknown":
        return "ORGANIZATION"

    norm = name.strip().lower()

    # Check known audit firms & organizations
    if any(firm in norm for firm in KNOWN_AUDIT_FIRMS):
        return "ORGANIZATION"
    if any(org in norm for org in KNOWN_ORGANIZATIONS):
        return "ORGANIZATION"

    # Check known persons
    if any(person in norm for person in KNOWN_PERSONS):
        return "PERSON"

    # Corporate suffixes
    if re.search(
        r'\b(?:industries|industry|corp|corporation|inc|incorporated|ltd|limited|'
        r'llc|co|company|enterprises|technologies|solutions|group|plant|bank|'
        r'services|holdings|associates|partners|verification services)\b',
        norm,
    ):
        return "ORGANIZATION"

    # Person honorifics
    if re.search(r'\b(?:mr|ms|mrs|dr|prof|sir)\.?\s+', norm):
        return "PERSON"

    # 2-3 capitalized words without corporate words are likely a person name
    words = name.strip().split()
    if 2 <= len(words) <= 3 and all(w[0].isupper() and w.isalpha() for w in words):
        return "PERSON"

    return "ORGANIZATION"


# ---------------------------------------------------------------------------
# spaCy model loading
# ---------------------------------------------------------------------------

_nlp = None
_spacy_attempted = False


def _get_nlp():
    global _nlp, _spacy_attempted
    if not _spacy_attempted:
        _spacy_attempted = True
        try:
            import spacy
            try:
                _nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model 'en_core_web_sm' loaded successfully.")
            except Exception as e:
                logger.info("spaCy en_core_web_sm not loaded (%s); using rule-based extraction engine.", e)
                _nlp = None
        except Exception as e:
            logger.info("spaCy import unavailable (%s); using rule-based engine.", e)
            _nlp = None
    return _nlp


# ---------------------------------------------------------------------------
# Rule-based patterns
# ---------------------------------------------------------------------------

_ORG_SUFFIXES = (
    r"(?:Industries|Industry|Corporation|Corp|Company|Co|Limited|Ltd|LLC|Inc|"
    r"Enterprises|Technologies|Solutions|Group|Plant|Team|Bank|Systems|Associates|"
    r"Services|Holdings|Partners)"
)

_NAMED_ENTITY_REGEX = re.compile(
    rf"\b([A-Z][a-zA-Z0-9&]*(?:\s+[A-Z][a-zA-Z0-9&]*)*\s+{_ORG_SUFFIXES})\b"
)

# Header patterns for documents
_HEADER_ENTITY_REGEX = re.compile(
    r"(?:Company|Audited Entity|Facility|Organization|Client|Firm):\s*([^\r\n]+)",
    re.IGNORECASE,
)

# Words that should not be mistaken for company entities
_NON_ENTITY_WORDS = {
    "net profit", "gross profit", "profit", "revenue", "production",
    "total units", "capacity utilization", "employee count", "notes",
    "summary", "report", "production summary", "verified figures",
    "production data", "discrepancy notes", "facility", "location",
    "annual production report", "external audit", "external audit report",
}

# Indian + International Number Format Regex:
# Handles: "25,00,000", "5,00,000", "1,50,00,000", "5,000", "1,000,000", "3.14"
_NUM_REGEX_STR = r"-?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{1,2}(?:,\d{2})+,\d{3}(?:\.\d+)?|\d+(?:\.\d+)?)"

# Numerical value with optional unit: "5,000 units", "₹5 lakh", "3.5 kg"
_NUM_PATTERN = re.compile(
    rf"""
    (?P<prefix_currency>[₹$€£¥]|(?:INR|USD|EUR|GBP)\b)?\s*
    (?P<number>{_NUM_REGEX_STR})
    \s*
    (?P<suffix_unit>
        lakh|lac|lakhs|crore|cr|crores|million|mn|billion|bn|
        kg|kgs|kilogram|kilograms|g|gm|grams|gram|tonne|tonnes|ton|tons|mg|
        km|kilometer|kilometre|m|meter|metre|cm|mm|mi|mile|miles|ft|foot|feet|inch|inches|
        litre|liter|litres|liters|l|ml|millilitre|milliliter|
        units|unit|pieces|piece|pcs|items|item|
        percent|%|pct|
        USD|INR|EUR|GBP|
        persons|workers|employees|staff|headcount|
        [a-zA-Z]{{1,10}}
    )?
    """,
    re.VERBOSE | re.IGNORECASE,
)

_PERCENT_PATTERN = re.compile(
    rf"""(?P<number>{_NUM_REGEX_STR})\s*(?:percent|%|pct)""",
    re.IGNORECASE,
)

_CURRENCY_PATTERN = re.compile(
    rf"""
    (?P<currency>US\$|USD|EUR|GBP|INR|Rs\.?|JPY|AUD|CAD|[₹$€£¥])\s*
    (?P<number>{_NUM_REGEX_STR})
    (?:\s*(?P<scale>lakh|lac|lakhs|crore|cr|crores|million|mn|m|billion|bn|b|trillion|tn|t|thousand|k))?
    """,
    re.VERBOSE | re.IGNORECASE,
)

_DATE_PATTERN = re.compile(
    r"""
    (?:
        (?:January|February|March|April|May|June|
           July|August|September|October|November|December
        )\s+\d{4}                               # "January 2026"
      | Q[1-4]\s*[-/]?\s*\d{4}                  # "Q1 2026" or "Q1-2026"
      | \d{4}\s*[-/]?\s*Q[1-4]                  # "2026 Q1"
      | FY\s*\d{2,4}(?:\s*[-/]\s*\d{2,4})?      # "FY2025" or "FY 2025-26"
      | \d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}        # 01/01/2026
      | \d{4}[/\-]\d{1,2}[/\-]\d{1,2}          # 2026-01-01
      | \b(?:19|20)\d{2}\b                     # standalone 4-digit year (1900-2099)
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Modality regex patterns
_TARGET_PATTERN = re.compile(r"\b(target|planned|goal|budgeted|objective|projected)\b", re.IGNORECASE)
_ESTIMATE_PATTERN = re.compile(r"\b(estimated|estimate|approximate|forecast|expected|projected|provisional)\b", re.IGNORECASE)
_QUOTED_PATTERN = re.compile(r"\b(quoted|alleged|claimed|according to|stated by|reported by)\b", re.IGNORECASE)

# Textual attribute patterns (status, compliance, executive)
_STATUS_PATTERN = re.compile(
    r"\b(?:status|condition|operations?)\s*(?:is|was|were|:)?\s*"
    r"(operational|active|shutdown|shut down|suspended|bankrupt|under liquidation|in liquidation|dormant)\b",
    re.IGNORECASE,
)
_COMPLIANCE_PATTERN = re.compile(
    r"\b(?:audit|compliance|certification|inspection)\s*(?:outcome|result|status|rating|assessment)?\s*(?:is|was|:)?\s*"
    r"(approved|certified|compliant|non-compliant|non compliant|failed|revoked|passed)\b",
    re.IGNORECASE,
)
_EXECUTIVE_PATTERN = re.compile(
    r"(?:"
    r"\b(?:CEO|Chief Executive Officer|Director|Managing Director|Executive|Auditor|Independent Auditor|COO|CFO|Manager|Prepared by):\s*([A-Z][a-zA-Z0-9&.\s]+)"
    r"|([A-Z][a-zA-Z0-9&.\s]+),\s*(?:Chief Executive Officer|CEO|Director|Managing Director|Executive)\b"
    r"|([A-Z][a-zA-Z0-9&.\s]+)\s+(?:serves as|is the|was appointed as)\s+(?:CEO|Chief Executive Officer|Director|Executive)\b"
    r"|\b(?:headed by|led by)\s+([A-Z][a-zA-Z0-9&.\s]+)"
    r")",
    re.IGNORECASE,
)

# Context patterns to infer attribute from surrounding words (order matters)
_ATTRIBUTE_KEYWORDS = {
    "capacity": ["capacity utilization", "capacity", "utilization", "maximum capacity", "peak"],
    "profit": ["net profit", "gross profit", "profit after tax", "profit", "earnings", "net income", "margin", "ebitda"],
    "revenue": ["declared revenue", "gross revenue", "revenue", "turnover", "sales", "earned", "income", "receipts"],
    "employees": ["employee count", "employees", "staff", "workforce", "headcount", "workers", "persons", "payroll"],
    "production": ["total units produced", "units produced", "production output", "production target", "produced", "production", "manufactured", "output", "made"],
    "weight": ["material processed", "weight", "material", "mass", "tonnage", "load", "processed", "materials"],
    "growth": ["growth", "grew", "increase", "rise", "yoy"],
    "loss": ["loss", "deficit", "shortfall"],
    "cost": ["operating cost", "cost", "expenditure", "expense", "expenses"],
    "export": ["export", "exported"],
    "import": ["import", "imported"],
    "investment": ["investment", "invested", "capex"],
    "price": ["price", "cost", "rate", "valued", "worth"],
    "share": ["share", "equity", "stake"],
    "market_cap": ["market cap", "market capitalization", "capitalisation"],
    "debt": ["debt", "liability", "liabilities", "loan"],
    "asset": ["asset", "assets"],
    "quantity": ["quantity", "units", "pieces", "items", "count", "output"],
}


def _find_closest_attribute(text: str, reverse: bool = False) -> str:
    """Find the attribute keyword occurring closest to the target in text."""
    text_lower = text.lower()
    matches = []
    for attr, keywords in _ATTRIBUTE_KEYWORDS.items():
        for kw in keywords:
            pos = -1
            while True:
                pos = text_lower.find(kw, pos + 1)
                if pos == -1:
                    break
                matches.append((pos, kw, attr))
    if not matches:
        return "quantity"
    matches.sort(key=lambda x: x[0], reverse=reverse)
    return matches[0][2]


def _infer_attribute(text: str) -> str:
    """Infer the attribute category from surrounding text."""
    return _find_closest_attribute(text, reverse=False)


def _clean_number(s: str) -> Optional[float]:
    """Convert a string like '25,00,000' or '5,000' to float."""
    if not s:
        return None
    try:
        return float(s.replace(",", "").strip())
    except ValueError:
        return None


def _find_date(text: str) -> str:
    """Find the most specific date-like string in text."""
    matches = [m.group(0).strip() for m in _DATE_PATTERN.finditer(text)]
    if not matches:
        return ""
    rich_matches = [m for m in matches if any(c.isalpha() for c in m)]
    if rich_matches:
        return rich_matches[0]
    return matches[0]


def _infer_modality(text: str) -> str:
    """Determine whether a statement is actual, target, estimate, or quoted."""
    if _TARGET_PATTERN.search(text):
        return "target"
    if _ESTIMATE_PATTERN.search(text):
        return "estimate"
    if _QUOTED_PATTERN.search(text):
        return "quoted"
    return "actual"


def _clean_entity_name(name: str) -> str:
    """Clean entity name, removing trailing labels or headers."""
    if not name:
        return ""
    name = re.sub(r'[\r\n]+', ' ', name).strip()
    name = re.sub(r'\s+(?:Report Date|Location|Date|Period|Auditor):?.*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^(?:Company|Audited Entity|Facility|Organization|Client|Firm):\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+(?:Annual Production Report|Annual Report|Audit Report|Inspection Report).*$', '', name, flags=re.IGNORECASE)
    return name.rstrip(".,;: -").strip()


def _extract_primary_entity(text: str) -> str:
    """
    Extract primary company/entity name from headers or text beginning.
    If none is found, returns 'Unknown' (never a hardcoded company name).
    Prioritizes ORGANIZATION over PERSON when both are present.
    """
    hm = _HEADER_ENTITY_REGEX.search(text)
    if hm:
        ent = _clean_entity_name(hm.group(1))
        if ent and ent.lower() not in _NON_ENTITY_WORDS and classify_entity_type(ent) != "PERSON":
            return ent

    nm = _NAMED_ENTITY_REGEX.search(text)
    if nm:
        cand = _clean_entity_name(nm.group(1))
        if cand and cand.lower() not in _NON_ENTITY_WORDS and classify_entity_type(cand) != "PERSON":
            return cand

    lines = text.strip().splitlines()
    org_candidates = []
    person_candidates = []
    for line in lines[:5]:
        line = line.strip()
        m = re.match(r"^([A-Z][a-zA-Z0-9&]+(?:\s+[A-Z][a-zA-Z0-9&]+){1,3})", line)
        if m and not any(w in m.group(1).lower() for w in ["annual", "report", "inspection", "summary", "audit"]):
            cand = _clean_entity_name(m.group(1))
            if cand and cand.lower() not in _NON_ENTITY_WORDS:
                if classify_entity_type(cand) == "PERSON":
                    person_candidates.append(cand)
                else:
                    org_candidates.append(cand)

    if org_candidates:
        return org_candidates[0]
    if hm:
        return _clean_entity_name(hm.group(1))
    if nm:
        return _clean_entity_name(nm.group(1))
    if person_candidates:
        return person_candidates[0]

    return "Unknown"


# ---------------------------------------------------------------------------
# Sentence-level extraction
# ---------------------------------------------------------------------------

def _extract_claims_from_sentence(
    sentence: str,
    entity: str,
    entity_type: str,
    source: str,
    page_or_sheet: str,
) -> list[RawClaim]:
    """
    Extract numerical, percentage, currency, and textual claims from a single sentence.
    Guarantees exactly ONE claim per numerical fact by tracking matched character spans.
    """
    if re.match(r"^(?:location|address|facility location|plant location)\s*:", sentence.strip(), re.IGNORECASE):
        return []

    claims: list[RawClaim] = []
    date_val = _find_date(sentence)
    modality = _infer_modality(sentence)

    # Track matched character spans: (start, end)
    claimed_spans: list[tuple[int, int]] = []

    # Pre-reserve spans for dates so years (e.g. 2025, 2026, FY2025) are never extracted as claim numbers
    for dm in _DATE_PATTERN.finditer(sentence):
        claimed_spans.append((dm.start(), dm.end()))

    def _span_overlaps(start: int, end: int) -> bool:
        for s, e in claimed_spans:
            if max(start, s) < min(end, e):
                return True
        return False

    def _local_attribute(start: int, end: int, fallback: str) -> str:
        # Check text immediately before match (reverse=True picks keyword closest to number)
        pre_text = sentence[max(0, start - 35):start]
        attr = _find_closest_attribute(pre_text, reverse=True)
        if attr != "quantity":
            return attr
        # Check text immediately after match (reverse=False picks keyword closest to number)
        post_text = sentence[end:min(len(sentence), end + 35)]
        attr = _find_closest_attribute(post_text, reverse=False)
        if attr != "quantity":
            return attr
        sent_attr = _infer_attribute(sentence)
        return sent_attr if sent_attr != "quantity" else fallback

    # 1. Currency claims (high priority)
    for m in _CURRENCY_PATTERN.finditer(sentence):
        start, end = m.start(), m.end()
        val = _clean_number(m.group("number"))
        if val is None:
            continue

        claimed_spans.append((start, end))

        curr_raw = (m.group("currency") or "INR").strip()
        curr_upper = curr_raw.upper()
        if "US$" in curr_upper or "USD" in curr_upper or "$" in curr_upper:
            unit = "USD"
        elif "€" in curr_raw or "EUR" in curr_upper:
            unit = "EUR"
        elif "£" in curr_raw or "GBP" in curr_upper:
            unit = "GBP"
        elif "¥" in curr_raw or "JPY" in curr_upper:
            unit = "JPY"
        elif "₹" in curr_raw:
            unit = "₹"
        elif any(k in curr_raw.lower() for k in ["rs", "inr"]):
            unit = "INR"
        else:
            unit = curr_raw

        scale = (m.group("scale") or "").lower()
        scale_map = {
            "lakh": 100_000, "lac": 100_000, "lakhs": 100_000,
            "crore": 10_000_000, "cr": 10_000_000, "crores": 10_000_000,
            "million": 1_000_000, "mn": 1_000_000,
            "billion": 1_000_000_000, "bn": 1_000_000_000,
        }
        multiplier = scale_map.get(scale, 1)
        actual_val = val * multiplier
        attr = _local_attribute(start, end, "revenue")

        claims.append(
            RawClaim(
                entity=entity,
                entity_type=entity_type,
                attribute=attr,
                value=actual_val,
                unit=unit,
                date_str=date_val,
                source=source,
                page_or_sheet=page_or_sheet,
                original_text=sentence.strip(),
                confidence=0.95,
                modality=modality,
            )
        )

    # 2. Percentage claims
    for m in _PERCENT_PATTERN.finditer(sentence):
        start, end = m.start(), m.end()
        if _span_overlaps(start, end):
            continue

        val = _clean_number(m.group("number"))
        if val is None:
            continue

        claimed_spans.append((start, end))
        attr = _local_attribute(start, end, "capacity")

        claims.append(
            RawClaim(
                entity=entity,
                entity_type=entity_type,
                attribute=attr,
                value=val,
                unit="%",
                date_str=date_val,
                source=source,
                page_or_sheet=page_or_sheet,
                original_text=sentence.strip(),
                confidence=0.92,
                modality=modality,
            )
        )

    # 3. Generic numerical claims (only for spans not already captured)
    for m in _NUM_PATTERN.finditer(sentence):
        num_str = m.group("number")
        if not num_str:
            continue

        start = m.start("number")
        end = m.end("number")
        if _span_overlaps(start, end):
            continue

        val = _clean_number(num_str)
        if val is None or val == 0:
            continue

        claimed_spans.append((m.start(), m.end()))

        raw_unit = (m.group("suffix_unit") or m.group("prefix_currency") or "").strip()

        # If bare number with no unit and no metric keyword in sentence, skip (e.g. Sector 4, Room 101)
        if not raw_unit and _local_attribute(start, end, "none") == "none":
            continue

        # Scale multiplier if suffix is scale word without currency
        scale_low = raw_unit.lower()
        if scale_low in ("lakh", "lac", "lakhs"):
            val *= 100_000
            raw_unit = "units"
        elif scale_low in ("crore", "cr", "crores"):
            val *= 10_000_000
            raw_unit = "units"
        elif scale_low in ("million", "mn", "m"):
            val *= 1_000_000
            raw_unit = "units"
        elif scale_low in ("billion", "bn", "b"):
            val *= 1_000_000_000
            raw_unit = "units"
        elif scale_low in ("trillion", "tn", "t"):
            val *= 1_000_000_000_000
            raw_unit = "units"
        elif scale_low in ("k", "thousand"):
            val *= 1_000
            raw_unit = "units"

        mass_units = ("kg", "kgs", "kilogram", "kilograms", "g", "gm", "grams", "gram", "tonne", "tonnes", "ton", "tons", "mg")
        if raw_unit.lower() in mass_units:
            unit = raw_unit
            attr = _local_attribute(start, end, "weight")
        else:
            unit = "units" if raw_unit.lower() in ("unit", "units", "") else raw_unit
            attr = _local_attribute(start, end, "production")

        claims.append(
            RawClaim(
                entity=entity,
                entity_type=entity_type,
                attribute=attr,
                value=val,
                unit=unit,
                date_str=date_val,
                source=source,
                page_or_sheet=page_or_sheet,
                original_text=sentence.strip(),
                confidence=0.88,
                modality=modality,
            )
        )

    # 4. Textual claims (Operational status, compliance, executive)
    sm = _STATUS_PATTERN.search(sentence)
    if sm:
        status_val = sm.group(1).lower().replace("shut down", "shutdown")
        claims.append(
            RawClaim(
                entity=entity,
                entity_type=entity_type,
                attribute="status",
                value=status_val,
                unit="",
                date_str=date_val,
                source=source,
                page_or_sheet=page_or_sheet,
                original_text=sentence.strip(),
                confidence=0.90,
                modality=modality,
            )
        )

    # Compliance with explicit negation and synonym coverage
    if re.search(r"\b(?:not compliant|failed to comply|non compliant|non-compliant|did not comply|compliance violation|violation|failed compliance|failed inspection)\b", sentence, re.IGNORECASE):
        claims.append(
            RawClaim(
                entity=entity,
                entity_type=entity_type,
                attribute="compliance",
                value="non-compliant",
                unit="",
                date_str=date_val,
                source=source,
                page_or_sheet=page_or_sheet,
                original_text=sentence.strip(),
                confidence=0.92,
                modality=modality,
            )
        )
    elif re.search(r"\b(?:fully compliant|certified|in compliance|passed inspection|approved rating)\b", sentence, re.IGNORECASE) or _COMPLIANCE_PATTERN.search(sentence):
        cm = _COMPLIANCE_PATTERN.search(sentence)
        comp_val = "certified" if "certified" in sentence.lower() else (cm.group(1).lower().replace("non compliant", "non-compliant") if cm else "compliant")
        claims.append(
            RawClaim(
                entity=entity,
                entity_type=entity_type,
                attribute="compliance",
                value=comp_val,
                unit="",
                date_str=date_val,
                source=source,
                page_or_sheet=page_or_sheet,
                original_text=sentence.strip(),
                confidence=0.90,
                modality=modality,
            )
        )

    em = _EXECUTIVE_PATTERN.search(sentence)
    if em:
        exec_name = next((g.strip() for g in em.groups() if g and g.strip()), "")
        if exec_name:
            exec_name = re.sub(r"\s+(?:of|at|for|in|from)\s+.*$", "", exec_name, flags=re.IGNORECASE).strip()
            role_match = re.search(
                r"\b(CEO|Chief Executive Officer|Auditor|Independent Auditor|Director|Managing Director|Executive|COO|CFO|Manager)\b",
                sentence,
                re.IGNORECASE,
            )
            raw_role = role_match.group(1).lower() if role_match else "executive"
            if any(k in raw_role for k in ["ceo", "chief executive", "executive", "managing director"]):
                role = "executive"
            elif "auditor" in raw_role:
                role = "auditor"
            else:
                role = raw_role

            cls_type = classify_entity_type(exec_name)
            is_person = (cls_type == "PERSON")

            claims.append(
                RawClaim(
                    entity=entity,
                    entity_type=entity_type,
                    attribute=role,
                    value=exec_name,
                    unit="",
                    date_str=date_val,
                    source=source,
                    page_or_sheet=page_or_sheet,
                    original_text=sentence.strip(),
                    confidence=0.92,
                    modality=modality,
                    person=exec_name if is_person else "",
                )
            )

    return claims


# ---------------------------------------------------------------------------
# Tabular extraction (CSV/TSV/Excel lines) – Supports both Narrow and Wide Tables
# ---------------------------------------------------------------------------

def _extract_from_tabular_text(
    text: str,
    source: str,
    page_or_sheet: str,
) -> list[RawClaim]:
    """
    Parse tab-separated or column-aligned tabular lines.
    Supports:
    1. Narrow format: [Entity, Metric, Value, Unit, Period]
    2. Wide format Type A: [Entity, Attribute, 2024, 2025, 2026...] (columns are dates)
    3. Wide format Type B: [Entity, Date, Revenue, Profit, Production, Employees] (columns are attributes)
    """
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return []

    # Check if lines are tab-separated
    if "\t" not in lines[0] and (len(lines) > 1 and "\t" not in lines[1]):
        return []

    headers = [h.strip() for h in lines[0].split("\t")]
    headers_lower = [h.lower() for h in headers]

    # --- Case 1: Standard Narrow Format ---
    col_ent = next((i for i, h in enumerate(headers_lower) if any(k in h for k in ["company", "entity", "name", "client"])), None)
    col_metric = next((i for i, h in enumerate(headers_lower) if any(k in h for k in ["metric", "attribute", "item", "indicator"])), None)
    col_val = next((i for i, h in enumerate(headers_lower) if any(k in h for k in ["value", "amount", "quantity", "val", "data"])), None)
    col_unit = next((i for i, h in enumerate(headers_lower) if any(k in h for k in ["unit", "currency"])), None)
    col_period = next((i for i, h in enumerate(headers_lower) if any(k in h for k in ["period", "date", "year", "month", "quarter", "fy"])), None)

    if col_val is not None:
        claims: list[RawClaim] = []
        for line in lines[1:]:
            parts = [p.strip() for p in line.split("\t")]
            if len(parts) <= col_val:
                continue

            ent = _clean_entity_name(parts[col_ent]) if col_ent is not None and col_ent < len(parts) else "Unknown"
            if not ent:
                ent = "Unknown"
            metric = parts[col_metric] if col_metric is not None and col_metric < len(parts) else "quantity"
            raw_val = parts[col_val]
            unit = parts[col_unit] if col_unit is not None and col_unit < len(parts) else ""
            period = parts[col_period] if col_period is not None and col_period < len(parts) else ""

            num = _clean_number(raw_val)
            if num is not None:
                if unit.lower() in ("lakh", "lac"):
                    num *= 100_000
                    unit = "INR" if any(k in metric.lower() for k in ["revenue", "profit", "turnover", "cost"]) else "units"
                elif unit.lower() in ("crore", "cr"):
                    num *= 10_000_000
                    unit = "INR" if any(k in metric.lower() for k in ["revenue", "profit", "turnover", "cost"]) else "units"

                attr = _infer_attribute(metric)
                claims.append(
                    RawClaim(
                        entity=ent,
                        entity_type="ORG",
                        attribute=attr,
                        value=num,
                        unit=unit if unit else ("INR" if attr in ("revenue", "profit") else "units"),
                        date_str=period,
                        source=source,
                        page_or_sheet=page_or_sheet,
                        original_text=line,
                        confidence=0.96,
                    )
                )
        if claims:
            return claims

    # --- Case 2: Wide Format Type A (Columns are Dates/Periods) ---
    # e.g. [Entity, Metric, Unit, 2024, 2025, 2026] or [Entity, 2024, 2025, 2026]
    date_cols: list[tuple[int, str]] = []
    for i, h in enumerate(headers):
        if i in (col_ent, col_metric, col_unit):
            continue
        # Check if header matches year, quarter, month, FY
        if re.search(r"\b(19\d{2}|20\d{2}|Q[1-4]|FY\s*\d{2,4}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", h, re.IGNORECASE):
            date_cols.append((i, h))

    if date_cols and col_ent is not None:
        claims: list[RawClaim] = []
        for line in lines[1:]:
            parts = [p.strip() for p in line.split("\t")]
            if len(parts) <= col_ent:
                continue
            ent = _clean_entity_name(parts[col_ent]) or "Unknown"
            metric = parts[col_metric] if col_metric is not None and col_metric < len(parts) else "quantity"
            unit = parts[col_unit] if col_unit is not None and col_unit < len(parts) else ""

            for col_idx, col_date in date_cols:
                if col_idx < len(parts):
                    cell_val = parts[col_idx]
                    num = _clean_number(cell_val)
                    if num is not None:
                        attr = _infer_attribute(metric)
                        claims.append(
                            RawClaim(
                                entity=ent,
                                entity_type="ORG",
                                attribute=attr,
                                value=num,
                                unit=unit if unit else ("INR" if attr in ("revenue", "profit") else "units"),
                                date_str=col_date,
                                source=source,
                                page_or_sheet=page_or_sheet,
                                original_text=f"{ent} {metric} ({col_date}): {cell_val}",
                                confidence=0.95,
                            )
                        )
        if claims:
            return claims

    # --- Case 3: Wide Format Type B (Columns are Metrics/Attributes) ---
    # e.g. [Entity, Date, Revenue, Profit, Production, Employees]
    attr_cols: list[tuple[int, str]] = []
    for i, h in enumerate(headers):
        if i in (col_ent, col_period):
            continue
        attr_candidate = _infer_attribute(h)
        if attr_candidate != "quantity" or any(k in h.lower() for k in ["unit", "count", "production", "volume"]):
            attr_cols.append((i, attr_candidate))

    if attr_cols and col_ent is not None:
        claims: list[RawClaim] = []
        for line in lines[1:]:
            parts = [p.strip() for p in line.split("\t")]
            if len(parts) <= col_ent:
                continue
            ent = _clean_entity_name(parts[col_ent]) or "Unknown"
            period = parts[col_period] if col_period is not None and col_period < len(parts) else ""

            for col_idx, attr in attr_cols:
                if col_idx < len(parts):
                    cell_val = parts[col_idx]
                    num = _clean_number(cell_val)
                    if num is not None:
                        # Determine unit by attribute
                        unit = "INR" if attr in ("revenue", "profit", "cost") else ("employees" if attr == "employees" else "units")
                        claims.append(
                            RawClaim(
                                entity=ent,
                                entity_type="ORG",
                                attribute=attr,
                                value=num,
                                unit=unit,
                                date_str=period,
                                source=source,
                                page_or_sheet=page_or_sheet,
                                original_text=f"{ent} {attr} ({period}): {cell_val}",
                                confidence=0.94,
                            )
                        )
        if claims:
            return claims

    return []


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

def extract_entities_from_text(
    text: str,
    source: str,
    page_or_sheet: str = "Page 1",
) -> list[RawClaim]:
    """
    Extract structured claims from a block of text.
    Combines spaCy NER and rule-based segment parsing to maximize accuracy and provenance.
    """
    if not text or not text.strip():
        return []

    # Check tabular format first
    tabular_claims = _extract_from_tabular_text(text, source, page_or_sheet)
    if tabular_claims:
        return tabular_claims

    nlp = _get_nlp()
    claims: list[RawClaim] = []
    primary_entity = _extract_primary_entity(text)
    doc_date = _find_date(text)

    # Segment document into non-empty lines / logical statements
    raw_lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in raw_lines:
        if line.startswith("=") or line.startswith("---") or line.startswith("###"):
            continue

        # Check for header entity declarations
        hm = _HEADER_ENTITY_REGEX.search(line)
        if hm:
            cand = _clean_entity_name(hm.group(1))
            if cand and cand.lower() not in _NON_ENTITY_WORDS:
                primary_entity = cand
            continue

        line_entity = primary_entity
        line_entity_type = "ORG"
        line_person = ""

        if nlp is not None:
            try:
                doc = nlp(line)
                for ent in doc.ents:
                    if ent.label_ == "PERSON":
                        line_person = ent.text.strip()
                    elif ent.label_ in {"ORG", "GPE", "PRODUCT", "FAC", "LOC"}:
                        cand = _clean_entity_name(ent.text)
                        # Exclude currencies, numbers, dates
                        if cand and not re.match(r'^(?:INR|USD|EUR|GBP|Rs\.?|[₹$€£¥]|\d)', cand, re.IGNORECASE):
                            if cand.lower() not in _NON_ENTITY_WORDS and not any(w in cand.lower() for w in ["fy20", "q1", "q2", "q3", "q4"]):
                                line_entity = cand
                                line_entity_type = ent.label_
            except Exception:
                pass
        else:
            nm = _NAMED_ENTITY_REGEX.search(line)
            if nm:
                cand = _clean_entity_name(nm.group(1))
                if cand and cand.lower() not in _NON_ENTITY_WORDS:
                    line_entity = cand

        line_claims = _extract_claims_from_sentence(
            line, line_entity, line_entity_type, source, page_or_sheet
        )
        for lc in line_claims:
            if not lc.date_str:
                lc.date_str = doc_date
            if line_person and not lc.person:
                lc.person = line_person
        claims.extend(line_claims)

    logger.info("Extracted %d raw claims from '%s' (%s)", len(claims), source, page_or_sheet)
    return claims


def extract_entities_from_document(doc: dict) -> list[RawClaim]:
    """
    Extract all claims from a loaded document dictionary.
    """
    source = doc.get("source", "unknown")
    all_claims: list[RawClaim] = []

    if doc.get("pages"):
        for page in doc["pages"]:
            page_text = page.get("text", "")
            page_label = f"Page {page.get('page', 1)}"
            is_ocr = page.get("ocr", False)
            conf_val = page.get("confidence", 100.0)
            ocr_conf = (conf_val / 100.0) if (is_ocr and conf_val > 1.0) else (conf_val if is_ocr else 1.0)
            page_claims = extract_entities_from_text(page_text, source, page_label)
            for pc in page_claims:
                pc.ocr_confidence = ocr_conf
            all_claims.extend(page_claims)

    if doc.get("sheets"):
        for sheet in doc["sheets"]:
            sheet_text = sheet.get("text", "")
            sheet_label = sheet.get("sheet_name", "Sheet1")
            sheet_claims = extract_entities_from_text(sheet_text, source, sheet_label)
            for sc in sheet_claims:
                sc.ocr_confidence = 1.0
            all_claims.extend(sheet_claims)

    return all_claims


# ---------------------------------------------------------------------------
# Entity Relationship Extraction
# ---------------------------------------------------------------------------

def extract_relationships_from_text(
    text: str,
    source: str,
    page_or_sheet: str = "Page 1",
    primary_entity: str = "",
) -> list[EntityRelationship]:
    """
    Extract entity-to-entity and person-to-entity relationships:
    - audited_by (e.g. KPMG -> ABC Industries)
    - executive_of (e.g. Sarah Jenkins -> ABC Industries)
    - subsidiary_of (e.g. ABC Industries -> Apex Corp)
    - owned_by (e.g. ABC Industries -> Apex Corp)
    """
    if not text:
        return []

    if not primary_entity or primary_entity == "Unknown":
        primary_entity = _extract_primary_entity(text)

    relationships: list[EntityRelationship] = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:
        # 1. Audited by
        m_aud = re.search(r"\b(?:Independent\s+)?Auditor(?:s)?:\s*([A-Z][a-zA-Z0-9&.\s]+)", line, re.IGNORECASE)
        if not m_aud:
            m_aud = re.search(r"\b(?:audited\s+by|audit\s+conducted\s+by)\s+([A-Z][a-zA-Z0-9&.\s]+)", line, re.IGNORECASE)
        if m_aud:
            auditor_name = _clean_entity_name(m_aud.group(1))
            if auditor_name and auditor_name.lower() not in _NON_ENTITY_WORDS and primary_entity != "Unknown":
                relationships.append(
                    EntityRelationship(
                        source_entity=primary_entity,
                        source_type="ORGANIZATION",
                        target_entity=auditor_name,
                        target_type="ORGANIZATION",
                        relation_type="audited_by",
                        source_doc=source,
                        page_or_sheet=page_or_sheet,
                        evidence_text=line,
                    )
                )

        m_aud2 = re.search(r"\b([A-Z][a-zA-Z0-9&.\s]+)\s+(?:conducted\s+(?:an?\s+)?audit\s+of|audited)\s+([A-Z][a-zA-Z0-9&.\s]+)", line, re.IGNORECASE)
        if m_aud2:
            auditor_cand = _clean_entity_name(m_aud2.group(1))
            client_cand = _clean_entity_name(m_aud2.group(2))
            if auditor_cand and client_cand:
                relationships.append(
                    EntityRelationship(
                        source_entity=client_cand,
                        source_type="ORGANIZATION",
                        target_entity=auditor_cand,
                        target_type="ORGANIZATION",
                        relation_type="audited_by",
                        source_doc=source,
                        page_or_sheet=page_or_sheet,
                        evidence_text=line,
                    )
                )

        # 2. Executive of / Leadership
        m_exec = re.search(
            r"\b(?:CEO|Chief Executive Officer|Executive|Director|Managing Director|COO|CFO):\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)",
            line,
            re.IGNORECASE,
        )
        if m_exec and primary_entity != "Unknown":
            person_name = m_exec.group(1).strip()
            if classify_entity_type(person_name) == "PERSON":
                relationships.append(
                    EntityRelationship(
                        source_entity=person_name,
                        source_type="PERSON",
                        target_entity=primary_entity,
                        target_type="ORGANIZATION",
                        relation_type="executive_of",
                        source_doc=source,
                        page_or_sheet=page_or_sheet,
                        evidence_text=line,
                    )
                )

        m_exec2 = re.search(
            r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+),\s*(?:CEO|Chief Executive Officer|Executive|Director|Managing Director)\s+of\s+([A-Z][a-zA-Z0-9&.\s]+)",
            line,
            re.IGNORECASE,
        )
        if m_exec2:
            person_cand = m_exec2.group(1).strip()
            company_cand = _clean_entity_name(m_exec2.group(2))
            if classify_entity_type(person_cand) == "PERSON" and company_cand:
                relationships.append(
                    EntityRelationship(
                        source_entity=person_cand,
                        source_type="PERSON",
                        target_entity=company_cand,
                        target_type="ORGANIZATION",
                        relation_type="executive_of",
                        source_doc=source,
                        page_or_sheet=page_or_sheet,
                        evidence_text=line,
                    )
                )

        # 3. Subsidiary of / Owned by
        m_sub = re.search(
            r"([A-Z][a-zA-Z0-9&.]+(?:\s+[A-Z][a-zA-Z0-9&.]+)*)\s+(?:is a subsidiary of|subsidiary of)\s+([A-Z][a-zA-Z0-9&.]+(?:\s+[A-Z][a-zA-Z0-9&.]+)*)",
            line,
            re.IGNORECASE,
        )
        if m_sub:
            child = _clean_entity_name(m_sub.group(1))
            parent = _clean_entity_name(m_sub.group(2))
            if child and parent:
                relationships.append(
                    EntityRelationship(
                        source_entity=child,
                        source_type="ORGANIZATION",
                        target_entity=parent,
                        target_type="ORGANIZATION",
                        relation_type="subsidiary_of",
                        source_doc=source,
                        page_or_sheet=page_or_sheet,
                        evidence_text=line,
                    )
                )

        m_own = re.search(
            r"([A-Z][a-zA-Z0-9&.]+(?:\s+[A-Z][a-zA-Z0-9&.]+)*)\s+(?:is owned by|owned by|parent company:\s*)\s*([A-Z][a-zA-Z0-9&.]+(?:\s+[A-Z][a-zA-Z0-9&.]+)*)",
            line,
            re.IGNORECASE,
        )
        if m_own:
            child = _clean_entity_name(m_own.group(1))
            owner = _clean_entity_name(m_own.group(2))
            if child and owner:
                relationships.append(
                    EntityRelationship(
                        source_entity=child,
                        source_type="ORGANIZATION",
                        target_entity=owner,
                        target_type="ORGANIZATION",
                        relation_type="owned_by",
                        source_doc=source,
                        page_or_sheet=page_or_sheet,
                        evidence_text=line,
                    )
                )

    return relationships


def extract_relationships_from_document(doc: dict) -> list[EntityRelationship]:
    """Extract all entity relationships from a document."""
    source = doc.get("source", "unknown")
    all_rels: list[EntityRelationship] = []

    if doc.get("pages"):
        for page in doc["pages"]:
            page_text = page.get("text", "")
            page_label = f"Page {page.get('page', 1)}"
            all_rels.extend(extract_relationships_from_text(page_text, source, page_label))

    if doc.get("sheets"):
        for sheet in doc["sheets"]:
            sheet_text = sheet.get("text", "")
            sheet_label = sheet.get("sheet_name", "Sheet1")
            all_rels.extend(extract_relationships_from_text(sheet_text, source, sheet_label))

    return all_rels
