"""
Document Loader – unified entry point for all file types.
Routes each file to the appropriate extractor and returns a normalized structure.
"""

import logging
from pathlib import Path
from typing import Any

from .pdf_extractor import extract_pdf, extract_pdf_with_ocr
from .image_extractor import extract_image
from .excel_extractor import extract_excel
from .csv_extractor import extract_csv
from .txt_extractor import extract_txt

logger = logging.getLogger(__name__)

# Mapping: extension -> extractor function
EXTRACTOR_MAP = {
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".tif": "image",
    ".xlsx": "excel",
    ".xls": "excel",
    ".csv": "csv",
    ".txt": "txt",
}


def load_document(file_path: str | Path, use_ocr_for_pdf: bool = True) -> dict[str, Any]:
    """
    Load a document from the given path.

    Returns a unified structure:
    {
        "source": str,
        "type": str,
        "pages": [...] or None,       # for page-based formats
        "sheets": [...] or None,      # for tabular formats
        "error": str | None,
        "full_text": str              # combined text across all pages/sheets
    }
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return {
            "source": file_path.name,
            "type": "unknown",
            "pages": None,
            "sheets": None,
            "error": f"File not found: {file_path}",
            "full_text": "",
        }

    ext = file_path.suffix.lower()
    file_type = EXTRACTOR_MAP.get(ext, "unknown")

    if file_type == "unknown":
        return {
            "source": file_path.name,
            "type": "unknown",
            "pages": None,
            "sheets": None,
            "error": f"Unsupported file type: {ext}",
            "full_text": "",
        }

    raw: dict[str, Any] = {}

    try:
        if file_type == "pdf":
            if use_ocr_for_pdf:
                raw = extract_pdf_with_ocr(file_path)
            else:
                raw = extract_pdf(file_path)
        elif file_type == "image":
            raw = extract_image(file_path)
            # Images come back in page format
        elif file_type == "excel":
            raw = extract_excel(file_path)
        elif file_type == "csv":
            raw = extract_csv(file_path)
        elif file_type == "txt":
            raw = extract_txt(file_path)
    except Exception as exc:
        logger.exception("Unexpected error loading %s", file_path.name)
        return {
            "source": file_path.name,
            "type": file_type,
            "pages": None,
            "sheets": None,
            "error": str(exc),
            "full_text": "",
        }

    # Normalise to unified structure
    pages = raw.get("pages")
    sheets = raw.get("sheets")

    # Build full_text
    full_text_parts: list[str] = []
    if pages:
        for p in pages:
            if p.get("text"):
                full_text_parts.append(p["text"])
    if sheets:
        for s in sheets:
            if s.get("text"):
                full_text_parts.append(s["text"])

    return {
        "source": raw.get("source", file_path.name),
        "type": file_type,
        "pages": pages,
        "sheets": sheets,
        "warnings": raw.get("warnings", []),
        "error": raw.get("error"),
        "full_text": "\n".join(full_text_parts),
    }


def load_multiple_documents(
    file_paths: list[str | Path], use_ocr_for_pdf: bool = True
) -> list[dict[str, Any]]:
    """Load multiple documents and return a list of unified document structures."""
    results = []
    for fp in file_paths:
        doc = load_document(fp, use_ocr_for_pdf=use_ocr_for_pdf)
        results.append(doc)
        if doc["error"]:
            logger.warning("Error loading %s: %s", fp, doc["error"])
    return results
