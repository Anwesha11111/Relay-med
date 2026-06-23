"""
T-GNN Engine — Temporal Graph Neural Network inference.

Phase 2: PyTorch Geometric integration point.
Currently uses a deterministic clinical-heuristic model that produces
meaningful risk scores based on the actual vital values in the health graph
(no pure random — same data → same prediction direction).

Replace `_heuristic_predict()` with a real T-GNN forward pass once
torch-geometric models are trained.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Literal, Optional, Tuple

from backend.services.health_graph import health_graph


# ---------------------------------------------------------------------------
# Clinical risk weights per vital type (higher = more influential)
# ---------------------------------------------------------------------------
_VITAL_RISK_WEIGHTS: Dict[str, float] = {
    "spo2":             -0.45,   # low SpO2 strongly predicts risk
    "heart_rate":        0.30,   # elevated HR → risk
    "blood_pressure":    0.25,
    "respiratory_rate":  0.20,
    "temperature":       0.15,
    "blood_glucose":     0.12,
    "chest_pain":        0.50,   # chest-pain flag → highest weight
}

# Normal reference values used to compute deviation
_NORMAL_VALUES: Dict[str, float] = {
    "spo2":             97.0,
    "heart_rate":       75.0,
    "blood_pressure":  120.0,
    "respiratory_rate": 15.0,
    "temperature":      37.0,
    "blood_glucose":   100.0,
    "chest_pain":        0.0,
}

# Normalisation denominators (approximate physiologic range)
_RANGE: Dict[str, float] = {
    "spo2":             10.0,
    "heart_rate":       60.0,
    "blood_pressure":   60.0,
    "respiratory_rate": 10.0,
    "temperature":       3.0,
    "blood_glucose":    80.0,
    "chest_pain":       10.0,
}

# Horizon multipliers: longer horizon → slightly higher uncertainty
_HORIZON_MULTIPLIER: Dict[str, float] = {
    "3m":  1.00,
    "6m":  1.08,
    "12m": 1.15,
}


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class TGNNPrediction:
    horizon: Literal["3m", "6m", "12m"]
    risk_score: float                        # 0.0 – 1.0
    confidence_interval: Tuple[float, float]
    feature_attributions: Dict[str, float]   # vital_type → attribution weight
    model_version: str = "heuristic-v1"
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Serialise to a plain dict for inclusion in RiskFinding.tgnn_prediction."""
        return {
            "horizon": self.horizon,
            "risk_score": round(self.risk_score, 4),
            "confidence_interval": [
                round(self.confidence_interval[0], 4),
                round(self.confidence_interval[1], 4),
            ],
            "feature_attributions": {k: round(v, 4) for k, v in self.feature_attributions.items()},
            "model_version": self.model_version,
            "generated_at": self.generated_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TGNNEngine:
    """
    Temporal GNN risk predictor.

    • Uses clinically-weighted deviations from normal vital values to compute
      a deterministic risk score — no pure random, so the same health data
      always produces the same prediction direction.
    • Feature attributions reflect actual vital-type clinical importance.
    • Confidence interval widens for longer horizons.

    Replace `_heuristic_predict()` with a real T-GNN once a PyG model is
    available.
    """

    # Vital types to query for prediction
    _VITAL_TYPES = list(_VITAL_RISK_WEIGHTS.keys())

    def predict(self, horizon: Literal["3m", "6m", "12m"] = "6m") -> TGNNPrediction:
        """Return a TGNNPrediction for the given forecast horizon."""
        try:
            return self._heuristic_predict(horizon)
        except Exception as exc:
            # Graceful fallback: return a low-confidence neutral score
            return TGNNPrediction(
                horizon=horizon,
                risk_score=0.5,
                confidence_interval=(0.35, 0.65),
                feature_attributions={},
                model_version="fallback",
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _heuristic_predict(self, horizon: Literal["3m", "6m", "12m"]) -> TGNNPrediction:
        """Deterministic heuristic model based on recent vital values."""
        attributions: Dict[str, float] = {}
        weighted_sum = 0.0
        total_weight = 0.0

        for vt in self._VITAL_TYPES:
            records = health_graph.get_recent_values(vt, days=7, use_privatized=False)
            if not records:
                continue

            # Average value over last 7 days
            avg_val = sum(r["value"] for r in records) / len(records)
            normal = _NORMAL_VALUES.get(vt, avg_val)
            scale = _RANGE.get(vt, 1.0) or 1.0
            weight = _VITAL_RISK_WEIGHTS.get(vt, 0.1)

            # Normalised deviation: positive → above normal, negative → below normal
            deviation = (avg_val - normal) / scale

            # For vital types where higher = worse (e.g. chest_pain, heart_rate)
            # the weight is positive; for SpO2 (lower = worse) weight is negative.
            contribution = weight * deviation
            attributions[vt] = round(contribution, 4)
            weighted_sum += contribution
            total_weight += abs(weight)

        if total_weight == 0:
            # No data at all → neutral prediction
            return TGNNPrediction(
                horizon=horizon,
                risk_score=0.5,
                confidence_interval=(0.35, 0.65),
                feature_attributions={},
            )

        # Normalise to [0, 1] via sigmoid
        raw_score = weighted_sum / total_weight
        risk_score = 1.0 / (1.0 + math.exp(-raw_score * 5))  # sigmoid with gain=5
        risk_score = max(0.0, min(1.0, risk_score))

        # Wider CI for longer horizons
        multiplier = _HORIZON_MULTIPLIER.get(horizon, 1.0)
        ci_half = 0.08 * multiplier
        ci = (
            max(0.0, round(risk_score - ci_half, 4)),
            min(1.0, round(risk_score + ci_half, 4)),
        )

        return TGNNPrediction(
            horizon=horizon,
            risk_score=round(risk_score, 4),
            confidence_interval=ci,
            feature_attributions=attributions,
        )

    @property
    def is_available(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

tgnn_engine = TGNNEngine()
