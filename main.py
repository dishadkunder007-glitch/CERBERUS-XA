"""
Main pipeline – orchestrates document loading, extraction, claim building,
contradiction detection, graph building and report generation.
"""

import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("contradiction_detection")


def run_pipeline(
    file_paths: list[str | Path],
    numerical_tolerance_pct: float = 2.0,
    merge_threshold: float = 92.0,
    similarity_threshold: float = 82.0,
    use_ocr_for_pdf: bool = True,
    output_dir: str | Path = "reports",
) -> dict:
    """
    Full end-to-end pipeline.

    Args:
        file_paths: list of document paths.
        numerical_tolerance_pct: % tolerance for numerical comparison.
        merge_threshold: RapidFuzz score to merge entity names.
        similarity_threshold: RapidFuzz score to flag possible entity matches.
        use_ocr_for_pdf: use OCR for PDF pages with no text.
        output_dir: directory to save reports.

    Returns:
        {
            "documents": [...],
            "claims": [...],
            "report": DetectionReport,
            "graph": nx.MultiDiGraph,
            "graph_json": dict,
            "reports": {
                "pdf": path | "",
                "csv": path | "",
                "json": path | "",
            }
        }
    """
    from src.extractors.document_loader import load_multiple_documents
    from src.entity_extraction import (
        extract_entities_from_document,
        extract_relationships_from_document,
    )
    from src.claim_builder import ClaimBuilder
    from src.contradiction_detector import ContradictionDetector
    from src.duplicates import detect_duplicates
    from src.graph_builder import GraphBuilder
    from src.report_generator import generate_json_report, generate_csv_report, generate_pdf_report

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load documents
    logger.info("Loading %d documents…", len(file_paths))
    documents = load_multiple_documents(file_paths, use_ocr_for_pdf=use_ocr_for_pdf)

    # 2. Extract raw claims & entity relationships
    logger.info("Extracting entities and relationships from documents…")
    raw_claims = []
    entity_relationships = []
    for doc in documents:
        if doc.get("error"):
            logger.warning("Skipping %s due to error: %s", doc["source"], doc["error"])
            continue
        raw_claims.extend(extract_entities_from_document(doc))
        entity_relationships.extend(extract_relationships_from_document(doc))

    logger.info("Total raw claims extracted: %d | Entity relationships: %d", len(raw_claims), len(entity_relationships))

    # 3. Build & normalize claims
    builder = ClaimBuilder(
        merge_threshold=merge_threshold,
        similarity_threshold=similarity_threshold,
    )
    claims = builder.build(raw_claims)
    logger.info("Normalized claims: %d", len(claims))

    # 4. Detect contradictions
    detector = ContradictionDetector(
        numerical_tolerance_pct=numerical_tolerance_pct,
    )
    detection_report = detector.detect(claims)

    logger.info(
        "Contradictions: %d | Consistent: %d | Uncertain: %d",
        detection_report.contradiction_count,
        detection_report.consistent_count,
        detection_report.uncertain_count,
    )

    # 4b. Detect duplicates & inconsistencies
    duplicate_report = detect_duplicates(documents, claims)
    logger.info(
        "Duplicates: %d groups | Near-duplicates: %d | Intra-doc inconsistencies: %d",
        duplicate_report.total_duplicate_groups,
        duplicate_report.total_near_duplicates,
        duplicate_report.total_intra_document_inconsistencies,
    )

    # 5. Build graph
    graph_builder = GraphBuilder()
    graph = graph_builder.build(
        claims,
        detection_report,
        entity_relationships=entity_relationships,
        numerical_tolerance_pct=numerical_tolerance_pct,
    )
    graph_json = graph_builder.to_json()

    # Save graph exports
    graph_builder.to_json(output_dir / "graph.json")
    try:
        graph_builder.to_graphml(output_dir / "graph.graphml")
    except Exception as e:
        logger.warning("GraphML export failed: %s", e)

    # 6. Generate reports
    json_path = output_dir / "contradiction_report.json"
    csv_path = output_dir / "contradiction_report.csv"
    pdf_path = output_dir / "contradiction_report.pdf"

    generate_json_report(detection_report, claims, json_path, entity_relationships=entity_relationships)
    generate_csv_report(detection_report, csv_path)
    generate_pdf_report(detection_report, claims, pdf_path, entity_relationships=entity_relationships)

    return {
        "documents": documents,
        "claims": claims,
        "report": detection_report,
        "duplicate_report": duplicate_report,
        "graph": graph,
        "graph_json": graph_json,
        "graph_builder": graph_builder,
        "reports": {
            "pdf": str(pdf_path) if pdf_path.exists() else "",
            "csv": str(csv_path) if csv_path.exists() else "",
            "json": str(json_path) if json_path.exists() else "",
        },
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Contradiction Detection System")
    parser.add_argument("files", nargs="+", help="Paths to input documents")
    parser.add_argument("--tolerance", type=float, default=2.0, help="Numerical tolerance %%")
    parser.add_argument("--output", default="reports", help="Output directory for reports")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR for PDFs")
    args = parser.parse_args()

    result = run_pipeline(
        file_paths=args.files,
        numerical_tolerance_pct=args.tolerance,
        output_dir=args.output,
        use_ocr_for_pdf=not args.no_ocr,
    )

    rpt = result["report"]
    print(f"\n{'='*60}")
    print(f"  CONTRADICTION DETECTION REPORT")
    print(f"{'='*60}")
    print(f"  Total Claims       : {rpt.total_claims}")
    print(f"  Contradictions     : {rpt.contradiction_count}")
    print(f"  Consistent Groups  : {len(rpt.consistent_groups)}")
    print(f"  Uncertain Groups   : {len(rpt.uncertain_groups)}")
    print(f"{'='*60}")

    for c in rpt.contradictions:
        print(f"\n[{c.contradiction_id}] {c.entity} – {c.attribute}")
        print(f"  Status     : {c.status}")
        print(f"  Confidence : {c.confidence:.1%}")
        print(f"  {c.explanation}")
        for cl in c.conflicting_claims:
            print(f"    • {cl.source} ({cl.page_or_sheet}): {cl.value} {cl.unit}")

    print(f"\nReports saved to: {args.output}/")
