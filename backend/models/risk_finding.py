from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional, Tuple, Dict
import uuid

@dataclass
class CounterfactualResult:
    variable: str
    change_description: str
    estimated_risk_delta: float
    confidence_interval: Tuple[float, float]
    assumptions: List[str]

@dataclass
class VitalRef:
    vital_id: str
    vital_type: str

@dataclass
class RiskFinding:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: Literal["rule_engine", "tgnn", "causal_engine"] = "rule_engine"
    rule_id: Optional[str] = None
    severity: Literal["red_flag", "yellow_flag", "info"] = "info"
    contributing_vitals: List[VitalRef] = field(default_factory=list)
    trust_score: float = 0.0
    confidence: float = 0.0
    plain_language_summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    causal_pathway: Optional[List[str]] = None
    counterfactual: Optional[CounterfactualResult] = None
    shap_values: Optional[Dict[str, float]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
