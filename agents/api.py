"""
FastAPI REST API Server for Tmb Tumor Mutation Burden Calc.
"""
import os
import secrets
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from .base import SecurityException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Tmb Tumor Mutation Burden Calc API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(Path(__file__).resolve().parent.parent / "web" / "index.html")


@app.get("/app.js", include_in_schema=False)
def application_script():
    return FileResponse(Path(__file__).resolve().parent.parent / "web" / "app.js", media_type="application/javascript")


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "tmb-tumor-mutation-burden-calc", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException:
        raise HTTPException(status_code=422, detail="Sensitive identifiers are not accepted")
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException:
        raise HTTPException(status_code=422, detail="Sensitive identifiers are not accepted")


@app.get("/api/audit/logs")
def api_audit_logs(x_audit_token: str = Header(default="")):
    expected = os.getenv("AUDIT_API_TOKEN")
    if not expected:
        raise HTTPException(status_code=503, detail="Audit log access is not configured")
    if not secrets.compare_digest(x_audit_token, expected):
        raise HTTPException(status_code=403, detail="Access denied")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
