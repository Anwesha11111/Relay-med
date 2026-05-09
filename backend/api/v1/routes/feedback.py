"""
Feedback API Routes — Submit and manage AI output feedback.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.services.feedback_service import feedback_service

router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    report_id: str = Field(..., description="ID of the AI report being corrected")
    feedback_type: str = Field(
        ..., description="Type: incorrect_diagnosis, wrong_recommendation, "
                         "false_alarm, missed_finding, data_error, other"
    )
    user_comment: str = Field("", description="Free-text explanation")
    corrected_value: Optional[float] = Field(None, description="Corrected value if applicable")
    user_role: str = Field("patient", description="patient, clinician, or reviewer")
    vital_type: Optional[str] = Field(None, description="Vital type if data_error")


@router.post("")
async def submit_feedback(req: FeedbackRequest):
    """Submit feedback on an AI output."""
    valid_types = [
        "incorrect_diagnosis", "wrong_recommendation",
        "false_alarm", "missed_finding", "data_error", "other",
    ]
    if req.feedback_type not in valid_types:
        raise HTTPException(400, f"Invalid feedback_type. Must be one of: {valid_types}")
    if req.user_role not in ["patient", "clinician", "reviewer"]:
        raise HTTPException(400, "user_role must be: patient, clinician, or reviewer")

    fb = feedback_service.submit_feedback(
        report_id=req.report_id,
        feedback_type=req.feedback_type,
        user_comment=req.user_comment,
        user_role=req.user_role,
        corrected_value=req.corrected_value,
        vital_type=req.vital_type,
    )
    return {"status": "submitted", "feedback_id": fb.id}


@router.get("/stats")
async def feedback_stats():
    """Get aggregated feedback statistics."""
    return feedback_service.get_feedback_stats()


@router.get("/pending")
async def pending_corrections():
    """Get corrections that have reached the concordance threshold."""
    return feedback_service.get_pending_corrections()


@router.post("/apply")
async def apply_corrections():
    """Apply verified corrections (clinician-only concordant corrections)."""
    result = feedback_service.apply_corrections()
    return result


@router.get("/history")
async def feedback_history(limit: int = 100):
    """Get recent feedback entries."""
    return feedback_service.get_all_feedback(limit=limit)
