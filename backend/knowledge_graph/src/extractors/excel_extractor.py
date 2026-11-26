"""
Excel Extractor – uses openpyxl to extract data from XLSX files.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def extract_excel(file_path: str | Path) -> dict[str, Any]:
    """
    Extract data from all sheets of an Excel (.xlsx) file.

    Returns:
        {
            "source": filename,
            "sheets": [
                {
                    "sheet_name": str,
                    "text": str,       # human-readable dump
                    "rows": [[...]]    # raw row data
                }
            ],
            "error": str | None
        }
    """
    file_path = Path(file_path)
    result: dict[str, Any] = {
        "source": file_path.name,
        "sheets": [],
        "error": None,
    }

    try:
        import openpyxl

        wb = openpyxl.load_workbook(str(file_path), read_only=True, data_only=True)

        if not wb.sheetnames:
            result["error"] = "Excel file has no sheets."
            logger.warning("Empty Excel file: %s", file_path.name)
            return result

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows: list[list[Any]] = []
            text_lines: list[str] = []

            for row in ws.iter_rows(values_only=True):
                # Filter out completely empty rows
                non_empty = [cell for cell in row if cell is not None]
                if not non_empty:
                    continue
                rows.append(list(row))
                text_lines.append(
                    "\t".join(str(cell) if cell is not None else "" for cell in row)
                )

            result["sheets"].append(
                {
                    "sheet_name": sheet_name,
                    "text": "\n".join(text_lines),
                    "rows": rows,
                }
            )

        wb.close()
        logger.info(
            "Excel extracted: %s (%d sheets)", file_path.name, len(result["sheets"])
        )

    except ImportError:
        result["error"] = "openpyxl not installed."
        logger.error("openpyxl not installed.")
    except Exception as exc:
        result["error"] = f"Excel extraction failed: {exc}"
        logger.exception("Excel extraction error for %s", file_path.name)

    return result
