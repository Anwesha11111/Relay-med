"""
Reports Route — GET /api/v1/reports
Triggers rule evaluation and returns explainability reports.
"""

from fastapi import APIRouter
from typing import List, Dict, Any
from backend.services.rule_engine import rule_engine
from backend.services.explainability_service import explainability_service
from backend.services.health_graph import health_graph

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/latest", response_model=List[Dict[str, Any]])
async def get_latest_reports():
    findings = rule_engine.evaluate()
    reports = explainability_service.generate_reports(findings)
    return [
        {
            "id": r.id,
            "finding_id": r.finding_id,
            "summary": r.plain_language_summary,
            "trust_score": r.trust_score,
            "confidence_pct": r.confidence_pct,
            "data_quality_warning": r.data_quality_warning,
            "recommendations": r.recommendations,
            "top_shap_features": r.top_shap_features,
            "counterfactual_summary": r.counterfactual_summary,
            "generated_at": r.generated_at.isoformat(),
        }
        for r in reports
    ]


@router.get("/graph/stats")
async def get_graph_stats():
    return {
        "node_count": health_graph.get_node_count(),
        "edge_count": health_graph.get_edge_count(),
    }


@router.get("/graph/nodes")
async def get_graph_nodes():
    return health_graph.get_all_nodes()


@router.get("/vitals/{vital_type}")
async def get_vital_history(vital_type: str, days: int = 30):
    records = health_graph.get_recent_values(vital_type, days=days)
    return [
        {
            "id": r["id"],
            "value": r["value"],
            "unit": r.get("unit", ""),
            "timestamp": r["timestamp"].isoformat() if hasattr(r["timestamp"], "isoformat") else str(r["timestamp"]),
            "trust_score": r.get("trust_score", 0),
            "tags": r.get("tags", []),
        }
        for r in records
    ]
