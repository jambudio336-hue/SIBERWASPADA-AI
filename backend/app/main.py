"""SIBERWASPADA AI REST API."""
from __future__ import annotations

import csv
import io
import random
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import database
from .detection import detect_event

app = FastAPI(
    title="SIBERWASPADA AI API",
    description="API defensif untuk pencatatan event, deteksi berbasis aturan, dan simulator lokal. Data simulator bukan telemetri nyata.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class EventIn(BaseModel):
    source_ip: str = Field(min_length=1, max_length=80)
    event_type: str = Field(min_length=1, max_length=80)
    severity: Literal["critical", "high", "medium", "low", "info"] = "info"
    message: str = Field(min_length=1, max_length=500)
    details: str = Field(default="", max_length=2000)
    is_simulated: bool = False


class IncidentStatusIn(BaseModel):
    status: Literal["open", "investigating", "resolved", "false_positive"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_event(payload: EventIn) -> dict:
    stamp = now_iso()
    event = payload.model_dump()
    event["timestamp"] = stamp
    event_id = database.insert_event(event)
    alerts = detect_event(event)
    for alert in alerts:
        database.insert_incident(event_id, alert, stamp)
    return {"id": event_id, **event, "detected_alerts": alerts}


@app.on_event("startup")
def startup() -> None:
    database.init_db()


@app.get("/")
def root() -> dict:
    return {"name": "SIBERWASPADA AI", "version": "0.1.0", "docs": "/docs", "mode": "defensive MVP"}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "siberwaspada-api", "time": now_iso()}


@app.get("/api/metrics")
def get_metrics() -> dict:
    return database.metrics()


@app.get("/api/events")
def get_events(
    limit: int = Query(default=100, ge=1, le=500),
    severity: str | None = Query(default=None, pattern="^(critical|high|medium|low|info)$"),
) -> list[dict]:
    return database.list_events(limit, severity)


@app.post("/api/events", status_code=201)
def create_event(payload: EventIn) -> dict:
    """Ingest a single event supplied by an authorized local operator."""
    return record_event(payload)


@app.get("/api/alerts")
def get_alerts(status: str | None = Query(default=None, pattern="^(open|investigating|resolved|false_positive)$")) -> list[dict]:
    return database.list_incidents(status)


@app.patch("/api/incidents/{incident_id}")
def patch_incident(incident_id: int, payload: IncidentStatusIn) -> dict:
    if not database.update_incident_status(incident_id, payload.status):
        raise HTTPException(status_code=404, detail="Insiden tidak ditemukan")
    return {"id": incident_id, "status": payload.status, "updated": True}


@app.post("/api/simulator/run")
def run_simulator() -> dict:
    """Generate benign, local demo records only; does not contact any target."""
    scenarios = [
        ("192.0.2.14", "login_failed", "medium", "Login gagal berulang (simulasi)", "Skenario edukasi autentikasi."),
        ("198.51.100.23", "rate_spike", "high", "Lonjakan request API (simulasi)", "Skenario edukasi kapasitas layanan."),
        ("203.0.113.8", "suspicious_path", "high", "Indikator path mencurigakan (simulasi)", "Skenario edukasi validasi input."),
        ("192.0.2.40", "service_down", "critical", "Health check layanan gagal (simulasi)", "Skenario edukasi respons insiden."),
        ("198.51.100.50", "normal_request", "info", "Request normal (simulasi)", "Aktivitas baseline sintetis."),
    ]
    # Fixed documentation-only IP ranges are used; no real target is contacted.
    selected = random.sample(scenarios, k=4)
    created = []
    for ip, event_type, severity, message, details in selected:
        created.append(record_event(EventIn(
            source_ip=ip, event_type=event_type, severity=severity,
            message=message, details=details, is_simulated=True
        )))
    return {
        "mode": "SIMULASI",
        "notice": "Semua event yang dibuat adalah sintetis. Tidak ada trafik dikirim ke jaringan atau target eksternal.",
        "created": len(created),
        "events": created,
        "metrics": database.metrics(),
    }


@app.get("/api/export/events.csv")
def export_events() -> StreamingResponse:
    rows = database.list_events(500)
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["id", "timestamp", "source_ip", "event_type", "severity", "message", "details", "is_simulated"],
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="siberwaspada-events.csv"'},
    )
