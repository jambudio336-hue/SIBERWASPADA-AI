"""SIBERWASPADA AI REST API."""
from __future__ import annotations

import csv
import io
import json
import os
import random
from datetime import datetime, timezone
from typing import Literal

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
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
    database.insert_audit(stamp, "kejadian.dicatat", "kejadian", event_id, f"Jenis={event['event_type']}; simulasi={bool(event.get('is_simulated', False))}")
    return {"id": event_id, **event, "detected_alerts": alerts}


@app.on_event("startup")
def startup() -> None:
    database.init_db()


@app.get("/")
def root():
    web_dir = os.getenv("SIBERWASPADA_WEB_DIR")
    index_file = os.path.join(web_dir, "index.html") if web_dir else ""
    if index_file and os.path.isfile(index_file):
        return FileResponse(index_file)
    return {"name": "SIBERWASPADA AI", "version": "0.2.0", "docs": "/docs", "mode": "defensive MVP"}


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
    database.insert_audit(now_iso(), "insiden.status_diubah", "insiden", incident_id, f"Status baru={payload.status}")
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



@app.get("/api/trends")
def get_trends(days: int = Query(default=7, ge=1, le=30)) -> dict:
    """Tren harian kejadian tersimpan; bukan ramalan."""
    return {
        "days": days,
        "generated_at": now_iso(),
        "notice": "Tren berdasarkan kejadian tersimpan; data simulasi tetap ditandai sebagai simulasi.",
        "items": database.event_trends(days),
    }


@app.get("/api/audit")
def get_audit(limit: int = Query(default=100, ge=1, le=500)) -> list[dict]:
    """Tampilkan jejak audit tindakan sistem/operator."""
    return database.list_audit(limit)


@app.post("/api/import/jsonl")
def import_jsonl(payload: str = Body(..., media_type="text/plain")) -> dict:
    """Impor JSONL dengan validasi seluruh batch sebelum penyimpanan."""
    if len(payload.encode("utf-8")) > 1_000_000:
        raise HTTPException(status_code=413, detail="Berkas terlalu besar; batas 1 MB.")
    lines = [line.strip() for line in payload.splitlines() if line.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="Berkas kosong.")
    if len(lines) > 500:
        raise HTTPException(status_code=413, detail="Maksimal 500 baris per impor.")
    validated: list[EventIn] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            raw = json.loads(line)
            if not isinstance(raw, dict):
                raise ValueError("Setiap baris harus berupa objek JSON.")
            simulated = raw.get("is_simulated", False)
            if not isinstance(simulated, bool):
                raise ValueError("is_simulated harus bernilai true atau false.")
            raw["is_simulated"] = simulated
            validated.append(EventIn.model_validate(raw))
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Baris {line_number} tidak valid: {str(exc)[:180]}") from exc
    imported = [record_event(item) for item in validated]
    database.insert_audit(now_iso(), "log.diimpor", "impor-jsonl", len(imported), f"{len(imported)} baris tervalidasi")
    return {
        "berhasil": len(imported),
        "gagal": 0,
        "catatan": "Setiap baris divalidasi sebelum disimpan. Periksa asal-usul dan izin log sebelum impor.",
        "kejadian": imported,
    }


@app.get("/api/rules")
def get_detection_rules() -> list[dict[str, str]]:
    """Document enabled deterministic rules for explainability."""
    return [
        {"rule_id": "AUTH-001", "name": "Kegagalan autentikasi", "event_types": "login_failed, auth_failure, failed_login", "severity": "medium", "enabled": "true"},
        {"rule_id": "NET-002", "name": "Lonjakan permintaan", "event_types": "rate_spike, http_burst", "severity": "high", "enabled": "true"},
        {"rule_id": "WEB-003", "name": "Pola path mencurigakan", "event_types": "suspicious_path, path_traversal_indicator", "severity": "high", "enabled": "true"},
        {"rule_id": "OPS-004", "name": "Layanan gagal health check", "event_types": "service_down, health_check_failed", "severity": "critical", "enabled": "true"},
    ]

@app.get("/api/reports/summary")
def report_summary() -> dict:
    """Return a transparent summary report from stored events and incidents."""
    metrics = database.metrics()
    incidents = database.list_incidents()
    statuses: dict[str, int] = {}
    severities: dict[str, int] = {}
    for item in incidents:
        statuses[item["status"]] = statuses.get(item["status"], 0) + 1
        severities[item["severity"]] = severities.get(item["severity"], 0) + 1
    resolved = statuses.get("resolved", 0)
    return {
        "generated_at": now_iso(),
        "data_mode": metrics["data_mode"],
        "notice": "Ringkasan berdasarkan data lokal; event simulasi bukan bukti insiden nyata.",
        "metrics": metrics,
        "incident_statuses": statuses,
        "incident_severities": severities,
        "resolved_ratio_percent": round(resolved * 100 / len(incidents), 1) if incidents else 0,
        "recommended_next_steps": [
            "Tinjau insiden kritis dan tinggi yang masih terbuka.",
            "Korelasikan event dengan sumber log resmi sebelum menyimpulkan adanya serangan.",
            "Catat keputusan operator dan validasi false positive.",
        ],
    }

@app.get("/api/export/incidents.csv")
def export_incidents() -> StreamingResponse:
    """Export recent incidents as a CSV report."""
    rows = database.list_incidents()
    buffer = io.StringIO()
    fields = ["id", "event_id", "created_at", "rule_id", "title", "severity", "status", "source_ip", "event_type", "description", "recommendation", "is_simulated"]
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="siberwaspada-incidents.csv"'})

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


# Sajikan antarmuka statis hanya ketika dibundel sebagai aplikasi desktop.
_web_dir = os.getenv("SIBERWASPADA_WEB_DIR")
if _web_dir and os.path.isdir(_web_dir):
    app.mount("/", StaticFiles(directory=_web_dir, html=True), name="frontend")
