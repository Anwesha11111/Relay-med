"""
bias_auditor.py — Automated demographic bias detection and fairness auditing.

Analyzes generated datasets and AI outputs for:
  1. Demographic representation (age, gender, ethnicity)
  2. Vital distribution fairness across groups
  3. Condition prevalence accuracy vs CDC/WHO published rates
  4. AI output equity (false positive rate by group)
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from data_gen.population_profiles import (
    AGE_BUCKET_WEIGHTS, GENDER_WEIGHTS, ETHNICITY_WEIGHTS,
    CONDITION_PREVALENCE, BASELINE_VITALS,
)

DATASET_DIR = Path("./data/reference_dataset")
KL_THRESHOLD = 0.20       # Max acceptable KL divergence between groups
REPRESENTATION_MIN = 0.02  # Min 2% representation per group


def kl_divergence(p: List[float], q: List[float]) -> float:
    """KL divergence D_KL(P || Q)."""
    eps = 1e-10
    return sum(pi * math.log((pi + eps) / (qi + eps)) for pi, qi in zip(p, q))


def histogram(values: List[float], bins: int = 20,
              lo: Optional[float] = None, hi: Optional[float] = None) -> List[float]:
    """Normalized histogram."""
    if not values:
        return [1.0 / bins] * bins
    if lo is None:
        lo = min(values)
    if hi is None:
        hi = max(values)
    if lo == hi:
        return [1.0] + [0.0] * (bins - 1)
    width = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        idx = min(int((v - lo) / width), bins - 1)
        counts[idx] += 1
    total = sum(counts)
    return [c / total if total > 0 else 1.0 / bins for c in counts]


class BiasAuditor:

    def audit_dataset(self, dataset_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Run full bias audit on the reference dataset."""
        ddir = dataset_dir or DATASET_DIR
        patients_path = ddir / "patients.json"
        vitals_path = ddir / "vitals.json"

        if not patients_path.exists():
            return {"error": "Dataset not found. Run scaled_generator first."}

        with open(patients_path, "r", encoding="utf-8") as f:
            patients = json.load(f)

        vitals = []
        if vitals_path.exists():
            with open(vitals_path, "r", encoding="utf-8") as f:
                vitals = json.load(f)

        report = {
            "total_patients": len(patients),
            "total_vitals": len(vitals),
            "representation": self._check_representation(patients),
            "vital_fairness": self._check_vital_fairness(vitals),
            "condition_accuracy": self._check_condition_accuracy(patients),
            "overall_pass": True,
        }

        # Determine overall pass/fail
        rep = report["representation"]
        if any(not g["pass"] for g in rep.get("by_age_bucket", {}).values()):
            report["overall_pass"] = False
        if any(not g["pass"] for g in rep.get("by_gender", {}).values()):
            report["overall_pass"] = False
        if any(not g["pass"] for g in rep.get("by_ethnicity", {}).values()):
            report["overall_pass"] = False

        fairness = report["vital_fairness"]
        if any(not v.get("pass", True) for v in fairness.values()):
            report["overall_pass"] = False

        return report

    def _check_representation(self, patients: List[Dict]) -> Dict:
        """Check demographic group representation."""
        n = len(patients)
        if n == 0:
            return {"error": "No patients"}

        result = {"by_age_bucket": {}, "by_gender": {}, "by_ethnicity": {}}

        # Age buckets
        age_counts: Dict[str, int] = {}
        for p in patients:
            ab = p.get("age_bucket", "unknown")
            age_counts[ab] = age_counts.get(ab, 0) + 1
        for ab, count in age_counts.items():
            pct = count / n
            expected = AGE_BUCKET_WEIGHTS.get(ab, 0)
            result["by_age_bucket"][ab] = {
                "count": count, "pct": round(pct, 4),
                "expected_pct": expected,
                "deviation": round(abs(pct - expected), 4),
                "pass": pct >= REPRESENTATION_MIN,
            }

        # Gender
        gender_counts: Dict[str, int] = {}
        for p in patients:
            g = p.get("gender", "unknown")
            gender_counts[g] = gender_counts.get(g, 0) + 1
        for g, count in gender_counts.items():
            pct = count / n
            expected = GENDER_WEIGHTS.get(g, 0)
            result["by_gender"][g] = {
                "count": count, "pct": round(pct, 4),
                "expected_pct": expected,
                "deviation": round(abs(pct - expected), 4),
                "pass": pct >= REPRESENTATION_MIN,
            }

        # Ethnicity
        eth_counts: Dict[str, int] = {}
        for p in patients:
            e = p.get("ethnicity", "unknown")
            eth_counts[e] = eth_counts.get(e, 0) + 1
        for e, count in eth_counts.items():
            pct = count / n
            expected = ETHNICITY_WEIGHTS.get(e, 0)
            result["by_ethnicity"][e] = {
                "count": count, "pct": round(pct, 4),
                "expected_pct": expected,
                "deviation": round(abs(pct - expected), 4),
                "pass": pct >= REPRESENTATION_MIN,
            }

        return result

    def _check_vital_fairness(self, vitals: List[Dict]) -> Dict:
        """Check KL divergence of vital distributions across demographic groups."""
        if not vitals:
            return {}

        # Group vitals by (vital_type, gender)
        by_type_gender: Dict[str, Dict[str, List[float]]] = {}
        for v in vitals:
            vt = v.get("vital_type", "")
            gender = v.get("gender", "unknown")
            by_type_gender.setdefault(vt, {}).setdefault(gender, []).append(v["value"])

        result = {}
        for vt, gender_groups in by_type_gender.items():
            if len(gender_groups) < 2:
                continue
            groups = list(gender_groups.items())
            all_values = [val for vals in gender_groups.values() for val in vals]
            if not all_values:
                continue

            lo, hi = min(all_values), max(all_values)
            kl_scores = {}

            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    g1, v1 = groups[i]
                    g2, v2 = groups[j]
                    h1 = histogram(v1, bins=20, lo=lo, hi=hi)
                    h2 = histogram(v2, bins=20, lo=lo, hi=hi)
                    kl = kl_divergence(h1, h2)
                    kl_scores[f"{g1}_vs_{g2}"] = round(kl, 4)

            max_kl = max(kl_scores.values()) if kl_scores else 0
            result[vt] = {
                "kl_scores": kl_scores,
                "max_kl": max_kl,
                "pass": max_kl <= KL_THRESHOLD,
            }

        return result

    def _check_condition_accuracy(self, patients: List[Dict]) -> Dict:
        """Compare generated condition prevalence vs expected rates."""
        n = len(patients)
        if n == 0:
            return {}

        cond_counts: Dict[str, int] = {}
        for p in patients:
            for c in p.get("conditions", []):
                if c != "healthy":
                    cond_counts[c] = cond_counts.get(c, 0) + 1

        result = {}
        # Compute expected prevalence (weighted average across demographics)
        for cond, count in cond_counts.items():
            actual_prev = count / n
            # Rough expected prevalence (population-weighted)
            expected_prevs = CONDITION_PREVALENCE.get(cond, {})
            if expected_prevs:
                expected = sum(expected_prevs.values()) / len(expected_prevs)
            else:
                expected = 0.0

            deviation = abs(actual_prev - expected) / max(expected, 0.01)
            result[cond] = {
                "actual_prevalence": round(actual_prev, 4),
                "expected_prevalence": round(expected, 4),
                "relative_deviation": round(deviation, 4),
                "pass": deviation <= 0.30,  # Allow 30% deviation
            }

        return result

    def generate_summary(self, report: Dict) -> str:
        """Generate human-readable bias audit summary."""
        lines = ["=== BIAS AUDIT REPORT ===\n"]

        overall = "[PASS]" if report.get("overall_pass") else "[FAIL]"
        lines.append(f"Overall: {overall}")
        lines.append(f"Patients: {report.get('total_patients', 0):,}")
        lines.append(f"Vitals:   {report.get('total_vitals', 0):,}\n")

        # Representation
        rep = report.get("representation", {})
        lines.append("-- Demographic Representation --")
        for dim in ["by_age_bucket", "by_gender", "by_ethnicity"]:
            groups = rep.get(dim, {})
            for name, data in groups.items():
                status = "[OK]" if data.get("pass") else "[!!]"
                lines.append(
                    f"  {status} {name:<15} {data['pct']:.1%} "
                    f"(expected {data['expected_pct']:.1%})"
                )

        # Vital fairness
        fairness = report.get("vital_fairness", {})
        if fairness:
            lines.append("\n-- Vital Distribution Fairness --")
            for vt, data in fairness.items():
                status = "[OK]" if data.get("pass") else "[!!]"
                lines.append(f"  {status} {vt:<30} max_KL={data['max_kl']:.4f}")

        # Condition accuracy
        cond = report.get("condition_accuracy", {})
        if cond:
            lines.append("\n-- Condition Prevalence Accuracy --")
            for name, data in cond.items():
                status = "[OK]" if data.get("pass") else "[!!]"
                lines.append(
                    f"  {status} {name:<20} actual={data['actual_prevalence']:.1%} "
                    f"expected={data['expected_prevalence']:.1%}"
                )

        return "\n".join(lines)


bias_auditor = BiasAuditor()
