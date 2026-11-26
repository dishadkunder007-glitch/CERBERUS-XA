import io
import time
import re
import datetime
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from .models import ContentItem, StandardExtractionResult
from .utils import extract_metric_from_text, deduplicate_content_items, COMMON_UNITS

logger = logging.getLogger("multimodal_processor.table")

def _parse_header_unit(header: str) -> tuple[str, Optional[str]]:
    """Extracts unit from column header, e.g. 'Revenue ($)' -> ('Revenue', '$')"""
    h_clean = str(header).strip()
    match = re.search(r"^(.*?)\s*[\(\[]([^\)\]]+)[\)\]]$", h_clean)
    if match:
        name = match.group(1).strip()
        candidate = match.group(2).strip().lower()
        if candidate in COMMON_UNITS or any(candidate.startswith(u) for u in COMMON_UNITS):
            return name, candidate
    return h_clean, None

def _format_cell_value(cell_val: Any) -> str:
    """Formats cell values handling whole numbers, dates, timestamps, and floats cleanly."""
    if cell_val is None or pd.isna(cell_val):
        return ""
    # Dates and timestamps
    if isinstance(cell_val, (pd.Timestamp, datetime.datetime)):
        if cell_val.hour == 0 and cell_val.minute == 0 and cell_val.second == 0:
            return cell_val.strftime("%Y-%m-%d")
        return cell_val.isoformat()
    if isinstance(cell_val, datetime.date):
        return cell_val.isoformat()
    # Floats that are actually whole numbers (e.g. 250.0 -> 250)
    if isinstance(cell_val, (float, np.floating)):
        if cell_val.is_integer():
            return str(int(cell_val))
        return str(round(cell_val, 6)).rstrip("0").rstrip(".") if "." in str(cell_val) else str(cell_val)
    return str(cell_val).strip()

def process_excel(
    file_bytes: bytes,
    filename: str = "spreadsheet.xlsx"
) -> StandardExtractionResult:
    """
    Extracts structured tabular data from XLSX and XLS files using Pandas & OpenPyXL/xlrd.
    Safely handles password-protected files, preserves sheet names, columns, rows, and units.
    """
    start_time = time.time()
    content_items: List[ContentItem] = []
    warnings: List[str] = []
    sheet_names: List[str] = []

    ext = filename.lower().split(".")[-1] if "." in filename else "xlsx"

    if not file_bytes or len(file_bytes) == 0:
        return StandardExtractionResult(
            source=filename,
            source_type="table",
            content=[],
            metadata={
                "filename": filename,
                "format": ext,
                "error": "Empty spreadsheet file",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

    try:
        engine = "openpyxl" if ext == "xlsx" else "xlrd"
        excel_file = pd.ExcelFile(io.BytesIO(file_bytes), engine=engine)
        sheet_names = excel_file.sheet_names
    except Exception as e:
        err_str = str(e)
        logger.error(f"Failed to read Excel file {filename}: {err_str}")
        error_msg = f"Invalid or corrupted Excel file: {err_str}"
        if "password" in err_str.lower() or "encrypt" in err_str.lower():
            error_msg = "Password-protected or encrypted Excel spreadsheet"
        return StandardExtractionResult(
            source=filename,
            source_type="table",
            content=[],
            metadata={
                "filename": filename,
                "format": ext,
                "error": error_msg,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

    for sheet_name in sheet_names:
        try:
            df = excel_file.parse(sheet_name=sheet_name)
            if df.empty or len(df.columns) == 0:
                continue

            # Drop completely empty rows and columns to eliminate noise
            df = df.dropna(how="all").dropna(axis=1, how="all")
            if df.empty:
                continue

            # Clean and normalize column names
            clean_columns = []
            for col_i, col in enumerate(df.columns):
                c_str = str(col).strip()
                if c_str.startswith("Unnamed:") or not c_str:
                    c_str = f"Column_{col_i + 1}"
                clean_columns.append(c_str)
            df.columns = clean_columns

            for row_idx, row in df.iterrows():
                row_num = row_idx + 1

                for col_name in df.columns:
                    cell_val = row[col_name]
                    if pd.isna(cell_val) or cell_val is None or str(cell_val).strip() == "":
                        continue

                    raw_str = _format_cell_value(cell_val)
                    if not raw_str:
                        continue

                    clean_col, header_unit = _parse_header_unit(col_name)

                    final_claim = clean_col
                    final_unit = header_unit
                    final_value = raw_str

                    if not final_unit:
                        _, extracted_val, extracted_unit = extract_metric_from_text(raw_str)
                        if extracted_unit:
                            final_unit = extracted_unit
                            final_value = extracted_val if extracted_val is not None else raw_str

                    content_items.append(
                        ContentItem(
                            claim=final_claim,
                            value=final_value,
                            unit=final_unit,
                            page=None,
                            sheet=sheet_name,
                            row=row_num,
                            column=clean_col,
                            confidence=None
                        )
                    )
        except Exception as sheet_err:
            warnings.append(f"Sheet '{sheet_name}' processing failed: {str(sheet_err)}")

    content_items = deduplicate_content_items(content_items)
    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    metadata: Dict[str, Any] = {
        "filename": filename,
        "format": ext,
        "file_size_bytes": len(file_bytes),
        "sheets": sheet_names,
        "total_sheets": len(sheet_names),
        "items_extracted": len(content_items),
        "processing_time_ms": elapsed_ms
    }
    if warnings:
        metadata["warnings"] = warnings

    return StandardExtractionResult(
        source=filename,
        source_type="table",
        content=content_items,
        metadata=metadata
    )

def process_csv(
    file_bytes: bytes,
    filename: str = "data.csv"
) -> StandardExtractionResult:
    """
    Extracts structured tabular data from CSV files using Pandas.
    Handles multiple encodings, delimiter variations (, ; \t |), quoted text, and missing values.
    """
    start_time = time.time()
    content_items: List[ContentItem] = []
    warnings: List[str] = []

    if not file_bytes or len(file_bytes) == 0:
        return StandardExtractionResult(
            source=filename,
            source_type="table",
            content=[],
            metadata={
                "filename": filename,
                "format": "csv",
                "error": "Empty CSV file",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

    encodings_to_try = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1", "utf-16"]
    delimiters_to_try = [None, ",", ";", "\t", "|"]
    df = None
    detected_encoding = None

    for enc in encodings_to_try:
        for delim in delimiters_to_try:
            try:
                if delim is None:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc, sep=None, engine="python", on_bad_lines="skip")
                else:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc, sep=delim, on_bad_lines="skip")
                if df is not None and not df.empty:
                    detected_encoding = enc
                    break
            except Exception:
                continue
        if df is not None and not df.empty:
            break

    # If still none, try fallback basic parse
    if df is None:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1", on_bad_lines="skip")
            detected_encoding = "latin1"
        except Exception as final_e:
            logger.error(f"Failed to decode CSV {filename}: {final_e}")
            return StandardExtractionResult(
                source=filename,
                source_type="table",
                content=[],
                metadata={
                    "filename": filename,
                    "format": "csv",
                    "error": f"Could not parse CSV: {str(final_e)}",
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2)
                }
            )

    # Clean empty rows and columns
    df = df.dropna(how="all").dropna(axis=1, how="all")
    if df.empty:
        return StandardExtractionResult(
            source=filename,
            source_type="table",
            content=[],
            metadata={
                "filename": filename,
                "format": "csv",
                "encoding": detected_encoding,
                "total_rows": 0,
                "total_columns": 0,
                "items_extracted": 0,
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        )

    clean_columns = []
    for col_i, col in enumerate(df.columns):
        c_str = str(col).strip()
        if c_str.startswith("Unnamed:") or not c_str:
            c_str = f"Column_{col_i + 1}"
        clean_columns.append(c_str)
    df.columns = clean_columns

    for row_idx, row in df.iterrows():
        row_num = row_idx + 1

        for col_name in df.columns:
            cell_val = row[col_name]
            if pd.isna(cell_val) or cell_val is None or str(cell_val).strip() == "":
                continue

            raw_str = _format_cell_value(cell_val)
            if not raw_str:
                continue

            clean_col, header_unit = _parse_header_unit(col_name)

            final_claim = clean_col
            final_unit = header_unit
            final_value = raw_str

            if not final_unit:
                _, extracted_val, extracted_unit = extract_metric_from_text(raw_str)
                if extracted_unit:
                    final_unit = extracted_unit
                    final_value = extracted_val if extracted_val is not None else raw_str

            content_items.append(
                ContentItem(
                    claim=final_claim,
                    value=final_value,
                    unit=final_unit,
                    page=None,
                    sheet=None,
                    row=row_num,
                    column=clean_col,
                    confidence=None
                )
            )

    content_items = deduplicate_content_items(content_items)
    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    metadata: Dict[str, Any] = {
        "filename": filename,
        "format": "csv",
        "file_size_bytes": len(file_bytes),
        "encoding": detected_encoding,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "items_extracted": len(content_items),
        "processing_time_ms": elapsed_ms
    }

    return StandardExtractionResult(
        source=filename,
        source_type="table",
        content=content_items,
        metadata=metadata
    )
