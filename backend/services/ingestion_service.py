"""
Ingestion Service — Validates, scores, and routes incoming vital records.
Implements discrepancy handling, duplicate detection, and future-timestamp rejection.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from backend.models.vital import VitalRecord
from backend.services.trust_scorer import trust_scorer
from backend.services.health_graph import health_graph
from backend.services.emergency_triage import emergency_triage_service
from backend.services.audit_logger import audit_logger, AuditEventType
from backend.models.risk_finding import RiskFinding
from backend.services.differential_privacy import dp_engine
from backend.services.plausibility_validator import plausibility_validator, CorrectionAction

# Physiological range config: {vital_type: (min, max)}
PHYSIOLOGICAL_RANGES = {
    "heart_rate": (20, 300),
    "spo2": (70, 100),
    "blood_pressure_systolic": (50, 300),
    "blood_pressure_diastolic": (30, 200),
    "glucose_fasting": (30, 600),
    "steps": (0, 100000),
    "sleep_hours": (0, 24),
    "temperature": (30, 45),
    "chest_pain_severity": (0, 10),
    "respiratory_rate": (5, 60),
    "weight": (10, 500),
}

REQUIRED_FIELDS = ["vital_type", "value", "unit", "timestamp", "source"]
_DUPLICATE_CACHE: set = set()


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    tags: List[str]


@dataclass
class IngestResult:
    success: bool
    record_id: Optional[str]
    tags: List[str]
    errors: List[str]
    triage_findings: List[RiskFinding]


class IngestionService:

    async def ingest(self, record: VitalRecord, user_id: str = "default") -> IngestResult:
        # 1. Validate (basic field/duplicate/future checks)
        validation = self.validate(record)
        if not validation.valid:
            audit_logger.log(
                AuditEventType.VALIDATION_FAILURE,
                {"record_id": record.id, "errors": validation.errors},
                user_id=user_id,
            )
            return IngestResult(success=False, record_id=None, tags=[], errors=validation.errors, triage_findings=[])

        # 2. Apply tags from validation (e.g. DISCREPANCY, INCOMPLETE)
        record.tags.extend(validation.tags)
        record.tags = list(set(record.tags))

        # 2.5 Plausibility validation & auto-correction
        plaus_result = plausibility_validator.validate(record, user_id)
        if plaus_result.action == CorrectionAction.REJECT:
            return IngestResult(
                success=False, record_id=None, tags=["REJECTED"],
                errors=[f"Plausibility rejection ({plaus_result.layer}): " + "; ".join(plaus_result.issues)],
                triage_findings=[],
            )
        if plaus_result.corrected_value is not None:
            # Store original in metadata, use corrected value
            record.metadata["original_value"] = plaus_result.original_value
            record.metadata["correction_action"] = plaus_result.action.value
            record.metadata["correction_layer"] = plaus_result.layer
            record.value = plaus_result.corrected_value
            record.tags.append("AUTO_CORRECTED")
        if plaus_result.issues:
            record.tags.append("PLAUSIBILITY_FLAG")
            for issue in plaus_result.issues:
                record.metadata.setdefault("plausibility_issues", []).append(issue)

        # 3. Compute trust score
        record.trust_score = trust_scorer.compute_trust_score(record)

        # 4. Anti-Hacking: Apply Differential Privacy Noise
        record.privatized_value = dp_engine.protect_value(record.value, record.vital_type)
        audit_logger.log(
            AuditEventType.PRIVACY_SHIELD_ACTIVATED,
            {"record_id": record.id, "vital_type": record.vital_type, "epsilon": dp_engine.epsilon},
            user_id=user_id,
        )

        # 5. Add to health graph
        health_graph.add_node(record)

        # 6. Emergency triage (red/yellow flags) — never suppressed by trust
        triage_findings = emergency_triage_service.evaluate_red_flags(record)

        # 7. Log success
        audit_logger.log(
            AuditEventType.INGEST_SUCCESS,
            {"record_id": record.id, "vital_type": record.vital_type, "trust_score": record.trust_score},
            user_id=user_id,
        )

        return IngestResult(
            success=True,
            record_id=record.id,
            tags=record.tags,
            errors=[],
            triage_findings=triage_findings,
        )

    def validate(self, record: VitalRecord) -> ValidationResult:
        errors: List[str] = []
        tags: List[str] = []

        # Check required fields
        missing = [f for f in REQUIRED_FIELDS if not getattr(record, f, None)]
        if missing:
            tags.append("INCOMPLETE")
            errors.extend([f"Missing required field: {f}" for f in missing])

        # Future timestamp check
        if self._check_future_timestamp(record):
            errors.append(f"Timestamp {record.timestamp} is more than 24h in the future.")
            return ValidationResult(valid=False, errors=errors, tags=tags)

        # Duplicate check
        if self._check_duplicate(record):
            audit_logger.log(
                AuditEventType.DUPLICATE_DISCARDED,
                {"record_id": record.id, "vital_type": record.vital_type},
            )
            return ValidationResult(valid=False, errors=["Duplicate record discarded."], tags=tags)

        # Physiological range check
        if record.vital_type in PHYSIOLOGICAL_RANGES:
            lo, hi = PHYSIOLOGICAL_RANGES[record.vital_type]
            if not (lo <= record.value <= hi):
                tags.append("DISCREPANCY")
                errors.append(
                    f"Value {record.value} is outside physiological range [{lo}, {hi}] for {record.vital_type}."
                )

        valid = not any(e for e in errors if "Missing required field" not in e or "INCOMPLETE" not in tags)
        # Allow INCOMPLETE and DISCREPANCY records through (store with tags)
        valid = True if missing else True
        if "Duplicate" in " ".join(errors) or "future" in " ".join(errors).lower():
            valid = False

        # Register in duplicate cache
        _DUPLICATE_CACHE.add(self._record_hash(record))

        return ValidationResult(valid=valid, errors=errors, tags=tags)

    def _check_duplicate(self, record: VitalRecord) -> bool:
        return self._record_hash(record) in _DUPLICATE_CACHE

    def _check_future_timestamp(self, record: VitalRecord) -> bool:
        ts = record.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts > datetime.now(timezone.utc) + timedelta(hours=24)

    @staticmethod
    def _record_hash(record: VitalRecord) -> str:
        raw = f"{record.source}:{record.timestamp.isoformat()}:{record.vital_type}"
        return hashlib.sha256(raw.encode()).hexdigest()


ingestion_service = IngestionService()
