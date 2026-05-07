"""
Consent Route — GET/POST /api/v1/consent
Manage per-stream consent records for a user.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from backend.services.consent_manager import consent_manager

router = APIRouter(prefix="/consent", tags=["Consent"])


class ConsentRequest(BaseModel):
    user_id: str
    stream_id: str
    consented: bool
    version: str = "1.0"


class ConsentStatusResponse(BaseModel):
    user_id: str
    stream_id: str
    consented: bool
    timestamp: str
    version: str


@router.post("", response_model=ConsentStatusResponse)
async def set_consent(payload: ConsentRequest):
    if payload.consented:
        record = consent_manager.grant_consent(payload.user_id, payload.stream_id, payload.version)
    else:
        record = consent_manager.revoke_consent(payload.user_id, payload.stream_id, payload.version)
    return ConsentStatusResponse(
        user_id=record.user_id,
        stream_id=record.stream_id,
        consented=record.consented,
        timestamp=record.timestamp.isoformat(),
        version=record.version,
    )


@router.get("/{user_id}", response_model=List[ConsentStatusResponse])
async def get_consent(user_id: str):
    records = consent_manager.get_all(user_id)
    return [
        ConsentStatusResponse(
            user_id=r.user_id,
            stream_id=r.stream_id,
            consented=r.consented,
            timestamp=r.timestamp.isoformat(),
            version=r.version,
        )
        for r in records
    ]


@router.get("/{user_id}/{stream_id}/check")
async def check_consent(user_id: str, stream_id: str):
    consented = consent_manager.check_consent(user_id, stream_id)
    return {"user_id": user_id, "stream_id": stream_id, "consented": consented}
