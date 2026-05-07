"""
Ingest Route — POST /api/v1/ingest
Receives a vital record, checks consent, and runs the full ingestion pipeline.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
import uuid

from backend.services.consent_manager import consent_manager
from backend.services.ingestion_service import ingestion_service
from backend.models.vital import VitalRecord

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


class IngestRequest(BaseModel):
    source: str = Field(..., example="fitbit")
    vital_type: str = Field(..., example="heart_rate")
    value: float = Field(..., example=72.5)
    unit: str = Field(..., example="bpm")
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = {}
    user_id: Optional[str] = "default"
    stream_id: Optional[str] = "wearable_vitals"


class IngestResponse(BaseModel):
    success: bool
    record_id: Optional[str]
    tags: List[str]
    errors: List[str]
    triage_alerts: List[Dict]


@router.post("", response_model=IngestResponse, status_code=201)
async def ingest_vital(payload: IngestRequest, request: Request):
    # 1. Consent check
    if not consent_manager.check_consent(payload.user_id, payload.stream_id):
        raise HTTPException(
            status_code=403,
            detail=f"Consent not granted for stream '{payload.stream_id}'. "
                   "Please grant consent before submitting data.",
        )

    # 2. Build VitalRecord
    record = VitalRecord(
        id=str(uuid.uuid4()),
        source=payload.source,
        vital_type=payload.vital_type,
        value=payload.value,
        unit=payload.unit,
        timestamp=payload.timestamp or datetime.utcnow(),
        metadata=payload.metadata or {},
    )

    # 3. Ingest
    result = await ingestion_service.ingest(record, user_id=payload.user_id)

    if not result.success and result.errors:
        non_tag_errors = [e for e in result.errors if "Missing required field" not in e]
        if non_tag_errors:
            raise HTTPException(status_code=422, detail=result.errors)

    return IngestResponse(
        success=result.success,
        record_id=result.record_id,
        tags=result.tags,
        errors=result.errors,
        triage_alerts=[
            {
                "severity": f.severity,
                "summary": f.plain_language_summary,
                "recommendations": f.recommendations,
            }
            for f in result.triage_findings
        ],
    )
