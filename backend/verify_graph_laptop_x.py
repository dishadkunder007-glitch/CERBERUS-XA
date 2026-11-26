"""
Verify Knowledge Graph construction & API response for the 2-file Laptop X fixture:
1. Manufacturer specification PDF
2. Scanned technician report (PNG via RapidOCR)
"""

import io
import json
import requests
import pymupdf
from PIL import Image, ImageDraw

BASE = "http://localhost:8000"


def test_laptop_x_graph():
    # 1. Empty state must return empty graph (no fabricated data)
    requests.post(f"{BASE}/reset")
    g_empty = requests.get(f"{BASE}/graph").json()
    assert g_empty == {"nodes": [], "links": []}, f"Expected empty graph, got {g_empty}"
    print("1. Empty backend graph check: PASS (0 nodes, 0 links)")

    # 2. Build Manufacturer Spec PDF
    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_textbox(
        pymupdf.Rect(50, 50, 545, 750),
        "LAPTOP X\nTechnical Specification Sheet\nNot a real product document.\n"
        "Model: Laptop X LX-16\nInstalled memory: 16 GB DDR5\n",
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    # 3. Build Scanned Technician Report PNG
    img = Image.new("RGB", (900, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text(
        (30, 40),
        "INSPECTION REPORT\n"
        "Device inspected is Laptop X (LX-16)\n"
        "Conclusion: The inspected unit has 16 GB RAM.\n",
        fill=(0, 0, 0),
    )
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_bytes = img_buf.getvalue()

    # Upload both files
    r1 = requests.post(
        f"{BASE}/process-file",
        files={"file": ("01_manufacturer_spec_sheet.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    r2 = requests.post(
        f"{BASE}/process-file",
        files={"file": ("scanned_technician_report.png", io.BytesIO(img_bytes), "image/png")},
    )
    print("2. Uploaded 2 files:", r1.status_code, r2.status_code)

    # 4. Inspect GET /graph
    g = requests.get(f"{BASE}/graph").json()
    nodes = g.get("nodes", [])
    links = g.get("links", [])
    print(f"3. Graph returned: {len(nodes)} nodes, {len(links)} links")
    print("\nNodes:")
    for n in nodes:
        print(f"  - [{n.get('type')}] {n.get('label')} (id={n.get('id')}, category={n.get('category')})")
    print("\nLinks:")
    for l in links:
        print(f"  - {l.get('source')} --[{l.get('relation')} / {l.get('type')}]--> {l.get('target')}")

    labels = {n.get("label") for n in nodes}
    relations = {l.get("relation") for l in links}
    contradict_links = [l for l in links if l.get("type") == "CONTRADICTS"]

    assert "Laptop X (LX-16)" in labels, f"Missing Laptop X node in {labels}"
    assert "RAM" in labels, f"Missing RAM node in {labels}"
    assert any("16 GB" in lbl for lbl in labels), f"Missing 16 GB node in {labels}"
    assert "01_manufacturer_spec_sheet.pdf" in labels
    assert "scanned_technician_report.png" in labels
    assert "Evidence Consistency: Consistent" in labels
    assert "has_RAM" in relations
    assert "supports" in relations
    assert "agrees_with" in relations
    assert len(contradict_links) == 0, f"Unexpected contradiction edges: {contradict_links}"

    print("\nALL KNOWLEDGE GRAPH CHECKS PASSED 100%!")
    requests.post(f"{BASE}/reset")


if __name__ == "__main__":
    test_laptop_x_graph()
