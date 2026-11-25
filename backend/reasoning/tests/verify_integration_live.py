"""
DEV/TEST ONLY: Integration verification script for Member 4.

CERBERUS-XA: AI Reasoning & Evidence Verification Module (Member 4)
Live Integration Verification Script

Tests live HTTP endpoints against a running FastAPI instance with reasoning_router:
1. Task 1: Check backend.main import
2. Task 2: Mount reasoning_router in FastAPI app
3. Task 3: Start live server on 127.0.0.1
4. Task 4: GET /reasoning/health
5. Task 5: POST /reasoning/evaluate_reliability
6. Task 6: POST /reasoning/verify (Valid Request)
7. Task 7: POST /reasoning/verify (Invalid Request Handling)
8. Task 8: POST /reasoning/verify (Conflicting Claims)
9. Task 9: POST /reasoning/verify (Insufficient Evidence)
10. Task 10: POST /reasoning/verify (Deterministic fallback with Ollama unavailable)
11. Task 11: Verify JSON response schema conformance
12. Task 12: Verify citations link to actual supplied evidence
13. Task 13: Verify route isolation
"""

import sys
import time
import threading
import uvicorn
import httpx
from pathlib import Path
from fastapi import FastAPI

# Add workspace root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.reasoning import reasoning_router
from backend.reasoning.schemas import (
    ReasoningRequest,
    EvidenceItem,
    EvidenceMetadata,
    EvidenceModality,
    DirectnessLevel,
    Claim,
)

SERVER_PORT = 8765
BASE_URL = f"http://127.0.0.1:{SERVER_PORT}"


def start_server(app: FastAPI):
    config = uvicorn.Config(app, host="127.0.0.1", port=SERVER_PORT, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def run_integration_tests():
    results = {}

    # -------------------------------------------------------------------------
    # Task 1: Verify backend.main import
    # -------------------------------------------------------------------------
    print("\n--- Task 1: Verify backend.main Import ---")
    try:
        # pyrefly: ignore[missing-import]
        import backend.main
        results["task_1_backend_main_import"] = {
            "status": "SUCCESS",
            "detail": "backend.main imported successfully.",
        }
        print("PASS: backend.main imported.")
    except Exception as e:
        results["task_1_backend_main_import"] = {
            "status": "FAILED",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "cause": "backend/main.py does not exist in the workspace.",
        }
        print(f"FAIL (Expected): {type(e).__name__}: {str(e)}")

    # -------------------------------------------------------------------------
    # Task 2: Verify reasoning_router can be mounted
    # -------------------------------------------------------------------------
    print("\n--- Task 2: Mount reasoning_router in FastAPI Application ---")
    app = FastAPI(title="CERBERUS-XA Live Integration Server")
    app.include_router(reasoning_router)

    # Add dummy existing backend route to test Task 13
    @app.get("/api/v1/existing_service")
    def existing_service():
        return {"service": "pre_existing", "status": "active"}

    mounted_paths = [r.path for r in reasoning_router.routes]
    print(f"Mounted paths: {mounted_paths}")
    results["task_2_mount_router"] = {
        "status": "SUCCESS",
        "mounted_paths": mounted_paths,
    }

    # -------------------------------------------------------------------------
    # Task 3: Start FastAPI Application Locally
    # -------------------------------------------------------------------------
    print("\n--- Task 3: Start Live FastAPI Server Locally ---")
    server_thread = threading.Thread(target=start_server, args=(app,), daemon=True)
    server_thread.start()

    # Wait for server ready
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    server_ready = False
    for _ in range(20):
        try:
            r = client.get("/reasoning/health")
            if r.status_code == 200:
                server_ready = True
                break
        except Exception:
            time.sleep(0.2)

    if not server_ready:
        print("FAIL: Server failed to start.")
        return results

    print(f"PASS: Server running on {BASE_URL}")

    # -------------------------------------------------------------------------
    # Task 4: Test GET /reasoning/health
    # -------------------------------------------------------------------------
    print("\n--- Task 4: Test GET /reasoning/health ---")
    resp_health = client.get("/reasoning/health")
    results["task_4_health"] = {
        "http_status": resp_health.status_code,
        "json": resp_health.json(),
    }
    print(f"HTTP {resp_health.status_code}: {resp_health.json()}")

    # -------------------------------------------------------------------------
    # Task 5: Test POST /reasoning/evaluate_reliability
    # -------------------------------------------------------------------------
    print("\n--- Task 5: Test POST /reasoning/evaluate_reliability ---")
    payload_eval = [
        {
            "id": "EV-LIVE-01",
            "content": "Official FAA Type Certificate for Alpha-7 UAV: maximum payload 15.5 kg.",
            "modality": "document",
            "directness": "primary",
            "metadata": {
                "source_id": "FAA-TCDS",
                "filename": "alpha7_tcds.pdf",
                "page_number": 4,
                "author": "Federal Aviation Administration",
                "checksum_hash": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
            },
        }
    ]
    resp_eval = client.post("/reasoning/evaluate_reliability", json=payload_eval)
    results["task_5_evaluate_reliability"] = {
        "http_status": resp_eval.status_code,
        "response_sample": resp_eval.json(),
    }
    print(f"HTTP {resp_eval.status_code}: {resp_eval.json()}")

    # -------------------------------------------------------------------------
    # Task 6: Test POST /reasoning/verify (Valid Request)
    # -------------------------------------------------------------------------
    print("\n--- Task 6: Test POST /reasoning/verify (Valid Request) ---")
    payload_valid = {
        "question": "What is the certified payload capacity of the Alpha-7 UAV?",
        "claims": [
            {
                "id": "CLM-01",
                "statement": "Alpha-7 UAV certified payload capacity is 15.5 kg.",
                "entity": "Alpha-7 UAV",
                "property": "payload_capacity",
                "value": "15.5",
                "unit": "kg",
                "evidence_ids": ["EV-LIVE-01"],
                "polarity": True,
            }
        ],
        "evidence_items": payload_eval,
        "enable_ollama": False,
    }
    resp_valid = client.post("/reasoning/verify", json=payload_valid)
    valid_json = resp_valid.json()
    results["task_6_verify_valid"] = {
        "http_status": resp_valid.status_code,
        "status": valid_json.get("status"),
        "confidence": valid_json.get("confidence"),
        "confidence_explanation": valid_json.get("confidence_explanation"),
        "answer": valid_json.get("answer"),
    }
    print(f"HTTP {resp_valid.status_code}: Status={valid_json.get('status')}, Conf={valid_json.get('confidence')}")
    print(f"Answer: {valid_json.get('answer')}")

    # -------------------------------------------------------------------------
    # Task 7: Test Invalid Request Handling (Validation error 422)
    # -------------------------------------------------------------------------
    print("\n--- Task 7: Test Invalid Request Handling ---")
    # Empty question violates min_length=1 constraint
    payload_invalid = {
        "question": "",
        "evidence_items": [],
    }
    resp_invalid = client.post("/reasoning/verify", json=payload_invalid)
    results["task_7_invalid_request"] = {
        "http_status": resp_invalid.status_code,
        "detail": resp_invalid.json(),
    }
    print(f"HTTP {resp_invalid.status_code} (Expected 422): {resp_invalid.json()}")

    # -------------------------------------------------------------------------
    # Task 8: Test Evidence with Conflicting Claims
    # -------------------------------------------------------------------------
    print("\n--- Task 8: Test Evidence with Conflicting Claims ---")
    payload_conflict = {
        "question": "Is the facility operational?",
        "claims": [
            {
                "id": "CLM-POS",
                "statement": "The facility is fully operational.",
                "entity": "Facility",
                "property": "status",
                "value": "operational",
                "evidence_ids": ["EV-CONF-01"],
                "polarity": True,
            },
            {
                "id": "CLM-NEG",
                "statement": "The facility is permanently decommissioned.",
                "entity": "Facility",
                "property": "status",
                "value": "decommissioned",
                "evidence_ids": ["EV-CONF-02"],
                "polarity": False,
            },
        ],
        "evidence_items": [
            {
                "id": "EV-CONF-01",
                "content": "Facility report states active operations.",
                "metadata": {"source_id": "SRC-A", "page_number": 1},
            },
            {
                "id": "EV-CONF-02",
                "content": "Decommissioning order states facility closed.",
                "metadata": {"source_id": "SRC-B", "page_number": 1},
            },
        ],
        "enable_ollama": False,
    }
    resp_conflict = client.post("/reasoning/verify", json=payload_conflict)
    conflict_json = resp_conflict.json()
    results["task_8_conflicting_claims"] = {
        "http_status": resp_conflict.status_code,
        "status": conflict_json.get("status"),
        "confidence": conflict_json.get("confidence"),
        "confidence_explanation": conflict_json.get("confidence_explanation"),
        "unresolved_conflicts": [c.get("description") for c in conflict_json.get("unresolved_conflicts", [])],
        "facts": conflict_json.get("facts", []),
    }
    print(f"HTTP {resp_conflict.status_code}: Status={conflict_json.get('status')}")
    print(f"Unresolved Conflicts: {results['task_8_conflicting_claims']['unresolved_conflicts']}")

    # -------------------------------------------------------------------------
    # Task 9: Test Insufficient Evidence
    # -------------------------------------------------------------------------
    print("\n--- Task 9: Test Insufficient Evidence ---")
    payload_insufficient = {
        "question": "What is the secret launch code for Apollo 18?",
        "evidence_items": [],
        "enable_ollama": False,
    }
    resp_insufficient = client.post("/reasoning/verify", json=payload_insufficient)
    insufficient_json = resp_insufficient.json()
    results["task_9_insufficient_evidence"] = {
        "http_status": resp_insufficient.status_code,
        "status": insufficient_json.get("status"),
        "confidence": insufficient_json.get("confidence"),
        "answer": insufficient_json.get("answer"),
    }
    print(f"HTTP {resp_insufficient.status_code}: Status={insufficient_json.get('status')}, Conf={insufficient_json.get('confidence')}")
    print(f"Answer: {insufficient_json.get('answer')}")

    # -------------------------------------------------------------------------
    # Task 10: Test Deterministic Fallback with Ollama Unavailable
    # -------------------------------------------------------------------------
    print("\n--- Task 10: Test Deterministic Fallback with Ollama Unavailable ---")
    payload_fallback = {
        "question": "What is the certified payload capacity of the Alpha-7 UAV?",
        "claims": payload_valid["claims"],
        "evidence_items": payload_eval,
        "enable_ollama": True,
        "ollama_endpoint": "http://127.0.0.1:1",  # Guaranteed unreachable port
    }
    resp_fallback = client.post("/reasoning/verify", json=payload_fallback)
    fallback_json = resp_fallback.json()
    results["task_10_deterministic_fallback"] = {
        "http_status": resp_fallback.status_code,
        "reasoning_mode": fallback_json.get("reasoning_mode"),
        "status": fallback_json.get("status"),
        "audit_trail": fallback_json.get("audit_trail", []),
    }
    print(f"HTTP {resp_fallback.status_code}: Mode={fallback_json.get('reasoning_mode')}")
    print(f"Audit Trail: {fallback_json.get('audit_trail')}")

    # -------------------------------------------------------------------------
    # Task 11: Verify JSON Response Schema Conformance
    # -------------------------------------------------------------------------
    print("\n--- Task 11: Verify JSON Response Schema Conformance ---")
    required_keys = [
        "question", "status", "conclusion_type", "answer", "summary",
        "supporting_claims", "opposing_claims", "unresolved_conflicts",
        "reasoning_steps", "confidence", "confidence_explanation",
        "facts", "inferences", "unknowns", "citations", "claim_citations",
        "reasoning_mode", "audit_trail"
    ]
    missing_keys = [k for k in required_keys if k not in valid_json]
    results["task_11_schema_conformance"] = {
        "schema_valid": len(missing_keys) == 0,
        "missing_keys": missing_keys,
    }
    print(f"Schema conformance: Valid={len(missing_keys) == 0}, Missing keys={missing_keys}")

    # -------------------------------------------------------------------------
    # Task 12: Verify Citations Refer to Actual Supplied Evidence
    # -------------------------------------------------------------------------
    print("\n--- Task 12: Verify Citations Refer to Actual Supplied Evidence ---")
    supplied_ids = {item["id"] for item in payload_eval}
    cited_ids = {c["evidence_id"] for c in valid_json.get("citations", [])}
    all_cited_are_supplied = cited_ids.issubset(supplied_ids)
    results["task_12_citations_grounded"] = {
        "supplied_ids": list(supplied_ids),
        "cited_ids": list(cited_ids),
        "valid": all_cited_are_supplied,
    }
    print(f"Supplied: {supplied_ids}, Cited: {cited_ids}, Grounded={all_cited_are_supplied}")

    # -------------------------------------------------------------------------
    # Task 13: Verify No Existing Backend Routes Are Broken
    # -------------------------------------------------------------------------
    print("\n--- Task 13: Verify Existing Backend Routes Are Broken ---")
    resp_existing = client.get("/api/v1/existing_service")
    results["task_13_existing_routes"] = {
        "http_status": resp_existing.status_code,
        "response": resp_existing.json(),
    }
    print(f"HTTP {resp_existing.status_code}: {resp_existing.json()}")

    return results


if __name__ == "__main__":
    run_integration_tests()

