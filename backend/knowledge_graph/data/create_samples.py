"""
Sample data generator – creates CSV and Excel sample files with
consistent and contradictory data for testing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def create_sample_excel():
    """Create a sample Excel file with contradictory production data."""
    try:
        import openpyxl
    except ImportError:
        print("openpyxl not installed – skipping Excel sample creation.")
        return

    out_dir = Path(__file__).parent.parent / "data" / "sample_docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Production Report"

    ws.append(["Company", "Metric", "Value", "Unit", "Period"])
    ws.append(["ABC Industries", "production", 4000, "units", "January 2026"])
    ws.append(["ABC Industries", "revenue", 2000000, "INR", "January 2026"])
    ws.append(["ABC Industries", "employees", 440, "persons", "January 2026"])
    ws.append(["XYZ Corporation", "production", 8000, "units", "January 2026"])

    # Second sheet – consistent data
    ws2 = wb.create_sheet("Q4 2025")
    ws2.append(["Company", "Metric", "Value", "Unit", "Period"])
    ws2.append(["ABC Industries", "production", 4800, "units", "December 2025"])
    ws2.append(["ABC Industries", "revenue", 2400000, "INR", "December 2025"])

    path = out_dir / "erp_excel.xlsx"
    wb.save(str(path))
    print(f"Excel sample created: {path}")


if __name__ == "__main__":
    create_sample_excel()
    print("Sample data generation complete.")
