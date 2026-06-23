"""
Explainability Service — Translates RiskFindings into structured ExplainabilityReports.
Applies differential privacy noise to exported confidence values.

Fixes applied:
  • Removed orphaned 'import random' that was trapped inside a triple-quoted
    string and was therefore never executed (NameError at runtime).
  • The fallback SHAP branch now calls SHAPExplainer.compute_shap() instead of
    using random.uniform(), making it consistent and reproducible.
  • causal_pathway_svg is populated from finding.causal_pathway when available
    (rendered as a plain SVG flowchart text block).
"""

from datetime import datetime
from typing import List, Optional
import uuid

from backend.models.risk_finding import RiskFinding
from backend.models.report import ExplainabilityReport
from backend.services.differential_privacy import dp_engine
from backend.services.audit_logger import audit_logger, AuditEventType
from backend.services.shap_explainer import SHAPExplainer

LOW_TRUST_THRESHOLD = 0.5


class ExplainabilityService:

    def generate_report(self, finding: RiskFinding) -> ExplainabilityReport:
        data_quality_warning = finding.trust_score < LOW_TRUST_THRESHOLD

        # Apply DP noise to confidence percentage before surfacing
        privatised_confidence = dp_engine.add_laplace_noise(
            finding.confidence * 100, sensitivity=5.0
        )
        privatised_confidence = max(0.0, min(100.0, privatised_confidence))

        # ── SHAP features ─────────────────────────────────────────────────────
        # Prefer real SHAP values already stored on the finding; otherwise
        # compute clinically-weighted attributions via SHAPExplainer.
        shap_source = finding.shap_values or SHAPExplainer.compute_shap(finding)
        top_shap: Optional[List] = None
        if shap_source:
            sorted_shap = sorted(shap_source.items(), key=lambda x: abs(x[1]), reverse=True)
            top_shap = sorted_shap[:5]

        # ── Counterfactual summary ────────────────────────────────────────────
        cf_summary = None
        if finding.counterfactual:
            cf = finding.counterfactual
            cf_summary = (
                f"If you {cf.change_description}, estimated risk change: "
                f"{cf.estimated_risk_delta:+.1%} "
                f"(CI: {cf.confidence_interval[0]:.1%}–{cf.confidence_interval[1]:.1%})."
            )

        # ── Causal pathway SVG ────────────────────────────────────────────────
        # Build a lightweight SVG/text flowchart from the causal_pathway list.
        causal_svg = self._build_causal_svg(finding.causal_pathway)

        report = ExplainabilityReport(
            id=str(uuid.uuid4()),
            finding_id=finding.id,
            plain_language_summary=self._enrich_summary(finding),
            contributing_vitals=finding.contributing_vitals,
            trust_score=finding.trust_score,
            confidence_pct=round(privatised_confidence, 1),
            data_quality_warning=data_quality_warning,
            top_shap_features=top_shap,
            causal_pathway_svg=causal_svg,
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

    # ── Private helpers ───────────────────────────────────────────────────────

    def _enrich_summary(self, finding: RiskFinding) -> str:
        summary = finding.plain_language_summary
        severity_prefix = {
            "red_flag":    "🔴 URGENT: ",
            "yellow_flag": "🟡 CAUTION: ",
            "info":        "ℹ️ INFO: ",
        }.get(finding.severity, "")
        trust_note = ""
        if finding.trust_score < LOW_TRUST_THRESHOLD:
            trust_note = f" [Data quality warning: trust score {finding.trust_score:.2f}]"
        return f"{severity_prefix}{summary}{trust_note}"

    @staticmethod
    def _build_causal_svg(pathway: Optional[List[str]]) -> Optional[str]:
        """
        Renders the causal pathway as an SVG flowchart.
        Each step in the pathway list becomes a rounded rectangle box with
        a downward arrow between them.  The result is a self-contained SVG
        string that can be embedded directly in HTML or stored as a field.
        """
        if not pathway:
            return None

        box_w, box_h = 360, 44
        arrow_h = 22
        padding_x, padding_y = 20, 16
        step_h = box_h + arrow_h
        total_h = padding_y * 2 + len(pathway) * step_h - arrow_h
        total_w = box_w + padding_x * 2

        # Colour palette
        colours = ["#4f46e5", "#7c3aed", "#9333ea", "#c026d3", "#db2777"]

        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{total_w}" height="{total_h}" '
            f'viewBox="0 0 {total_w} {total_h}" '
            f'style="font-family:Inter,Arial,sans-serif;font-size:12px;">',
            # Background
            f'<rect width="{total_w}" height="{total_h}" rx="10" fill="#0f172a"/>',
        ]

        for i, step in enumerate(pathway):
            y = padding_y + i * step_h
            colour = colours[i % len(colours)]
            # Escape XML special chars
            safe_step = (
                step.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
            )
            # Box
            lines.append(
                f'<rect x="{padding_x}" y="{y}" width="{box_w}" height="{box_h}" '
                f'rx="8" fill="{colour}" opacity="0.92"/>'
            )
            # Step number badge
            lines.append(
                f'<circle cx="{padding_x + 18}" cy="{y + box_h // 2}" r="11" fill="rgba(255,255,255,0.25)"/>'
            )
            lines.append(
                f'<text x="{padding_x + 18}" y="{y + box_h // 2 + 4}" '
                f'text-anchor="middle" fill="white" font-weight="bold">{i + 1}</text>'
            )
            # Step text (truncate if too long)
            display = safe_step if len(safe_step) <= 52 else safe_step[:49] + "…"
            lines.append(
                f'<text x="{padding_x + 38}" y="{y + box_h // 2 + 4}" '
                f'fill="white">{display}</text>'
            )
            # Arrow (skip after last box)
            if i < len(pathway) - 1:
                ax = padding_x + box_w // 2
                ay1 = y + box_h
                ay2 = ay1 + arrow_h - 4
                lines.append(
                    f'<line x1="{ax}" y1="{ay1}" x2="{ax}" y2="{ay2}" '
                    f'stroke="white" stroke-width="2" stroke-opacity="0.6"/>'
                )
                lines.append(
                    f'<polygon points="{ax},{ay2 + 6} {ax - 6},{ay2} {ax + 6},{ay2}" '
                    f'fill="white" opacity="0.6"/>'
                )

        lines.append("</svg>")
        return "\n".join(lines)


explainability_service = ExplainabilityService()
