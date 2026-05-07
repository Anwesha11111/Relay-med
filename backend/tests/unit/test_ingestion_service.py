"""
Unit tests — Ingestion Service validation logic
"""
import pytest
from datetime import datetime, timezone, timedelta
from backend.models.vital import VitalRecord
from backend.services.ingestion_service import IngestionService


@pytest.fixture
def svc():
    return IngestionService()


def make_record(**kwargs):
    defaults = dict(
        source="manual",
        vital_type="heart_rate",
        value=72.0,
        unit="bpm",
        timestamp=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return VitalRecord(**defaults)


def test_valid_record_passes(svc):
    rec = make_record()
    result = svc.validate(rec)
    assert result.valid is True
    assert not any("future" in e.lower() or "duplicate" in e.lower() for e in result.errors)


def test_future_timestamp_rejected(svc):
    rec = make_record(timestamp=datetime.now(timezone.utc) + timedelta(days=2))
    result = svc.validate(rec)
    assert result.valid is False
    assert any("future" in e.lower() for e in result.errors)


def test_out_of_range_tagged_discrepancy(svc):
    rec = make_record(vital_type="heart_rate", value=500.0)
    result = svc.validate(rec)
    assert "DISCREPANCY" in result.tags


def test_duplicate_detection(svc):
    rec = make_record()
    svc.validate(rec)   # first submission registers hash
    result2 = svc.validate(rec)  # second submission should be duplicate
    assert result2.valid is False
    assert any("duplicate" in e.lower() for e in result2.errors)


def test_spo2_range(svc):
    rec = make_record(vital_type="spo2", value=60.0)
    result = svc.validate(rec)
    assert "DISCREPANCY" in result.tags
