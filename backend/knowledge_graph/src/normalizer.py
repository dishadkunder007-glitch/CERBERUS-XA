"""
Normalizer – unit conversion, dimension canonicalization, value normalization,
and temporal interval parsing.

Handles:
- Indian number scale words (lakh, crore) and currency symbols (INR, ₹, Rs)
- Dimensional unit canonicalization (mass: g, length: m, volume: mL, currency: INR/USD/EUR/GBP, percentage: %, count: units)
- kg/g, tonne/g, km/m, L/mL standard conversions
- ISO date normalization (months, quarters, financial years, calendar years)
- Interval-based temporal overlap verification
"""

import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Unit and Dimension Mappings
# ---------------------------------------------------------------------------

UNIT_ALIASES: dict[str, str] = {
    # Currency
    "₹": "INR", "rs": "INR", "rs.": "INR", "inr": "INR", "rupee": "INR", "rupees": "INR",
    "$": "USD", "usd": "USD", "dollar": "USD", "dollars": "USD",
    "€": "EUR", "eur": "EUR", "euro": "EUR", "euros": "EUR",
    "£": "GBP", "gbp": "GBP", "pound": "GBP", "pounds": "GBP",
    # Weight / Mass
    "kg": "kg", "kilogram": "kg", "kilograms": "kg", "kgs": "kg",
    "g": "g", "gram": "g", "grams": "g", "gm": "g", "gms": "g",
    "mg": "mg", "milligram": "mg", "milligrams": "mg",
    "ton": "tonne", "tons": "tonne", "tonne": "tonne", "tonnes": "tonne",
    "metric ton": "tonne", "metric tons": "tonne",
    "lb": "lb", "lbs": "lb", "pound_mass": "lb",
    # Length
    "km": "km", "kilometer": "km", "kilometre": "km", "kilometres": "km", "kilometers": "km",
    "m": "m", "meter": "m", "metre": "m", "meters": "m", "metres": "m",
    "cm": "cm", "centimeter": "cm", "centimetre": "cm",
    "mm": "mm", "millimeter": "mm",
    "mi": "mi", "mile": "mi", "miles": "mi",
    "ft": "ft", "foot": "ft", "feet": "ft",
    "inch": "inch", "inches": "inch",
    # Volume
    "litre": "L", "liter": "L", "l": "L", "litres": "L", "liters": "L",
    "ml": "mL", "millilitre": "mL", "milliliter": "mL",
    # Count
    "unit": "units", "units": "units",
    "piece": "units", "pieces": "units", "pcs": "units",
    "item": "units", "items": "units",
    "employees": "employees", "workers": "employees", "staff": "employees",
    "persons": "employees", "headcount": "employees",
    # Percentage
    "%": "%", "percent": "%", "percentage": "%", "pct": "%",
    # Scale words
    "lakh": "lakh", "lac": "lakh", "lakhs": "lakh",
    "crore": "crore", "cr": "crore", "crores": "crore",
    "million": "million", "mn": "million",
    "billion": "billion", "bn": "billion",
}

# Base conversion factors to canonical SI / domain base unit
WEIGHT_TO_GRAMS: dict[str, float] = {
    "mg": 0.001,
    "g": 1.0,
    "kg": 1_000.0,
    "tonne": 1_000_000.0,
    "lb": 453.59237,
}

LENGTH_TO_METERS: dict[str, float] = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "km": 1_000.0,
    "inch": 0.0254,
    "ft": 0.3048,
    "mi": 1_609.344,
}

VOLUME_TO_ML: dict[str, float] = {
    "mL": 1.0,
    "L": 1_000.0,
}

SCALE_MULTIPLIERS: dict[str, float] = {
    "lakh": 100_000.0,
    "lac": 100_000.0,
    "crore": 10_000_000.0,
    "cr": 10_000_000.0,
    "million": 1_000_000.0,
    "billion": 1_000_000_000.0,
}


def normalize_unit(unit: str) -> str:
    """Return the normalized alias of a unit."""
    if not unit:
        return ""
    clean = unit.lower().strip()
    return UNIT_ALIASES.get(clean, clean)


def get_unit_dimension(unit: str) -> str:
    """
    Return the physical or economic dimension of a unit.
    Returns: 'mass', 'length', 'volume', 'currency_INR', 'currency_USD', etc.,
             'percentage', 'count', or 'unknown'
    """
    norm = normalize_unit(unit)
    if norm in WEIGHT_TO_GRAMS:
        return "mass"
    if norm in LENGTH_TO_METERS:
        return "length"
    if norm in VOLUME_TO_ML:
        return "volume"
    if norm == "INR":
        return "currency_INR"
    if norm == "USD":
        return "currency_USD"
    if norm == "EUR":
        return "currency_EUR"
    if norm == "GBP":
        return "currency_GBP"
    if norm == "%":
        return "percentage"
    if norm in ("units", "employees"):
        return norm
    return "count"


def get_canonical_unit(unit: str) -> str:
    """
    Return the canonical base unit for dimensional comparisons.
    For example:
      'kg', 'g', 'tonne' -> 'g'
      'km', 'm', 'cm'    -> 'm'
      'L', 'mL'          -> 'mL'
      '₹', 'INR', 'Rs'   -> 'INR'
      '%'                -> '%'
    """
    dimension = get_unit_dimension(unit)
    if dimension == "mass":
        return "g"
    if dimension == "length":
        return "m"
    if dimension == "volume":
        return "mL"
    if dimension.startswith("currency_"):
        return dimension.split("_", 1)[1]
    if dimension == "percentage":
        return "%"
    if dimension == "employees":
        return "employees"
    return "units"


def normalize_value(
    value: any,
    raw_unit: str = "",
    normalized_unit: str = "",
) -> Tuple[Optional[float], bool]:
    """
    Convert a value to its dimensionally normalized base float.

    Returns:
        (normalized_float, comparable)
    """
    if value is None:
        return None, False

    if isinstance(value, str):
        # Attempt to parse numeric string
        clean_str = value.replace(",", "").strip()
        try:
            fval = float(clean_str)
        except ValueError:
            return None, False
    else:
        try:
            fval = float(value)
        except (TypeError, ValueError):
            return None, False

    unit_low = (raw_unit or "").lower().strip()
    norm_u = normalize_unit(normalized_unit or raw_unit)

    # Scale words (lakh, crore, million, billion)
    multiplier = SCALE_MULTIPLIERS.get(unit_low, 1.0)
    fval *= multiplier

    # Mass to grams
    if norm_u in WEIGHT_TO_GRAMS:
        fval *= WEIGHT_TO_GRAMS[norm_u]
        return fval, True

    # Length to meters
    if norm_u in LENGTH_TO_METERS:
        fval *= LENGTH_TO_METERS[norm_u]
        return fval, True

    # Volume to mL
    if norm_u in VOLUME_TO_ML:
        fval *= VOLUME_TO_ML[norm_u]
        return fval, True

    return fval, True


# ---------------------------------------------------------------------------
# Temporal Interval Normalization and Overlap
# ---------------------------------------------------------------------------

MONTH_MAP = {
    "january": "01", "jan": "01",
    "february": "02", "feb": "02",
    "march": "03", "mar": "03",
    "april": "04", "apr": "04",
    "may": "05",
    "june": "06", "jun": "06",
    "july": "07", "jul": "07",
    "august": "08", "aug": "08",
    "september": "09", "sep": "09", "sept": "09",
    "october": "10", "oct": "10",
    "november": "11", "nov": "11",
    "december": "12", "dec": "12",
}

QUARTER_MONTHS = {
    "Q1": ("01", "03"),
    "Q2": ("04", "06"),
    "Q3": ("07", "09"),
    "Q4": ("10", "12"),
}


def normalize_date(date_str: str) -> str:
    """
    Normalize raw date string into canonical format:
    - Month: "2026-01"
    - Quarter: "2026-Q1"
    - Financial Year: "FY2025-26" or "FY2025"
    - Calendar Year: "2026"
    - Full Date: "2026-01-15"
    """
    if not date_str:
        return ""

    s = date_str.strip()

    # "January 2026" or "Jan 2026"
    m = re.match(r"([A-Za-z]+)\s+(\d{4})", s)
    if m:
        month_name = m.group(1).lower()
        year = m.group(2)
        if month_name in MONTH_MAP:
            return f"{year}-{MONTH_MAP[month_name]}"

    # "Q1 2026" or "2026 Q1" or "2026-Q1"
    m = re.match(r"(?:(Q[1-4])\s*[-/]?\s*(\d{4})|(\d{4})\s*[-/]?\s*(Q[1-4]))", s, re.IGNORECASE)
    if m:
        q = (m.group(1) or m.group(4)).upper()
        yr = m.group(2) or m.group(3)
        return f"{yr}-{q}"

    # Financial Year: "FY 2025-26", "FY2025-2026", "FY25-26", "FY2025", "FY25"
    m = re.match(r"^FY\s*(\d{2,4})(?:\s*[-/]\s*(\d{2,4}))?$", s, re.IGNORECASE)
    if m:
        start_yr = m.group(1)
        if len(start_yr) == 2:
            start_yr = "20" + start_yr
        end_yr = m.group(2)
        if end_yr:
            if len(end_yr) == 4:
                end_yr = end_yr[-2:]
            return f"FY{start_yr}-{end_yr}"
        return f"FY{start_yr}"

    # ISO "2026-01-15" or "2026/01/15"
    m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", s)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"

    # Day-first "15/01/2026" or "15-01-2026"
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", s)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"

    # Standalone 4-digit year: "2026"
    m = re.match(r"^(\d{4})$", s)
    if m:
        return m.group(1)

    return s


def _date_to_interval(norm_date: str) -> Optional[Tuple[str, str]]:
    """
    Map a normalized date string to an inclusive string interval (YYYY-MM-DD, YYYY-MM-DD).
    Returns None if date cannot be strictly parsed into an interval.
    """
    if not norm_date:
        return None

    # Full date: 2026-01-15
    if re.match(r"^\d{4}-\d{2}-\d{2}$", norm_date):
        return (norm_date, norm_date)

    # Month: 2026-01
    m = re.match(r"^(\d{4})-(\d{2})$", norm_date)
    if m:
        yr, mo = m.group(1), m.group(2)
        # 31 is safe upper bound for interval comparison
        return (f"{yr}-{mo}-01", f"{yr}-{mo}-31")

    # Quarter: 2026-Q1
    m = re.match(r"^(\d{4})-(Q[1-4])$", norm_date)
    if m:
        yr, q = m.group(1), m.group(2)
        start_mo, end_mo = QUARTER_MONTHS.get(q, ("01", "12"))
        return (f"{yr}-{start_mo}-01", f"{yr}-{end_mo}-31")

    # Financial year: FY2025-26 (Runs April 1, 2025 to March 31, 2026)
    m = re.match(r"^FY(\d{4})-(\d{2})$", norm_date)
    if m:
        start_yr = m.group(1)
        end_yr = str(int(start_yr) + 1)
        return (f"{start_yr}-04-01", f"{end_yr}-03-31")

    # Single financial year: FY2025
    m = re.match(r"^FY(\d{4})$", norm_date)
    if m:
        start_yr = m.group(1)
        end_yr = str(int(start_yr) + 1)
        return (f"{start_yr}-04-01", f"{end_yr}-03-31")

    # Calendar Year: 2026
    m = re.match(r"^(\d{4})$", norm_date)
    if m:
        yr = m.group(1)
        return (f"{yr}-01-01", f"{yr}-12-31")

    return None


def dates_overlap(date_a: str, date_b: str) -> bool:
    """
    Determine if two date representations refer to overlapping time periods.
    Uses exact date-interval intersections.
    If either date is unknown or cannot be strictly mapped, conservatively assumes True.
    """
    if not date_a or not date_b:
        return True

    norm_a = normalize_date(date_a)
    norm_b = normalize_date(date_b)

    if norm_a == norm_b:
        return True

    int_a = _date_to_interval(norm_a)
    int_b = _date_to_interval(norm_b)

    if int_a is not None and int_b is not None:
        start_a, end_a = int_a
        start_b, end_b = int_b
        # Two intervals [s_a, e_a] and [s_b, e_b] overlap iff s_a <= e_b and s_b <= e_a
        return (start_a <= end_b) and (start_b <= end_a)

    # Fallback heuristics for non-standard formats
    year_a = re.search(r"\b(19\d{2}|20\d{2})\b", date_a)
    year_b = re.search(r"\b(19\d{2}|20\d{2})\b", date_b)
    if year_a and year_b and year_a.group(1) != year_b.group(1):
        # Definitively different years
        return False

    return True
