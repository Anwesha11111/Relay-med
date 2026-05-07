"""
Integration tests — FastAPI endpoints via TestClient
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

USER_ID   = "test_user_integration"
STREAM_ID = "manual_input"


@pytest.fixture(autouse=True)
def grant_test_consent():
    """Grant consent before each test so ingestion is not blocked."""
    client.post("/api/v1/consent", json={
        "user_id": USER_ID, "stream_id": STREAM_ID, "consented": True
    })
    yield


# ── Health ────────────────────────────────────────────────────────

def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "llm_provider" in data


# ── Consent ───────────────────────────────────────────────────────

def test_grant_and_revoke_consent():
    r = client.post("/api/v1/consent", json={
        "user_id": USER_ID, "stream_id": "ehr_import", "consented": True
    })
    assert r.status_code == 200
    assert r.json()["consented"] is True

    r = client.post("/api/v1/consent", json={
        "user_id": USER_ID, "stream_id": "ehr_import", "consented": False
    })
    assert r.json()["consented"] is False


def test_get_consent_list():
    r = client.get(f"/api/v1/consent/{USER_ID}")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Ingest ────────────────────────────────────────────────────────

def test_ingest_valid_heart_rate():
    r = client.post("/api/v1/ingest", json={
        "source": "manual", "vital_type": "heart_rate",
        "value": 72.0, "unit": "bpm",
        "user_id": USER_ID, "stream_id": STREAM_ID,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["success"] is True
    assert data["record_id"] is not None


def test_ingest_blocked_without_consent():
    r = client.post("/api/v1/ingest", json={
        "source": "manual", "vital_type": "heart_rate",
        "value": 72.0, "unit": "bpm",
        "user_id": "no_consent_user", "stream_id": STREAM_ID,
    })
    assert r.status_code == 403


def test_ingest_critical_spo2_triggers_alert():
    r = client.post("/api/v1/ingest", json={
        "source": "fitbit", "vital_type": "spo2",
        "value": 82.0, "unit": "%",
        "user_id": USER_ID, "stream_id": STREAM_ID,
    })
    assert r.status_code == 201
    data = r.json()
    assert len(data["triage_alerts"]) > 0
    assert data["triage_alerts"][0]["severity"] == "red_flag"


# ── Reports ───────────────────────────────────────────────────────

def test_get_latest_reports():
    r = client.get("/api/v1/reports/latest")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_graph_stats():
    r = client.get("/api/v1/reports/graph/stats")
    assert r.status_code == 200
    data = r.json()
    assert "node_count" in data
    assert "edge_count" in data


# ── Audit ─────────────────────────────────────────────────────────

def test_audit_log_returns_entries():
    r = client.get("/api/v1/audit/logs?hours=24&limit=50")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_audit_event_types():
    r = client.get("/api/v1/audit/event-types")
    assert r.status_code == 200
    types = r.json()
    assert "INGEST_SUCCESS" in types
    assert "CONSENT_GRANT" in types
