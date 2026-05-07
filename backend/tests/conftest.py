"""
conftest.py — Shared pytest fixtures for SecureMed AI Health Companion.

Available fixtures
------------------
client          FastAPI TestClient with automatic consent pre-seeded.
user_id         The test user ID string used across all tests.
stream_id       The test stream ID string.
sample_vital    Factory: call with kwargs to get a VitalRecord.
sample_finding  Factory: call with kwargs to get a RiskFinding.
sample_report   A ready-made ExplainabilityReport for unit tests.
mock_llm        Patches LLMAdapter.complete with a fast deterministic stub.
ingestion_svc   Fresh IngestionService with cleared duplicate cache.
trust_svc       Fresh TrustScorer instance.
triage_svc      Fresh EmergencyTriageService instance.
run_async       Helper to run coroutines from sync tests.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from typing import AsyncIterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.vital import VitalRecord
from backend.models.risk_finding import RiskFinding, VitalRef
from backend.models.report import ExplainabilityReport
from backend.services.ingestion_service import IngestionService
from backend.services.trust_scorer import TrustScorer
from backend.services.emergency_triage import EmergencyTriageService


# ── Constants ──────────────────────────────────────────────────────────────────

TEST_USER_ID   = "test_user"
TEST_STREAM_ID = "manual_input"


# ── HTTP Client ────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Session-scoped TestClient.
    Grants consent once before all tests so ingest endpoints work.
    """
    with TestClient(app) as c:
        c.post("/api/v1/consent", json={
            "user_id": TEST_USER_ID,
            "stream_id": TEST_STREAM_ID,
            "consented": True,
        })
        yield c


@pytest.fixture
def user_id() -> str:
    return TEST_USER_ID


@pytest.fixture
def stream_id() -> str:
    return TEST_STREAM_ID


# ── VitalRecord Factory ────────────────────────────────────────────────────────


@pytest.fixture
def sample_vital():
    """
    Factory for VitalRecord.  Call with keyword overrides:

        rec = sample_vital(vital_type="spo2", value=85.0, source="fitbit")
    """
    def _make(
        source: str = "manual",
        vital_type: str = "heart_rate",
        value: float = 72.0,
        unit: str = "bpm",
        minutes_old: int = 5,
        trust_score: float | None = None,
        tags: list[str] | None = None,
        **kwargs,
    ) -> VitalRecord:
        ts = datetime.now(timezone.utc) - timedelta(minutes=minutes_old)
        return VitalRecord(
            source=source,
            vital_type=vital_type,
            value=value,
            unit=unit,
            timestamp=ts,
            trust_score=trust_score,
            tags=tags or [],
            **kwargs,
        )
    return _make


# ── RiskFinding Factory ────────────────────────────────────────────────────────


@pytest.fixture
def sample_finding():
    """Factory for RiskFinding with sensible defaults."""
    def _make(
        severity: str = "yellow_flag",
        rule_id: str = "TEST_RULE",
        trust_score: float = 0.85,
        confidence: float = 0.75,
        plain_language_summary: str = "Test finding summary.",
        recommendations: list[str] | None = None,
        **kwargs,
    ) -> RiskFinding:
        return RiskFinding(
            source="rule_engine",
            rule_id=rule_id,
            severity=severity,
            contributing_vitals=[VitalRef(vital_id="v1", vital_type="heart_rate")],
            trust_score=trust_score,
            confidence=confidence,
            plain_language_summary=plain_language_summary,
            recommendations=recommendations or ["See a doctor."],
            **kwargs,
        )
    return _make


# ── ExplainabilityReport Fixture ───────────────────────────────────────────────


@pytest.fixture
def sample_report() -> ExplainabilityReport:
    """A ready-made ExplainabilityReport for unit tests that need one."""
    return ExplainabilityReport(
        id="rep-001",
        finding_id="find-001",
        plain_language_summary="🟡 CAUTION: Elevated heart rate trend.",
        contributing_vitals=[VitalRef(vital_id="v1", vital_type="heart_rate")],
        trust_score=0.85,
        confidence_pct=78.0,
        data_quality_warning=False,
        top_shap_features=None,
        causal_pathway_svg=None,
        counterfactual_summary=None,
        recommendations=["Schedule a cardiology consultation."],
        generated_at=datetime.utcnow(),
    )


# ── Isolated Service Instances ─────────────────────────────────────────────────


@pytest.fixture
def ingestion_svc() -> IngestionService:
    """Fresh IngestionService — clears the module-level duplicate cache."""
    from backend.services import ingestion_service as _mod
    _mod._DUPLICATE_CACHE.clear()
    return IngestionService()


@pytest.fixture
def trust_svc() -> TrustScorer:
    return TrustScorer()


@pytest.fixture
def triage_svc() -> EmergencyTriageService:
    return EmergencyTriageService()


# ── LLM Stub ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_llm():
    """
    Patches LLMAdapter.complete with a deterministic stub so tests never
    hit the network.

    Usage
    -----
        def test_something(client, mock_llm):
            r = client.post("/api/v1/conversation/chat", json={...})
            assert r.status_code == 200
    """
    async def _fake_complete(prompt: str, stream: bool = False) -> AsyncIterator[str]:
        yield "Stubbed LLM response."

    with patch(
        "backend.services.llm_adapter.LLMAdapter.complete",
        side_effect=_fake_complete,
    ):
        yield


# ── Async Helper ───────────────────────────────────────────────────────────────


@pytest.fixture
def run_async():
    """Run a coroutine from a sync test: result = run_async(some_coro())"""
    def _run(coro):
        return asyncio.get_event_loop().run_until_complete(coro)
    return _run
