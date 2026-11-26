import io
import time
import logging
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from PIL import Image, ImageOps

from .models import ContentItem, StandardExtractionResult
from .ocr_engine import perform_ocr, is_ocr_available
from .utils import extract_metric_from_text, split_into_sentences, deduplicate_content_items

logger = logging.getLogger("multimodal_processor.image")

def process_image(
    file_bytes: bytes,
    filename: str = "image.png"
) -> StandardExtractionResult:
    """
    Extracts structured text and evidence claims from JPG, JPEG, and PNG images.
    Corrects EXIF orientation, applies OpenCV preprocessing, runs local OCR,
    and returns standardized JSON claims with confidence scores.
    """
    start_time = time.time()
    content_items: List[ContentItem] = []
    warnings: List[str] = []

    ext = filename.lower().split(".")[-1] if "." in filename else "png"

    if not file_bytes or len(file_bytes) == 0:
        return StandardExtractionResult(
            source=filename,
            source_type="image",
            content=[],
            metadata={
                "filename": filename,
                "format": ext,
                "error": "Empty image file",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

    # Decode image with EXIF orientation correction
    img: Optional[np.ndarray] = None
    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        # Correct orientation based on EXIF tags (e.g. smartphone photos)
        pil_img = ImageOps.exif_transpose(pil_img)
        img = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)
    except Exception as e_pil:
        logger.debug(f"PIL decode/orientation failed, attempting cv2 decode: {e_pil}")
        try:
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e_cv:
            logger.error(f"Failed to decode image {filename}: {e_cv}")

    if img is None or img.size == 0:
        return StandardExtractionResult(
            source=filename,
            source_type="image",
            content=[],
            metadata={
                "filename": filename,
                "format": ext,
                "error": "Corrupted, unreadable, or invalid image format",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

    h, w = img.shape[:2]
    avg_conf = None
    ocr_applied = False

    if is_ocr_available():
        try:
            raw_text, avg_conf, word_boxes = perform_ocr(img)
            ocr_applied = True

            # Build a lookup for line-level confidence if available
            box_conf_map = {}
            for box_item in word_boxes:
                b_text = box_item.get("text", "").strip()
                if b_text:
                    box_conf_map[b_text] = box_item.get("confidence", avg_conf)

            sentences = split_into_sentences(raw_text)
            for sentence in sentences:
                claim, val, unit = extract_metric_from_text(sentence)
                if claim and len(claim.strip()) > 0:
                    # Match confidence to line if possible, otherwise use document average
                    conf = box_conf_map.get(sentence, avg_conf)
                    content_items.append(
                        ContentItem(
                            claim=claim,
                            value=val,
                            unit=unit,
                            page=None,
                            sheet=None,
                            row=None,
                            column=None,
                            confidence=conf
                        )
                    )
        except Exception as ocr_err:
            warnings.append(f"Image OCR failed: {str(ocr_err)}")
    else:
        warnings.append("No OCR engine is installed or available; cannot extract text from image.")

    content_items = deduplicate_content_items(content_items)
    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    metadata: Dict[str, Any] = {
        "filename": filename,
        "format": ext,
        "file_size_bytes": len(file_bytes),
        "dimensions": {"width": w, "height": h},
        "ocr_applied": ocr_applied,
        "overall_confidence": avg_conf,
        "items_extracted": len(content_items),
        "processing_time_ms": elapsed_ms
    }
    if warnings:
        metadata["warnings"] = warnings

    return StandardExtractionResult(
        source=filename,
        source_type="image",
        content=content_items,
        metadata=metadata
    )
