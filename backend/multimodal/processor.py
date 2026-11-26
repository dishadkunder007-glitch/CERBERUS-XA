import os
import time
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any

from .models import StandardExtractionResult, ContentItem
from .config import SUPPORTED_EXTENSIONS
from .pdf_processor import process_pdf
from .image_processor import process_image
from .table_processor import process_excel, process_csv

logger = logging.getLogger("multimodal_processor")

def process_file_data(file_bytes: bytes, filename: str) -> StandardExtractionResult:
    """
    Main dispatch function for the multimodal processor.
    Accepts raw file bytes and original filename, detects the file type,
    invokes the appropriate specialized extractor, and returns a standardized JSON structure.
    """
    start_time = time.time()
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        return StandardExtractionResult(
            source=filename,
            source_type="unknown",
            content=[],
            metadata={
                "filename": filename,
                "format": ext.lstrip("."),
                "error": f"Unsupported file format: '{ext}'. Supported formats: {list(SUPPORTED_EXTENSIONS.keys())}",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

    category = SUPPORTED_EXTENSIONS[ext]

    if ext == ".pdf":
        return process_pdf(file_bytes, filename=filename)
    elif ext in [".jpg", ".jpeg", ".png"]:
        return process_image(file_bytes, filename=filename)
    elif ext in [".xlsx", ".xls"]:
        return process_excel(file_bytes, filename=filename)
    elif ext == ".csv":
        return process_csv(file_bytes, filename=filename)
    else:
        return StandardExtractionResult(
            source=filename,
            source_type=category,
            content=[],
            metadata={
                "filename": filename,
                "format": ext.lstrip("."),
                "error": "Unhandled file extension",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

def process_file_path(file_path: Union[str, Path]) -> StandardExtractionResult:
    """Reads a file from the filesystem and processes it."""
    path = Path(file_path)
    if not path.exists():
        return StandardExtractionResult(
            source=path.name,
            source_type="unknown",
            content=[],
            metadata={
                "filename": path.name,
                "error": f"File not found: {str(path)}"
            }
        )

    try:
        data = path.read_bytes()
        return process_file_data(data, filename=path.name)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return StandardExtractionResult(
            source=path.name,
            source_type="unknown",
            content=[],
            metadata={
                "filename": path.name,
                "error": f"Could not read file: {str(e)}"
            }
        )
