"""
T-GNN Engine — Phase 2 stub (Temporal Graph Neural Network).
Will use PyTorch Geometric when Phase 2 is activated.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Literal, Tuple


@dataclass
class TGNNPrediction:
    horizon: Literal["3m", "6m", "12m"]
    risk_score: float
    confidence_interval: Tuple[float, float]
    feature_attributions: Dict[str, float]
    generated_at: datetime = field(default_factory=datetime.utcnow)


class TGNNEngine:
    """
    Phase 2 stub. Returns a placeholder prediction.
    Replace predict() body with PyTorch Geometric T-GNN inference in Phase 2.
    """

    def predict(self, horizon: Literal["3m", "6m", "12m"] = "6m") -> TGNNPrediction:
        # Phase 2: load PyTorch Geometric model, run inference on health_graph
        # Note: Inference is performed on 'privatized_value' to ensure user privacy 
        # and prevent data reconstruction by the model weights.
        return TGNNPrediction(
            horizon=horizon,
            risk_score=0.0,
            confidence_interval=(0.0, 0.0),
            feature_attributions={},
            generated_at=datetime.utcnow(),
        )

    @property
    def is_available(self) -> bool:
        """Returns True when Phase 2 model weights are present."""
        return False


tgnn_engine = TGNNEngine()
