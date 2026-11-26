"""
Report Generator – produces PDF, CSV, and JSON reports with full source attribution.

Features:
- Complete explanations without truncation (no 200/300-char truncation)
- Guaranteed single-line CRLF / LF on Windows by opening files with newline=''
- Consistent metrics across JSON, CSV, and PDF exports
- Complete provenance and evidence tracking
"""

import csv
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .claim_builder import Claim
from .contradiction_detector import ContradictionResult, DetectionReport
from .entity_extraction import EntityRelationship

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON Report
# ---------------------------------------------------------------------------

def generate_json_report(
    report: DetectionReport,
    claims: list[Claim],
    output_path: Optional[str | Path] = None,
    entity_relationships: Optional[list[EntityRelationship]] = None,
) -> str:
    """Generate a comprehensive JSON report and return the JSON string."""
    data: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_claims": report.total_claims,
            "contradictions": report.contradiction_count,
            "consistent_claims": report.consistent_count,
            "uncertain_claims": report.uncertain_count,
            "entity_relationships_count": len(entity_relationships) if entity_relationships else 0,
        },
        "contradictions": [],
        "consistent_groups": [],
        "entity_relationships": [],
        "all_claims": [],
    }

    for c in report.contradictions:
        entry = {
            "contradiction_id": c.contradiction_id,
            "entity": c.entity,
            "entity_normalized": c.entity_normalized,
            "attribute": c.attribute,
            "status": c.status,
            "verdict": getattr(c, "verdict", "contradiction"),
            "explanation": c.explanation,  # Full explanation, no truncation
            "confidence": c.confidence,
            "confidence_breakdown": getattr(c, "confidence_breakdown", {}),
            "confidence_explanation": getattr(c, "confidence_explanation", ""),
            "contradiction_type": c.contradiction_type,
            "tolerance_used": c.tolerance_used,
            "conflicting_claims": [
                {
                    "claim_id": cl.claim_id,
                    "entity": cl.entity,
                    "value": cl.value,
                    "value_normalized": cl.value_normalized,
                    "unit": cl.unit,
                    "unit_normalized": cl.unit_normalized,
                    "source": cl.source,
                    "page_or_sheet": cl.page_or_sheet,
                    "date": cl.date_str,
                    "modality": cl.modality,
                    "dimension": cl.dimension,
                    "ocr_confidence": getattr(cl, "ocr_confidence", 1.0),
                    "flags": getattr(cl, "flags", []),
                    "original_text": cl.original_text,  # Full text, no truncation
                }
                for cl in c.conflicting_claims
            ],
        }
        data["contradictions"].append(entry)

    for i, grp in enumerate(report.consistent_groups, 1):
        data["consistent_groups"].append({
            "group_id": f"CONSISTENT-{i:03d}",
            "entity": grp[0].entity_normalized if grp else "",
            "attribute": grp[0].attribute if grp else "",
            "claims": [
                {
                    "claim_id": cl.claim_id,
                    "source": cl.source,
                    "value": cl.value,
                    "unit": cl.unit,
                    "date": cl.date_str,
                }
                for cl in grp
            ],
        })

    if entity_relationships:
        for rel in entity_relationships:
            data["entity_relationships"].append({
                "source_entity": rel.source_entity,
                "source_type": rel.source_type,
                "target_entity": rel.target_entity,
                "target_type": rel.target_type,
                "relation_type": rel.relation_type,
                "source_doc": rel.source_doc,
                "page_or_sheet": rel.page_or_sheet,
                "evidence_text": rel.evidence_text,
                "confidence": rel.confidence,
            })

    for cl in claims:
        data["all_claims"].append({
            "claim_id": cl.claim_id,
            "entity": cl.entity,
            "entity_normalized": cl.entity_normalized,
            "entity_type": cl.entity_type,
            "attribute": cl.attribute,
            "value": cl.value,
            "value_normalized": cl.value_normalized,
            "unit": cl.unit,
            "unit_normalized": cl.unit_normalized,
            "date": cl.date_str,
            "date_normalized": cl.date_normalized,
            "source": cl.source,
            "page_or_sheet": cl.page_or_sheet,
            "confidence": cl.confidence,
            "modality": cl.modality,
            "dimension": cl.dimension,
            "person": cl.person,
            "original_text": cl.original_text,
        })

    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(json_str)
        logger.info("JSON report saved to %s", output_path)

    return json_str


# ---------------------------------------------------------------------------
# CSV Report
# ---------------------------------------------------------------------------

def generate_csv_report(
    report: DetectionReport,
    output_path: Optional[str | Path] = None,
) -> str:
    """
    Generate a CSV report of contradictions.
    Guarantees proper line endings on Windows without doubled carriage returns.
    Preserves complete explanations without truncation.
    """
    rows = []
    headers = [
        "Contradiction ID", "Entity", "Attribute", "Status", "Verdict",
        "Source", "Page/Sheet", "Value", "Unit", "Date", "Modality",
        "Explanation", "Confidence", "Confidence Breakdown"
    ]
    rows.append(headers)

    for c in report.contradictions:
        verdict = getattr(c, "verdict", "contradiction")
        breakdown_str = json.dumps(getattr(c, "confidence_breakdown", {}))
        if not c.conflicting_claims:
            rows.append([
                c.contradiction_id,
                c.entity,
                c.attribute,
                c.status,
                verdict,
                "",
                "",
                "",
                "",
                "",
                "",
                c.explanation,
                f"{c.confidence:.3f}",
                breakdown_str,
            ])
        else:
            for cl in c.conflicting_claims:
                rows.append([
                    c.contradiction_id,
                    c.entity,
                    c.attribute,
                    c.status,
                    verdict,
                    cl.source,
                    cl.page_or_sheet,
                    str(cl.value),
                    cl.unit,
                    cl.date_str,
                    cl.modality,
                    c.explanation,  # Full explanation without truncation
                    f"{c.confidence:.3f}",
                    breakdown_str,
                ])

    # In-memory buffer for returning string
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    csv_str = output.getvalue()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        # Using newline='' prevents doubled carriage returns (\r\r\n) on Windows
        with open(out_p, "w", newline="", encoding="utf-8") as f:
            f_writer = csv.writer(f)
            f_writer.writerows(rows)
        logger.info("CSV report saved to %s", output_path)

    return csv_str


# ---------------------------------------------------------------------------
# PDF Report (using reportlab)
# ---------------------------------------------------------------------------

def generate_pdf_report(
    report: DetectionReport,
    claims: list[Claim],
    output_path: str | Path,
    entity_relationships: Optional[list[EntityRelationship]] = None,
) -> str:
    """Generate a high-quality PDF audit report using reportlab."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )

        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=18,
            textColor=colors.HexColor("#1E3A5F"),
        )
        story.append(Paragraph("CERBERUX-XA Contradiction Detection Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1E3A5F")))
        story.append(Spacer(1, 0.4 * cm))

        # Summary Table
        story.append(Paragraph("Executive Summary", styles["Heading2"]))
        summary_data = [
            ["Metric", "Value"],
            ["Total Claims Extracted", str(report.total_claims)],
            ["Contradictions Detected", str(report.contradiction_count)],
            ["Consistent Claims", str(report.consistent_count)],
            ["Uncertain Claims", str(report.uncertain_count)],
            ["Entity Relationships", str(len(entity_relationships) if entity_relationships else 0)],
        ]
        summary_table = Table(summary_data, colWidths=[9 * cm, 5 * cm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF2F7")]),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5 * cm))

        # Contradictions
        story.append(Paragraph("Detected Contradictions", styles["Heading2"]))
        story.append(Spacer(1, 0.2 * cm))

        if not report.contradictions:
            story.append(Paragraph("No contradictions detected across ingested sources.", styles["Normal"]))
        else:
            for i, c in enumerate(report.contradictions, 1):
                story.append(
                    Paragraph(
                        f"{i}. [{c.contradiction_id}] {c.entity} – {c.attribute}",
                        styles["Heading3"],
                    )
                )
                story.append(
                    Paragraph(
                        f"<b>Status:</b> {c.status} | <b>Confidence:</b> {c.confidence:.1%}",
                        styles["Normal"],
                    )
                )
                # Full explanation without truncation
                story.append(Paragraph(f"<b>Explanation:</b> {c.explanation}", styles["Normal"]))
                story.append(Spacer(1, 0.2 * cm))

                # Conflicting claims table
                tdata = [["Source", "Page/Sheet", "Value", "Unit", "Date"]]
                for cl in c.conflicting_claims:
                    tdata.append([
                        cl.source, cl.page_or_sheet, str(cl.value), cl.unit, cl.date_str
                    ])

                tbl = Table(tdata, colWidths=[4.5 * cm, 3 * cm, 3 * cm, 2.5 * cm, 3 * cm])
                tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C0392B")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FDEAEA")]),
                ]))
                story.append(tbl)
                story.append(Spacer(1, 0.4 * cm))

        # Entity Relationships section
        if entity_relationships:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph("Entity Relationships & Governance", styles["Heading2"]))
            rdata = [["Source Entity", "Relationship", "Target Entity", "Source Document"]]
            for r in entity_relationships:
                rdata.append([r.source_entity, r.relation_type, r.target_entity, r.source_doc])
            rtbl = Table(rdata, colWidths=[4 * cm, 3.5 * cm, 4.5 * cm, 4 * cm])
            rtbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F6")]),
            ]))
            story.append(rtbl)

        doc.build(story)
        logger.info("PDF report saved to %s", output_path)
        return str(output_path)

    except ImportError:
        logger.error("reportlab not installed. Cannot generate PDF.")
        return ""
    except Exception as exc:
        logger.exception("PDF report generation failed: %s", exc)
        return ""
