from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

@dataclass
class AuditEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "" # e.g. "CONSENT_GRANT", "INGEST_SUCCESS", "AUTH_FAILURE"
    user_id: str = ""
    source_ip: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = field(default_factory=list)
