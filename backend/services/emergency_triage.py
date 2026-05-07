"""
Emergency Triage Service — Evaluates red/yellow flag conditions on every ingestion.

GUARANTEE: Red_Flag alerts are NEVER suppressed by low Trust_Score —
           the alert fires with a data quality note appended when trust is low.
"""

from typing import List, Optional
from backend.models.vital import VitalRecord
from backend.models.risk_finding import RiskFinding, VitalRef
from backend.services.audit_logger import audit_logger, AuditEventType
from backend.config import settings
import uuid
from datetime import datetime


LOW_TRUST_THRESHOLD = 0.5


class EmergencyTriageService:
    def evaluate_red_flags(self, record: VitalRecord) -> List[RiskFinding]:
        findings: List[RiskFinding] = []

        # ── Red Flag: Low SpO2 ────────────────────────────────────────────────
        if record.vital_type == "spo2" and record.value < settings.SPO2_RED_FLAG_THRESHOLD:
            finding = self._make_finding(
                severity="red_flag",
                rule_id="ETS_SPO2_CRITICAL",
                summary=(
                    f"Critical SpO2 level detected: {record.value}% "
                    f"(threshold: {settings.SPO2_RED_FLAG_THRESHOLD}%). "
                    f"Seek immediate medical attention."
                ),
                record=record,
                recommendations=[
                    "Call emergency services (911) immediately.",
                    "Do not remain alone.",
                    "If available, use supplemental oxygen.",
                ],
            )
            findings.append(finding)
            audit_logger.log(
                AuditEventType.RED_FLAG_ALERT,
                {"rule": "ETS_SPO2_CRITICAL", "value": record.value, "trust_score": record.trust_score},
                user_id="system",
            )

        # ── Red Flag: Chest Pain ───────────────────────────────────────────────
        if record.vital_type == "chest_pain_severity" and record.value >= settings.CHEST_PAIN_RED_FLAG_THRESHOLD:
            finding = self._make_finding(
                severity="red_flag",
                rule_id="ETS_CHEST_PAIN_CRITICAL",
                summary=(
                    f"High chest pain severity reported: {record.value}/10. "
                    f"This may indicate a cardiac event."
                ),
                record=record,
                recommendations=[
                    "Call emergency services (911) immediately.",
                    "Chew aspirin (325 mg) if not allergic and no contraindications.",
                    "Remain calm and seated. Do not drive yourself.",
                ],
            )
            findings.append(finding)
            audit_logger.log(
                AuditEventType.RED_FLAG_ALERT,
                {"rule": "ETS_CHEST_PAIN_CRITICAL", "value": record.value, "trust_score": record.trust_score},
                user_id="system",
            )

        # Append data quality note if trust is low (but NEVER suppress)
        if record.trust_score is not None and record.trust_score < LOW_TRUST_THRESHOLD:
            for f in findings:
                f.plain_language_summary += (
                    f" ⚠️ Data quality note: trust score is low ({record.trust_score:.2f}). "
                    "Please verify this reading with a calibrated device."
                )

        return findings

    def _make_finding(
        self,
        severity: str,
        rule_id: str,
        summary: str,
        record: VitalRecord,
        recommendations: List[str],
    ) -> RiskFinding:
        return RiskFinding(
            id=str(uuid.uuid4()),
            source="rule_engine",
            rule_id=rule_id,
            severity=severity,
            contributing_vitals=[VitalRef(vital_id=record.id, vital_type=record.vital_type)],
            trust_score=record.trust_score or 0.0,
            confidence=1.0,  # Threshold-based rules have deterministic confidence
            plain_language_summary=summary,
            recommendations=recommendations,
            timestamp=datetime.utcnow(),
        )


emergency_triage_service = EmergencyTriageService()
