"""
validate.py — Validates synthetic data distributions vs expected population stats
using KL divergence to ensure the generated data is clinically realistic.

Extended with demographic distribution validation and bias metrics.
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

    print(f"\n[VALIDATE] Validating {len(records)} records across {len(by_type)} vital types...\n")
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

        status = "[PASS]" if kl < KL_THRESHOLD else "[FAIL]"
        if kl >= KL_THRESHOLD:
            all_pass = False

        actual_mean = sum(values) / len(values)
        actual_std  = math.sqrt(sum((v - actual_mean) ** 2 for v in values) / len(values))

        print(f"  {status}  {vt:<35} "
              f"n={len(values):<5} "
              f"mean={actual_mean:>7.1f} (ref {mean:>6.1f})  "
              f"std={actual_std:>6.1f} (ref {std:>5.1f})  "
              f"KL={kl:.4f}")

    print(f"\n{'[PASS] All distributions within KL threshold.' if all_pass else '[FAIL] Some distributions deviate beyond threshold.'}\n")
    return all_pass


def validate_demographics(dataset_dir: str = "./data/reference_dataset") -> bool:
    """Validate demographic distribution of the generated dataset."""
    ddir = Path(dataset_dir)
    patients_path = ddir / "patients.json"

    if not patients_path.exists():
        print(f"[WARN] Patients file not found: {patients_path}")
        return False

    with open(patients_path, "r", encoding="utf-8") as f:
        patients = json.load(f)

    n = len(patients)
    print(f"\n[DEMO] Demographic Validation -- {n} patients\n")

    from data_gen.population_profiles import (
        AGE_BUCKET_WEIGHTS, GENDER_WEIGHTS, ETHNICITY_WEIGHTS,
    )

    all_pass = True

    # Age distribution
    print("  -- Age Buckets --")
    age_counts: Dict[str, int] = {}
    for p in patients:
        ab = p.get("age_bucket", "unknown")
        age_counts[ab] = age_counts.get(ab, 0) + 1
    for ab, expected_w in AGE_BUCKET_WEIGHTS.items():
        actual_w = age_counts.get(ab, 0) / n
        deviation = abs(actual_w - expected_w)
        ok = deviation < 0.05  # Allow 5% deviation
        status = "[OK]" if ok else "[!!]"
        if not ok:
            all_pass = False
        print(f"    {status} {ab:<15} {actual_w:.1%} (expected {expected_w:.1%}, dev={deviation:.1%})")

    # Gender distribution
    print("  -- Gender --")
    gender_counts: Dict[str, int] = {}
    for p in patients:
        g = p.get("gender", "unknown")
        gender_counts[g] = gender_counts.get(g, 0) + 1
    for g, expected_w in GENDER_WEIGHTS.items():
        actual_w = gender_counts.get(g, 0) / n
        deviation = abs(actual_w - expected_w)
        ok = deviation < 0.05
        status = "[OK]" if ok else "[!!]"
        if not ok:
            all_pass = False
        print(f"    {status} {g:<15} {actual_w:.1%} (expected {expected_w:.1%}, dev={deviation:.1%})")

    # Ethnicity distribution
    print("  -- Ethnicity --")
    eth_counts: Dict[str, int] = {}
    for p in patients:
        e = p.get("ethnicity", "unknown")
        eth_counts[e] = eth_counts.get(e, 0) + 1
    for e, expected_w in ETHNICITY_WEIGHTS.items():
        actual_w = eth_counts.get(e, 0) / n
        deviation = abs(actual_w - expected_w)
        ok = deviation < 0.05
        status = "[OK]" if ok else "[!!]"
        if not ok:
            all_pass = False
        print(f"    {status} {e:<15} {actual_w:.1%} (expected {expected_w:.1%}, dev={deviation:.1%})")

    # Condition distribution
    print("  -- Conditions --")
    cond_counts: Dict[str, int] = {}
    for p in patients:
        for c in p.get("conditions", []):
            cond_counts[c] = cond_counts.get(c, 0) + 1
    for c, count in sorted(cond_counts.items(), key=lambda x: -x[1]):
        print(f"    {c:<20} {count:>5} ({count/n:.1%})")

    result = "[PASS] Demographics within tolerance." if all_pass else "[FAIL] Some demographics deviate beyond tolerance."
    print(f"\n{result}\n")
    return all_pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Validate synthetic data distributions")
    parser.add_argument("--file", type=str, default="./data/synthetic_records.json")
    parser.add_argument("--dataset-dir", type=str, default="./data/reference_dataset")
    parser.add_argument("--demographics", action="store_true", help="Also validate demographics")
    args = parser.parse_args()

    ok = validate_file(args.file)

    if args.demographics:
        demo_ok = validate_demographics(args.dataset_dir)
        ok = ok and demo_ok

    raise SystemExit(0 if ok else 1)
