"""
models/trust_score.py — TrustScore dataclass.

Holds the decomposed trust score produced by TrustScorer so that
callers can inspect each component separately in addition to the
final blended value.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TrustScore:
    """
    Decomposed trust score for a single VitalRecord.

    Attributes
    ----------
    record_id : str
        ID of the VitalRecord this score was computed for.
    final_score : float
        Blended score in [0.0, 1.0].
    source_reliability : float
        Component score based on the data source (wearable > manual > EHR).
    completeness_ratio : float
        Fraction of optional fields that were populated.
    recency_factor : float
        Freshness penalty: 1.0 for brand-new data, approaches 0 for data
        older than the staleness threshold.
    computed_at : datetime
        UTC timestamp of when the score was calculated.
    """

    record_id: str
    final_score: float
    source_reliability: float
    completeness_ratio: float
    recency_factor: float
    computed_at: datetime

    def __post_init__(self) -> None:
        for attr in ("final_score", "source_reliability", "completeness_ratio", "recency_factor"):
            val = getattr(self, attr)
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"TrustScore.{attr} must be in [0.0, 1.0], got {val!r}"
                )

    @property
    def label(self) -> str:
        """Human-readable quality label derived from final_score."""
        if self.final_score >= 0.85:
            return "high"
        if self.final_score >= 0.60:
            return "medium"
        return "low"

    def as_dict(self) -> dict:
        return {
            "record_id":          self.record_id,
            "final_score":        round(self.final_score, 4),
            "source_reliability": round(self.source_reliability, 4),
            "completeness_ratio": round(self.completeness_ratio, 4),
            "recency_factor":     round(self.recency_factor, 4),
            "label":              self.label,
            "computed_at":        self.computed_at.isoformat(),
        }
