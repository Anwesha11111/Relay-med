"""
Causal Engine — Phase 3 stub (DoWhy causal inference).
Will use DoWhy + CausalNex when Phase 3 is activated.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple


@dataclass
class CausalInferenceResult:
    treatment_variable: str
    outcome_variable: str
    estimated_effect: float
    confidence_interval: Tuple[float, float]
    assumptions: List[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)


class CausalEngine:
    """
    Phase 3 stub. Returns placeholder results.
    Replace estimate_effect() with DoWhy causal graph inference in Phase 3.
    """

    def estimate_effect(
        self,
        treatment: str,
        outcome: str,
    ) -> CausalInferenceResult:
        # Phase 3: build causal graph from health_graph, run DoWhy refutation tests
        return CausalInferenceResult(
            treatment_variable=treatment,
            outcome_variable=outcome,
            estimated_effect=0.0,
            confidence_interval=(0.0, 0.0),
            assumptions=["Phase 3 not yet active."],
        )

    @property
    def is_available(self) -> bool:
        return False


causal_engine = CausalEngine()
