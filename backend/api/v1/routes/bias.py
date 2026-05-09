"""
Bias Audit API Routes — Run and retrieve demographic bias reports.
"""

from fastapi import APIRouter
from typing import Optional
from pathlib import Path
from backend.services.bias_auditor import bias_auditor

router = APIRouter(prefix="/bias", tags=["Bias Audit"])


@router.get("/audit")
async def run_bias_audit(dataset_dir: Optional[str] = None):
    """Run a full bias audit on the reference dataset."""
    ddir = Path(dataset_dir) if dataset_dir else None
    report = bias_auditor.audit_dataset(ddir)
    return report


@router.get("/report")
async def get_bias_report(dataset_dir: Optional[str] = None):
    """Get a human-readable bias audit report."""
    ddir = Path(dataset_dir) if dataset_dir else None
    report = bias_auditor.audit_dataset(ddir)
    summary = bias_auditor.generate_summary(report)
    return {"report": report, "summary": summary}
