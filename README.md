# CERBERUS-XA — Multimodal Evidence Graph & Conflict-Aware Reasoning System

> *"Where Every Modality Can Contradict the Others."*  
> *"Every Source Has a Voice. Every Claim Faces Verification."*

---

## 🛡️ Project Overview

**CERBERUS-XA** is an offline-capable multimodal intelligence investigation platform engineered for defense, fraud examination, and forensic investigation. Unlike conventional chatbot-style question-answering systems that assume input documents are truthful and consistent, CERBERUS-XA assumes **sources may contradict, omit, or misrepresent facts across modalities**.

The system ingests **unstructured PDF documents, high-resolution optical imagery, scanned records, and tabular spreadsheets/CSVs**, extracts atomic claims with spatial/row coordinates, constructs a connected knowledge graph, resolves entity aliases, uncovers cross-modal contradictions, evaluates source reliability without fabricating ungrounded scores, flags adversarial/manipulated content, and delivers traceable, evidence-backed answers.

---

## 🎯 Problem Statement

Modern intelligence analysts and investigators face an overwhelming volume of multimodal data from disparate origins. Traditional LLM-based tools suffer from critical shortcomings:
1. **Blind Trust & Hallucination**: Assuming all input text or tabular data is factually consistent.
2. **Modal Blind Spots**: Inability to reconcile contradictions where text claims one value (e.g. *"$120,000 shipment value"* in a PDF) while a customs receipt image or cargo manifest table specifies another (*"$450,000"*).
3. **Black-Box Reasoning**: Providing answers without verifiable, coordinate-level citations back to the source bounding box or table cell.
4. **Vulnerability to Manipulation**: Susceptibility to prompt injections and adversarial data buried within scanned documents or CSV fields.

**CERBERUS-XA resolves this by treating every claim as a node in an adversarial evidence graph, cross-verifying facts across all modalities before rendering a forensic verdict.**

---

## ✨ Key Features

### 1. Unified 6-Hub Intelligence Command Center
- **Landing Hub**: Cinematic operational command portal showcasing system capabilities and system health.
- **Overview & Dashboard**: Real-time stats on ingested documents, active entities, contradiction counts, and audit trails.
- **Evidence Center**: Multi-format ingestion vault supporting PDF, PNG/JPG, and CSV/XLSX files with live coordinate-level claim extractions.
- **Knowledge Graph Hub**: Dynamic 2D/3D force-directed relationship topology with fuzzy entity resolution and alias clustering.
- **Conflict & Trust Analysis**: Cross-modal contradiction radar, evidence reliability matrix, and adversarial prompt-injection scanner.
- **AI Investigation Hub & Answer Studio**: Natural-language forensic inquiry engine with step-by-step reasoning chains, coordinate citations, and exportable reports (JSON, CSV, PDF, Markdown).
- **Reports & Audit Trail**: Immutable investigation history with multi-case retention and verification replay.

### 2. Deep Multimodal Processing Pipeline
- **PDF Extraction**: Text blocks, spatial bounding boxes, page indices, and metadata via PyMuPDF.
- **Optical Character Recognition (OCR)**: Scanned documents, receipts, badges, and scene images extracted via RapidOCR (ONNX Runtime) with confidence scoring.
- **Tabular Extraction**: CSV and Excel sheets extracted cell-by-cell with row/column coordinate preservation using Pandas and OpenPyXL.

### 3. Knowledge Graph & Cross-Modal Conflict Detection
- **Entity Resolution**: Levenshtein distance and RapidFuzz matching to cluster aliases (e.g., *"Nordic Freight Ltd."* vs. *"Nordic-Freight Logistics"*).
- **Contradiction Engine**: Identifies numeric, temporal, and categorical conflicts across different modalities for the same entity and attribute.
- **NetworkX Topology**: Visualizes nodes, directed claim edges, and conflict links.

### 4. Conflict-Aware Reasoning & Forensic Verification
- **Traceable Citations**: Every conclusion cites specific evidence IDs, modalities, bounding boxes, or table rows.
- **Verdict Classification**: Renders verdicts (*ANSWERED*, *CONFLICT_DETECTED*, *INSUFFICIENT_EVIDENCE*, *ADVERSARIAL_DETECTED*) with calibrated confidence ratios.
- **Prompt Injection Defense**: Suspicion detector flags attempts to override system instructions inside ingested files.
- **Dual-Mode Execution**: Live FastAPI backend integration with automatic fallback to high-fidelity simulated demo mode when offline.

---

## 🏗️ System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                        CERBERUS-XA SYSTEM                                         |
+---------------------------------------------------------------------------------------------------+
                                                  |
           +--------------------------------------+--------------------------------------+
           |                                                                             |
           v                                                                             v
+-----------------------------------------+                 +-----------------------------------------+
|        FRONTEND COMMAND CENTER          |                 |          FASTAPI BACKEND API            |
|       (React 18 + Vite 6 + Tailwind)    |                 |        (Python 3.10+ / Uvicorn)         |
|                                         |                 |                                         |
|  - 6 Intelligence Workspace Hubs        |  REST Contracts |  - Member 2: Multimodal Ingestion       |
|  - Interactive Network Topology         | <=============> |    (PyMuPDF, RapidOCR, Pandas, PIL)     |
|  - Real-Time Contradiction Radar        |  (Axios Client) |  - Member 3: Knowledge Graph            |
|  - Evidence Vault & Modality Explorer   |                 |    (NetworkX, RapidFuzz, ClaimBuilder)  |
|  - Dual Mode (Live API / Demo Fallback) |                 |  - Member 4: Reasoning & Verification   |
+-----------------------------------------+                 |    (CitationBuilder, SuspicionDetector) |
                                                            +-----------------------------------------+
```

---

## 📂 Project Folder Structure

```
CERBERUS-XA/
├── backend/                        # Python FastAPI Intelligence Backend
│   ├── main.py                     # Unified FastAPI application entry point
│   ├── test_pipeline.py            # End-to-end backend integration test
│   ├── verify_tasks_1_2_3.py       # Verification & regression test suite
│   ├── multimodal/                 # Member 2: Ingestion & OCR processing
│   │   ├── processor.py            # Multimodal extractor (PDF, images, tables)
│   │   ├── models.py               # Extraction schemas & data models
│   │   └── ocr_engine.py           # RapidOCR ONNX runtime integration
│   ├── knowledge_graph/            # Member 3: Graph & entity resolution
│   │   └── src/                    # Graph builder, claim builder, contradiction detector
│   └── reasoning/                  # Member 4: Conflict-aware reasoning engine
│       ├── service.py              # Reasoning router & pipeline execution
│       ├── schemas.py              # Pydantic schemas (ReasoningRequest, EvidenceItem)
│       ├── citation_builder.py     # Source citation & coordinate linking
│       ├── suspicion_detector.py   # Adversarial prompt-injection detection
│       └── tests/                  # Pytest verification suites
├── src/                            # React 18 Frontend Application
│   ├── App.jsx                     # Root application with 6-hub router & layout
│   ├── main.jsx                    # React DOM entry point
│   ├── index.css                   # Tailwind styles, radar animations & glassmorphism
│   ├── components/                 # Reusable UI components
│   │   ├── Navbar.jsx              # Global navigation bar with backend status
│   │   ├── Sidebar.jsx             # 6 primary intelligence hub navigation
│   │   ├── RightPanel.jsx          # Live contradiction radar & file feed
│   │   ├── KnowledgeGraph.jsx      # Force-directed interactive network graph
│   │   └── ReportViewer.jsx        # Forensic dossier viewer with export actions
│   ├── context/
│   │   └── InvestigationContext.jsx# Centralized investigation state & API bindings
│   ├── pages/                      # 20 Modular Intelligence Page Views
│   │   ├── LandingPage.jsx         # Cinematic hero showcase
│   │   ├── Dashboard.jsx           # Overview metrics & activity feeds
│   │   ├── EvidenceCenterPage.jsx  # Unified ingestion vault & previews
│   │   ├── KnowledgeGraphHubPage.jsx# Graph exploration & entity resolution
│   │   ├── ConflictTrustPage.jsx   # Contradiction lab & adversarial scanner
│   │   ├── AIInvestigationPage.jsx # Natural-language inquiry & reasoning steps
│   │   └── ReportsAuditPage.jsx    # Audit trail, case history & evaluations
│   └── services/                   # Axios API service clients
│       ├── api.js                  # Base Axios configuration & interceptors
│       ├── evidenceService.js      # File upload, claims, and vault APIs
│       └── investigationService.js # Investigation query & report export APIs
├── dist/                           # Production build output (gitignored)
├── public/                         # Public static web assets
├── firebase.json                   # Firebase Hosting configuration
├── .firebaserc                     # Firebase project alias
├── .env.example                    # Sample environment configuration
├── package.json                    # Node dependencies and build scripts
├── requirements.txt                # Python backend dependencies
├── tailwind.config.js              # Custom theme colors & typography
└── vite.config.js                  # Vite configuration & server options
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend Framework** | React 18, Vite 6, Tailwind CSS 3.4 |
| **UI Components & Icons** | Framer Motion (page animations), Lucide React, Recharts |
| **HTTP Client** | Axios with custom interceptors and timeout management |
| **Backend Framework** | FastAPI 0.110+, Uvicorn 0.28+, Pydantic 2.0+ |
| **Multimodal Extraction** | PyMuPDF (PDF), RapidOCR ONNX (OCR), Pillow (Images), Pandas & OpenPyXL (Tables) |
| **Graph & Entity Resolution** | NetworkX 3.3+, RapidFuzz 3.9+, PyYAML |
| **Deployment Platforms** | Firebase Hosting (Frontend SPA), Cloud Run / Docker (Backend API) |

---

## ⚙️ Environment Variables Setup

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Configurable options:

```ini
# Frontend API Base URL (FastAPI Backend)
VITE_API_BASE_URL=http://localhost:8000

# Enable offline fallback demo data when FastAPI is unreachable
VITE_ENABLE_DEMO_FALLBACK=true
```

---

## 🚀 Installation & Local Execution

### Prerequisites
- **Node.js**: v18.0.0 or higher (v24 LTS tested)
- **Python**: v3.10 or higher (v3.14 tested)

### 1. Frontend Setup
```bash
# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
The frontend command center will be available at `http://localhost:5173`.

### 2. Backend Setup
```bash
# Create and activate virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Python backend dependencies
pip install -r requirements.txt

# Start Unified FastAPI Backend server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
The interactive Swagger API documentation will be available at `http://localhost:8000/docs`.

### 3. Production Build
```bash
# Build the optimized production bundle
npm run build

# Preview production build locally
npm run preview
```

---

## ☁️ Firebase Deployment Instructions

CERBERUS-XA is configured for deployment to **Firebase Hosting** for high-performance global CDN delivery with client-side SPA routing.

### 1. Install & Authenticate Firebase CLI
```bash
# Log in to your Firebase account
npx firebase-tools login
```

### 2. Link Your Firebase Project
```bash
# Use your target Firebase project ID
npx firebase-tools use <your-firebase-project-id>
```

### 3. Deploy to Firebase Hosting
```bash
# Build production bundle
npm run build

# Deploy hosting assets
npx firebase-tools deploy --only hosting
```

Your application will be live at: `https://<your-firebase-project-id>.web.app`.

---

## 🖼️ Visual Identity & Screenshots

The platform features a defense-grade dark palette (`#050A16`) with electric cyan accents (`#36D8F2`), gold highlights (`#F5B942`), and amber conflict indicators (`#FFB547`).

- **Cinematic Guardian Artwork**: High-resolution three-headed robotic guardian at `src/assets/cerberus-three-heads.png`.
- **Radar Scan Visualizer**: Real-time rotating radar scanning active evidence for anomalies.
- **Interactive Force Graph**: Dynamic physics-based entity relationship mapping.

---

## 🔮 Future Enhancements

- [ ] **Real-Time WebRTC Video Stream Analysis**: Frame-by-frame contradiction tagging in video feeds.
- [ ] **Zero-Knowledge Evidence Proofs**: Cryptographic proofs of document authenticity without disclosing sensitive content.
- [ ] **Collaborative Multi-Analyst Dossier Rooms**: Real-time shared investigation canvases.
- [ ] **Containerized Docker Compose Setup**: Single-command orchestration for frontend, FastAPI, Ollama LLM, and Redis cache.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
