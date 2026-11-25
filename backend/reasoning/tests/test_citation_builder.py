"""
CERBERUS-X: AI Reasoning & Evidence Verification Module
Unit Tests for Component 5: Citation Builder & Traceability System

Guarantees Verified:
1. Supported source types: PDF, Scan, Image, Table, CSV, Record, Text.
2. Preserves source metadata (page, section, table, row, image, url).
3. Cites supporting claims (polarity=True).
4. Cites conflicting claims (polarity=False).
5. Supports multiple citations per answer/claim.
6. Never invents page numbers.
7. Never invents filenames.
8. Never invents source IDs.
9. Missing citation metadata must be reported.
10. Detects invalid evidence references.
11. Deduplicates repeated citation references.
12. Formats clean structured citation objects matching the CERBERUS-X spec.
"""

import pytest
from backend.reasoning.schemas import (
    Claim,
    EvidenceItem,
    EvidenceMetadata,
    EvidenceModality,
)
from backend.reasoning.citation_builder import CitationBuilder


@pytest.fixture
def builder():
    return CitationBuilder()


# -----------------------------------------------------------------------------
# Test 1: Supported Source Types across all 7 modalities
# -----------------------------------------------------------------------------
def test_valid_citations_across_all_source_types(builder):
    """Verifies that all 7 required source types are identified and metadata preserved."""
    items = [
        EvidenceItem(
            id="EV-PDF",
            content="Revenue increased by 14% year-over-year.",
            modality=EvidenceModality.DOCUMENT,
            metadata=EvidenceMetadata(
                source_id="SRC-ANNUAL-2024",
                filename="annual_report.pdf",
                file_type="application/pdf",
                page_number=14,
                section="Financial Highlights",
            ),
        ),
        EvidenceItem(
            id="EV-SCAN",
            content="Signed contract specifies delivery deadline of Oct 15.",
            modality=EvidenceModality.SCAN,
            metadata=EvidenceMetadata(
                source_id="SRC-LEGAL-VAULT",
                filename="scanned_contract.tiff",
                file_type="image/tiff",
                page_number=3,
            ),
        ),
        EvidenceItem(
            id="EV-IMG",
            content="Satellite imagery shows facility operational with 4 active bays.",
            modality=EvidenceModality.IMAGE,
            metadata=EvidenceMetadata(
                source_id="SRC-GEO-SAT",
                filename="aerial_compound.png",
                image_id="IMG-BAY-04",
            ),
        ),
        EvidenceItem(
            id="EV-TBL",
            content="Server logs table indicates 99.98% uptime for US-East.",
            modality=EvidenceModality.TABLE,
            metadata=EvidenceMetadata(
                source_id="SRC-OPS-MONITOR",
                filename="metrics_dashboard.html",
                table_name="uptime_sla_q3",
                row_id="ROW-USEAST-1",
            ),
        ),
        EvidenceItem(
            id="EV-CSV",
            content="Transaction 8912 marked as cleared with amount $450,000.",
            modality=EvidenceModality.DOCUMENT,
            metadata=EvidenceMetadata(
                source_id="SRC-BANK-EXPORT",
                filename="cleared_settlements.csv",
                file_type="text/csv",
                row_id="ROW-8912",
            ),
        ),
        EvidenceItem(
            id="EV-REC",
            content="Patient record confirms discharge on 2024-08-12.",
            modality=EvidenceModality.RECORD,
            metadata=EvidenceMetadata(
                source_id="SRC-EMR-SYSTEM",
                record_id="REC-PAT-5541",
            ),
        ),
        EvidenceItem(
            id="EV-TXT",
            content="Meeting notes state that project phase 2 begins in Q1.",
            modality=EvidenceModality.DOCUMENT,
            metadata=EvidenceMetadata(
                source_id="SRC-INTERNAL-WIKI",
                filename="project_kickoff_notes.txt",
                section="Next Steps",
            ),
        ),
    ]

    citations = builder.build_citations_for_evidence(items)
    assert len(citations) == 7

    cit_map = {c.evidence_id: c for c in citations}

    # 1. PDF
    assert cit_map["EV-PDF"].source_type == "document"
    assert cit_map["EV-PDF"].format == "pdf"
    assert cit_map["EV-PDF"].page_number == 14
    assert cit_map["EV-PDF"].section == "Financial Highlights"
    assert "Page 14" in cit_map["EV-PDF"].location_locator

    # 2. Scanned document
    assert cit_map["EV-SCAN"].source_type == "scan"
    assert cit_map["EV-SCAN"].format == "tiff"
    assert cit_map["EV-SCAN"].page_number == 3

    # 3. Image
    assert cit_map["EV-IMG"].source_type == "image"
    assert cit_map["EV-IMG"].format == "png"
    assert cit_map["EV-IMG"].image_id == "IMG-BAY-04"
    assert "Image 'IMG-BAY-04'" in cit_map["EV-IMG"].location_locator

    # 4. Table
    assert cit_map["EV-TBL"].source_type == "table"
    assert cit_map["EV-TBL"].format == "html"
    assert cit_map["EV-TBL"].table_name == "uptime_sla_q3"
    assert cit_map["EV-TBL"].row_id == "ROW-USEAST-1"

    # 5. CSV dataset
    assert cit_map["EV-CSV"].source_type == "document"
    assert cit_map["EV-CSV"].format == "csv"
    assert cit_map["EV-CSV"].row_id == "ROW-8912"

    # 6. Structured record
    assert cit_map["EV-REC"].source_type == "record"
    assert cit_map["EV-REC"].row_id == "REC-PAT-5541"

    # 7. Text file
    assert cit_map["EV-TXT"].source_type == "document"
    assert cit_map["EV-TXT"].format == "txt"
    assert cit_map["EV-TXT"].section == "Next Steps"


# -----------------------------------------------------------------------------
# Test 2: Cite Supporting and Conflicting Claims (Multiple citations per answer)
# -----------------------------------------------------------------------------
def test_cite_supporting_and_conflicting_claims(builder):
    """Verifies that both supporting and counter/conflicting claims are cited accurately."""
    ev1 = EvidenceItem(
        id="EV-SUPP-01",
        content="Testing phase completed on schedule.",
        modality=EvidenceModality.DOCUMENT,
        metadata=EvidenceMetadata(
            source_id="PMO-REPORT",
            filename="qa_status.pdf",
            page_number=10,
        ),
    )
    ev2 = EvidenceItem(
        id="EV-OPP-01",
        content="Testing phase failed integration benchmarks.",
        modality=EvidenceModality.DOCUMENT,
        metadata=EvidenceMetadata(
            source_id="ENG-AUDIT",
            filename="audit_log.pdf",
            page_number=22,
        ),
    )

    claims = [
        Claim(
            id="CLM-001",
            statement="Project testing was completed successfully on schedule.",
            evidence_ids=["EV-SUPP-01"],
            polarity=True,
        ),
        Claim(
            id="CLM-002",
            statement="Integration benchmarks failed during testing.",
            evidence_ids=["EV-OPP-01"],
            polarity=False,
        ),
    ]

    claim_citations = builder.build_claim_citations(claims, [ev1, ev2])
    assert len(claim_citations) == 2

    supp_cit = claim_citations[0]
    assert supp_cit.claim_id == "CLM-001"
    assert supp_cit.polarity is True
    assert len(supp_cit.citations) == 1
    assert supp_cit.citations[0].evidence_id == "EV-SUPP-01"
    assert supp_cit.citations[0].page_number == 10

    opp_cit = claim_citations[1]
    assert opp_cit.claim_id == "CLM-002"
    assert opp_cit.polarity is False
    assert len(opp_cit.citations) == 1
    assert opp_cit.citations[0].evidence_id == "EV-OPP-01"
    assert opp_cit.citations[0].page_number == 22


# -----------------------------------------------------------------------------
# Test 3: Multiple Citations Per Claim / Answer
# -----------------------------------------------------------------------------
def test_multiple_citations_per_claim(builder):
    """Verifies that a claim can link to multiple independent evidence sources."""
    ev1 = EvidenceItem(
        id="EV-01",
        content="Flight AX-201 departed at 08:00 UTC.",
        metadata=EvidenceMetadata(source_id="ATC-LOGS", filename="atc_q1.pdf", page_number=4),
    )
    ev2 = EvidenceItem(
        id="EV-02",
        content="Flight AX-201 transponder pinged near runway 22 at 08:01 UTC.",
        metadata=EvidenceMetadata(source_id="RADAR-DATA", filename="radar_records.csv", row_id="4401"),
    )

    claim = Claim(
        id="CLM-MULTI",
        statement="Flight AX-201 departed at 08:00 UTC from runway 22.",
        evidence_ids=["EV-01", "EV-02"],
        polarity=True,
    )

    claim_citations = builder.build_claim_citations([claim], [ev1, ev2])
    assert len(claim_citations) == 1
    citations = claim_citations[0].citations
    assert len(citations) == 2
    assert citations[0].evidence_id == "EV-01"
    assert citations[1].evidence_id == "EV-02"


# -----------------------------------------------------------------------------
# Test 4: Zero-Fabrication: Never Invent Page Numbers
# -----------------------------------------------------------------------------
def test_never_invent_page_numbers(builder):
    """Ensures missing page numbers on document/scan are reported, never guessed or fabricated."""
    doc_no_page = EvidenceItem(
        id="EV-NO-PAGE",
        content="Policy mandates two-factor authentication for remote access.",
        modality=EvidenceModality.DOCUMENT,
        metadata=EvidenceMetadata(
            source_id="SEC-POLICY",
            filename="security_guidelines.pdf",
            # page_number omitted intentionally
        ),
    )

    cit_item = builder.build_citation_item(doc_no_page)
    assert cit_item.page_number is None
    assert "page_number" in cit_item.missing_fields
    assert "Page" not in cit_item.formatted_citation

    claim = Claim(
        id="CLM-SEC",
        statement="2FA is mandatory for remote access.",
        evidence_ids=["EV-NO-PAGE"],
    )
    claim_citations = builder.build_claim_citations([claim], [doc_no_page])
    assert len(claim_citations) == 1
    assert any("missing page_number" in m for m in claim_citations[0].missing_metadata)


# -----------------------------------------------------------------------------
# Test 5: Zero-Fabrication: Never Invent Filenames
# -----------------------------------------------------------------------------
def test_never_invent_filenames(builder):
    """Ensures missing filenames are reported in missing_fields, never invented."""
    item_no_fn = EvidenceItem(
        id="EV-NO-FN",
        content="Telemetry data shows normal operating temperature of 68F.",
        modality=EvidenceModality.RECORD,
        metadata=EvidenceMetadata(
            source_id="IOT-STREAM-01",
            record_id="STREAM-9912",
            # filename omitted
        ),
    )

    cit_item = builder.build_citation_item(item_no_fn)
    assert cit_item.filename is None
    assert "filename" in cit_item.missing_fields
    assert "File:" not in cit_item.formatted_citation


# -----------------------------------------------------------------------------
# Test 6: Zero-Fabrication: Never Invent Source IDs
# -----------------------------------------------------------------------------
def test_never_invent_source_ids(builder):
    """Ensures missing source IDs are reported in missing_fields and fallback handled without inventing."""
    item_no_src = EvidenceItem(
        id="EV-NO-SRC",
        content="Unattributed memorandum regarding budget surplus.",
        modality=EvidenceModality.DOCUMENT,
        metadata=EvidenceMetadata(
            source_id="",  # Empty source ID
            filename="memo_unattributed.pdf",
            page_number=1,
        ),
    )

    cit_item = builder.build_citation_item(item_no_src)
    assert cit_item.source_id is None
    assert "source_id" in cit_item.missing_fields
    assert "UNKNOWN_SOURCE" in cit_item.formatted_citation


# -----------------------------------------------------------------------------
# Test 7: Detect Invalid Evidence References
# -----------------------------------------------------------------------------
def test_detect_invalid_evidence_references(builder):
    """Ensures referenced evidence IDs that do not exist in the manifest are detected and reported."""
    real_ev = EvidenceItem(
        id="EV-VALID-01",
        content="Solar array generation reached 450 kWh.",
        metadata=EvidenceMetadata(source_id="ENERGY-DB", filename="solar.csv"),
    )

    claim = Claim(
        id="CLM-GHOST",
        statement="Solar generation reached 450 kWh and wind reached 120 kWh.",
        evidence_ids=["EV-VALID-01", "EV-NONEXISTENT-999"],
    )

    claim_citations = builder.build_claim_citations([claim], [real_ev])
    assert len(claim_citations) == 1
    cc = claim_citations[0]

    # Valid item is cited
    assert len(cc.citations) == 1
    assert cc.citations[0].evidence_id == "EV-VALID-01"

    # Phantom item is caught
    assert "EV-NONEXISTENT-999" in cc.invalid_evidence_ids
    assert any("EV-NONEXISTENT-999" in m for m in cc.missing_metadata)


# -----------------------------------------------------------------------------
# Test 8: Deduplicate Repeated Citation References
# -----------------------------------------------------------------------------
def test_deduplicate_repeated_citation_references(builder):
    """Ensures repeated citations to the same evidence ID are cleanly deduplicated."""
    ev1 = EvidenceItem(
        id="EV-DUP-01",
        content="Factory unit output was 10,000 units.",
        metadata=EvidenceMetadata(source_id="ERP-SYSTEM", filename="prod.pdf", page_number=5),
    )
    ev2 = EvidenceItem(
        id="EV-DUP-02",
        content="Defect rate was 0.02%.",
        metadata=EvidenceMetadata(source_id="ERP-SYSTEM", filename="qa.pdf", page_number=7),
    )

    # Claim repeating EV-DUP-01 three times
    claim = Claim(
        id="CLM-REPEATED",
        statement="Factory unit output was 10,000 units with high quality.",
        evidence_ids=["EV-DUP-01", "EV-DUP-01", "EV-DUP-02", "EV-DUP-01"],
    )

    claim_citations = builder.build_claim_citations([claim], [ev1, ev2])
    assert len(claim_citations) == 1
    cited_ids = [c.evidence_id for c in claim_citations[0].citations]
    assert cited_ids == ["EV-DUP-01", "EV-DUP-02"]

    # Also check build_citations_for_evidence deduplication
    citations = builder.build_citations_for_evidence([ev1, ev1, ev2, ev1])
    assert len(citations) == 2
    assert [c.evidence_id for c in citations] == ["EV-DUP-01", "EV-DUP-02"]


# -----------------------------------------------------------------------------
# Test 9: Empty Citation Lists & Edge Cases
# -----------------------------------------------------------------------------
def test_empty_citation_lists(builder):
    """Verifies graceful handling of empty inputs."""
    # Empty claims
    assert builder.build_claim_citations([], []) == []

    # Claim with no evidence IDs
    empty_claim = Claim(
        id="CLM-UNSUPPORTED",
        statement="Unsubstantiated speculation without references.",
        evidence_ids=[],
    )
    res = builder.build_claim_citations([empty_claim], [])
    assert len(res) == 1
    assert res[0].citations == []
    assert any("no linked evidence" in m.lower() for m in res[0].missing_metadata)

    # Empty evidence items
    assert builder.build_citations_for_evidence([]) == []
    assert "No citations available" in builder.format_citations_block([])


# -----------------------------------------------------------------------------
# Test 10: Structured Output Format & Dict Serialization
# -----------------------------------------------------------------------------
def test_structured_citation_dict_format(builder):
    """
    Verifies that ClaimCitation.to_citation_dict() produces the clean format
    specified in the CERBERUS-X requirements:
    {
      "claim_id": "claim_01",
      "statement": "The report identifies the project as completed.",
      "citations": [
        {
          "evidence_id": "ev_001",
          "filename": "project_report.pdf",
          "page_number": 5,
          "section": "Results"
        }
      ]
    }
    """
    item = EvidenceItem(
        id="ev_001",
        content="The report identifies the project as completed.",
        modality=EvidenceModality.DOCUMENT,
        metadata=EvidenceMetadata(
            source_id="project_office",
            filename="project_report.pdf",
            page_number=5,
            section="Results",
        ),
    )
    claim = Claim(
        id="claim_01",
        statement="The report identifies the project as completed.",
        evidence_ids=["ev_001"],
    )

    claim_citations = builder.build_claim_citations([claim], [item])
    assert len(claim_citations) == 1
    cc_dict = claim_citations[0].to_citation_dict()

    assert cc_dict["claim_id"] == "claim_01"
    assert cc_dict["statement"] == "The report identifies the project as completed."
    assert len(cc_dict["citations"]) == 1

    cit = cc_dict["citations"][0]
    assert cit["evidence_id"] == "ev_001"
    assert cit["filename"] == "project_report.pdf"
    assert cit["page_number"] == 5
    assert cit["section"] == "Results"


# -----------------------------------------------------------------------------
# Test 11: Modality Source Type Population (Never Null for Known Modalities)
# -----------------------------------------------------------------------------
def test_citation_source_type_populated_across_all_modalities(builder):
    """
    Part D.1: Populate citation.source_type from evidence modality
    (document, image, table, structured_data).
    Asserts citation.source_type is never null when modality is known.
    """
    modalities_to_test = [
        (EvidenceModality.DOCUMENT, "document"),
        (EvidenceModality.IMAGE, "image"),
        (EvidenceModality.TABLE, "table"),
        (EvidenceModality.STRUCTURED, "structured"),
    ]

    for mod_enum, expected_fragment in modalities_to_test:
        item = EvidenceItem(
            id=f"EV-{mod_enum.value.upper()}",
            content=f"Verified content for modality {mod_enum.value}.",
            modality=mod_enum,
            metadata=EvidenceMetadata(source_id=f"SRC-{mod_enum.value.upper()}"),
        )

        citations = builder.build_citations_for_evidence([item])
        assert len(citations) == 1
        cit = citations[0]

        # Assert source_type is populated and strictly matches modality enum value
        assert cit.source_type is not None
        assert isinstance(cit.source_type, str)
        assert cit.source_type == expected_fragment


