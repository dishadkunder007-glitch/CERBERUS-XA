"""
CSV Extractor – uses pandas to extract data from CSV files.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def extract_csv(file_path: str | Path) -> dict[str, Any]:
    """
    Extract data from a CSV file.

    Returns:
        {
            "source": filename,
            "sheets": [{"sheet_name": "Sheet1", "text": str, "rows": [[...]]}],
            "error": str | None
        }
    """
    file_path = Path(file_path)
    result: dict[str, Any] = {
        "source": file_path.name,
        "sheets": [],
        "error": None,
    }

    try:
        import pandas as pd

        # Try multiple encodings
        df = None
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                df = pd.read_csv(str(file_path), encoding=enc, on_bad_lines="warn")
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            result["error"] = "Could not decode CSV with common encodings."
            return result

        if df.empty:
            result["error"] = "CSV file is empty."
            logger.warning("Empty CSV: %s", file_path.name)
            return result

        rows = [list(df.columns)] + df.values.tolist()
        text_lines = ["\t".join(str(c) for c in row) for row in rows]

        result["sheets"].append(
            {
                "sheet_name": "Sheet1",
                "text": "\n".join(text_lines),
                "rows": rows,
            }
        )

        logger.info("CSV extracted: %s (%d rows)", file_path.name, len(df))

    except ImportError:
        result["error"] = "pandas not installed."
        logger.error("pandas not installed.")
    except Exception as exc:
        result["error"] = f"CSV extraction failed: {exc}"
        logger.exception("CSV extraction error for %s", file_path.name)

    return result
