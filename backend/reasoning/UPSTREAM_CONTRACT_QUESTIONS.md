# CERBERUS-XA — Upstream Contract Confirmation Questions for Members 2 & 3

**From:** Member 4 (AI Reasoning & Evidence Verification)  
**To:** Member 2 (Processor) & Member 3 (Knowledge Graph)  
**Status:** **ASSUMED — Awaiting confirmation or correction**

---

## Context
Member 4's reasoning module is built and passing 86 unit and integration tests. To ensure reliable inter-module data flow once your modules are committed, Member 4 has implemented an integration adapter (`backend/reasoning/adapter.py`). 

Because your code is not yet committed to this repository, the field names below are **assumed based on common conventions**. Please review the expected fields and let me know if any keys need to be corrected.

---

## 1. Questions for Member 2 (Document & Multi-Modal Processor)

### Evidence Item / Chunk Schema
Member 4's adapter currently expects evidence chunks to provide the following keys (or one of their aliases):

| Field Purpose | Required / Optional | Assumed Aliases Checked by Adapter | Default if Missing |
| :--- | :---: | :--- | :--- |
| **Evidence ID** | **Required** | `id`, `chunk_id`, `evidence_id`, `doc_id` | **Fails (raises AdapterError)** |
| **Text Content** | **Required** | `content`, `text`, `extracted_text`, `body`, `raw_text`, `snippet` | **Fails (raises AdapterError)** |
| **Source Modality** | **Required** | `modality`, `source_type`, `file_type` (e.g. `'pdf'`, `'image'`, `'ocr'`, `'table'`, `'csv'`, `'scan'`) | **Fails (raises AdapterError)** |
| **Source ID** | Optional | `metadata.source_id`, `source`, `source_name` | `"UNKNOWN_PROCESSOR_SRC"` (warning logged) |
| **Filename** | Optional | `metadata.filename`, `file_name`, `doc_name` | `None` |
| **Page Number** | Optional | `metadata.page_number`, `page`, `page_no` | `None` |
| **Directness** | Optional | `directness` (`'primary'`, `'secondary'`, `'hearsay'`, `'unverified'`) | `'primary'` (warning logged) |
| **Confidence** | Optional | `metadata.extraction_confidence`, `ocr_confidence`, `confidence` | `1.0` |

*Questions for Member 2:*
1. What exact top-level key contains your processed chunks (e.g., `{"documents": [...]}`, `{"chunks": [...]}`, or a bare `[...]`)?
2. Are you using `id` or `chunk_id` for chunk identifiers?
3. Are you using `content` or `text` for extracted content?
4. What string values do you emit for multi-modal formats (e.g., `'pdf'`, `'ocr'`, `'table'`, `'csv'`)?

---

### Extracted Claims Schema (if emitted by Processor)
| Field Purpose | Required / Optional | Assumed Aliases Checked by Adapter | Default if Missing |
| :--- | :---: | :--- | :--- |
| **Statement** | **Required** | `statement`, `text`, `claim`, `assertion` | **Fails (raises AdapterError)** |
| **Claim ID** | Optional | `id`, `claim_id` | Auto-generated (`CLM-PROC-xxx`) |
| **Subject Entity** | Optional | `entity`, `subject` | `None` |
| **Property** | Optional | `property`, `predicate`, `attribute` | `None` |
| **Value** | Optional | `value`, `object` | `None` |
| **Unit** | Optional | `unit`, `dimension` | `None` |
| **Linked Evidence** | Optional | `evidence_ids`, `evidence_id`, `sources` | `[]` |

*Questions for Member 2:*
1. Does your pipeline extract atomic claims/propositions, or does Member 3 perform claim extraction?

---

## 2. Questions for Member 3 (Knowledge Graph)

### Relationship / Edge Triples Schema
Member 4's adapter currently expects knowledge graph triples to provide the following keys:

| Field Purpose | Required / Optional | Assumed Aliases Checked by Adapter | Default if Missing |
| :--- | :---: | :--- | :--- |
| **Source Entity** | **Required** | `source_entity`, `source`, `head`, `subject`, `from` | **Fails (raises AdapterError)** |
| **Relation** | **Required** | `relation`, `predicate`, `edge`, `type`, `rel` | **Fails (raises AdapterError)** |
| **Target Entity** | **Required** | `target_entity`, `target`, `tail`, `object`, `to` | **Fails (raises AdapterError)** |
| **Confidence** | Optional | `confidence`, `weight`, `score` | `1.0` |
| **Evidence IDs** | Optional | `evidence_ids`, `citations`, `source_ids` | `[]` |
| **Provenance** | Optional | `provenance` | `"Member3_KnowledgeGraph"` |

*Questions for Member 3:*
1. Does your module output a bare list of triples `[...]` or a dictionary like `{"edges": [...], "nodes": [...]}`?
2. Do you use graph terminology (`head`, `predicate`, `tail`) or entity terminology (`source_entity`, `relation`, `target_entity`)?
3. How are supporting evidence IDs attached to edges (e.g. `evidence_ids`, `citations`, or edge attributes)?

---

## Summary
Please confirm your actual keys or send a sample JSON output from each of your modules. Member 4's adapter will be updated to match your exact output schema without requiring any changes to your code.
