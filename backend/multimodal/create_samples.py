import os
from pathlib import Path
import pymupdf as fitz  # PyMuPDF
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

def generate_samples(target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Standard text PDF
    pdf_path = target_dir / "sample_report.pdf"
    doc = fitz.open()
    # Page 1
    p1 = doc.new_page()
    p1.insert_text((50, 72), "CERBERUS-XA Project Status Report", fontsize=16)
    p1.insert_text((50, 110), "Production quantity: 5000 units", fontsize=12)
    p1.insert_text((50, 140), "Target delivery date was confirmed for Q3.", fontsize=12)
    p1.insert_text((50, 170), "Battery capacity: 4500 mAh", fontsize=12)
    # Page 2
    p2 = doc.new_page()
    p2.insert_text((50, 72), "Financial and Thermal Metrics", fontsize=16)
    p2.insert_text((50, 110), "Operating temperature reached 85 °C", fontsize=12)
    p2.insert_text((50, 140), "Revenue: $1200000", fontsize=12)
    p2.insert_text((50, 170), "System error rate: 0.05 %", fontsize=12)
    doc.save(str(pdf_path))
    doc.close()
    print(f"Created {pdf_path}")

    # 2. Image files (PNG, JPG & JPEG)
    img_path_png = target_dir / "sample_chart.png"
    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), "CERBERUS Sensor Telemetry", fill=(0, 0, 0))
    draw.text((30, 90), "Maximum speed: 120 km", fill=(0, 0, 0))
    draw.text((30, 140), "Peak power: 850 W", fill=(0, 0, 0))
    draw.text((30, 190), "Inspection status: Approved", fill=(0, 0, 0))
    img.save(str(img_path_png), "PNG")
    print(f"Created {img_path_png}")

    img_path_jpg = target_dir / "sample_receipt.jpg"
    img.save(str(img_path_jpg), "JPEG")
    print(f"Created {img_path_jpg}")

    img_path_jpeg = target_dir / "sample_photo.jpeg"
    img.save(str(img_path_jpeg), "JPEG")
    print(f"Created {img_path_jpeg}")

    # 3. Scanned PDF (Pure image inside PDF, no text stream)
    scanned_pdf_path = target_dir / "sample_scanned.pdf"
    scanned_doc = fitz.open()
    sp = scanned_doc.new_page(width=600, height=300)
    sp.insert_image(fitz.Rect(0, 0, 600, 300), filename=str(img_path_png))
    scanned_doc.save(str(scanned_pdf_path))
    scanned_doc.close()
    print(f"Created {scanned_pdf_path}")

    # 4. Excel files (.xlsx and legacy .xls)
    xlsx_path = target_dir / "sample_metrics.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df1 = pd.DataFrame([
            {"Component": "Turbine Alpha", "Power Output (kW)": "450", "Efficiency (%)": "92.5", "Status": "Optimal"},
            {"Component": "Turbine Beta", "Power Output (kW)": "480", "Efficiency (%)": "94.1", "Status": "Maintenance"},
            {"Component": "Cooling System", "Power Output (kW)": "50", "Efficiency (%)": None, "Status": "Operational"}
        ])
        df1.to_excel(writer, sheet_name="Turbine_Performance", index=False)

        df2 = pd.DataFrame([
            {"Quarter": "Q1", "Operating Expense ($)": "150000", "Headcount": "45"},
            {"Quarter": "Q2", "Operating Expense ($)": "175000", "Headcount": "48"}
        ])
        df2.to_excel(writer, sheet_name="Financial_Summary", index=False)
    print(f"Created {xlsx_path}")

    # Legacy XLS file (.xls)
    try:
        import xlwt
        xls_path = target_dir / "sample_legacy.xls"
        wb = xlwt.Workbook()
        ws = wb.add_sheet("Factory_Output")
        headers = ["Machine", "Capacity (units)", "Pressure (bar)", "Status"]
        for c, h in enumerate(headers):
            ws.write(0, c, h)
        ws.write(1, 0, "Hydraulic Press A")
        ws.write(1, 1, 1200)
        ws.write(1, 2, 8.5)
        ws.write(1, 3, "Active")
        ws.write(2, 0, "CNC Lathe B")
        ws.write(2, 1, 450)
        ws.write(2, 2, 4.2)
        ws.write(2, 3, "Standby")
        wb.save(str(xls_path))
        print(f"Created {xls_path}")
    except Exception as e:
        print(f"Could not generate sample_legacy.xls: {e}")

    # 5. CSV files (normal with missing values, and malformed)
    csv_path = target_dir / "sample_inventory.csv"
    csv_content = """Item ID,Item Name,Quantity (units),Unit Cost ($),Condition
ITEM-001,High Pressure Valve,250,45.50,New
ITEM-002,Hydraulic Pump,35,820.00,Certified
ITEM-003,Filter Cartridge,,12.00,
ITEM-004,Pressure Sensor,120,65.00,New
"""
    csv_path.write_text(csv_content, encoding="utf-8")
    print(f"Created {csv_path}")

    malformed_csv_path = target_dir / "sample_malformed.csv"
    malformed_content = """ColA,ColB,ColC
1,2,3
4,5,6,extra_broken_column_data
7,8,9
"""
    malformed_csv_path.write_text(malformed_content, encoding="utf-8")
    print(f"Created {malformed_csv_path}")

if __name__ == "__main__":
    generate_samples(Path(__file__).resolve().parent / "samples")
