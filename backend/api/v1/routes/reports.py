"""
Reports Route — GET /api/v1/reports
Triggers rule evaluation and returns explainability reports with full
SHAP / causal-pathway / TGNN data.
"""

from fastapi import APIRouter
from typing import List, Dict, Any
from backend.services.rule_engine import rule_engine
from backend.services.explainability_service import explainability_service
from backend.services.health_graph import health_graph
from backend.services.tgnn_engine import tgnn_engine
from backend.services.shap_explainer import SHAPExplainer

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/latest", response_model=List[Dict[str, Any]])
async def get_latest_reports():
    findings = rule_engine.evaluate()
    reports = explainability_service.generate_reports(findings)

    # Build a findings lookup so we can attach TGNN + causal data
    findings_by_id = {f.id: f for f in findings}

    return [
        {
            "id": r.id,
            "finding_id": r.finding_id,
            "summary": r.plain_language_summary,
            "severity": findings_by_id[r.finding_id].severity if r.finding_id in findings_by_id else "info",
            "trust_score": r.trust_score,
            "confidence_pct": r.confidence_pct,
            "data_quality_warning": r.data_quality_warning,
            "recommendations": r.recommendations,
            # SHAP
            "top_shap_features": r.top_shap_features,
            # Causal AI
            "causal_pathway": findings_by_id[r.finding_id].causal_pathway if r.finding_id in findings_by_id else None,
            "causal_pathway_svg": r.causal_pathway_svg,
            # TGNN
            "tgnn_prediction": findings_by_id[r.finding_id].tgnn_prediction if r.finding_id in findings_by_id else None,
            # Counterfactual
            "counterfactual_summary": r.counterfactual_summary,
            "generated_at": r.generated_at.isoformat(),
        }
        for r in reports
    ]


@router.get("/ai-summary", response_model=Dict[str, Any])
async def get_ai_summary():
    """
    Returns a consolidated AI summary:
      - TGNN risk forecast for 3m / 6m / 12m horizons
      - Top SHAP features across all findings
      - Active causal pathways
    """
    findings = rule_engine.evaluate()

    # TGNN: multi-horizon predictions
    tgnn_3m  = tgnn_engine.predict("3m").to_dict()
    tgnn_6m  = tgnn_engine.predict("6m").to_dict()
    tgnn_12m = tgnn_engine.predict("12m").to_dict()

    # SHAP: aggregate top features across all active findings
    shap_aggregate: Dict[str, float] = {}
    for f in findings:
        shap_vals = f.shap_values or SHAPExplainer.compute_shap(f)
        for feat, val in shap_vals.items():
            shap_aggregate[feat] = round(shap_aggregate.get(feat, 0.0) + val, 4)
    top_shap = sorted(shap_aggregate.items(), key=lambda x: abs(x[1]), reverse=True)[:6]

    # Causal: collect unique pathways
    causal_pathways = []
    seen_pathways: set = set()
    for f in findings:
        if f.causal_pathway:
            key = f.causal_pathway[0]
            if key not in seen_pathways:
                seen_pathways.add(key)
                causal_pathways.append({
                    "severity": f.severity,
                    "pathway": f.causal_pathway,
                })

    return {
        "tgnn": {
            "3m":  tgnn_3m,
            "6m":  tgnn_6m,
            "12m": tgnn_12m,
        },
        "shap": {
            "top_features": top_shap,
            "finding_count": len(findings),
        },
        "causal": {
            "active_pathways": causal_pathways,
        },
        "flags": {
            "red":    sum(1 for f in findings if f.severity == "red_flag"),
            "yellow": sum(1 for f in findings if f.severity == "yellow_flag"),
            "info":   sum(1 for f in findings if f.severity == "info"),
        },
    }


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
