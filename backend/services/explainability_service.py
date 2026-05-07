"""
Explainability Service — Translates RiskFindings into structured ExplainabilityReports.
Applies differential privacy noise to exported confidence values.
"""

from datetime import datetime
from typing import List
import uuid

from backend.models.risk_finding import RiskFinding
from backend.models.report import ExplainabilityReport
from backend.services.differential_privacy import dp_engine
from backend.services.audit_logger import audit_logger, AuditEventType

LOW_TRUST_THRESHOLD = 0.5


class ExplainabilityService:

    def generate_report(self, finding: RiskFinding) -> ExplainabilityReport:
        data_quality_warning = finding.trust_score < LOW_TRUST_THRESHOLD

        # Apply DP noise to confidence percentage before surfacing
        privatised_confidence = dp_engine.add_laplace_noise(
            finding.confidence * 100, sensitivity=5.0
        )
        privatised_confidence = max(0.0, min(100.0, privatised_confidence))

        # Build top SHAP features if available
        top_shap = None
        if finding.shap_values:
            sorted_shap = sorted(finding.shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
            top_shap = sorted_shap[:5]

        # Counterfactual summary
        cf_summary = None
        if finding.counterfactual:
            cf = finding.counterfactual
            cf_summary = (
                f"If you {cf.change_description}, estimated risk change: "
                f"{cf.estimated_risk_delta:+.1%} "
                f"(CI: {cf.confidence_interval[0]:.1%}–{cf.confidence_interval[1]:.1%})."
            )

        report = ExplainabilityReport(
            id=str(uuid.uuid4()),
            finding_id=finding.id,
            plain_language_summary=self._enrich_summary(finding),
            contributing_vitals=finding.contributing_vitals,
            trust_score=finding.trust_score,
            confidence_pct=round(privatised_confidence, 1),
            data_quality_warning=data_quality_warning,
            top_shap_features=top_shap,
            causal_pathway_svg=None,
            counterfactual_summary=cf_summary,
            recommendations=finding.recommendations,
            generated_at=datetime.utcnow(),
        )

        audit_logger.log(
            AuditEventType.REPORT_GENERATED,
            {"report_id": report.id, "finding_id": finding.id, "severity": finding.severity},
        )
        return report

    def generate_reports(self, findings: List[RiskFinding]) -> List[ExplainabilityReport]:
        return [self.generate_report(f) for f in findings]

    def _enrich_summary(self, finding: RiskFinding) -> str:
        summary = finding.plain_language_summary
        severity_prefix = {
            "red_flag": "🔴 URGENT: ",
            "yellow_flag": "🟡 CAUTION: ",
            "info": "ℹ️ INFO: ",
        }.get(finding.severity, "")
        trust_note = ""
        if finding.trust_score < LOW_TRUST_THRESHOLD:
            trust_note = f" [Data quality warning: trust score {finding.trust_score:.2f}]"
        return f"{severity_prefix}{summary}{trust_note}"


explainability_service = ExplainabilityService()
