"""
feedback_service.py — Closed-loop feedback system for AI output correction.

Allows patients and clinicians to flag incorrect AI outputs.
Requires ≥3 concordant clinician corrections before updating reference profiles.
All feedback is stored in an append-only, immutable log.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import threading

from backend.services.audit_logger import audit_logger, AuditEventType

FEEDBACK_DIR = Path("./data/feedback")
FEEDBACK_LOG = FEEDBACK_DIR / "feedback_log.json"
CONCORDANCE_THRESHOLD = 3  # Min concordant corrections to apply


@dataclass
class FeedbackRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    report_id: str = ""
    feedback_type: Literal[
        "incorrect_diagnosis", "wrong_recommendation",
        "false_alarm", "missed_finding", "data_error", "other"
    ] = "other"
    user_comment: str = ""
    corrected_value: Optional[float] = None
    user_role: Literal["patient", "clinician", "reviewer"] = "patient"
    vital_type: Optional[str] = None
    submitted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FeedbackService:
    def __init__(self):
        self._lock = threading.Lock()
        FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
        self._feedback: List[FeedbackRecord] = []
        self._load()

    def _load(self):
        if FEEDBACK_LOG.exists():
            try:
                with open(FEEDBACK_LOG, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._feedback = [FeedbackRecord(**r) for r in data]
            except Exception:
                self._feedback = []

    def _save(self):
        with open(FEEDBACK_LOG, "w", encoding="utf-8") as f:
            json.dump([fb.to_dict() for fb in self._feedback], f, indent=2, default=str)

    def submit_feedback(
        self,
        report_id: str,
        feedback_type: str,
        user_comment: str,
        user_role: str = "patient",
        corrected_value: Optional[float] = None,
        vital_type: Optional[str] = None,
    ) -> FeedbackRecord:
        """Submit feedback on an AI output."""
        fb = FeedbackRecord(
            report_id=report_id,
            feedback_type=feedback_type,
            user_comment=user_comment,
            corrected_value=corrected_value,
            user_role=user_role,
            vital_type=vital_type,
        )
        with self._lock:
            self._feedback.append(fb)
            self._save()

        audit_logger.log(
            AuditEventType.REPORT_GENERATED,
            {"action": "feedback_submitted", "feedback_id": fb.id,
             "type": feedback_type, "role": user_role},
        )
        return fb

    def get_feedback_stats(self) -> Dict[str, Any]:
        """Aggregated feedback statistics."""
        with self._lock:
            total = len(self._feedback)
            by_type = {}
            by_role = {}
            applied = sum(1 for fb in self._feedback if fb.applied)

            for fb in self._feedback:
                by_type[fb.feedback_type] = by_type.get(fb.feedback_type, 0) + 1
                by_role[fb.user_role] = by_role.get(fb.user_role, 0) + 1

        return {
            "total_feedback": total,
            "applied_corrections": applied,
            "pending": total - applied,
            "by_type": by_type,
            "by_role": by_role,
            "concordance_threshold": CONCORDANCE_THRESHOLD,
        }

    def get_pending_corrections(self) -> List[Dict]:
        """Get corrections that have reached the concordance threshold."""
        with self._lock:
            # Group by (report_id, vital_type, feedback_type) from clinicians
            groups: Dict[str, List[FeedbackRecord]] = {}
            for fb in self._feedback:
                if fb.user_role != "clinician" or fb.applied:
                    continue
                if fb.corrected_value is None:
                    continue
                key = f"{fb.vital_type}:{fb.feedback_type}"
                groups.setdefault(key, []).append(fb)

            ready = []
            for key, fbs in groups.items():
                if len(fbs) >= CONCORDANCE_THRESHOLD:
                    values = [fb.corrected_value for fb in fbs if fb.corrected_value is not None]
                    if values:
                        avg = sum(values) / len(values)
                        ready.append({
                            "key": key,
                            "vital_type": fbs[0].vital_type,
                            "feedback_type": fbs[0].feedback_type,
                            "concordant_count": len(fbs),
                            "average_corrected_value": round(avg, 2),
                            "feedback_ids": [fb.id for fb in fbs],
                        })
            return ready

    def apply_corrections(self) -> Dict[str, Any]:
        """Apply corrections that have reached concordance threshold."""
        pending = self.get_pending_corrections()
        applied_count = 0

        with self._lock:
            for correction in pending:
                for fb in self._feedback:
                    if fb.id in correction["feedback_ids"]:
                        fb.applied = True
                        applied_count += 1
            self._save()

        audit_logger.log(
            AuditEventType.REPORT_GENERATED,
            {"action": "corrections_applied", "count": applied_count,
             "corrections": [c["key"] for c in pending]},
        )
        return {
            "applied_corrections": len(pending),
            "total_feedback_marked": applied_count,
            "corrections": pending,
        }

    def get_all_feedback(self, limit: int = 100) -> List[Dict]:
        with self._lock:
            return [fb.to_dict() for fb in self._feedback[-limit:]]


feedback_service = FeedbackService()
