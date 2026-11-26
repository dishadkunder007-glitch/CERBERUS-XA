import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Configurable Tesseract path (can be overridden via TESSERACT_CMD env var)
TESSERACT_CMD = os.getenv("TESSERACT_CMD", None)
if not TESSERACT_CMD:
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract"
    ]
    for p in possible_paths:
        expanded = os.path.expandvars(p)
        if os.path.exists(expanded):
            TESSERACT_CMD = expanded
            break

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    ".pdf": "document",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".xlsx": "table",
    ".xls": "table",
    ".csv": "table"
}

# OCR configuration
OCR_MIN_TEXT_LENGTH_PER_PAGE = 30  # If page text < this and images exist, consider scanned
DEFAULT_OCR_TIMEOUT = 10  # Seconds
MAX_IMAGE_DIMENSION = 2000  # Resize large images for ultra-fast processing
