# CERBERUS-XA — Multimodal Evidence Graph & Conflict-Aware Reasoning

> **"Where Every Modality Can Contradict the Others."**  
> **"Every Source Has a Voice. Every Claim Faces Verification."**

---

## 1. Project Description

**CERBERUS-XA** is an offline-capable multimodal evidence investigation and conflict-aware intelligence platform. Rather than functioning as a generic chatbot or file viewer, it is engineered for forensic auditing, supply-chain verification, and cross-document contradiction analysis.

It ingests **PDF documents, scanned images, optical imagery (PNG/JPG), and structured tabular files (CSV/XLSX/XLS)**, extracts atomic claims with page/row provenance, constructs a connected Knowledge Graph, resolves cross-source entities, detects numerical/temporal/textual contradictions, evaluates 6-dimension source reliability, flags adversarial tampering, and produces traceable, evidence-backed answers (explicitly abstaining with `INSUFFICIENT_EVIDENCE` when evidence is inadequate).

---

## 2. Problem Statement

Real-world investigations span heterogeneous formats (invoices in PDF, warehouse logs in CSV, inspection notes in scanned images). Conventional RAG or single-modality pipelines suffer from:
- **Modality Bias**: Favoring clean digital text over scanned/tabular records.
- **Hidden Contradictions**: Failing to catch discrepancies across independent files (e.g., `500 units` invoiced vs. `450 units` received).
- **Unverified Hallucinations**: Generating confident answers even when evidence is missing or conflicting.

CERBERUS-XA solves this by treating every source equally, surfacing conflicts explicitly, and linking every conclusion to verifiable source coordinates.

---

## 3. Key Features

- **Multimodal Ingestion**: Parses PDFs (`PyMuPDF`), images/scans (`RapidOCR` / `Pillow`), and spreadsheets (`Pandas` / `OpenPyXL`).
- **Knowledge Graph & Entity Resolution**: Builds a NetworkX multi-relational graph unifying entities, attributes, quantities, sources, support edges (`supports`, `agrees_with`), and contradiction edges (`contradicts`).
- **Contradiction Detection**: Detects cross-source numerical, temporal, and textual discrepancies.
- **6-Dimension Source Reliability & Adversarial Defense**: Evaluates provenance, directness, corroboration, consistency, and completeness; flags metadata backdating and prompt-injection patterns.
- **Conflict-Aware 7-Stage Reasoning**: Synthesizes traceable verdicts (`ANSWERED`, `CONFLICTED`, `INSUFFICIENT_EVIDENCE`) with deterministic offline fallback and optional local Ollama (`qwen2.5:7b-instruct`) synthesis.
- **Multi-Format Dossier Export**: Exports investigation reports as **Markdown (`.md`)**, **JSON**, **CSV**, and **PDF**.
- **Dual Theme & Demo/Live Modes**: Supports high-contrast Dark and Light themes plus a pre-loaded Jury Benchmark Demo mode (`Operation Boreas`) alongside Live Ingest mode.

---

## 4. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite 6, Tailwind CSS, Framer Motion, Axios, Recharts, Lucide Icons |
| **Unified Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic v2 |
| **Multimodal Extraction** | PyMuPDF (`fitz`), RapidOCR (`rapidocr-onnxruntime`), Pillow, Pandas, OpenPyXL |
| **Knowledge Graph & Matching** | NetworkX, RapidFuzz |
| **AI Reasoning** | Deterministic 7-Stage Verification Engine + Optional Local Ollama (`qwen2.5:7b-instruct`) |
| **Frontend Hosting** | Firebase Hosting (Static SPA) |

---

## 5. System Architecture

```
+-------------------------------------------------------------------+
|               CERBERUS-XA React + Vite UI (Port 5173)             |
|  Overview | Evidence Center | Knowledge Graph | Conflict & Trust  |
|               AI Investigation | Reports & Audit                  |
+-------------------------------------------------------------------+
                                  |  REST API (Axios -> Port 8000)
                                  v
+-------------------------------------------------------------------+
|            Unified FastAPI Server (backend/main.py)               |
+-------------------------------------------------------------------+
   |                              |                              |
   v                              v                              v
[Member 2: Multimodal]    [Member 3: Knowledge Graph]   [Member 4: Reasoning]
backend/multimodal/       backend/knowledge_graph/      backend/reasoning/
- POST /process-file      - GET /graph                  - POST /investigate
- POST /process-batch     - GET /conflicts              - POST /reasoning/verify
- GET /evidence           - GET /entity-resolution      - GET /reliability
- DELETE /evidence/{id}   - GET /claims                 - GET /adversarial
                                                        - GET /export-report
```

---

## 6. Project Folder Structure

```
CERBERUS-XA/
├── backend/
│   ├── main.py                  # Unified FastAPI entrypoint & pipeline orchestrator
│   ├── multimodal/              # PDF, Image/OCR, and Table extraction engine
│   ├── knowledge_graph/         # Entity matching, contradiction detector, NetworkX graph
│   ├── reasoning/               # 7-stage reasoning, reliability, suspicion & citation builder
│   ├── verify_deep.py           # End-to-end backend & export verification suite
│   ├── verify_graph_laptop_x.py # Knowledge Graph 2-file verification
│   └── verify_conflict_vs_nonconflict.py
├── src/
│   ├── components/              # Navbar, Sidebar, RightPanel, KnowledgeGraph, ReportViewer, etc.
│   ├── context/                 # InvestigationContext (Live & Demo state management)
│   ├── pages/                   # 6 Command Center hubs + LandingPage
│   ├── services/                # Axios API clients (evidence, conflict, graph, investigation)
│   └── data/demoData.js         # Jury Benchmark Demo dataset
├── sample_evidence/             # Sample CSV evidence files
├── firebase.json                # Firebase Hosting SPA configuration
├── requirements.txt             # Consolidated Python backend dependencies
├── package.json                 # Frontend dependencies & Vite scripts
└── .env.example                 # Environment variable template
```

---

## 7. Installation Instructions

### Prerequisites
- **Node.js** 18+ and **npm**
- **Python** 3.10+
- *(Optional)* **Ollama** running locally with `qwen2.5:7b-instruct` for LLM-augmented phrasing

### Frontend Setup
```bash
npm install
```

### Backend Setup
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

---

## 8. Environment Variable Setup

Copy `.env.example` to `.env` (never commit `.env` to Git):
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_DEMO_FALLBACK=true
```
For production Firebase deployments connected to a hosted Python backend, set `VITE_API_BASE_URL` to your HTTPS backend URL before running `npm run build`.

---

## 9. Local Execution Instructions

1. **Start the Unified FastAPI Backend** (Port `8000`):
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
   Interactive API docs: `http://localhost:8000/docs`

2. **Start the React + Vite Frontend** (Port `5173`):
   ```bash
   npm run dev -- --host 0.0.0.0 --port 5173
   ```
   Open `http://localhost:5173` in your browser.

3. **Run Verification Suites**:
   ```bash
   npm run build
   python backend/verify_deep.py
   python backend/verify_conflict_vs_nonconflict.py
   python backend/verify_graph_laptop_x.py
   ```

---

## 10. Firebase Deployment Instructions

> **Note on Architecture Compatibility**: Firebase Hosting serves the static React/Vite SPA (`dist/`). Because the Python FastAPI backend uses PyMuPDF, RapidOCR ONNX, and NetworkX, it cannot execute inside Firebase Hosting itself—deploy `backend/` on a Python container host (e.g., Google Cloud Run, Render, or Railway) or run it locally, and point `VITE_API_BASE_URL` to it. Without a live backend URL, the hosted frontend operates in **Demo Mode**.

```bash
npm install -g firebase-tools
firebase login
npm run build
firebase deploy --only hosting
```

---

## 11. Screenshots

- **Cinematic Landing Page**: Three-headed Cerberus sentinel carousel with Dark & Light theme support.
- **Evidence Center & Vault**: Multi-format drag-and-drop ingestion with per-file deletion and provenance inspection.
- **Knowledge Graph**: Interactive SVG graph showing entities, supporting sources, consistency status, and conflict edges.
- **AI Investigation & Reports**: Traceable verdicts with concise reasoning, citations, and `.md`/`.json`/`.csv`/`.pdf` exports.

---

## 12. Future Enhancements

- Cloud Run / Docker containerization for one-click cloud backend deployment alongside Firebase Hosting.
- Persistent database storage (PostgreSQL / Firestore) for multi-user case history across sessions.
- Asynchronous background job queue for very large multi-hundred-page PDF batches.
