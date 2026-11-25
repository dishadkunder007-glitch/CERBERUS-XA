"""
Text Extractor – reads plain text (.txt) files.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def extract_txt(file_path: str | Path) -> dict[str, Any]:
    """
    Extract text from a plain text file.

    Returns:
        {
            "source": filename,
            "pages": [{"page": 1, "text": str, "tables": []}],
            "error": str | None
        }
    """
    file_path = Path(file_path)
    result: dict[str, Any] = {
        "source": file_path.name,
        "pages": [],
        "error": None,
    }

    try:
        text = None
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                text = file_path.read_text(encoding=enc)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            result["error"] = "Could not decode text file."
            return result

        if not text.strip():
            result["error"] = "Text file is empty."
            logger.warning("Empty TXT: %s", file_path.name)
            return result

        result["pages"].append({"page": 1, "text": text.strip(), "tables": []})
        logger.info("TXT extracted: %s", file_path.name)

    except Exception as exc:
        result["error"] = f"TXT extraction failed: {exc}"
        logger.exception("TXT extraction error for %s", file_path.name)

    return result
