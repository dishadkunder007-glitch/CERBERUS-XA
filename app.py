"""
Contradiction Detection System – Streamlit Dashboard
CERBERUX-XA AI-Powered Cross-Document Contradiction Detection
"""

import io
import json
import logging
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Path setup – make src importable
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

from src.extractors.document_loader import load_multiple_documents
from src.entity_extraction import extract_entities_from_document, extract_relationships_from_document
from src.claim_builder import ClaimBuilder, Claim
from src.contradiction_detector import ContradictionDetector, DetectionReport
from src.graph_builder import GraphBuilder
from src.report_generator import generate_json_report, generate_csv_report, generate_pdf_report

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CERBERUX-XA | Contradiction Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for High Contrast & Professional Dark UI
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Dark canvas with high contrast typography */
    .stApp {
        background-color: #0E1117;
        color: #F0F6FC;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #F0F6FC !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }
    
    p, span, li, label {
        color: #C9D1D9 !important;
        font-size: 0.96rem;
    }
    
    .stMarkdown p {
        color: #C9D1D9 !important;
        line-height: 1.6;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #161B22 0%, #21262D 100%);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 22px 16px;
        text-align: center;
        margin: 8px 0;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
    }
    .metric-card h2 {
        font-size: 2.6rem !important;
        margin: 0 !important;
        font-weight: 800 !important;
        line-height: 1.1;
    }
    .metric-card p {
        color: #8B949E !important;
        font-size: 0.85rem !important;
        margin-top: 6px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    /* Contradiction & consistency alert cards */
    .contradiction-card {
        background: linear-gradient(135deg, #2D1515, #3D1818);
        border-left: 5px solid #FF5252;
        border: 1px solid rgba(255, 82, 82, 0.35);
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
        color: #FFCDD2 !important;
    }
    .contradiction-card b, .contradiction-card strong {
        color: #FFFFFF !important;
    }

    .consistent-card {
        background: linear-gradient(135deg, #0D2B15, #143D1F);
        border-left: 5px solid #2ECC71;
        border: 1px solid rgba(46, 204, 113, 0.35);
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
        color: #C8E6C9 !important;
    }

    .uncertain-card {
        background: linear-gradient(135deg, #2B2000, #3E2F00);
        border-left: 5px solid #F39C12;
        border: 1px solid rgba(243, 156, 18, 0.35);
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
        color: #FFE082 !important;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #238636, #2EA043);
        color: #FFFFFF !important;
        border: 1px solid rgba(240, 246, 252, 0.15);
        border-radius: 8px;
        padding: 0.6rem 1.4rem;
        font-weight: 700;
        box-shadow: 0 3px 8px rgba(0,0,0,0.3);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #2EA043, #3FB950);
        box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
        transform: translateY(-1px);
    }

    /* Quick Action Hero Box */
    .hero-box {
        background: linear-gradient(135deg, #161B22 0%, #1F2937 100%);
        border: 1px solid #30363D;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* Tables & expanders */
    div[data-testid="stExpander"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stAlert"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        color: #F0F6FC !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
def _init_state():
    defaults = {
        "documents": [],
        "claims": [],
        "detection_report": None,
        "graph_builder": None,
        "entity_relationships": [],
        "processing_done": False,
        "numerical_tolerance": 2.0,
        "merge_threshold": 92.0,
        "similarity_threshold": 82.0,
        "use_ocr": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ---------------------------------------------------------------------------
# Pipeline Helpers
# ---------------------------------------------------------------------------

def _build_pipeline(docs, tolerance, merge_thr, sim_thr):
    """Run entity extraction, claim building, contradiction detection, and graph construction."""
    from src.duplicates import detect_duplicates

    all_raw = []
    all_rels = []
    for doc in docs:
        if not doc.get("error"):
            all_raw.extend(extract_entities_from_document(doc))
            all_rels.extend(extract_relationships_from_document(doc))

    builder = ClaimBuilder(merge_threshold=merge_thr, similarity_threshold=sim_thr)
    claims = builder.build(all_raw)

    detector = ContradictionDetector(numerical_tolerance_pct=tolerance)
    report = detector.detect(claims)

    dup_report = detect_duplicates(docs, claims)

    gb = GraphBuilder()
    gb.build(
        claims,
        report,
        entity_relationships=all_rels,
        numerical_tolerance_pct=tolerance,
    )

    return claims, report, gb, all_rels, dup_report


def _load_and_run_sample_dataset():
    """Load the built-in multimodal sample dataset and execute detection."""
    sample_dir = _ROOT / "data" / "sample_docs"
    sample_files = [
        sample_dir / "sample_report.pdf",
        sample_dir / "sample_chart_receipt.png",
        sample_dir / "erp_production.xlsx",
        sample_dir / "erp_warehouse.csv",
        sample_dir / "external_audit.txt",
    ]
    # Fallback to existing files if any are missing
    existing_files = [f for f in sample_files if f.exists()]
    if not existing_files:
        existing_files = list(sample_dir.glob("*.*"))

    if not existing_files:
        st.error("❌ No sample files found in data/sample_docs/")
        return

    with st.spinner("⏳ Ingesting multimodal documents (PDF, PNG OCR, XLSX, CSV, TXT) and running contradiction analysis..."):
        docs = load_multiple_documents(existing_files, use_ocr_for_pdf=st.session_state.use_ocr)
        claims, report, gb, rels, dup_report = _build_pipeline(
            docs,
            st.session_state.numerical_tolerance,
            st.session_state.merge_threshold,
            st.session_state.similarity_threshold,
        )
        st.session_state.documents = docs
        st.session_state.claims = claims
        st.session_state.detection_report = report
        st.session_state.graph_builder = gb
        st.session_state.entity_relationships = rels
        st.session_state.duplicate_report = dup_report
        st.session_state.processing_done = True
        st.rerun()


def _metric_card(title: str, value: str, color: str = "#58A6FF") -> str:
    return f"""
    <div class="metric-card">
        <h2 style="color:{color};">{value}</h2>
        <p>{title}</p>
    </div>
    """


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        # High-contrast branded logo banner
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:1.2rem; padding: 10px 14px; background: rgba(88,166,255,0.08); border-radius: 10px; border: 1px solid rgba(88,166,255,0.25);">
                <span style="font-size:2rem;">🛡️</span>
                <div>
                    <div style="font-size:1.2rem; font-weight:800; color:#58A6FF; letter-spacing:0.5px;">CERBERUX-XA</div>
                    <div style="font-size:0.75rem; color:#8B949E; font-weight:600; letter-spacing:0.8px;">CONTRADICTION DETECTOR</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### ⚙️ Detection Settings")

        st.session_state.numerical_tolerance = st.slider(
            "Numerical Tolerance (%)",
            min_value=0.0, max_value=20.0,
            value=float(st.session_state.numerical_tolerance),
            step=0.5,
            help="Values within this percentage tolerance are treated as consistent (accounts for rounding).",
        )
        st.session_state.merge_threshold = st.slider(
            "Entity Merge Threshold",
            min_value=50.0, max_value=100.0,
            value=float(st.session_state.merge_threshold),
            step=1.0,
            help="RapidFuzz corporate suffix score above which entity names are merged.",
        )
        st.session_state.similarity_threshold = st.slider(
            "Entity Similarity Flag Threshold",
            min_value=50.0, max_value=100.0,
            value=float(st.session_state.similarity_threshold),
            step=1.0,
            help="Score above which entity names are flagged as potential matches without merging.",
        )
        st.session_state.use_ocr = st.toggle(
            "OCR for Images & Scanned PDFs",
            value=bool(st.session_state.use_ocr),
            help="Uses Tesseract OCR to read text from PNG, JPG, and scanned PDF documents.",
        )

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size:0.85rem; color:#8B949E; line-height:1.6;">
                <b>Version:</b> 1.0.0<br>
                <b>Core:</b> spaCy · RapidFuzz · NetworkX<br>
                <b>Engine:</b> Deterministic Multi-Source Reasoning
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Tab 1: Dashboard
# ---------------------------------------------------------------------------

def render_dashboard():
    report: DetectionReport | None = st.session_state.detection_report
    claims: list[Claim] = st.session_state.claims
    documents = st.session_state.documents

    st.markdown("## 📊 Executive Overview")

    # If no data yet, show welcoming hero banner and 1-click demo button
    if not st.session_state.processing_done:
        st.markdown(
            """
            <div class="hero-box">
                <h3 style="color:#58A6FF !important; margin-top:0;">🚀 Welcome to the AI-Powered Contradiction Detection System</h3>
                <p style="color:#C9D1D9; font-size:1.05rem;">
                    Analyze multiple documents across various file formats (<b>PDF, PNG/JPG OCR, Excel, CSV, TXT</b>).
                    The system automatically extracts entities, builds canonical claims, detects conflicting facts,
                    and maps multi-source provenance without randomly picking a single winner.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_cta, col_info = st.columns([1.5, 1])
        with col_cta:
            st.markdown("#### ⚡ Quick Start: Load Multi-Source Demo")
            st.write(
                "Click below to immediately load and analyze 5 sample documents demonstrating the "
                "classic multi-document contradiction scenario:"
            )
            st.markdown(
                """
                - 📄 **PDF Report**: `sample_report.pdf` (Production: 5,000 units, Revenue: ₹25L)
                - 🖼️ **Image OCR**: `sample_chart_receipt.png` (Production: 3,000 units, Revenue: ₹18L)
                - 📊 **Excel Spreadsheet**: `erp_production.xlsx` (Production: 4,000 units, Revenue: ₹20L)
                - 📋 **CSV Data**: `erp_warehouse.csv` (Production: 4,500 units, Revenue: ₹22L)
                - 📝 **Audit Report**: `external_audit.txt` (Production: 5,000 units, Revenue: ₹25L)
                """
            )
            if st.button("🚀 Load & Analyze Sample Dataset Now", type="primary", use_container_width=True):
                _load_and_run_sample_dataset()

        with col_info:
            st.markdown("#### 🔍 What the Engine Verifies")
            st.markdown(
                """
                1. **Entity Normalization**: Merges corporate variants (e.g. *ABC Industries* vs *ABC Industries Ltd.*).
                2. **Attribute & Unit Compatibility**: Converts metric units and currencies into comparable standards.
                3. **Temporal Alignment**: Compares claims within identical or overlapping time periods.
                4. **Zero Winner Bias**: Preserves all conflicting statements with complete source references.
                5. **Multi-Source Graph**: Connects entities, claims, and documents via NetworkX.
                """
            )
        return

    # Metric Cards when analysis is ready
    dup_report = getattr(st.session_state, "duplicate_report", None)
    dup_count = (dup_report.total_duplicate_groups + dup_report.total_near_duplicates) if dup_report else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(
            _metric_card("Documents Ingested", str(len(documents)), "#58A6FF"),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            _metric_card("Claims Extracted", str(len(claims)), "#3FB950"),
            unsafe_allow_html=True,
        )
    with col3:
        contr_count = report.contradiction_count if report else 0
        color = "#FF7B72" if contr_count > 0 else "#3FB950"
        st.markdown(
            _metric_card("Contradictions", str(contr_count), color),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            _metric_card("Duplicates / Variants", str(dup_count), "#A371F7"),
            unsafe_allow_html=True,
        )
    with col5:
        uncert = report.uncertain_count if report else 0
        st.markdown(
            _metric_card("Uncertain / Pending", str(uncert), "#D29922"),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    if report:
        col_chart, col_sources = st.columns([1, 1])

        with col_chart:
            st.markdown("### 📈 Claim Status Breakdown")
            labels = ["Contradictions", "Consistent", "Uncertain"]
            values = [
                report.contradiction_count,
                report.consistent_count,
                report.uncertain_count,
            ]
            colors_pie = ["#FF5252", "#2ECC71", "#F39C12"]
            fig = go.Figure(
                data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.45,
                    marker=dict(colors=colors_pie, line=dict(color="#161B22", width=2)),
                    textinfo="label+value+percent",
                    textfont=dict(color="#FFFFFF", size=13),
                )]
            )
            fig.update_layout(
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
                font_color="#F0F6FC",
                showlegend=True,
                margin=dict(t=20, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_sources:
            st.markdown("### 📁 Document Inventory")
            doc_data = []
            for d in documents:
                doc_data.append({
                    "Filename": d["source"],
                    "Format": d["type"].upper(),
                    "Status": "⚠️ Error" if d["error"] else "✅ Extracted",
                    "Details": d["error"] if d["error"] else f"Loaded successfully",
                })
            df_docs = pd.DataFrame(doc_data)
            st.dataframe(df_docs, use_container_width=True, hide_index=True)

        # Highlight detected contradictions banner
        if report.contradictions:
            st.markdown("### 🚨 High-Priority Contradiction Alerts")
            for c in report.contradictions:
                st.markdown(
                    f"""
                    <div class="contradiction-card">
                        <div style="font-size:1.1rem; font-weight:700; color:#FFFFFF; margin-bottom:6px;">
                            ⚡ Conflict Identified: {c.entity} — <span style="text-transform:uppercase;">{c.attribute}</span>
                        </div>
                        <div><b>Explanation:</b> {c.explanation}</div>
                        <div style="margin-top:6px; font-size:0.88rem; color:#FFA4A4;">
                            <b>Conflicting Sources:</b> {', '.join({cl.source for cl in c.conflicting_claims})}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# Tab 2: Upload & Process
# ---------------------------------------------------------------------------

def render_upload():
    st.markdown("## 📁 Upload Documents for Verification")

    # One-click demo loader button
    col_demo1, col_demo2 = st.columns([2, 1])
    with col_demo1:
        st.write("Upload custom files, or quickly test the system with our multimodal sample package:")
    with col_demo2:
        if st.button("⚡ Quick-Load 5 Sample Files", use_container_width=True):
            _load_and_run_sample_dataset()

    st.markdown("---")

    uploaded_files = st.file_uploader(
        "Select Documents (PDF, PNG, JPG, XLSX, CSV, TXT)",
        accept_multiple_files=True,
        type=["pdf", "png", "jpg", "jpeg", "xlsx", "csv", "txt"],
        help="Upload multiple files simultaneously. Supported formats: PDF, PNG, JPG, XLSX, CSV, TXT.",
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) ready for ingestion.")
        file_info = [
            {"Filename": f.name, "Size (KB)": f"{f.size/1024:.1f}", "MIME Type": f.type or "N/A"}
            for f in uploaded_files
        ]
        st.dataframe(pd.DataFrame(file_info), use_container_width=True, hide_index=True)

    col1, col2 = st.columns([1, 4])
    with col1:
        run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)
    with col2:
        reset_btn = st.button("🔄 Clear All", use_container_width=False)

    if reset_btn:
        for key in ["documents", "claims", "detection_report", "graph_builder"]:
            st.session_state[key] = [] if key in ("documents", "claims") else None
        st.session_state.processing_done = False
        st.rerun()

    if run_btn:
        if not uploaded_files:
            st.error("Please select or upload at least one document before running analysis.")
            return

        progress_bar = st.progress(0, text="Initializing extraction...")
        status_area = st.empty()

        try:
            file_bytes_dict = {uf.name: uf.read() for uf in uploaded_files}

            progress_bar.progress(20, text="📄 Extracting text & OCR from documents...")
            status_area.info("Processing files with format-specific extractors...")

            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_paths = []
                for fname, fbytes in file_bytes_dict.items():
                    tp = Path(tmpdir) / fname
                    tp.write_bytes(fbytes)
                    tmp_paths.append(tp)

                docs = load_multiple_documents(
                    tmp_paths,
                    use_ocr_for_pdf=st.session_state.use_ocr,
                )

                progress_bar.progress(45, text="🔍 Extracting entities & numerical facts (spaCy NER)...")
                status_area.info("Extracting companies, dates, monetary values, and quantities...")

                all_raw = []
                all_rels = []
                for doc in docs:
                    if not doc.get("error"):
                        raw = extract_entities_from_document(doc)
                        all_raw.extend(raw)
                        rels = extract_relationships_from_document(doc)
                        all_rels.extend(rels)

                progress_bar.progress(65, text="🔗 Building claims & fuzzy entity matching (RapidFuzz)...")
                status_area.info("Normalizing entities and aligning attributes...")

                builder = ClaimBuilder(
                    merge_threshold=st.session_state.merge_threshold,
                    similarity_threshold=st.session_state.similarity_threshold,
                )
                claims = builder.build(all_raw)

                progress_bar.progress(85, text="⚡ Detecting contradictions across sources...")
                status_area.info("Evaluating temporal and numerical consistency...")

                detector = ContradictionDetector(
                    numerical_tolerance_pct=st.session_state.numerical_tolerance,
                )
                report = detector.detect(claims)

                from src.duplicates import detect_duplicates
                dup_report = detect_duplicates(docs, claims)

                progress_bar.progress(95, text="🕸️ Generating NetworkX relationship graph...")
                status_area.info("Constructing node and edge mapping...")

                gb = GraphBuilder()
                gb.build(
                    claims,
                    report,
                    entity_relationships=all_rels,
                    numerical_tolerance_pct=st.session_state.numerical_tolerance,
                )

                progress_bar.progress(100, text="✅ Analysis complete!")
                status_area.success(
                    f"Processed {len(docs)} document(s) with {len(claims)} claim(s). "
                    f"Identified {report.contradiction_count} contradiction(s)."
                )

                st.session_state.documents = docs
                st.session_state.claims = claims
                st.session_state.detection_report = report
                st.session_state.graph_builder = gb
                st.session_state.entity_relationships = all_rels
                st.session_state.duplicate_report = dup_report
                st.session_state.entity_relationships = all_rels
                st.session_state.processing_done = True

        except Exception as exc:
            logger.exception("Pipeline execution failed")
            st.error(f"Analysis error: {exc}")
            progress_bar.empty()


# ---------------------------------------------------------------------------
# Tab 3: Extracted Claims
# ---------------------------------------------------------------------------

def render_claims():
    st.markdown("## 📋 Extracted & Normalized Claims")

    claims: list[Claim] = st.session_state.claims
    if not claims:
        st.info("No claims available yet. Upload documents or click 'Quick-Load 5 Sample Files' to begin.")
        return

    rows = []
    for c in claims:
        rows.append({
            "Claim ID": c.claim_id,
            "Entity": c.entity,
            "Normalized Entity": c.entity_normalized,
            "Attribute": c.attribute,
            "Value": c.value,
            "Unit": c.unit,
            "Date / Period": c.date_str,
            "Source File": c.source,
            "Page / Sheet": c.page_or_sheet,
            "Confidence": f"{c.confidence:.0%}",
        })
    df = pd.DataFrame(rows)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        entity_filter = st.text_input("🔍 Filter by Entity Name", "")
    with col2:
        attr_filter = st.text_input("🔍 Filter by Attribute", "")
    with col3:
        source_filter = st.selectbox(
            "Filter by Source Document",
            ["All"] + sorted(df["Source File"].unique().tolist()),
        )

    filtered = df.copy()
    if entity_filter:
        filtered = filtered[
            filtered["Entity"].str.contains(entity_filter, case=False, na=False)
            | filtered["Normalized Entity"].str.contains(entity_filter, case=False, na=False)
        ]
    if attr_filter:
        filtered = filtered[filtered["Attribute"].str.contains(attr_filter, case=False, na=False)]
    if source_filter != "All":
        filtered = filtered[filtered["Source File"] == source_filter]

    filtered["Raw Value"] = filtered["Raw Value"].astype(str)
    filtered["Normalized Value"] = filtered["Normalized Value"].astype(str)
    st.caption(f"Displaying {len(filtered)} of {len(df)} total claims")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    csv_data = filtered.to_csv(index=False)
    st.download_button(
        "⬇️ Download Filtered Claims (CSV)",
        data=csv_data,
        file_name="extracted_claims.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Tab 4: Contradiction Analysis
# ---------------------------------------------------------------------------

def render_contradictions():
    st.markdown("## ⚡ Contradiction Analysis & Traceability")

    report: DetectionReport | None = st.session_state.detection_report
    if report is None:
        st.info("No analysis data available. Run analysis from the Dashboard or Upload tab first.")
        return

    view = st.radio(
        "Filter View",
        ["🔴 Contradictions Only", "🟢 Consistent Groups", "🟡 Uncertain / Inconclusive", "All Records"],
        horizontal=True,
    )

    if "🔴 Contradictions Only" in view or "All Records" in view:
        st.markdown(f"### 🔴 Detected Contradictions ({report.contradiction_count})")
        if not report.contradictions:
            st.success("✅ Zero contradictions detected! All claims across all documents are consistent.")
        else:
            for c in report.contradictions:
                with st.expander(
                    f"[{c.contradiction_id}] {c.entity} — {c.attribute.upper()}  |  Confidence: {c.confidence:.0%}",
                    expanded=True,
                ):
                    verdict_str = getattr(c, "verdict", "contradiction").upper()
                    breakdown = getattr(c, "confidence_breakdown", {})
                    breakdown_html = ""
                    if breakdown:
                        parts = [f"<b>{k.replace('_', ' ').title()}:</b> {v:.2f}" for k, v in breakdown.items()]
                        breakdown_html = f"<div style='margin-top:6px; font-size:0.85rem; color:#8B949E;'>" + " &nbsp;|&nbsp; ".join(parts) + "</div>"

                    st.markdown(
                        f"""
                        <div class="contradiction-card">
                            <b>Status:</b> {c.status} &nbsp;|&nbsp; <b>Verdict:</b> <span style="color:#F85149; font-weight:700;">{verdict_str}</span><br>
                            <b>Finding:</b> {c.explanation}
                            {breakdown_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    tdata = []
                    for cl in c.conflicting_claims:
                        tdata.append({
                            "Source Document": cl.source,
                            "Location": cl.page_or_sheet,
                            "Claimed Value": cl.value,
                            "Unit": cl.unit,
                            "Time Period": cl.date_str,
                            "Confidence": f"{cl.confidence:.0%}",
                            "Original Text Excerpt": cl.original_text,
                        })
                    st.markdown("**Conflicting Evidence Sources (All Preserved):**")
                    st.dataframe(pd.DataFrame(tdata), use_container_width=True, hide_index=True)

    if "🟢 Consistent Groups" in view or "All Records" in view:
        st.markdown(f"### 🟢 Consistent Groups ({len(report.consistent_groups)})")
        for i, grp in enumerate(report.consistent_groups, 1):
            if grp:
                with st.expander(
                    f"Consistent Group {i}: {grp[0].entity_normalized} — {grp[0].attribute} ({len(grp)} sources matching)"
                ):
                    tdata = [
                        {
                            "Source Document": cl.source,
                            "Value": cl.value,
                            "Unit": cl.unit,
                            "Date": cl.date_str,
                            "Original Text": cl.original_text,
                        }
                        for cl in grp
                    ]
                    st.dataframe(pd.DataFrame(tdata), use_container_width=True, hide_index=True)

    if "🟡 Uncertain / Inconclusive" in view or "All Records" in view:
        st.markdown(f"### 🟡 Uncertain Claims ({len(report.uncertain_groups)})")
        for i, grp in enumerate(report.uncertain_groups, 1):
            if grp:
                with st.expander(
                    f"Uncertain Group {i}: {grp[0].entity_normalized} — {grp[0].attribute} ({len(grp)} claims)"
                ):
                    tdata = [
                        {
                            "Source Document": cl.source,
                            "Value": cl.value,
                            "Unit": cl.unit,
                            "Date": cl.date_str,
                        }
                        for cl in grp
                    ]
                    st.dataframe(pd.DataFrame(tdata), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Tab 5: Graph Visualization
# ---------------------------------------------------------------------------

def render_graph():
    st.markdown("## 🕸️ Knowledge & Conflict Graph")

    gb: GraphBuilder | None = st.session_state.graph_builder
    if gb is None or gb.G.number_of_nodes() == 0:
        st.info("No graph generated yet. Run analysis to construct relationship graph.")
        return

    graph_data = gb.get_plotly_data()
    all_traces = graph_data["edge_traces"] + graph_data["node_traces"]
    fig = go.Figure(data=[go.Scatter(**t) for t in all_traces], layout=graph_data["layout"])
    fig.update_layout(
        height=620,
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font_color="#F0F6FC",
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    G = gb.G
    with col1:
        st.metric("Total Graph Nodes", G.number_of_nodes())
    with col2:
        st.metric("Relationship Edges", G.number_of_edges())
    with col3:
        entity_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "entity"]
        st.metric("Entity Nodes", len(entity_nodes))

    col_a, col_b = st.columns(2)
    with col_a:
        json_str = json.dumps(gb.to_json(), indent=2)
        st.download_button(
            "⬇️ Export Graph as JSON",
            data=json_str,
            file_name="knowledge_graph.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_b:
        try:
            import networkx as nx
            with tempfile.NamedTemporaryFile(suffix=".graphml", delete=False) as tf:
                nx.write_graphml(G, tf.name)
                graphml_bytes = Path(tf.name).read_bytes()
            st.download_button(
                "⬇️ Export Graph as GraphML",
                data=graphml_bytes,
                file_name="knowledge_graph.graphml",
                mime="application/xml",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"GraphML export unavailable: {e}")


# ---------------------------------------------------------------------------
# Tab 6: Source Traceability & Provenance Inspector
# ---------------------------------------------------------------------------

def render_traceability():
    st.markdown("## 🔍 Source Traceability & Provenance Inspector")

    claims: list[Claim] = st.session_state.claims
    report: DetectionReport | None = st.session_state.detection_report

    if not claims:
        st.info("No claims available for inspection. Ingest documents and run analysis first.")
        return

    st.markdown(
        "Trace every claim back to its exact document origin, page/sheet, modality, "
        "and conflict status."
    )

    # Build conflict map: claim_id -> (status, contradiction_id)
    conflict_map = {}
    if report:
        for c in report.contradictions:
            for cl in c.conflicting_claims:
                conflict_map[cl.claim_id] = ("🔴 CONTRADICTION", c.contradiction_id)
        for i, grp in enumerate(report.consistent_groups, 1):
            for cl in grp:
                conflict_map[cl.claim_id] = ("🟢 CONSISTENT", f"GRP-{i:02d}")
        for j, grp in enumerate(report.uncertain_groups, 1):
            for cl in grp:
                conflict_map[cl.claim_id] = ("🟡 UNCERTAIN", f"UNCERT-{j:02d}")

    # Traceability cards
    for idx, cl in enumerate(claims, 1):
        status_badge, group_ref = conflict_map.get(cl.claim_id, ("⚪ UNVERIFIED", "NONE"))
        with st.expander(
            f"[{idx}] {cl.entity_normalized} — {cl.attribute.upper()} ({cl.value} {cl.unit}) | {status_badge} ({cl.source})",
            expanded=(idx <= 3),
        ):
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"**Claim ID:** `{cl.claim_id}`")
                st.markdown(f"**Original Entity:** `{cl.entity}`")
                st.markdown(f"**Canonical Entity:** `{cl.entity_normalized}`")
                st.markdown(f"**Attribute:** `{cl.attribute}`")
                st.markdown(f"**Claimed Value:** `{cl.value} {cl.unit}`")
                st.markdown(f"**Canonical Value:** `{cl.value_normalized} {cl.unit_normalized}`")
            with c2:
                st.markdown(f"**Source Document:** `{cl.source}`")
                st.markdown(f"**Document Location:** `{cl.page_or_sheet}`")
                st.markdown(f"**Modality / Fact Type:** `{cl.modality.upper()}`")
                st.markdown(f"**Temporal Interval:** `{cl.date_normalized or cl.date_str or 'Not Specified'}`")
                st.markdown(f"**Extraction Confidence:** `{cl.confidence:.0%}`")
                st.markdown(f"**Conflict Evaluation:** `{status_badge} ({group_ref})`")

            st.markdown("**Original Extracted Excerpt:**")
            st.code(cl.original_text, language="text")


# ---------------------------------------------------------------------------
# Tab 7: Reports & Export
# ---------------------------------------------------------------------------

def render_reports():
    st.markdown("## 📄 Comprehensive Reports & Export")

    report: DetectionReport | None = st.session_state.detection_report
    claims: list[Claim] = st.session_state.claims

    if report is None:
        st.info("Run analysis first to produce downloadable reports.")
        return

    st.markdown("### 📥 Download Formal Reports")
    col1, col2, col3 = st.columns(3)

    rels = getattr(st.session_state, "entity_relationships", [])

    with col1:
        json_str = generate_json_report(report, claims, entity_relationships=rels)
        st.download_button(
            "📥 Download JSON Report",
            data=json_str,
            file_name=f"contradiction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col2:
        csv_str = generate_csv_report(report)
        st.download_button(
            "📥 Download CSV Report",
            data=csv_str,
            file_name=f"contradiction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col3:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            pdf_path = tf.name

        result_path = generate_pdf_report(report, claims, pdf_path, entity_relationships=rels)
        if result_path:
            pdf_bytes = Path(result_path).read_bytes()
            st.download_button(
                "📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"contradiction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.warning("PDF report generation requires reportlab.")

    st.markdown("---")
    st.markdown("### 📝 Audit Summary")
    st.markdown(
        f"""
        | Metric | Count / Detail |
        |---|---|
        | **Total Claims Analyzed** | {report.total_claims} |
        | **Contradictions Identified** | {report.contradiction_count} |
        | **Consistent Fact Groups** | {report.consistent_count} |
        | **Uncertain Claims** | {report.uncertain_count} |
        | **Generated At** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
        """
    )


# ---------------------------------------------------------------------------
# Main Layout
# ---------------------------------------------------------------------------

def main():
    render_sidebar()

    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:8px;">
            <span style="font-size:2.4rem;">🔍</span>
            <div>
                <h1 style="margin:0; font-size:2rem; color:#FFFFFF;">AI-Powered Contradiction Detection System</h1>
                <div style="color:#8B949E; font-size:0.95rem;">
                    Multimodal document ingestion · Entity disambiguation · Deterministic conflict detection · NetworkX graph
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "📊 Dashboard",
        "📁 Upload & Process",
        "📋 Extracted Claims",
        "⚡ Contradictions",
        "🕸️ Graph",
        "🔍 Source Traceability",
        "📄 Reports",
    ])

    with tabs[0]:
        render_dashboard()
    with tabs[1]:
        render_upload()
    with tabs[2]:
        render_claims()
    with tabs[3]:
        render_contradictions()
    with tabs[4]:
        render_graph()
    with tabs[5]:
        render_traceability()
    with tabs[6]:
        render_reports()


if __name__ == "__main__":
    main()
