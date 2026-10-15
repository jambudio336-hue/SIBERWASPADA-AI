"""Deterministic, explainable detection rules for defensive monitoring."""
from __future__ import annotations

from collections import Counter
from typing import Any


def detect_event(event: dict[str, Any]) -> list[dict[str, str]]:
    """Return alert candidates. No network activity is performed here."""
    event_type = str(event.get("event_type", "")).lower()
    source_ip = str(event.get("source_ip", "unknown"))
    details = str(event.get("details", "")).lower()
    results: list[dict[str, str]] = []

    if event_type in {"login_failed", "auth_failure", "failed_login"}:
        results.append({
            "rule_id": "AUTH-001",
            "severity": "medium",
            "title": "Kegagalan autentikasi",
            "description": f"Percobaan autentikasi gagal tercatat dari sumber {source_ip}. Tinjau konteks sebelum mengambil tindakan.",
            "recommendation": "Periksa log autentikasi terkait, verifikasi apakah aktivitas diharapkan, dan gunakan MFA serta pembatasan percobaan login.",
        })

    if event_type in {"rate_spike", "http_burst"}:
        results.append({
            "rule_id": "NET-002",
            "severity": "high",
            "title": "Lonjakan permintaan",
            "description": f"Event melaporkan lonjakan permintaan dari sumber {source_ip}. Event ini belum membuktikan serangan.",
            "recommendation": "Bandingkan dengan baseline, periksa metrik layanan, dan evaluasi rate limiting pada sistem yang Anda kelola.",
        })

    if event_type in {"suspicious_path", "path_traversal_indicator"} or "../" in details:
        results.append({
            "rule_id": "WEB-003",
            "severity": "high",
            "title": "Pola path mencurigakan",
            "description": "Event memuat indikator traversal path atau pola akses web yang perlu ditinjau.",
            "recommendation": "Validasi log aplikasi, pastikan normalisasi path dan kontrol akses diterapkan, lalu uji perbaikan pada lingkungan milik sendiri.",
        })

    if event_type in {"service_down", "health_check_failed"}:
        results.append({
            "rule_id": "OPS-004",
            "severity": "critical",
            "title": "Layanan gagal health check",
            "description": "Event melaporkan layanan tidak lolos pemeriksaan kesehatan.",
            "recommendation": "Konfirmasi dari monitoring independen, periksa log dan dependensi, lalu jalankan prosedur pemulihan yang disetujui.",
        })

    return results


def summarize_events(events: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(e.get("severity", "info")).lower() for e in events)
    return {
        "total": len(events),
        "critical": counts["critical"],
        "high": counts["high"],
        "medium": counts["medium"],
        "low": counts["low"],
        "info": counts["info"],
    }
