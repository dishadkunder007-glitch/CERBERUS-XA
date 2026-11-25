"""
CERBERUS-XA Multimodal Data Processing Module
Standardized evidence extraction from PDF, Images (JPG, PNG, JPEG), Excel, and CSV.
"""

from .models import ContentItem, StandardExtractionResult, BatchExtractionResult
from .processor import process_file_data, process_file_path
from .pdf_processor import process_pdf
from .image_processor import process_image
from .table_processor import process_excel, process_csv
from .ocr_engine import is_ocr_available, is_tesseract_available, perform_ocr, get_active_ocr_engine_name

__all__ = [
    "ContentItem",
    "StandardExtractionResult",
    "BatchExtractionResult",
    "process_file_data",
    "process_file_path",
    "process_pdf",
    "process_image",
    "process_excel",
    "process_csv",
    "is_ocr_available",
    "is_tesseract_available",
    "perform_ocr",
    "get_active_ocr_engine_name",
]
