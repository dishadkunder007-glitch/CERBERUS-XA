"""
Verify BOTH:
1. Conflict files (invoice 500 units + inventory 500 + delivery note 450 units) -> detects REAL 500 vs 450 conflict!
2. Non-conflict files (invoice 500 + inventory 500, OR Laptop X 16 GB PDF + 16 GB PNG) -> detects 0 conflicts (ANSWERED)!
"""

import io
import requests
import pymupdf
from PIL import Image, ImageDraw

BASE = "http://localhost:8000"


def make_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_textbox(pymupdf.Rect(50, 50, 545, 750), text)
    b = doc.tobytes()
    doc.close()
    return b


def make_png(text: str) -> bytes:
    img = Image.new("RGB", (900, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main():
    print("=== 1. CONFLICT SCENARIO (500 vs 450 on Part P-4471) ===")
    requests.post(f"{BASE}/reset")
    inv_pdf = make_pdf(
        "INVOICE INV-8812\n"
        "Supplier: Apex Aero Parts\n"
        "Bill to: Bengaluru Aerospace Works, BLR-01\n"
        "Date shipped: 12 Nov 2026\n"
        "P-4471 Actuator bracket: 500 units\n"
    )
    inv_csv = (
        "row,part,qty_received,date,warehouse\n"
        "3317,P-4102,120,2026-11-12,BLR-01\n"
        "3318,P-4471,500,2026-11-12,BLR-01\n"
        "3319,P-4533,60,2026-11-12,BLR-01\n"
    ).encode("utf-8")
    deliv_png = make_png(
        "DELIVERY NOTE\n"
        "Part P-4471 received: 450 units\n"
        "Date: 12/11/2026\n"
        "Warehouse: BLR-01\n"
    )

    requests.post(f"{BASE}/process-file", files={"file": ("invoice_8812.pdf", io.BytesIO(inv_pdf), "application/pdf")})
    requests.post(f"{BASE}/process-file", files={"file": ("inventory.csv", io.BytesIO(inv_csv), "text/csv")})
    requests.post(f"{BASE}/process-file", files={"file": ("delivery_note.png", io.BytesIO(deliv_png), "image/png")})

    confs = requests.get(f"{BASE}/conflicts").json()
    print("GET /conflicts count:", len(confs))
    for c in confs:
        print(" ", c.get("entity"), "|", c.get("attribute"), "|", c.get("values"))

    res1 = requests.post(f"{BASE}/investigate", json={
        "question": "How many units of part P-4471 were actually received on 12 Nov 2026?"
    }).json()
    print("AI Verdict:", res1.get("verdict"), "->", res1.get("finalVerdict"), "| Conf:", res1.get("confidence"))
    print("Contradicting items:", len(res1.get("contradictingEvidence", [])))
    print("Summary:", res1.get("summaryAnswer"))
    assert res1.get("verdict") == "CONFLICTED", f"Expected CONFLICTED, got {res1.get('verdict')}"
    assert len(res1.get("contradictingEvidence", [])) > 0, "Expected contradictingEvidence > 0"

    print("\n=== 2. NON-CONFLICT SCENARIO (Laptop X 16 GB PDF + 16 GB PNG) ===")
    requests.post(f"{BASE}/reset")
    spec_pdf = make_pdf(
        "LAPTOP X\nTechnical Specification Sheet\nNot a real product document.\n"
        "Model: Laptop X LX-16\nInstalled memory: 16 GB DDR5\n"
    )
    tech_png = make_png(
        "INSPECTION REPORT\n"
        "Device inspected is Laptop X (LX-16)\n"
        "Conclusion: The inspected unit has 16 GB RAM.\n"
    )
    requests.post(f"{BASE}/process-file", files={"file": ("01_manufacturer_spec_sheet.pdf", io.BytesIO(spec_pdf), "application/pdf")})
    requests.post(f"{BASE}/process-file", files={"file": ("scanned_technician_report.png", io.BytesIO(tech_png), "image/png")})

    confs2 = requests.get(f"{BASE}/conflicts").json()
    print("GET /conflicts count:", len(confs2))
    res2 = requests.post(f"{BASE}/investigate", json={
        "question": "What is the actual RAM capacity of Laptop X?"
    }).json()
    print("AI Verdict:", res2.get("verdict"), "->", res2.get("finalVerdict"), "| Conf:", res2.get("confidence"))
    print("Contradicting items:", len(res2.get("contradictingEvidence", [])))
    print("Summary:", res2.get("summaryAnswer"))
    assert res2.get("verdict") in ("ANSWERED", "PARTIALLY_ANSWERED"), f"Expected ANSWERED, got {res2.get('verdict')}"
    assert len(res2.get("contradictingEvidence", [])) == 0, "Expected 0 contradictingEvidence"
    assert len(confs2) == 0, f"Expected 0 conflicts, got {confs2}"

    requests.post(f"{BASE}/reset")
    print("\nBOTH CONFLICT AND NON-CONFLICT SCENARIOS PASSED 100%!")


if __name__ == "__main__":
    main()
