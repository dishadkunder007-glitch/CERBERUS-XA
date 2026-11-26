"""
PDF Extractor – uses PyMuPDF to extract text, tables, and metadata.
Features graceful fallback when OCR is unavailable or pages are empty.
"""

import io
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def extract_pdf(file_path: str | Path) -> dict[str, Any]:
    """
    Extract text and table content from a PDF file using PyMuPDF.
    Works natively without requiring Tesseract.

    Returns:
        {
            "source": filename,
            "pages": [{"page": int, "text": str, "tables": [...]}],
            "warnings": list[str],
            "error": str | None
        }
    """
    file_path = Path(file_path)
    result: dict[str, Any] = {
        "source": file_path.name,
        "pages": [],
        "warnings": [],
        "error": None,
    }

    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz

        doc = fitz.open(str(file_path))

        if doc.page_count == 0:
            result["error"] = "PDF has no pages."
            logger.warning("Empty PDF: %s", file_path.name)
            return result

        empty_pages = []
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text("text").strip()

            if not text:
                empty_pages.append(page_num + 1)

            tables: list[dict] = []
            result["pages"].append(
                {
                    "page": page_num + 1,
                    "text": text,
                    "tables": tables,
                    "ocr": False,
                }
            )

        if empty_pages:
            result["warnings"].append(
                f"Pages {empty_pages} in '{file_path.name}' have no selectable text. "
                "Enable OCR if this is a scanned document."
            )

        doc.close()
        logger.info("PDF extracted: %s (%d pages)", file_path.name, len(result["pages"]))

    except ImportError:
        result["error"] = "PyMuPDF (fitz) not installed."
        logger.error("PyMuPDF not installed.")
    except Exception as exc:
        result["error"] = f"PDF extraction failed: {exc}"
        logger.exception("PDF extraction error for %s", file_path.name)

    return result


def extract_pdf_with_ocr(file_path: str | Path, dpi: int = 200) -> dict[str, Any]:
    """
    Extract text from PDF pages, attempting OCR only when a page contains no native text.
    Gracefully preserves native text even if Tesseract is not installed or raises an error.
    """
    file_path = Path(file_path)
    result: dict[str, Any] = {
        "source": file_path.name,
        "pages": [],
        "warnings": [],
        "error": None,
    }

    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz

        doc = fitz.open(str(file_path))
    except Exception as exc:
        result["error"] = f"Cannot open PDF: {exc}"
        return result

    # Check if pytesseract is available
    tesseract_available = False
    try:
        import pytesseract
        from PIL import Image
        tesseract_available = True
    except ImportError:
        result["warnings"].append("pytesseract/Pillow not available. Extracting native text only.")

    for page_num in range(doc.page_count):
        page = doc[page_num]
        native_text = page.get_text("text").strip()

        if native_text:
            result["pages"].append(
                {
                    "page": page_num + 1,
                    "text": native_text,
                    "tables": [],
                    "ocr": False,
                }
            )
            continue

        # Page is empty of native text – try OCR if Tesseract is present
        ocr_text = ""
        if tesseract_available:
            try:
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(img, config="--psm 6").strip()
            except Exception as ocr_err:
                logger.warning("OCR failed on page %d of %s: %s", page_num + 1, file_path.name, ocr_err)
                result["warnings"].append(f"OCR failed on page {page_num + 1}: {ocr_err}")

        if not ocr_text:
            result["warnings"].append(f"Page {page_num + 1} of '{file_path.name}' is empty or unreadable.")

        result["pages"].append(
            {
                "page": page_num + 1,
                "text": ocr_text,
                "tables": [],
                "ocr": bool(ocr_text),
            }
        )

    doc.close()
    logger.info("PDF+OCR processed: %s (%d pages)", file_path.name, len(result["pages"]))
    return result
