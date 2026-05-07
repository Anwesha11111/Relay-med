"""
Trust Scorer — Computes Trust_Score ∈ [0.0, 1.0] for each validated VitalRecord.

Formula:
  trust_score = w_source * source_reliability
              + w_completeness * completeness_ratio
              + w_recency * recency_factor
"""

from datetime import datetime, timezone
from backend.models.vital import VitalRecord
from backend.config import settings

# Optional fields that contribute to completeness score
OPTIONAL_FIELDS = ["metadata"]

SOURCE_RELIABILITY: dict = {
    "fitbit": 1.0,
    "apple_health": 1.0,
    "manual": 0.7,
    "ehr": 0.5,
}


class TrustScorer:
    def __init__(self):
        self.w_source = settings.TRUST_WEIGHT_SOURCE
        self.w_completeness = settings.TRUST_WEIGHT_COMPLETENESS
        self.w_recency = settings.TRUST_WEIGHT_RECENCY
        self.staleness_days = settings.STALENESS_THRESHOLD_DAYS

    def compute_trust_score(self, record: VitalRecord) -> float:
        source_rel = SOURCE_RELIABILITY.get(record.source, 0.5)
        completeness = self._completeness(record)
        recency = self._recency(record)

        score = (
            self.w_source * source_rel
            + self.w_completeness * completeness
            + self.w_recency * recency
        )
        return round(min(max(score, 0.0), 1.0), 4)

    def _completeness(self, record: VitalRecord) -> float:
        total = len(OPTIONAL_FIELDS)
        if total == 0:
            return 1.0
        present = sum(1 for f in OPTIONAL_FIELDS if getattr(record, f, None))
        return present / total

    def _recency(self, record: VitalRecord) -> float:
        now = datetime.now(timezone.utc)
        ts = record.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age_days = (now - ts).total_seconds() / 86400
        return max(0.0, 1.0 - (age_days / self.staleness_days))


trust_scorer = TrustScorer()
