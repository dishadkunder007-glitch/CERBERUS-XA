# DEV/TEST ONLY - Scratch test script for live verification
import json
import subprocess
import os

SCRATCH_DIR = os.path.join(os.path.dirname(__file__), "curl_payloads")
os.makedirs(SCRATCH_DIR, exist_ok=True)

# 1. Evaluate Reliability Payload
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
            "checksum_hash": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
        }
    }
]
eval_path = os.path.join(SCRATCH_DIR, "eval.json")
with open(eval_path, "w") as f:
    json.dump(payload_eval, f)

# 2. Valid Verify Payload
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
            "polarity": True
        }
    ],
    "evidence_items": payload_eval,
    "enable_ollama": False
}
valid_path = os.path.join(SCRATCH_DIR, "valid.json")
with open(valid_path, "w") as f:
    json.dump(payload_valid, f)

# 3. Invalid Verify Payload (empty question)
payload_invalid = {
    "question": "",
    "evidence_items": []
}
invalid_path = os.path.join(SCRATCH_DIR, "invalid.json")
with open(invalid_path, "w") as f:
    json.dump(payload_invalid, f)

# 4. Conflicting Claims Payload
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
            "polarity": True
        },
        {
            "id": "CLM-NEG",
            "statement": "The facility is permanently decommissioned.",
            "entity": "Facility",
            "property": "status",
            "value": "decommissioned",
            "evidence_ids": ["EV-CONF-02"],
            "polarity": False
        }
    ],
    "evidence_items": [
        {
            "id": "EV-CONF-01",
            "content": "Facility report states active operations.",
            "metadata": {"source_id": "SRC-A", "page_number": 1}
        },
        {
            "id": "EV-CONF-02",
            "content": "Decommissioning order states facility closed.",
            "metadata": {"source_id": "SRC-B", "page_number": 1}
        }
    ],
    "enable_ollama": False
}
conflict_path = os.path.join(SCRATCH_DIR, "conflict.json")
with open(conflict_path, "w") as f:
    json.dump(payload_conflict, f)

# 5. Insufficient Evidence Payload
payload_insufficient = {
    "question": "What is the secret launch code for Apollo 18?",
    "evidence_items": [],
    "enable_ollama": False
}
insufficient_path = os.path.join(SCRATCH_DIR, "insufficient.json")
with open(insufficient_path, "w") as f:
    json.dump(payload_insufficient, f)

# 6. Fallback with Unreachable Ollama
payload_fallback = {
    "question": "What is the certified payload capacity of the Alpha-7 UAV?",
    "claims": payload_valid["claims"],
    "evidence_items": payload_eval,
    "enable_ollama": True,
    "ollama_endpoint": "http://127.0.0.1:1"
}
fallback_path = os.path.join(SCRATCH_DIR, "fallback.json")
with open(fallback_path, "w") as f:
    json.dump(payload_fallback, f)

commands = [
    ("Task 4: GET /reasoning/health", f'curl.exe -i -s http://127.0.0.1:8000/reasoning/health'),
    ("Task 5: POST /reasoning/evaluate_reliability", f'curl.exe -i -s -X POST http://127.0.0.1:8000/reasoning/evaluate_reliability -H "Content-Type: application/json" -d "@{eval_path}"'),
    ("Task 6: POST /reasoning/verify (Valid Request)", f'curl.exe -i -s -X POST http://127.0.0.1:8000/reasoning/verify -H "Content-Type: application/json" -d "@{valid_path}"'),
    ("Task 7: POST /reasoning/verify (Invalid Request Handling)", f'curl.exe -i -s -X POST http://127.0.0.1:8000/reasoning/verify -H "Content-Type: application/json" -d "@{invalid_path}"'),
    ("Task 8: POST /reasoning/verify (Conflicting Claims)", f'curl.exe -i -s -X POST http://127.0.0.1:8000/reasoning/verify -H "Content-Type: application/json" -d "@{conflict_path}"'),
    ("Task 9: POST /reasoning/verify (Insufficient Evidence)", f'curl.exe -i -s -X POST http://127.0.0.1:8000/reasoning/verify -H "Content-Type: application/json" -d "@{insufficient_path}"'),
    ("Task 10: POST /reasoning/verify (Deterministic Fallback with Ollama Unavailable)", f'curl.exe -i -s -X POST http://127.0.0.1:8000/reasoning/verify -H "Content-Type: application/json" -d "@{fallback_path}"'),
]

for label, cmd in commands:
    print(f"\n=======================================================")
    print(f"### {label}")
    print(f"Command: {cmd}")
    print(f"=======================================================")
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print("STDERR:", proc.stderr)
