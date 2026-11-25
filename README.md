# CERBERUS-XA — Frontend & UI Intelligence Platform

> **Multimodal Evidence Graph Construction & Conflict-Aware Reasoning**  
> *"Where Every Modality Can Contradict the Others."*  
> *"Every Source Has a Voice. Every Claim Faces Verification."*  
> **24-Hour AI/ML Hackathon | Member 1: Frontend & UI Development**

---

## 🛡️ Project Overview

**CERBERUS-XA** is an offline-capable multimodal intelligence investigation command center. Rather than acting as a generic chatbot or ordinary file manager, it is engineered for defense, fraud examination, and forensic investigation.

It ingests **PDF documents, high-resolution optical imagery, scanned records, and tabular spreadsheets/CSVs**, extracts atomic claims with spatial/row coordinates, constructs a connected knowledge graph, resolves entity aliases, uncovers cross-modal contradictions, evaluates source reliability without fabricating ungrounded scores, flags adversarial/manipulated content, and delivers traceable, evidence-backed answers.

---

## 🤖 Visual Identity & Artwork Integration

The primary visual identity features the three-headed robotic guardian:
- **Location**: `src/assets/cerberus-three-heads.png`
- **Landing Page**: Large cinematic hero background with a dark navy vignette overlay so all three robotic heads remain visible across all screen sizes.
- **Dashboard Overview**: Low-opacity watermark visual on the upper right command center.
- **Color Palette**:
  - Main Background: `#050A16`
  - Secondary Background: `#0B1426`
  - Card Background: `#101C30`
  - Glass Panels: `rgba(16, 28, 48, 0.72)`
  - Primary Blue: `#3478F6`
  - Electric Cyan: `#36D8F2`
  - Gold: `#F5B942`
  - Success Green: `#21C997`
  - Conflict Amber: `#FFB547`
  - Suspicious Red: `#FF536B`
  - Main Text: `#F1F5F9`
  - Secondary Text: `#94A3B8`

---

## 🏢 3-Zone Workspace Command Center Architecture

1. **Zone A (Left Sidebar)**: Collapsible, responsive navigation with 14 intelligence modules:
   1. *Overview* (`Dashboard.jsx`)
   2. *Investigations* (`InvestigationsPage.jsx`)
   3. *Data Ingestion* (`UploadPage.jsx`)
   4. *Evidence Vault* (`EvidencePage.jsx`)
   5. *Modality Explorer* (`ModalityExplorer.jsx`)
   6. *Knowledge Graph* (`KnowledgeGraphPage.jsx`)
   7. *Entity Resolution* (`EntityResolutionPage.jsx`)
   8. *Conflict Detection* (`ConflictPage.jsx`)
   9. *Reliability Analysis* (`ReliabilityPage.jsx`)
   10. *Adversarial Analysis* (`AdversarialPage.jsx`)
   11. *AI Reasoning Engine* (`ReasoningPage.jsx`)
   12. *Answer Studio* (`ReportPage.jsx`)
   13. *Audit & Evaluation* (`AuditPage.jsx`)
   14. *Settings* (`SettingsPage.jsx`)

2. **Zone B (Center Workspace)**: The active intelligence view with statistics cards, interactive charts, and evidence inspection panels.

3. **Zone C (Right Intelligence Panel)**: Collapsible real-time status monitor:
   - Live FastAPI connectivity status (only reports `ONLINE` when confirmed by `/health`)
   - Active contradiction radar
   - Adversarial red flag alerts
   - Vault files feed

---

## 👥 4-Member Team Architecture & Integration

```
+-------------------------------------------------------------------------+
|                  CERBERUS-XA MULTIMODAL INTELLIGENCE                     |
+-------------------------------------------------------------------------+
       |
       v
+-----------------------+     REST Contracts      +------------------------+
|  Member 2: Ingest     | ----------------------> |  Member 1: UI Console  |
|  Multimodal Extraction|   POST /process-file    |  React + Vite + Tailw. |
|  PDF, Image, Table    |   POST /process-batch   |  Recharts + Axios      |
+-----------------------+                         +------------------------+
       |                                                      ^
       v                                                      |
+-----------------------+     REST Contracts                  |
|  Member 3: Graph      | ------------------------------------+
|  Conflict Detection   |   GET /claims
|  Topology & Edges     |   GET /conflicts & GET /graph
|  Entity Resolution    |   GET /entity-resolution
+-----------------------+                                     |
       |                                                      |
       v                                                      |
+-----------------------+     REST Contracts                  |
|  Member 4: Reasoning  | ------------------------------------+
|  Neural Verification  |   POST /investigate
|  Reliability & Audit  |   GET /investigation-report/{id}
|  Forensic Dossier     |   GET /reliability & GET /adversarial
+-----------------------+
```

---

## 🚀 Quickstart & Setup

```bash
# 1. Install dependencies
npm install

# 2. Start development server
npm run dev

# 3. Build production bundle
npm run build
```

Open [http://localhost:5173](http://localhost:5173) in your browser.
