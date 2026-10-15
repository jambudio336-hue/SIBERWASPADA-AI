import os
import tempfile

# Use an isolated test database before importing the application modules.
_tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
_tmp.close()
os.environ["SIBERWASPADA_DB"] = _tmp.name

from fastapi.testclient import TestClient
from app.main import app
from app import database

client = TestClient(app)


def setup_function():
    database.init_db()
    with database.connect() as conn:
        conn.execute("DELETE FROM audit_log")
        conn.execute("DELETE FROM incidents")
        conn.execute("DELETE FROM events")


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_event_ingestion_creates_alert():
    response = client.post("/api/events", json={
        "source_ip": "192.0.2.10",
        "event_type": "login_failed",
        "severity": "medium",
        "message": "Login gagal test",
        "details": "uji otomatis",
        "is_simulated": True
    })
    assert response.status_code == 201
    assert response.json()["detected_alerts"][0]["rule_id"] == "AUTH-001"
    assert client.get("/api/alerts").json()


def test_simulator_labels_generated_events():
    response = client.post("/api/simulator/run")
    assert response.status_code == 200
    assert response.json()["mode"] == "SIMULASI"
    assert response.json()["created"] == 4
    assert all(event["is_simulated"] for event in response.json()["events"])



def test_rules_catalog_and_summary_report():
    rules = client.get("/api/rules")
    report = client.get("/api/reports/summary")
    assert rules.status_code == 200
    assert len(rules.json()) == 4
    assert report.status_code == 200
    assert "recommended_next_steps" in report.json()
    assert "data_mode" in report.json()


def test_incident_csv_export():
    client.post("/api/events", json={
        "source_ip": "192.0.2.11",
        "event_type": "login_failed",
        "severity": "medium",
        "message": "CSV export test",
        "is_simulated": True
    })
    response = client.get("/api/export/incidents.csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "AUTH-001" in response.text



def test_jsonl_import_is_validated_and_audited():
    payload = '{"source_ip":"192.0.2.30","event_type":"login_failed","severity":"medium","message":"Impor uji","details":"log uji","is_simulated":true}\n'
    response = client.post("/api/import/jsonl", content=payload, headers={"Content-Type": "text/plain"})
    assert response.status_code == 200
    assert response.json()["berhasil"] == 1
    assert client.get("/api/audit").json()
    assert client.get("/api/trends?days=7").status_code == 200


def test_jsonl_import_rejects_invalid_batch_without_partial_write():
    payload = '{"source_ip":"192.0.2.31","event_type":"normal_request","severity":"info","message":"valid"}\n{"broken":'
    response = client.post("/api/import/jsonl", content=payload, headers={"Content-Type": "text/plain"})
    assert response.status_code == 422
    assert client.get("/api/events").json() == []
