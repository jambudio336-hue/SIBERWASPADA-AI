"""Small SQLite persistence layer; database is created locally on first run."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("SIBERWASPADA_DB", str(Path(__file__).resolve().parents[1] / "data" / "siberwaspada.sqlite3")))


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source_ip TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'info',
            message TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            is_simulated INTEGER NOT NULL DEFAULT 0
        )""")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            rule_id TEXT NOT NULL,
            title TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL DEFAULT '',
            actor TEXT NOT NULL DEFAULT 'operator-lokal',
            details TEXT NOT NULL DEFAULT ''
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC)")


def insert_event(event: dict[str, Any]) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO events(timestamp,source_ip,event_type,severity,message,details,is_simulated)
               VALUES(?,?,?,?,?,?,?)""",
            (event["timestamp"], event["source_ip"], event["event_type"], event["severity"],
             event["message"], event.get("details", ""), int(bool(event.get("is_simulated", False)))),
        )
        return int(cur.lastrowid)


def insert_incident(event_id: int, alert: dict[str, str], created_at: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO incidents(event_id,rule_id,title,severity,description,recommendation,status,created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (event_id, alert["rule_id"], alert["title"], alert["severity"], alert["description"],
             alert["recommendation"], "open", created_at),
        )
        return int(cur.lastrowid)


def list_events(limit: int = 100, severity: str | None = None) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    with connect() as conn:
        if severity:
            rows = conn.execute(
                "SELECT * FROM events WHERE severity=? ORDER BY id DESC LIMIT ?", (severity.lower(), limit)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def list_incidents(status: str | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        if status:
            rows = conn.execute(
                """SELECT i.*, e.source_ip, e.event_type, e.is_simulated
                   FROM incidents i JOIN events e ON e.id=i.event_id
                   WHERE i.status=? ORDER BY i.id DESC LIMIT 300""", (status.lower(),)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT i.*, e.source_ip, e.event_type, e.is_simulated
                   FROM incidents i JOIN events e ON e.id=i.event_id
                   ORDER BY i.id DESC LIMIT 300"""
            ).fetchall()
        return [dict(r) for r in rows]


def update_incident_status(incident_id: int, status: str) -> bool:
    with connect() as conn:
        cur = conn.execute("UPDATE incidents SET status=? WHERE id=?", (status, incident_id))
        return cur.rowcount > 0


def metrics() -> dict[str, Any]:
    with connect() as conn:
        event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        simulated_count = conn.execute("SELECT COUNT(*) FROM events WHERE is_simulated=1").fetchone()[0]
        open_count = conn.execute("SELECT COUNT(*) FROM incidents WHERE status='open'").fetchone()[0]
        rows = conn.execute("SELECT severity, COUNT(*) c FROM events GROUP BY severity").fetchall()
        by_severity = {r["severity"]: r["c"] for r in rows}
        return {
            "total_events": event_count,
            "simulated_events": simulated_count,
            "open_incidents": open_count,
            "by_severity": by_severity,
            "data_mode": "demo-and-local",
        }


def insert_audit(timestamp: str, action: str, entity_type: str, entity_id: str = "", details: str = "", actor: str = "operator-lokal") -> int:
    """Append an audit record; never store secrets or raw uploaded file contents."""
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO audit_log(timestamp,action,entity_type,entity_id,actor,details) VALUES(?,?,?,?,?,?)",
            (timestamp, action[:80], entity_type[:80], str(entity_id)[:120], actor[:120], details[:500]),
        )
        return int(cur.lastrowid)


def list_audit(limit: int = 100) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    with connect() as conn:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]


def event_trends(days: int = 7) -> list[dict[str, Any]]:
    days = max(1, min(int(days), 30))
    with connect() as conn:
        rows = conn.execute(
            """SELECT substr(timestamp,1,10) AS date, COUNT(*) AS total,
                      SUM(CASE WHEN severity='critical' THEN 1 ELSE 0 END) AS critical,
                      SUM(CASE WHEN severity='high' THEN 1 ELSE 0 END) AS high,
                      SUM(CASE WHEN is_simulated=1 THEN 1 ELSE 0 END) AS simulated
               FROM events
               WHERE timestamp >= datetime('now', ?)
               GROUP BY substr(timestamp,1,10) ORDER BY date ASC""",
            (f"-{days - 1} days",),
        ).fetchall()
        return [dict(row) for row in rows]
