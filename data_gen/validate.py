"""
validate.py — Validates synthetic data distributions vs expected population stats
using KL divergence to ensure the generated data is clinically realistic.
"""

import json
import math
from pathlib import Path
from typing import List, Dict


def kl_divergence(p: List[float], q: List[float]) -> float:
    """KL divergence D_KL(P || Q). Bins must have equal length and sum to 1."""
    eps = 1e-10
    return sum(pi * math.log((pi + eps) / (qi + eps)) for pi, qi in zip(p, q))


def histogram(values: List[float], bins: int = 20) -> List[float]:
    """Normalised histogram (probability mass per bin)."""
    if not values:
        return [0.0] * bins
    lo, hi = min(values), max(values)
    if lo == hi:
        return [1.0] + [0.0] * (bins - 1)
    width = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        idx = min(int((v - lo) / width), bins - 1)
        counts[idx] += 1
    total = sum(counts)
    return [c / total for c in counts]


# ── Reference distributions (approximate healthy adult population) ──
REFERENCE_MEANS = {
    "heart_rate":               72,
    "spo2":                     97,
    "blood_pressure_systolic":  118,
    "blood_pressure_diastolic": 76,
    "glucose_fasting":          95,
    "steps":                    7500,
    "sleep_hours":              7.0,
}

REFERENCE_STDS = {
    "heart_rate":               10,
    "spo2":                     2,
    "blood_pressure_systolic":  14,
    "blood_pressure_diastolic": 10,
    "glucose_fasting":          18,
    "steps":                    3000,
    "sleep_hours":              1.2,
}

KL_THRESHOLD = 0.15  # Maximum acceptable KL divergence


def generate_gaussian_reference(mean: float, std: float, n: int = 1000) -> List[float]:
    import random
    return [random.gauss(mean, std) for _ in range(n)]


def validate_file(path: str = "./data/synthetic_records.json") -> bool:
    file = Path(path)
    if not file.exists():
        print(f"[WARN] File not found: {path}")
        return False

    with open(file, "r", encoding="utf-8") as f:
        records = json.load(f)

    # Group by vital type
    by_type: Dict[str, List[float]] = {}
    for rec in records:
        vt = rec.get("vital_type")
        if vt:
            by_type.setdefault(vt, []).append(float(rec["value"]))

    print(f"\n📋 Validating {len(records)} records across {len(by_type)} vital types…\n")
    all_pass = True

    for vt, values in by_type.items():
        if vt not in REFERENCE_MEANS:
            continue

        mean = REFERENCE_MEANS[vt]
        std  = REFERENCE_STDS[vt]
        ref  = generate_gaussian_reference(mean, std)

        # Use shared range for both histograms
        lo = min(min(values), min(ref))
        hi = max(max(values), max(ref))

        def hist_shared(vals, bins=20):
            if lo == hi:
                return [1.0] + [0.0] * (bins - 1)
            width = (hi - lo) / bins
            counts = [0] * bins
            for v in vals:
                idx = min(int((v - lo) / width), bins - 1)
                counts[idx] += 1
            total = sum(counts)
            return [c / total for c in counts]

        p = hist_shared(values)
        q = hist_shared(ref)
        kl = kl_divergence(p, q)

        status = "✅ PASS" if kl < KL_THRESHOLD else "❌ FAIL"
        if kl >= KL_THRESHOLD:
            all_pass = False

        actual_mean = sum(values) / len(values)
        actual_std  = math.sqrt(sum((v - actual_mean) ** 2 for v in values) / len(values))

        print(f"  {status}  {vt:<35} "
              f"n={len(values):<5} "
              f"mean={actual_mean:>7.1f} (ref {mean:>6.1f})  "
              f"std={actual_std:>6.1f} (ref {std:>5.1f})  "
              f"KL={kl:.4f}")

    print(f"\n{'✅ All distributions within KL threshold.' if all_pass else '❌ Some distributions deviate beyond threshold.'}\n")
    return all_pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate synthetic data distributions")
    parser.add_argument("--file", type=str, default="./data/synthetic_records.json")
    args = parser.parse_args()
    ok = validate_file(args.file)
    raise SystemExit(0 if ok else 1)
