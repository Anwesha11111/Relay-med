"""
Audit Route — GET /api/v1/audit
Query the append-only audit log.
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime, timedelta
from backend.services.audit_logger import audit_logger, AuditEventType

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs")
async def get_logs(
    event_type: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=8760),
    limit: int = Query(100, ge=1, le=1000),
):
    start = datetime.utcnow() - timedelta(hours=hours)
    entries = audit_logger.query(event_type=event_type, start=start, limit=limit)
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "user_id": e.user_id,
            "timestamp": e.timestamp.isoformat(),
            "payload": e.payload,
        }
        for e in entries
    ]


@router.get("/event-types")
async def get_event_types():
    return [e.value for e in AuditEventType]
