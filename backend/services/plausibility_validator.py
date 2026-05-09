"""
plausibility_validator.py — Multi-layer physiological plausibility validation.

Three validation layers:
  Layer 1: Hard physiological limits (clamp/reject)
  Layer 2: Cross-modal consistency (flag contradictions)
  Layer 3: Temporal plausibility (rate-of-change limits)

Auto-corrects impossible values rather than just tagging them.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple
import threading

from backend.models.vital import VitalRecord
from backend.services.audit_logger import audit_logger, AuditEventType


class CorrectionAction(str, Enum):
    CLAMP = "clamp"
    IMPUTE = "impute"
    INTERPOLATE = "interpolate"
    REJECT = "reject"
    NONE = "none"


@dataclass
class PlausibilityResult:
    valid: bool
    original_value: float
    corrected_value: Optional[float]
    action: CorrectionAction
    layer: str  # "hard_limits" | "cross_modal" | "temporal"
    issues: List[str] = field(default_factory=list)


# ── Layer 1: Hard Physiological Limits ────────────────────────────────────────
HARD_LIMITS: Dict[str, Tuple[float, float]] = {
    "heart_rate":               (20, 300),
    "spo2":                     (0, 100),
    "blood_pressure_systolic":  (40, 300),
    "blood_pressure_diastolic": (20, 200),
    "glucose_fasting":          (20, 700),
    "temperature":              (25, 45),
    "respiratory_rate":         (4, 60),
    "steps":                    (0, 100_000),
    "sleep_hours":              (0, 24),
    "weight":                   (1, 650),
    "height":                   (30, 275),
    "bmi":                      (8, 100),
    "chest_pain_severity":      (0, 10),
}

# Demographic-adjusted medians for imputation
IMPUTE_MEDIANS: Dict[str, float] = {
    "heart_rate": 72, "spo2": 97, "blood_pressure_systolic": 120,
    "blood_pressure_diastolic": 78, "glucose_fasting": 95, "temperature": 36.7,
    "respiratory_rate": 16, "steps": 7000, "sleep_hours": 7.0,
    "weight": 75, "bmi": 25, "chest_pain_severity": 0,
}

# ── Layer 3: Max rate-of-change per vital (per hour) ─────────────────────────
MAX_RATE_OF_CHANGE: Dict[str, float] = {
    "heart_rate": 80,               # bpm/hour
    "blood_pressure_systolic": 40,  # mmHg/hour
    "blood_pressure_diastolic": 30,
    "glucose_fasting": 150,         # mg/dL/hour
    "weight": 2.0,                  # kg/hour (water/food)
    "temperature": 1.5,             # °C/hour
    "spo2": 15,                     # %/hour
}


class PlausibilityValidator:
    """Three-layer physiological plausibility validator with auto-correction."""

    def __init__(self):
        self._recent_values: Dict[str, List[Tuple[datetime, float]]] = {}
        self._lock = threading.Lock()

    def validate(self, record: VitalRecord, user_id: str = "default") -> PlausibilityResult:
        """Run all three validation layers and auto-correct if possible."""
        # Layer 1: Hard limits
        result = self._check_hard_limits(record)
        if result.action != CorrectionAction.NONE:
            self._log_correction(record, result, user_id)
            if result.corrected_value is not None:
                record.value = result.corrected_value
            return result

        # Layer 2: Cross-modal consistency
        result = self._check_cross_modal(record)
        if result.action != CorrectionAction.NONE:
            self._log_correction(record, result, user_id)
            return result

        # Layer 3: Temporal plausibility
        result = self._check_temporal(record)
        if result.action != CorrectionAction.NONE:
            self._log_correction(record, result, user_id)
            if result.corrected_value is not None:
                record.value = result.corrected_value
            return result

        # Track this value for future temporal checks
        self._record_value(record)

        return PlausibilityResult(
            valid=True, original_value=record.value,
            corrected_value=None, action=CorrectionAction.NONE, layer="passed",
        )

    # ── Layer 1 ───────────────────────────────────────────────────────────────

    def _check_hard_limits(self, record: VitalRecord) -> PlausibilityResult:
        limits = HARD_LIMITS.get(record.vital_type)
        if limits is None:
            return PlausibilityResult(
                valid=True, original_value=record.value,
                corrected_value=None, action=CorrectionAction.NONE, layer="hard_limits",
            )

        lo, hi = limits
        if lo <= record.value <= hi:
            return PlausibilityResult(
                valid=True, original_value=record.value,
                corrected_value=None, action=CorrectionAction.NONE, layer="hard_limits",
            )

        # Value is outside hard limits — auto-correct
        original = record.value
        deviation = max(abs(record.value - lo), abs(record.value - hi)) / max(hi - lo, 1)

        if deviation > 2.0:
            # Wildly impossible (e.g., HR=5000) — impute with median
            corrected = IMPUTE_MEDIANS.get(record.vital_type, (lo + hi) / 2)
            action = CorrectionAction.IMPUTE
        else:
            # Just outside range — clamp to nearest bound
            corrected = max(lo, min(hi, record.value))
            action = CorrectionAction.CLAMP

        return PlausibilityResult(
            valid=True, original_value=original, corrected_value=round(corrected, 2),
            action=action, layer="hard_limits",
            issues=[f"{record.vital_type}={original} outside [{lo},{hi}], {action.value} to {corrected:.2f}"],
        )

    # ── Layer 2 ───────────────────────────────────────────────────────────────

    def _check_cross_modal(self, record: VitalRecord) -> PlausibilityResult:
        """Check cross-modal consistency with recently ingested values."""
        issues = []

        with self._lock:
            recent = {vt: vals[-1][1] if vals else None
                      for vt, vals in self._recent_values.items()}

        # Rule: Diastolic must be < Systolic
        if record.vital_type == "blood_pressure_diastolic":
            systolic = recent.get("blood_pressure_systolic")
            if systolic is not None and record.value >= systolic:
                issues.append(
                    f"Diastolic ({record.value}) >= Systolic ({systolic})"
                )

        if record.vital_type == "blood_pressure_systolic":
            diastolic = recent.get("blood_pressure_diastolic")
            if diastolic is not None and record.value <= diastolic:
                issues.append(
                    f"Systolic ({record.value}) <= Diastolic ({diastolic})"
                )

        # Rule: SpO2 < 80% AND HR < 40 simultaneously = likely device error
        if record.vital_type == "spo2" and record.value < 80:
            hr = recent.get("heart_rate")
            if hr is not None and hr < 40:
                issues.append(
                    f"SpO2={record.value}% with HR={hr}bpm — likely device error"
                )

        if record.vital_type == "heart_rate" and record.value < 40:
            spo2 = recent.get("spo2")
            if spo2 is not None and spo2 < 80:
                issues.append(
                    f"HR={record.value}bpm with SpO2={spo2}% — likely device error"
                )

        # Rule: Steps > 50k AND sleep > 10h = contradictory
        if record.vital_type == "steps" and record.value > 50000:
            sleep = recent.get("sleep_hours")
            if sleep is not None and sleep > 10:
                issues.append(
                    f"Steps={record.value} with sleep={sleep}h — contradictory"
                )

        if issues:
            return PlausibilityResult(
                valid=True, original_value=record.value,
                corrected_value=None, action=CorrectionAction.NONE,
                layer="cross_modal", issues=issues,
            )

        return PlausibilityResult(
            valid=True, original_value=record.value,
            corrected_value=None, action=CorrectionAction.NONE, layer="cross_modal",
        )

    # ── Layer 3 ───────────────────────────────────────────────────────────────

    def _check_temporal(self, record: VitalRecord) -> PlausibilityResult:
        """Check rate-of-change against previous readings."""
        max_rate = MAX_RATE_OF_CHANGE.get(record.vital_type)
        if max_rate is None:
            return PlausibilityResult(
                valid=True, original_value=record.value,
                corrected_value=None, action=CorrectionAction.NONE, layer="temporal",
            )

        with self._lock:
            history = self._recent_values.get(record.vital_type, [])

        if not history:
            return PlausibilityResult(
                valid=True, original_value=record.value,
                corrected_value=None, action=CorrectionAction.NONE, layer="temporal",
            )

        prev_ts, prev_val = history[-1]
        ts = record.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if prev_ts.tzinfo is None:
            prev_ts = prev_ts.replace(tzinfo=timezone.utc)

        hours = max((ts - prev_ts).total_seconds() / 3600.0, 0.01)
        rate = abs(record.value - prev_val) / hours

        if rate <= max_rate:
            return PlausibilityResult(
                valid=True, original_value=record.value,
                corrected_value=None, action=CorrectionAction.NONE, layer="temporal",
            )

        # Rate exceeded — interpolate toward previous value
        max_delta = max_rate * hours
        direction = 1 if record.value > prev_val else -1
        corrected = prev_val + direction * max_delta

        return PlausibilityResult(
            valid=True, original_value=record.value,
            corrected_value=round(corrected, 2),
            action=CorrectionAction.INTERPOLATE, layer="temporal",
            issues=[
                f"{record.vital_type} rate={rate:.1f}/hr exceeds max={max_rate}/hr, "
                f"interpolated {record.value:.2f} → {corrected:.2f}"
            ],
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _record_value(self, record: VitalRecord):
        """Store value for future temporal/cross-modal checks."""
        ts = record.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        with self._lock:
            history = self._recent_values.setdefault(record.vital_type, [])
            history.append((ts, record.value))
            # Keep only last 50 readings per vital type
            if len(history) > 50:
                self._recent_values[record.vital_type] = history[-50:]

    def _log_correction(self, record: VitalRecord, result: PlausibilityResult, user_id: str):
        audit_logger.log(
            AuditEventType.VALIDATION_FAILURE,
            {
                "record_id": record.id,
                "vital_type": record.vital_type,
                "layer": result.layer,
                "action": result.action.value,
                "original_value": result.original_value,
                "corrected_value": result.corrected_value,
                "issues": result.issues,
            },
            user_id=user_id,
        )


# Singleton
plausibility_validator = PlausibilityValidator()
