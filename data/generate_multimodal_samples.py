"""
Generates rich multimodal test files for contradiction detection:
- PDF (via ReportLab)
- PNG image (via Pillow)
- Excel XLSX (via OpenPyXL)
- CSV (via standard csv)
- TXT (audit report)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import openpyxl

SAMPLE_DIR = Path(__file__).parent / "sample_docs"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

def generate_pdf():
    pdf_path = SAMPLE_DIR / "sample_report.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Monthly Operations Summary - January 2026")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 710, "Organization: ABC Industries")
    c.drawString(50, 680, "Production quantity: 5,000 units manufactured in January 2026.")
    c.drawString(50, 650, "Total monthly revenue: INR 25,00,000 recorded for January 2026.")
    c.drawString(50, 620, "Workforce count: 450 employees on active payroll.")
    c.drawString(50, 590, "Plant operating capacity utilization: 92% across all shifts.")
    c.drawString(50, 550, "Prepared by: Sarah Jenkins, Chief Operations Officer")
    c.save()
    print(f"Generated PDF: {pdf_path}")

def generate_png():
    img_path = SAMPLE_DIR / "sample_chart_receipt.png"
    # Create white canvas with text
    img = Image.new("RGB", (700, 450), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Header
    draw.rectangle([0, 0, 700, 60], fill=(24, 43, 73))
    draw.text((20, 18), "ABC Industries - Plant Floor OCR Log", fill=(255, 255, 255))
    
    # Data rows
    y = 90
    draw.text((30, y), "Company: ABC Industries Ltd.", fill=(0, 0, 0))
    y += 40
    draw.text((30, y), "Reporting Month: January 2026", fill=(0, 0, 0))
    y += 40
    draw.text((30, y), "Actual Production Output: 3,000 units", fill=(180, 0, 0))
    y += 40
    draw.text((30, y), "Gross Monthly Revenue: INR 18,00,000", fill=(0, 0, 0))
    y += 40
    draw.text((30, y), "Floor Staff Count: 410 employees", fill=(0, 0, 0))
    y += 40
    draw.text((30, y), "Capacity Utilization: 65%", fill=(0, 0, 0))
    
    img.save(str(img_path))
    print(f"Generated PNG: {img_path}")

def generate_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ERP Jan 2026"
    ws.append(["Entity", "Attribute", "Value", "Unit", "Period"])
    ws.append(["ABC Industries", "production", 4000, "units", "January 2026"])
    ws.append(["ABC Industries", "revenue", 2000000, "INR", "January 2026"])
    ws.append(["ABC Industries", "employees", 440, "employees", "January 2026"])
    ws.append(["ABC Industries", "capacity", 85, "%", "January 2026"])
    
    xlsx_path = SAMPLE_DIR / "erp_production.xlsx"
    wb.save(str(xlsx_path))
    print(f"Generated Excel: {xlsx_path}")

def generate_csv():
    csv_path = SAMPLE_DIR / "erp_warehouse.csv"
    content = (
        "Entity,Attribute,Value,Unit,Period\n"
        "ABC Industries,production,4500,units,January 2026\n"
        "ABC Industries,revenue,2200000,INR,January 2026\n"
        "ABC Industries,employees,430,employees,January 2026\n"
        "ABC Industries,capacity,88,%,January 2026\n"
    )
    csv_path.write_text(content, encoding="utf-8")
    print(f"Generated CSV: {csv_path}")

def generate_txt():
    txt_path = SAMPLE_DIR / "external_audit.txt"
    content = (
        "EXTERNAL AUDIT REPORT\n"
        "Date: January 2026\n"
        "Entity: ABC Industries Manufacturing Plant\n"
        "\n"
        "Audit Findings:\n"
        "- Total production verified at 5,000 units during January 2026.\n"
        "- Verified revenue of INR 25,00,000 for the period.\n"
        "- Verified active headcount of 450 employees.\n"
        "- Plant operational capacity confirmed at 92%.\n"
        "\n"
        "Auditor: KPMG Verification Services\n"
    )
    txt_path.write_text(content, encoding="utf-8")
    print(f"Generated TXT: {txt_path}")

if __name__ == "__main__":
    generate_pdf()
    generate_png()
    generate_excel()
    generate_csv()
    generate_txt()
    print("All multimodal sample files created successfully!")
