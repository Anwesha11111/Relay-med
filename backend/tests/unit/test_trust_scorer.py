"""
Unit tests — Trust Scorer
"""
import pytest
from datetime import datetime, timezone, timedelta
from backend.models.vital import VitalRecord
from backend.services.trust_scorer import TrustScorer


@pytest.fixture
def scorer():
    return TrustScorer()


def make_record(source="fitbit", minutes_old=10):
    ts = datetime.now(timezone.utc) - timedelta(minutes=minutes_old)
    return VitalRecord(
        source=source,
        vital_type="heart_rate",
        value=72.0,
        unit="bpm",
        timestamp=ts,
        metadata={"device": "Fitbit Charge 6"},
    )


def test_fitbit_recent_high_score(scorer):
    rec = make_record("fitbit", minutes_old=10)
    score = scorer.compute_trust_score(rec)
    assert score >= 0.8, f"Expected high trust for recent Fitbit data, got {score}"


def test_manual_lower_than_wearable(scorer):
    fitbit = make_record("fitbit", minutes_old=10)
    manual = make_record("manual", minutes_old=10)
    assert scorer.compute_trust_score(fitbit) > scorer.compute_trust_score(manual)


def test_old_data_low_recency(scorer):
    old = make_record("fitbit", minutes_old=60 * 24 * 10)  # 10 days old
    score = scorer.compute_trust_score(old)
    assert score < 0.7, f"Expected lower trust for stale data, got {score}"


def test_score_within_bounds(scorer):
    for source in ["fitbit", "manual", "ehr", "apple_health"]:
        rec = make_record(source)
        s = scorer.compute_trust_score(rec)
        assert 0.0 <= s <= 1.0, f"Score out of bounds for {source}: {s}"
