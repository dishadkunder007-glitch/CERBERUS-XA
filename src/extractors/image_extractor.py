"""
Image Extractor – uses Pillow and pytesseract for advanced OCR on image documents.

Features:
- Image upscaling (bicubic interpolation for small or low-DPI images)
- Grayscale conversion
- Contrast enhancement and Otsu-like thresholding
- Multi-PSM fallback (PSM 6 -> PSM 3 -> PSM 11)
- Word-level OCR confidence score aggregation
- Explicit empty extraction warnings
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def _preprocess_image(img: Any) -> Any:
    """Preprocess image for optimal Tesseract OCR performance."""
    from PIL import Image, ImageEnhance, ImageFilter

    # Convert to RGB first if palette or RGBA
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Upscale if dimensions are small
    w, h = img.size
    if w < 1200 or h < 1200:
        scale = max(2, int(1500 / max(w, h, 1)))
        img = img.resize((w * scale, h * scale), resample=Image.Resampling.BICUBIC)

    # Grayscale
    gray = img.convert("L")

    # Contrast enhancement
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(1.8)

    # Sharpness enhancement
    sharpener = ImageEnhance.Sharpness(enhanced)
    sharpened = sharpener.enhance(1.5)

    # Adaptive binarization threshold
    threshold = 140
    binary = sharpened.point(lambda p: 255 if p > threshold else 0)

    return binary


def extract_image(file_path: str | Path) -> dict[str, Any]:
    """
    Extract text from an image file using enhanced pytesseract OCR with multiple PSM fallbacks.

    Returns:
        {
            "source": filename,
            "pages": [{"page": 1, "text": str, "tables": [], "ocr": True, "confidence": float}],
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

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        result["error"] = f"Unsupported image format: {file_path.suffix}"
        logger.warning("Unsupported image format: %s", file_path.suffix)
        return result

    try:
        import pytesseract
        from PIL import Image

        raw_img = Image.open(str(file_path))
        processed_img = _preprocess_image(raw_img)

        # Multi-PSM fallback list: 6 (single uniform block), 3 (fully automatic), 11 (sparse text)
        psm_modes = ["--oem 3 --psm 6", "--oem 3 --psm 3", "--oem 3 --psm 11"]
        best_text = ""
        best_conf = 0.0

        for config in psm_modes:
            try:
                # Attempt to get word data and confidence
                data = pytesseract.image_to_data(processed_img, config=config, output_type=pytesseract.Output.DICT)
                confs = [float(c) for c in data.get("conf", []) if str(c).replace("-1", "").strip()]
                avg_conf = (sum(confs) / len(confs)) if confs else 0.0
                text = " ".join([w for w in data.get("text", []) if w.strip()])

                if len(text.strip()) > len(best_text.strip()):
                    best_text = text.strip()
                    best_conf = avg_conf

                if len(best_text) > 20 and best_conf > 50:
                    break
            except Exception:
                # Direct string fallback
                try:
                    text = pytesseract.image_to_string(processed_img, config=config).strip()
                    if len(text) > len(best_text):
                        best_text = text
                except Exception:
                    pass

        # If processed image yielded no text, try raw original image directly
        if not best_text.strip():
            try:
                best_text = pytesseract.image_to_string(raw_img).strip()
            except Exception:
                pass

        if not best_text.strip():
            result["warnings"].append(f"OCR returned empty or unreadable text for image '{file_path.name}'.")
            logger.warning("Empty OCR output for image: %s", file_path.name)

        result["pages"].append(
            {
                "page": 1,
                "text": best_text,
                "tables": [],
                "ocr": True,
                "confidence": round(best_conf, 2),
            }
        )

        logger.info("Image OCR completed: %s (length=%d, conf=%.1f)", file_path.name, len(best_text), best_conf)

    except ImportError as exc:
        result["error"] = f"Required library not installed: {exc}"
        logger.error("Missing library for image OCR: %s", exc)
    except Exception as exc:
        # Check if tesseract binary is missing from PATH
        if "tesseract is not installed" in str(exc).lower():
            result["warnings"].append(f"Tesseract OCR executable not detected in system PATH. Cannot OCR '{file_path.name}'.")
            result["error"] = "Tesseract OCR binary not found in system PATH."
        else:
            result["error"] = f"Image OCR extraction failed: {exc}"
        logger.exception("Image OCR error for %s", file_path.name)

    return result
