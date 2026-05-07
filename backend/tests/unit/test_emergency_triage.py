"""
Unit tests — Emergency Triage Service
"""
import pytest
from datetime import datetime, timezone
from backend.models.vital import VitalRecord
from backend.services.emergency_triage import EmergencyTriageService


@pytest.fixture
def svc():
    return EmergencyTriageService()


def make_record(vital_type, value, trust_score=0.9):
    return VitalRecord(
        source="fitbit",
        vital_type=vital_type,
        value=value,
        unit="",
        timestamp=datetime.now(timezone.utc),
        trust_score=trust_score,
    )


def test_low_spo2_triggers_red_flag(svc):
    rec = make_record("spo2", 85.0)
    findings = svc.evaluate_red_flags(rec)
    assert len(findings) == 1
    assert findings[0].severity == "red_flag"
    assert findings[0].rule_id == "ETS_SPO2_CRITICAL"


def test_normal_spo2_no_alert(svc):
    rec = make_record("spo2", 98.0)
    findings = svc.evaluate_red_flags(rec)
    assert len(findings) == 0


def test_high_chest_pain_red_flag(svc):
    rec = make_record("chest_pain_severity", 9.0)
    findings = svc.evaluate_red_flags(rec)
    assert any(f.severity == "red_flag" for f in findings)


def test_low_trust_appends_warning_but_fires(svc):
    rec = make_record("spo2", 85.0, trust_score=0.3)
    findings = svc.evaluate_red_flags(rec)
    assert len(findings) == 1  # NEVER suppressed
    assert "trust score is low" in findings[0].plain_language_summary


def test_normal_chest_pain_no_alert(svc):
    rec = make_record("chest_pain_severity", 3.0)
    findings = svc.evaluate_red_flags(rec)
    assert len(findings) == 0
