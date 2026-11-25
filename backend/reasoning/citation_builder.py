"""
CERBERUS-X: AI Reasoning & Evidence Verification Module
Component 5: Evidence Citation and Traceability System

Guarantees:
- Every factual statement in the final answer links to evidence that actually exists in input.
- Supports PDF documents, Scanned documents, Images, Tables, CSV datasets, Structured records, Text files.
- Preserves all available source metadata without inventing fields.
- Cites supporting and conflicting claims.
- Allows multiple citations per statement/answer.
- Never invents page numbers, filenames, or source IDs.
- Reports missing citation metadata.
- Detects invalid evidence references.
- Deduplicates repeated citation references.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Set, Any
from .schemas import (
    Citation,
    CitationItem,
    Claim,
    ClaimCitation,
    EvidenceItem,
    EvidenceMetadata,
    EvidenceModality,
)


class CitationBuilder:
    """
    Constructs traceable, auditable citations strictly grounded in verified evidence metadata.
    Enforces zero-fabrication guarantees and detects invalid references.
    """

    def build_claim_citations(
        self,
        claims: List[Claim],
        evidence_items: List[EvidenceItem],
    ) -> List[ClaimCitation]:
        """
        Builds structured citations for each claim (supporting or conflicting).
        Detects invalid evidence IDs, deduplicates references, and catalogs missing metadata.
        """
        claim_citations: List[ClaimCitation] = []
        evidence_map = {ev.id: ev for ev in evidence_items}

        for claim in claims:
            citations_for_claim: List[CitationItem] = []
            missing_metadata_for_claim: List[str] = []
            invalid_evidence_ids: List[str] = []
            seen_evidence_ids: Set[str] = set()

            for eid in claim.evidence_ids:
                # 9. Detect invalid evidence references
                if eid not in evidence_map:
                    invalid_evidence_ids.append(eid)
                    missing_metadata_for_claim.append(
                        f"Referenced evidence ID '{eid}' does not exist in evidence manifest"
                    )
                    continue

                # 10. Deduplicate repeated citation references for this claim
                if eid in seen_evidence_ids:
                    continue
                seen_evidence_ids.add(eid)

                ev_item = evidence_map[eid]
                cit_item = self.build_citation_item(ev_item, claim_id=claim.id)
                citations_for_claim.append(cit_item)

                if cit_item.missing_fields:
                    missing_metadata_for_claim.extend(
                        f"Item '{eid}': missing {field}" for field in cit_item.missing_fields
                    )

            if not claim.evidence_ids:
                missing_metadata_for_claim.append("Claim has no linked evidence references.")

            claim_citations.append(
                ClaimCitation(
                    claim_id=claim.id,
                    statement=claim.statement,
                    polarity=claim.polarity,
                    citations=citations_for_claim,
                    missing_metadata=sorted(list(set(missing_metadata_for_claim))),
                    invalid_evidence_ids=sorted(list(set(invalid_evidence_ids))),
                )
            )

        return claim_citations

    def build_citation_item(
        self,
        item: EvidenceItem,
        claim_id: Optional[str] = None,
    ) -> CitationItem:
        """
        Builds a single CitationItem for an evidence item, strictly preserving supplied fields
        and cataloging missing metadata without fabricating values.
        """
        meta: EvidenceMetadata = item.metadata
        missing_fields: List[str] = []

        # Source ID check (Never invent)
        source_id = meta.source_id.strip() if meta.source_id and meta.source_id.strip() and meta.source_id.strip().upper() != "UNKNOWN" else None
        if not source_id:
            missing_fields.append("source_id")

        # Filename check (Never invent)
        filename = meta.filename.strip() if meta.filename and meta.filename.strip() else None
        if not filename:
            missing_fields.append("filename")

        # Page number check (Never invent)
        page_number = meta.page_number
        is_doc_or_scan = (
            item.modality in (EvidenceModality.DOCUMENT, EvidenceModality.SCAN)
            or (filename and filename.lower().endswith(".pdf"))
            or (meta.file_type and "pdf" in meta.file_type.lower())
            or (meta.file_type and "scan" in meta.file_type.lower())
        )
        if page_number is None and is_doc_or_scan:
            missing_fields.append("page_number")

        # Section check
        section = meta.section.strip() if meta.section and meta.section.strip() else None

        # Paragraph check
        paragraph = meta.paragraph or meta.custom_attributes.get("paragraph")

        # Table Name / ID
        table_name = meta.table_name or meta.table_id or meta.custom_attributes.get("table_name")

        # Row / Record ID
        row_id = meta.row_id or meta.record_id or meta.custom_attributes.get("row_id")

        # Image ID
        image_id = meta.image_id or meta.custom_attributes.get("image_id")

        # URL
        url = meta.url or meta.custom_attributes.get("url")

        # Infer Source Type and Format
        source_type = self._determine_source_type(item, meta)
        fmt = self._determine_format(item, meta)

        # Extracted Text Excerpt
        extracted_text = (item.content[:160] + "...") if len(item.content) > 160 else item.content

        # Standard human-readable citation string
        parts: List[str] = [f"Source: {source_id or 'UNKNOWN_SOURCE'}"]
        if filename:
            parts.append(f"File: {filename}")
        if source_type:
            parts.append(f"Type: {source_type}")
        if fmt:
            parts.append(f"Format: {fmt}")
        if page_number is not None:
            parts.append(f"Page {page_number}")
        if section:
            parts.append(f"Section '{section}'")
        if table_name:
            parts.append(f"Table '{table_name}'")
        if row_id:
            parts.append(f"Row/Record '{row_id}'")
        if image_id:
            parts.append(f"Image '{image_id}'")
        if url:
            parts.append(f"URL: {url}")
        parts.append(f"Evidence ID: {item.id}")

        formatted = " | ".join(parts)

        return CitationItem(
            evidence_id=item.id,
            source_id=source_id,
            filename=filename,
            source_type=source_type,
            format=fmt,
            page_number=page_number,
            section=section,
            paragraph=paragraph,
            table_name=table_name,
            row_id=row_id,
            image_id=image_id,
            url=url,
            extracted_text=extracted_text,
            claim_id=claim_id,
            formatted_citation=formatted,
            missing_fields=missing_fields,
        )

    def build_citations_for_evidence(
        self,
        evidence_items: List[EvidenceItem],
        referenced_ids: Optional[Set[str]] = None,
    ) -> List[Citation]:
        """
        Builds standard Citation list for response integration.
        Deduplicates references and preserves traceability metadata.
        """
        citations: List[Citation] = []
        target_items = (
            [ev for ev in evidence_items if ev.id in referenced_ids]
            if referenced_ids is not None
            else evidence_items
        )

        seen_ids: Set[str] = set()
        idx = 1
        for ev in target_items:
            if ev.id in seen_ids:
                continue
            seen_ids.add(ev.id)

            cit_item = self.build_citation_item(ev)
            citation = Citation(
                citation_id=f"[{idx}]",
                evidence_id=ev.id,
                source_id=cit_item.source_id or "UNKNOWN_SOURCE",
                filename=cit_item.filename,
                location_locator=self._format_location_locator(cit_item),
                formatted_citation=f"[{idx}] {cit_item.formatted_citation}",
                verifiable_metadata={
                    "evidence_id": ev.id,
                    "source_id": cit_item.source_id or "UNKNOWN_SOURCE",
                    "filename": cit_item.filename,
                    "source_type": cit_item.source_type,
                    "format": cit_item.format,
                    "page_number": str(cit_item.page_number) if cit_item.page_number is not None else None,
                    "section": cit_item.section,
                    "table_name": cit_item.table_name,
                    "row_id": cit_item.row_id,
                    "image_id": cit_item.image_id,
                    "url": cit_item.url,
                    "checksum_hash": ev.metadata.checksum_hash,
                },
                source_type=cit_item.source_type,
                format=cit_item.format,
                page_number=cit_item.page_number,
                section=cit_item.section,
                paragraph=cit_item.paragraph,
                table_name=cit_item.table_name,
                row_id=cit_item.row_id,
                image_id=cit_item.image_id,
                url=cit_item.url,
                extracted_text=cit_item.extracted_text,
                missing_fields=cit_item.missing_fields,
            )
            citations.append(citation)
            idx += 1

        return citations

    def format_citations_block(self, citations: List[Citation]) -> str:
        """Renders bibliographic citation block for report display."""
        if not citations:
            return "No citations available (insufficient or unreferenced evidence)."
        return "\n".join(c.formatted_citation for c in citations)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _determine_source_type(self, item: EvidenceItem, meta: EvidenceMetadata) -> str:
        # Revert "PDF document": source_type is strictly the modality enum value (document, image, table, etc.)
        mod = item.modality
        if hasattr(mod, "value"):
            return str(mod.value).lower()
        elif isinstance(mod, str):
            return mod.lower()
        return "document"

    def _determine_format(self, item: EvidenceItem, meta: EvidenceMetadata) -> Optional[str]:
        # Specific file format or encoding (e.g. pdf, csv, png, tiff, txt)
        meta_source_type = getattr(meta, "source_type", None)
        if meta_source_type and str(meta_source_type).strip():
            mst = str(meta_source_type).strip().lower()
            if mst in ("pdf", "csv", "png", "jpg", "jpeg", "tiff", "txt", "scan", "table", "html"):
                return mst

        fn = (meta.filename or "").lower() if meta else ""
        ft = (meta.file_type or "").lower() if meta else ""

        if fn.endswith(".pdf") or "pdf" in ft:
            return "pdf"
        elif fn.endswith(".csv") or "csv" in ft:
            return "csv"
        elif fn.endswith((".tiff", ".tif")):
            return "tiff"
        elif fn.endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
            return fn.rsplit(".", 1)[-1]
        elif fn.endswith(".txt") or "text" in ft:
            return "txt"
        elif fn.endswith(".html"):
            return "html"
        return None

    def _format_location_locator(self, cit: CitationItem) -> str:
        locators: List[str] = []
        if cit.page_number is not None:
            locators.append(f"Page {cit.page_number}")
        if cit.section:
            locators.append(f"Section '{cit.section}'")
        if cit.paragraph is not None:
            locators.append(f"Para. {cit.paragraph}")
        if cit.table_name:
            locators.append(f"Table '{cit.table_name}'")
        if cit.row_id:
            locators.append(f"Row/Record '{cit.row_id}'")
        if cit.image_id:
            locators.append(f"Image '{cit.image_id}'")
        return ", ".join(locators) if locators else "Document body"
