"""Test script — demonstrates all four components working."""
import sys
import os

# ── 1. Plausibility Validator Tests ──────────────────────────────────────────
print("=" * 60)
print("  TEST 1: PLAUSIBILITY VALIDATOR (impossible value correction)")
print("=" * 60)

from backend.services.plausibility_validator import plausibility_validator
from backend.models.vital import VitalRecord
from datetime import datetime, timezone

tests = [
    ("heart_rate", 500, "bpm", "HR=500 (impossible)"),
    ("heart_rate", -10, "bpm", "HR=-10 (negative)"),
    ("spo2", 120, "%", "SpO2=120% (over 100)"),
    ("spo2", 65, "%", "SpO2=65% (dangerously low)"),
    ("blood_pressure_systolic", 350, "mmHg", "SysBP=350 (extreme)"),
    ("glucose_fasting", 5000, "mg/dL", "Glucose=5000 (wildly impossible)"),
    ("steps", -500, "steps", "Steps=-500 (negative)"),
    ("sleep_hours", 30, "hrs", "Sleep=30hrs (>24)"),
    ("temperature", 50, "C", "Temp=50C (lethal)"),
    ("heart_rate", 72, "bpm", "HR=72 (normal - should pass)"),
]

for vt, val, unit, label in tests:
    r = VitalRecord(
        vital_type=vt, value=val, unit=unit,
        source="manual", timestamp=datetime.now(timezone.utc),
    )
    result = plausibility_validator.validate(r)
    if result.corrected_value is not None:
        print(f"  [CORRECTED] {label:<40} {val} -> {result.corrected_value} ({result.action.value})")
    else:
        print(f"  [OK]        {label:<40} {val} (passed)")

# ── 2. Feedback Service Tests ────────────────────────────────────────────────
print()
print("=" * 60)
print("  TEST 2: FEEDBACK SERVICE (closed-loop corrections)")
print("=" * 60)

from backend.services.feedback_service import feedback_service

# Submit 3 clinician corrections (concordance threshold)
for i in range(3):
    fb = feedback_service.submit_feedback(
        report_id="test-report-001",
        feedback_type="false_alarm",
        user_comment=f"Clinician correction #{i+1}: HR alert was false positive",
        user_role="clinician",
        corrected_value=72.0 + i,
        vital_type="heart_rate",
    )
    print(f"  Submitted clinician feedback #{i+1}: {fb.id[:8]}...")

# Submit 1 patient feedback (does not count toward concordance)
fb_patient = feedback_service.submit_feedback(
    report_id="test-report-002",
    feedback_type="wrong_recommendation",
    user_comment="The sleep recommendation was not helpful",
    user_role="patient",
)
print(f"  Submitted patient feedback: {fb_patient.id[:8]}...")

stats = feedback_service.get_feedback_stats()
print(f"\n  Feedback Stats:")
print(f"    Total:     {stats['total_feedback']}")
print(f"    By role:   {stats['by_role']}")
print(f"    By type:   {stats['by_type']}")
print(f"    Threshold: {stats['concordance_threshold']} concordant corrections needed")

pending = feedback_service.get_pending_corrections()
print(f"\n  Pending corrections (>= threshold): {len(pending)}")
for p in pending:
    print(f"    - {p['vital_type']}: avg corrected value = {p['average_corrected_value']}")

# ── 3. Bias Auditor Tests ────────────────────────────────────────────────────
print()
print("=" * 60)
print("  TEST 3: BIAS AUDITOR (demographic fairness)")
print("=" * 60)

from backend.services.bias_auditor import bias_auditor

report = bias_auditor.audit_dataset()
summary = bias_auditor.generate_summary(report)
print(summary)

# ── 4. Ingestion Pipeline Integration Test ───────────────────────────────────
print()
print("=" * 60)
print("  TEST 4: INGESTION PIPELINE (end-to-end with plausibility)")
print("=" * 60)

from backend.services.ingestion_service import ingestion_service
import asyncio

async def test_ingestion():
    # Test 1: Normal value
    r1 = VitalRecord(
        vital_type="heart_rate", value=75, unit="bpm",
        source="fitbit", timestamp=datetime.now(timezone.utc),
    )
    result1 = await ingestion_service.ingest(r1)
    print(f"  Normal HR=75:     success={result1.success}, tags={result1.tags}")

    # Test 2: Impossible value (should auto-correct)
    r2 = VitalRecord(
        vital_type="spo2", value=110, unit="%",
        source="manual", timestamp=datetime.now(timezone.utc),
    )
    result2 = await ingestion_service.ingest(r2)
    print(f"  SpO2=110 (bad):   success={result2.success}, tags={result2.tags}")
    if r2.metadata.get("original_value"):
        print(f"    -> Original: {r2.metadata['original_value']}, Corrected to: {r2.value}")

    # Test 3: Wildly impossible value
    r3 = VitalRecord(
        vital_type="heart_rate", value=9999, unit="bpm",
        source="manual", timestamp=datetime.now(timezone.utc),
    )
    result3 = await ingestion_service.ingest(r3)
    print(f"  HR=9999 (insane): success={result3.success}, tags={result3.tags}")
    if r3.metadata.get("original_value"):
        print(f"    -> Original: {r3.metadata['original_value']}, Corrected to: {r3.value}")

asyncio.run(test_ingestion())

print()
print("=" * 60)
print("  ALL TESTS COMPLETE")
print("=" * 60)
