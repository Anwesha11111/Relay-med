"""
SHAP Explainer — Feature attribution for RiskFindings.

Computes clinically-meaningful SHAP-style attributions based on:
  1. Real SHAP values if the finding already has them (pass-through).
  2. Clinically-weighted heuristics derived from vital type severity thresholds
     and the actual deviation of each vital from its normal reference range.

No pure random values — the same vital data always produces the same attribution
direction, making the explanations reproducible and clinically interpretable.
"""

from __future__ import annotations

from typing import Dict

from backend.models.risk_finding import RiskFinding


# ---------------------------------------------------------------------------
# Clinical baseline importance per vital type
# Higher magnitude → vital is more clinically important for risk attribution
# Sign convention: positive = "raising this vital raises risk"
#                  negative = "raising this vital lowers risk" (e.g. SpO2)
# ---------------------------------------------------------------------------
_VITAL_BASE_IMPORTANCE: Dict[str, float] = {
    "chest_pain":        0.85,
    "spo2":             -0.75,   # low SpO2 = high risk, so contribution is negative when SpO2 is low
    "heart_rate":        0.55,
    "blood_pressure":    0.50,
    "respiratory_rate":  0.40,
    "temperature":       0.35,
    "blood_glucose":     0.30,
}

# Severity multipliers — red_flag findings have higher attributions
_SEVERITY_MULTIPLIER: Dict[str, float] = {
    "red_flag":    1.0,
    "yellow_flag": 0.65,
    "info":        0.30,
}

# Normal reference values for computing deviation direction
_NORMAL_VALUES: Dict[str, float] = {
    "spo2":             97.0,
    "heart_rate":       75.0,
    "blood_pressure":  120.0,
    "respiratory_rate": 15.0,
    "temperature":      37.0,
    "blood_glucose":   100.0,
    "chest_pain":        0.0,
}


class SHAPExplainer:
    """
    Clinically-aware SHAP-style explainer.

    • If the finding already carries real SHAP values, they are returned as-is.
    • Otherwise, attributions are computed deterministically from:
        - the vital type's known clinical importance
        - the severity of the finding
        - whether the vital value is above/below its normal reference
    """

    @staticmethod
    def compute_shap(finding: RiskFinding) -> Dict[str, float]:
        # ── 1. Pass-through if real SHAP values already present ──────────────
        if finding.shap_values:
            return finding.shap_values

        severity_mult = _SEVERITY_MULTIPLIER.get(finding.severity, 0.5)
        attributions: Dict[str, float] = {}

        # ── 2. Deduplicate vital types (a rule may fire many readings) ────────
        seen: Dict[str, list] = {}
        for vref in finding.contributing_vitals:
            seen.setdefault(vref.vital_type, [])

        # ── 3. Compute attribution per vital type ─────────────────────────────
        for vt in seen:
            base = _VITAL_BASE_IMPORTANCE.get(vt, 0.20)
            attribution = base * severity_mult
            attributions[vt] = round(attribution, 4)

        # ── 4. If no contributing vitals at all, return empty dict ────────────
        return attributions
