import os
import io
import time
import logging
from typing import List, Dict, Any, Optional
import pymupdf as fitz  # PyMuPDF
from PIL import Image

from .models import ContentItem, StandardExtractionResult
from .ocr_engine import perform_ocr, is_ocr_available
from .utils import extract_metric_from_text, split_into_sentences, deduplicate_content_items
from .config import OCR_MIN_TEXT_LENGTH_PER_PAGE

logger = logging.getLogger("multimodal_processor.pdf")

def process_pdf(
    file_bytes: bytes,
    filename: str = "document.pdf",
    force_ocr: bool = False
) -> StandardExtractionResult:
    """
    Extracts structured evidence claims from PDF documents using PyMuPDF.
    Handles digitally generated PDFs, scanned PDFs, paragraphs, and embedded tables.
    Maintains page-level traceability and zero hallucination.
    """
    start_time = time.time()
    content_items: List[ContentItem] = []
    warnings: List[str] = []
    is_scanned_doc = False
    ocr_applied = False
    total_pages = 0

    if not file_bytes or len(file_bytes) == 0:
        return StandardExtractionResult(
            source=filename,
            source_type="document",
            content=[],
            metadata={
                "filename": filename,
                "format": "pdf",
                "error": "Empty file provided",
                "total_pages": 0,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        logger.error(f"Failed to open PDF {filename}: {str(e)}")
        return StandardExtractionResult(
            source=filename,
            source_type="document",
            content=[],
            metadata={
                "filename": filename,
                "format": "pdf",
                "error": f"Corrupted or invalid PDF: {str(e)}",
                "total_pages": 0,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

    # Check for encrypted or password-protected PDF
    if doc.is_encrypted:
        if not doc.authenticate(""):
            doc.close()
            return StandardExtractionResult(
                source=filename,
                source_type="document",
                content=[],
                metadata={
                    "filename": filename,
                    "format": "pdf",
                    "error": "Password-protected or encrypted PDF",
                    "total_pages": 0,
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2)
                }
            )

    total_pages = len(doc)
    if total_pages == 0:
        doc.close()
        return StandardExtractionResult(
            source=filename,
            source_type="document",
            content=[],
            metadata={
                "filename": filename,
                "format": "pdf",
                "total_pages": 0,
                "warning": "PDF has 0 pages",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

    for page_idx in range(total_pages):
        page_num = page_idx + 1
        page = doc[page_idx]

        # 1. Native text extraction via structured blocks in reading order
        blocks = page.get_text("blocks")
        sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
        page_paragraphs: List[str] = []

        for b in sorted_blocks:
            if b[6] == 0:  # Text block
                block_text = b[4].strip()
                if not block_text:
                    continue
                # Unify wrapped lines within the paragraph
                lines = [l.strip() for l in block_text.split("\n") if l.strip()]
                joined_lines = []
                for l in lines:
                    if joined_lines and joined_lines[-1].endswith("-"):
                        joined_lines[-1] = joined_lines[-1][:-1] + l
                    else:
                        joined_lines.append(l)
                paragraph = " ".join(joined_lines)
                page_paragraphs.append(paragraph)

        raw_text = "\n".join(page_paragraphs)
        page_images = page.get_images()

        # Check if page is scanned/image-only
        page_is_scanned = (
            force_ocr or
            (len(raw_text) < OCR_MIN_TEXT_LENGTH_PER_PAGE and len(page_images) > 0) or
            (len(raw_text) == 0)
        )

        page_confidence = None

        if page_is_scanned:
            is_scanned_doc = True
            if is_ocr_available():
                try:
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    ocr_text, conf, _ = perform_ocr(img_bytes)
                    if ocr_text.strip():
                        raw_text = ocr_text.strip()
                        page_confidence = conf
                        ocr_applied = True
                except Exception as ocr_err:
                    warnings.append(f"Page {page_num} OCR failed: {str(ocr_err)}")
            else:
                warnings.append(
                    f"Page {page_num} appears scanned, but no OCR engine is available on the system."
                )

        # 2. Extract structured sentences and claims from paragraph text
        sentences = split_into_sentences(raw_text)
        for sentence in sentences:
            claim, val, unit = extract_metric_from_text(sentence)
            if claim and len(claim.strip()) > 0:
                content_items.append(
                    ContentItem(
                        claim=claim,
                        value=val,
                        unit=unit,
                        page=page_num,
                        sheet=None,
                        row=None,
                        column=None,
                        confidence=page_confidence
                    )
                )

        # 3. Check for native tables in the page
        try:
            if hasattr(page, "find_tables"):
                tables = page.find_tables()
                for table in (tables or []):
                    table_data = table.extract()
                    if table_data and len(table_data) > 1:
                        headers = [str(h).strip() if h is not None else f"Col_{i+1}" for i, h in enumerate(table_data[0])]
                        for row_i, row in enumerate(table_data[1:]):
                            for col_i, cell in enumerate(row):
                                if cell is not None and str(cell).strip():
                                    col_name = headers[col_i] if col_i < len(headers) else f"Col_{col_i+1}"
                                    c_val = str(cell).strip()
                                    t_claim, t_val, t_unit = extract_metric_from_text(c_val)
                                    content_items.append(
                                        ContentItem(
                                            claim=col_name,
                                            value=t_val if t_val is not None else c_val,
                                            unit=t_unit,
                                            page=page_num,
                                            sheet=None,
                                            row=row_i + 1,
                                            column=col_name,
                                            confidence=page_confidence
                                        )
                                    )
        except Exception as tab_err:
            logger.debug(f"Table parsing skipped on page {page_num}: {tab_err}")

    doc.close()
    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    # Deduplicate items while maintaining order
    content_items = deduplicate_content_items(content_items)

    metadata: Dict[str, Any] = {
        "filename": filename,
        "format": "pdf",
        "file_size_bytes": len(file_bytes),
        "total_pages": total_pages,
        "is_scanned": is_scanned_doc,
        "ocr_applied": ocr_applied,
        "items_extracted": len(content_items),
        "processing_time_ms": elapsed_ms
    }
    if warnings:
        metadata["warnings"] = warnings

    return StandardExtractionResult(
        source=filename,
        source_type="document",
        content=content_items,
        metadata=metadata
    )
