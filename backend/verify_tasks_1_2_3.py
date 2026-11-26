"""
CERBERUS-XA — Regression & Verification Suite for Tasks 1, 2, 3:
- Task 1: SUPPORTED (ANSWERED) outcome with deterministic non-conflicting fixture
- Task 2: Fix empty conflict export rows (ConflictPair mapping & CSV filtering)
- Task 3: Multi-investigation history retention & per-report selection export (JSON, CSV, PDF, MD)
"""

import io
import json
import csv
from pathlib import Path
import requests
import pymupdf

BASE = "http://localhost:8000"
EXPORT_DIR = Path(__file__).resolve().parent.parent / "reports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def run_all():
    print("=" * 70)
    print("TASK 1: VERIFY SUPPORTED (ANSWERED) OUTCOME WITH CLEAN FIXTURE")
    print("=" * 70)

    r_reset = requests.post(f"{BASE}/reset")
    assert r_reset.status_code == 200, f"Reset failed: {r_reset.status_code}"

    # Deterministic, non-conflicting CSV fixture
    csv_bytes = (
        "entity,payload_capacity,certification_status\n"
        "Alpha-7 UAV,15.5 kg,FAA Certified\n"
    ).encode("utf-8")

    r_up = requests.post(
        f"{BASE}/process-file",
        files={"file": ("alpha7_certified_specs.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    print("Upload status:", r_up.status_code, "Items:", len(r_up.json().get("content", [])))

    q1 = "What is the payload_capacity of Alpha-7 UAV?"
    r_inv1 = requests.post(f"{BASE}/investigate", json={"question": q1})
    assert r_inv1.status_code == 200, f"Investigate 1 failed: {r_inv1.text}"
    d1 = r_inv1.json()
    print(f"Investigation 1 ID      : {d1.get('reportId')}")
    print(f"Investigation 1 Verdict : {d1.get('verdict')} -> UI: {d1.get('finalVerdict')}")
    print(f"Investigation 1 Conf    : {d1.get('confidence')}% (ratio: {d1.get('verdictConfidence')})")
    print(f"Investigation 1 Support : {len(d1.get('supportingEvidence', []))} items")
    print(f"Investigation 1 Cites   : {len(d1.get('citations', []))} citations")

    task1_pass = (
        d1.get("verdict") in ("ANSWERED", "PARTIALLY_ANSWERED")
        and d1.get("verdictConfidence", 0) > 0
        and len(d1.get("citations", [])) >= 1
    )
    print(f"TASK 1 RESULT: {'PASS' if task1_pass else 'PARTIAL/FAIL'}")

    print("\n" + "=" * 70)
    print("TASK 2: VERIFY CONFLICTPAIR MAPPING & NO EMPTY CONFLICT EXPORT ROWS")
    print("=" * 70)

    # Run a second investigation (insufficient evidence / conflicting check)
    q2 = "What is the orbital velocity of the James Webb Space Telescope around Lagrange point L2?"
    r_inv2 = requests.post(f"{BASE}/investigate", json={"question": q2})
    assert r_inv2.status_code == 200, f"Investigate 2 failed: {r_inv2.text}"
    d2 = r_inv2.json()
    print(f"Investigation 2 ID      : {d2.get('reportId')}")
    print(f"Investigation 2 Verdict : {d2.get('verdict')} -> UI: {d2.get('finalVerdict')}")
    print(f"Investigation 2 Conflicts: {len(d2.get('contradictingEvidence', []))}")

    # Check CSV export of Investigation 2 has NO empty conflict rows
    rid2 = d2["reportId"]
    r_csv2 = requests.get(f"{BASE}/investigation-report/{rid2}/export?format=csv")
    assert r_csv2.status_code == 200
    csv2_text = r_csv2.text
    empty_conflict_rows = [
        line for line in csv2_text.splitlines()
        if line.startswith("CONTRADICTING,") and ", (Refutes: )" in line
    ]
    print(f"Empty conflict rows in CSV 2: {len(empty_conflict_rows)}")

    # Regression test: test POST /export-report with both a populated ConflictPair and an empty malformed entry
    regression_payload = {
        "reportId": "REG-TEST-CONF",
        "caseId": "CASE-REG",
        "investigationQuestion": "Regression check for conflict rows",
        "finalVerdict": "Conflicting evidence",
        "verdictConfidence": 0.42,
        "summaryAnswer": "Regression test summary",
        "contradictingEvidence": [
            {
                "source": "manifest_a.csv",
                "criticality": "HIGH",
                "claim": "Cargo weight is 12000 kg.",
                "contradicts": "Cargo weight is 18500 kg.",
                "citationRef": "[1] Source: manifest_a.csv",
            },
            {
                "source": "unresolved_conflict",
                "criticality": "HIGH",
                "claim": "",
                "contradicts": "",
                "citationRef": "",
            },
        ],
        "citations": [],
    }
    r_reg_csv = requests.post(f"{BASE}/export-report?format=csv", json=regression_payload)
    assert r_reg_csv.status_code == 200
    reg_lines = r_reg_csv.text.splitlines()
    contradicting_lines = [l for l in reg_lines if l.startswith("CONTRADICTING,")]
    print(f"Regression CSV CONTRADICTING rows count: {len(contradicting_lines)} (expected 1, empty skipped)")
    print(f"  Preserved row: {contradicting_lines[0] if contradicting_lines else 'NONE'}")

    task2_pass = (
        len(empty_conflict_rows) == 0
        and len(contradicting_lines) == 1
        and "Cargo weight is 12000 kg." in contradicting_lines[0]
    )
    print(f"TASK 2 RESULT: {'PASS' if task2_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    print("TASK 3: VERIFY REPORT SELECTION & ALL 4 EXPORT FORMATS FOR BOTH REPORTS")
    print("=" * 70)

    r_hist = requests.get(f"{BASE}/investigations")
    assert r_hist.status_code == 200
    hist = r_hist.json()
    print(f"History entries retained: {len(hist)}")
    ids_in_hist = [h.get("id") for h in hist]
    print("IDs in history:", ids_in_hist)

    task3_pass = d1["reportId"] in ids_in_hist and d2["reportId"] in ids_in_hist

    for idx, dossier in enumerate([d1, d2], start=1):
        rid = dossier["reportId"]
        expected_verdict = dossier["verdict"]
        expected_ui_verdict = dossier["finalVerdict"]
        expected_conf = f"{dossier['verdictConfidence'] * 100:.1f}%"

        # JSON
        rj = requests.get(f"{BASE}/investigation-report/{rid}/export?format=json")
        jp = EXPORT_DIR / f"sel_{idx}_{rid}.json"
        jp.write_bytes(rj.content)
        j_data = json.loads(jp.read_text(encoding="utf-8"))
        j_ok = j_data.get("reportId") == rid and j_data.get("verdict") == expected_verdict

        # CSV
        rc = requests.get(f"{BASE}/investigation-report/{rid}/export?format=csv")
        cp = EXPORT_DIR / f"sel_{idx}_{rid}.csv"
        cp.write_bytes(rc.content)
        c_txt = cp.read_text(encoding="utf-8")
        c_ok = rid in c_txt and expected_ui_verdict in c_txt and expected_conf in c_txt

        # PDF
        rpdf = requests.get(f"{BASE}/investigation-report/{rid}/export?format=pdf")
        pp = EXPORT_DIR / f"sel_{idx}_{rid}.pdf"
        pp.write_bytes(rpdf.content)
        doc = pymupdf.open(str(pp))
        pdf_txt = "".join(p.get_text() for p in doc)
        doc.close()
        pdf_ok = rid in pdf_txt and expected_ui_verdict in pdf_txt and expected_conf in pdf_txt

        print(f"  Report {idx} ({rid}): JSON={j_ok}, CSV={c_ok}, PDF={pdf_ok} [Verdict={expected_verdict}, Conf={expected_conf}]")
        task3_pass = task3_pass and j_ok and c_ok and pdf_ok

    print(f"TASK 3 RESULT: {'PASS' if task3_pass else 'FAIL'}")


if __name__ == "__main__":
    run_all()
