from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class ConsentRecord:
    user_id: str
    stream_id: str # e.g. "wearable_vitals", "manual_input", "ehr_import"
    consented: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"
