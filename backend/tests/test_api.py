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
