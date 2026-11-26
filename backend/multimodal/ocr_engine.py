import os
import shutil
import logging
from typing import Tuple, List, Dict, Optional, Any
import numpy as np
import cv2
from PIL import Image

from .config import TESSERACT_CMD, MAX_IMAGE_DIMENSION

logger = logging.getLogger("multimodal_processor.ocr")

_RAPID_OCR_INSTANCE: Optional[Any] = None
_RAPID_OCR_INITIALIZED: bool = False
_TESSERACT_AVAILABLE: Optional[bool] = None

# Configure pytesseract binary if detected or configured
try:
    import pytesseract
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
except ImportError:
    pytesseract = None


def get_rapid_ocr_engine() -> Optional[Any]:
    """Initializes and returns cached RapidOCR instance if available."""
    global _RAPID_OCR_INSTANCE, _RAPID_OCR_INITIALIZED
    if _RAPID_OCR_INITIALIZED:
        return _RAPID_OCR_INSTANCE

    try:
        from rapidocr_onnxruntime import RapidOCR
        _RAPID_OCR_INSTANCE = RapidOCR()
        _RAPID_OCR_INITIALIZED = True
        logger.info("RapidOCR (PaddleOCR ONNX engine) initialized successfully.")
        return _RAPID_OCR_INSTANCE
    except Exception as e:
        logger.warning(f"Failed to initialize RapidOCR: {e}")
        _RAPID_OCR_INSTANCE = None
        _RAPID_OCR_INITIALIZED = True
        return None


def is_tesseract_available() -> bool:
    """Check if external tesseract binary is actually accessible and executable."""
    global _TESSERACT_AVAILABLE
    if _TESSERACT_AVAILABLE is not None:
        return _TESSERACT_AVAILABLE

    if pytesseract is None:
        _TESSERACT_AVAILABLE = False
        return False

    cmd = pytesseract.pytesseract.tesseract_cmd
    if cmd and os.path.isabs(cmd):
        if not os.path.exists(cmd):
            _TESSERACT_AVAILABLE = False
            return False
    else:
        if not shutil.which(cmd or "tesseract"):
            _TESSERACT_AVAILABLE = False
            return False

    try:
        pytesseract.get_tesseract_version()
        _TESSERACT_AVAILABLE = True
    except Exception:
        _TESSERACT_AVAILABLE = False

    return _TESSERACT_AVAILABLE


def is_ocr_available() -> bool:
    """Returns True if any production-ready local OCR engine (RapidOCR or Tesseract) is ready."""
    if get_rapid_ocr_engine() is not None:
        return True
    return is_tesseract_available()


def get_active_ocr_engine_name() -> str:
    """Returns the identifier of the active local OCR backend."""
    if get_rapid_ocr_engine() is not None:
        return "RapidOCR (PaddleOCR ONNX)"
    elif is_tesseract_available():
        return "Tesseract OCR"
    return "None (Unavailable)"


def preprocess_image_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Optimized OpenCV image preprocessing for fast and accurate OCR:
    1. Resize down if excessively large to keep processing < 0.5s
    2. Convert to Grayscale
    3. Gaussian blur to reduce noise
    4. Adaptive/Otsu thresholding for crisp character segmentation
    """
    if image is None or image.size == 0:
        return image

    h, w = image.shape[:2]
    if max(h, w) > MAX_IMAGE_DIMENSION:
        scale = MAX_IMAGE_DIMENSION / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    if len(image.shape) == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif len(image.shape) == 3 and image.shape[2] == 4:
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:
        gray = image.copy()

    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def perform_ocr(image_input: Any) -> Tuple[str, Optional[float], List[Dict[str, Any]]]:
    """
    Performs OCR on an image (PIL Image, numpy array, or raw bytes).
    Prioritizes high-accuracy RapidOCR ONNX, falling back to Tesseract OCR if configured.
    Returns:
        (extracted_text, average_confidence, word_level_data)
    """
    if not is_ocr_available():
        logger.warning("No OCR engine is available on the system.")
        return "", None, []

    # 1. Convert input to BGR numpy array
    cv_img: Optional[np.ndarray] = None
    try:
        if isinstance(image_input, Image.Image):
            cv_img = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            cv_img = image_input
        elif isinstance(image_input, (bytes, bytearray)):
            nparr = np.frombuffer(image_input, np.uint8)
            cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        if cv_img is None or cv_img.size == 0:
            return "", None, []
    except Exception as conv_err:
        logger.error(f"Failed to prepare image for OCR: {conv_err}")
        return "", None, []

    # 2. Try RapidOCR (PaddleOCR ONNX) first
    rapid_engine = get_rapid_ocr_engine()
    if rapid_engine is not None:
        try:
            ocr_result, _ = rapid_engine(cv_img)
            if not ocr_result:
                # Retry with preprocessed image if initial direct pass detected nothing
                preprocessed = preprocess_image_for_ocr(cv_img)
                ocr_result, _ = rapid_engine(preprocessed)

            if ocr_result:
                lines = []
                confidences = []
                details = []
                for box, text_content, score in ocr_result:
                    cleaned_text = str(text_content).strip()
                    if cleaned_text:
                        lines.append(cleaned_text)
                        conf = float(score)
                        confidences.append(conf)
                        details.append({
                            "text": cleaned_text,
                            "confidence": round(conf, 4),
                            "box": box
                        })

                full_text = "\n".join(lines)
                avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else None
                return full_text, avg_confidence, details
            return "", None, []
        except Exception as rapid_err:
            logger.warning(f"RapidOCR execution encountered an error: {rapid_err}. Falling back to Tesseract...")

    # 3. Fallback to Tesseract OCR if RapidOCR did not succeed
    if is_tesseract_available() and pytesseract is not None:
        try:
            processed = preprocess_image_for_ocr(cv_img)
            data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)

            extracted_words = []
            confidences = []
            word_details = []

            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text = data["text"][i].strip()
                conf = float(data["conf"][i])
                if text and conf >= 0:
                    extracted_words.append(text)
                    confidences.append(conf)
                    word_details.append({
                        "text": text,
                        "confidence": round(conf / 100.0, 4),
                        "left": data["left"][i],
                        "top": data["top"][i],
                        "width": data["width"][i],
                        "height": data["height"][i]
                    })

            full_text = " ".join(extracted_words)
            avg_confidence = round(sum(confidences) / (len(confidences) * 100.0), 4) if confidences else None
            return full_text, avg_confidence, word_details
        except Exception as tess_err:
            logger.error(f"Tesseract OCR fallback failed: {tess_err}")

    return "", None, []
