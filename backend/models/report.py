from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional, Tuple
import uuid
from .risk_finding import VitalRef

@dataclass
class ExplainabilityReport:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    finding_id: str = ""
    plain_language_summary: str = ""
    contributing_vitals: List[VitalRef] = field(default_factory=list)
    trust_score: float = 0.0
    confidence_pct: float = 0.0
    data_quality_warning: bool = False
    top_shap_features: Optional[List[Tuple[str, float]]] = None
    causal_pathway_svg: Optional[str] = None
    counterfactual_summary: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    format: Literal["json"] = "json"
