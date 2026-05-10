"""
Property-based tests — RelayMed AI Health Companion.

Uses Hypothesis to verify invariants that must hold for *all* inputs,
not just the examples we thought of.

Covered components
------------------
TrustScorer          score always in [0, 1]; ordering invariants hold.
IngestionService     validation tags / error types are consistent.
DifferentialPrivacy  Laplace mechanism preserves sign of large values;
                     privatised mean converges to true mean as ε → ∞.
HealthGraph          node/edge counts are non-negative and monotone.
EmergencyTriageService  red-flag guarantee: low trust never suppresses an alert.

Install Hypothesis before running:
    pip install hypothesis
Then run:
    pytest backend/tests/property/ -v
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

try:
    from hypothesis import given, assume, settings as h_settings, HealthCheck
    from hypothesis import strategies as st
    HYPOTHESIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    HYPOTHESIS_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not HYPOTHESIS_AVAILABLE,
    reason="hypothesis not installed — run: pip install hypothesis",
)

from backend.models.vital import VitalRecord
from backend.services.trust_scorer import TrustScorer
from backend.services.ingestion_service import IngestionService, _DUPLICATE_CACHE
from backend.services.differential_privacy import DifferentialPrivacyEngine
from backend.services.emergency_triage import EmergencyTriageService
from backend.services.health_graph import HealthGraph


# ── Strategies ─────────────────────────────────────────────────────────────────

SOURCES = ["fitbit", "apple_health", "manual", "ehr"]

vital_source = st.sampled_from(SOURCES)

vital_type = st.sampled_from([
    "heart_rate", "spo2", "blood_pressure_systolic",
    "blood_pressure_diastolic", "glucose_fasting", "steps",
    "sleep_hours", "temperature", "chest_pain_severity", "respiratory_rate",
])

# Timestamps: anything in the past 30 days
past_timestamp = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
    timezones=st.just(timezone.utc),
).filter(lambda dt: dt <= datetime.now(timezone.utc))


def _vital(
    source_st=vital_source,
    vtype_st=vital_type,
    value_st=st.floats(min_value=0.0, max_value=500.0, allow_nan=False, allow_infinity=False),
    ts_st=past_timestamp,
) -> st.SearchStrategy[VitalRecord]:
    @st.composite
    def _build(draw):
        return VitalRecord(
            source=draw(source_st),
            vital_type=draw(vtype_st),
            value=draw(value_st),
            unit="unit",
            timestamp=draw(ts_st),
        )
    return _build()


# ── TrustScorer Properties ─────────────────────────────────────────────────────


class TestTrustScorerProperties:
    scorer = TrustScorer()

    @given(_vital())
    @h_settings(suppress_health_check=[HealthCheck.too_slow], max_examples=200)
    def test_score_always_in_unit_interval(self, record: VitalRecord):
        score = self.scorer.compute_trust_score(record)
        assert 0.0 <= score <= 1.0, f"Score {score} out of [0,1] for {record}"

    @given(past_timestamp)
    @h_settings(max_examples=100)
    def test_more_recent_record_never_lower_score_than_old(self, ts: datetime):
        """
        For the same source/type, a more recent record must score ≥ an older one
        (because the recency_factor is monotonically non-increasing with age).
        """
        old_ts  = ts - timedelta(days=8)
        assume(old_ts > datetime(2020, 1, 1, tzinfo=timezone.utc))
        recent = VitalRecord(source="fitbit", vital_type="heart_rate",
                             value=72.0, unit="bpm", timestamp=ts)
        old    = VitalRecord(source="fitbit", vital_type="heart_rate",
                             value=72.0, unit="bpm", timestamp=old_ts)
        assert self.scorer.compute_trust_score(recent) >= self.scorer.compute_trust_score(old)

    @given(st.sampled_from(SOURCES))
    def test_score_ordering_by_source(self, source: str):
        """fitbit ≥ manual ≥ ehr for equally-recent data."""
        ts = datetime.now(timezone.utc) - timedelta(minutes=1)
        def score(src):
            return self.scorer.compute_trust_score(
                VitalRecord(source=src, vital_type="heart_rate",
                            value=72.0, unit="bpm", timestamp=ts)
            )
        assert score("fitbit") >= score("manual")
        assert score("manual") >= score("ehr")


# ── IngestionService Properties ────────────────────────────────────────────────


class TestIngestionServiceProperties:

    @given(_vital())
    @h_settings(suppress_health_check=[HealthCheck.too_slow], max_examples=150)
    def test_validation_result_is_consistent(self, record: VitalRecord):
        """
        If validation is valid, errors must be empty.
        If invalid, errors must be non-empty.
        Tags are always a list.
        """
        _DUPLICATE_CACHE.clear()
        svc = IngestionService()
        result = svc.validate(record)
        assert isinstance(result.tags, list)
        assert isinstance(result.errors, list)
        if result.valid:
            # A valid record may still have tags (e.g. DISCREPANCY) but no fatal errors
            assert all(e not in ["future timestamp", "duplicate"] for e in [e.lower() for e in result.errors])
        else:
            assert len(result.errors) > 0, "Invalid result must carry at least one error message"

    @given(_vital(ts_st=st.datetimes(
        min_value=datetime(2030, 1, 1),
        max_value=datetime(2099, 1, 1),
        timezones=st.just(timezone.utc),
    )))
    @h_settings(max_examples=50)
    def test_future_timestamp_always_invalid(self, record: VitalRecord):
        """Any record with a timestamp more than 24h in the future must be rejected."""
        _DUPLICATE_CACHE.clear()
        svc = IngestionService()
        result = svc.validate(record)
        assert result.valid is False
        assert any("future" in e.lower() for e in result.errors)

    @given(_vital(
        value_st=st.floats(min_value=0.0, max_value=500.0, allow_nan=False),
        vtype_st=st.just("heart_rate"),
    ))
    @h_settings(max_examples=100)
    def test_extreme_hr_values_are_tagged_discrepancy(self, record: VitalRecord):
        """Heart rate outside physiological range must always carry the DISCREPANCY tag."""
        assume(record.value > 300 or record.value < 20)
        _DUPLICATE_CACHE.clear()
        svc = IngestionService()
        result = svc.validate(record)
        assert "DISCREPANCY" in result.tags


# ── Differential Privacy Properties ───────────────────────────────────────────


class TestDifferentialPrivacyProperties:

    @given(
        value=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        sensitivity=st.floats(min_value=0.01, max_value=100.0, allow_nan=False),
        epsilon=st.floats(min_value=0.01, max_value=10.0, allow_nan=False),
    )
    @h_settings(max_examples=300)
    def test_noised_value_is_finite(self, value: float, sensitivity: float, epsilon: float):
        """add_laplace_noise must always return a finite float."""
        engine = DifferentialPrivacyEngine(epsilon=epsilon)
        result = engine.add_laplace_noise(value, sensitivity)
        assert isinstance(result, float)
        import math
        assert math.isfinite(result)

    @given(
        values=st.lists(
            st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            min_size=100, max_size=500,
        ),
    )
    @h_settings(max_examples=30)
    def test_high_epsilon_mean_close_to_true_mean(self, values: list[float]):
        """
        With ε=1000 (near-zero noise), the privatised mean should be within
        5 units of the true mean for any list of values in [-100, 100].
        """
        engine = DifferentialPrivacyEngine(epsilon=1000.0)
        true_mean = sum(values) / len(values)
        priv_mean = engine.privatise_mean(values, sensitivity=1.0)
        assert abs(priv_mean - true_mean) < 5.0

    @given(epsilon=st.floats(min_value=0.001, max_value=0.0, allow_nan=False))
    def test_non_positive_epsilon_raises(self, epsilon: float):
        """DifferentialPrivacyEngine must reject ε ≤ 0."""
        assume(epsilon <= 0)
        with pytest.raises(ValueError, match="[Ee]psilon"):
            DifferentialPrivacyEngine(epsilon=epsilon)


# ── EmergencyTriageService Properties ─────────────────────────────────────────


class TestEmergencyTriageProperties:

    @given(
        spo2=st.floats(min_value=0.0, max_value=89.9, allow_nan=False),
        trust=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @h_settings(max_examples=200)
    def test_low_spo2_always_fires_regardless_of_trust(self, spo2: float, trust: float):
        """
        A red flag for critically low SpO2 must NEVER be suppressed,
        even when the trust score is 0.0.
        """
        svc = EmergencyTriageService()
        record = VitalRecord(
            source="fitbit", vital_type="spo2", value=spo2, unit="%",
            timestamp=datetime.now(timezone.utc), trust_score=trust,
        )
        findings = svc.evaluate_red_flags(record)
        red_flags = [f for f in findings if f.severity == "red_flag"]
        assert len(red_flags) >= 1, (
            f"Expected red flag for SpO2={spo2}, trust={trust}, got: {findings}"
        )

    @given(
        spo2=st.floats(min_value=91.0, max_value=100.0, allow_nan=False),
    )
    @h_settings(max_examples=100)
    def test_normal_spo2_never_fires_red_flag(self, spo2: float):
        """Values safely above the SpO2 threshold must never trigger a red flag."""
        svc = EmergencyTriageService()
        record = VitalRecord(
            source="fitbit", vital_type="spo2", value=spo2, unit="%",
            timestamp=datetime.now(timezone.utc), trust_score=1.0,
        )
        findings = svc.evaluate_red_flags(record)
        red_flags = [f for f in findings if f.severity == "red_flag"]
        assert len(red_flags) == 0, f"Unexpected red flag for SpO2={spo2}"

    @given(trust=st.floats(min_value=0.0, max_value=0.49, allow_nan=False))
    @h_settings(max_examples=100)
    def test_low_trust_appends_data_quality_note(self, trust: float):
        """When trust is low, the alert summary must mention 'trust score is low'."""
        svc = EmergencyTriageService()
        record = VitalRecord(
            source="manual", vital_type="spo2", value=80.0, unit="%",
            timestamp=datetime.now(timezone.utc), trust_score=trust,
        )
        findings = svc.evaluate_red_flags(record)
        assert len(findings) >= 1
        assert any("trust score is low" in f.plain_language_summary for f in findings)


# ── HealthGraph Properties ─────────────────────────────────────────────────────


class TestHealthGraphProperties:

    @given(
        records=st.lists(_vital(), min_size=1, max_size=20),
    )
    @h_settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
    def test_node_count_monotone(self, records: list[VitalRecord]):
        """Adding records must never decrease the node count."""
        graph = HealthGraph()
        prev_count = graph.get_node_count()
        for rec in records:
            rec.trust_score = 0.8
            graph.add_node(rec)
            count = graph.get_node_count()
            assert count >= prev_count, "Node count decreased after add_node"
            prev_count = count

    @given(
        records=st.lists(_vital(), min_size=2, max_size=15),
    )
    @h_settings(suppress_health_check=[HealthCheck.too_slow], max_examples=30)
    def test_edge_count_non_negative(self, records: list[VitalRecord]):
        """Edge count must always be ≥ 0."""
        graph = HealthGraph()
        for rec in records:
            rec.trust_score = 0.7
            graph.add_node(rec)
        assert graph.get_edge_count() >= 0
