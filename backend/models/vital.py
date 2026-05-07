from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
import uuid

@dataclass
class VitalRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: Literal["fitbit", "apple_health", "manual", "ehr"] = "manual"
    vital_type: str = "" # e.g. "heart_rate", "spo2", "blood_pressure_systolic"
    value: float = 0.0
    privatized_value: Optional[float] = None
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    trust_score: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
