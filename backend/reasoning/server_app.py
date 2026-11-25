"""
DEV/TEST ONLY: not the project entrypoint; main.py is owned by the lead.

CERBERUS-XA: AI Reasoning & Evidence Verification Module (Member 4)
Throwaway Live Verification Server Application
Mounts reasoning_router exclusively under backend/reasoning/.
"""

from fastapi import FastAPI
from backend.reasoning.service import router as reasoning_router

app = FastAPI(title="CERBERUS-XA Reasoning Standalone Server")
app.include_router(reasoning_router)


@app.get("/")
def root():
    return {"module": "Member 4: Reasoning", "status": "running"}
