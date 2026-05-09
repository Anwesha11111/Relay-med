"""
scaled_generator.py — Demographic-stratified synthetic health data generator.

Generates thousands of synthetic patients with realistic demographic profiles,
condition assignments, and longitudinal vital sign records.

Usage:
    python -m data_gen.scaled_generator --patients 5000 --days 365
    python -m data_gen.scaled_generator --patients 500 --days 90 --quick
"""

import json
import math
import random
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from data_gen.population_profiles import (
    AGE_BUCKETS, AGE_RANGES, AGE_BUCKET_WEIGHTS,
    GENDERS, GENDER_WEIGHTS,
    ETHNICITIES, ETHNICITY_WEIGHTS,
    CONDITIONS, CONDITION_PREVALENCE,
    BASELINE_VITALS, DEVICE_PROFILES,
    get_vital_profile, get_condition_prevalence,
)

# ── Output directory ──────────────────────────────────────────────────────────
OUTPUT_DIR = Path("./data/reference_dataset")

# ── Which vitals to generate per reading slot ─────────────────────────────────
VITAL_TYPES_PER_SLOT = [
    "heart_rate", "spo2", "blood_pressure_systolic",
    "blood_pressure_diastolic", "steps", "sleep_hours",
    "glucose_fasting", "respiratory_rate", "temperature",
]

# Vitals measured less frequently (weekly/monthly)
WEEKLY_VITALS = ["weight", "bmi"]

SOURCES = list(DEVICE_PROFILES.keys())
SOURCE_WEIGHTS = [0.30, 0.30, 0.30, 0.10]  # fitbit, apple_health, manual, ehr

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class SyntheticPatient:
    patient_id: str
    age: int
    age_bucket: str
    gender: str
    ethnicity: str
    conditions: List[str]
    primary_device: str
    bmi_baseline: float = 25.0
    weight_baseline: float = 75.0
    height_cm: float = 170.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VitalReading:
    record_id: str
    patient_id: str
    vital_type: str
    value: float
    unit: str
    source: str
    timestamp: str
    age_bucket: str
    gender: str
    conditions: List[str]
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConditionRecord:
    patient_id: str
    condition: str
    onset_date: str
    diagnosed_by: str = "simulated"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Sampling helpers ──────────────────────────────────────────────────────────

def _weighted_choice(options: list, weights: list) -> Any:
    return random.choices(options, weights=weights, k=1)[0]


def _sample_age(age_bucket: str) -> int:
    lo, hi = AGE_RANGES[age_bucket]
    return random.randint(lo, hi)


def _sample_bmi(age_bucket: str, gender: str, has_obesity: bool) -> float:
    """Sample a realistic BMI based on demographics."""
    if has_obesity:
        mean, std = 34.0, 5.0
    elif age_bucket == "pediatric":
        mean, std = 19.0, 3.0
    elif gender == "female":
        mean, std = 26.0, 4.5
    else:
        mean, std = 25.5, 4.0

    # Age adjustment
    if age_bucket == "middle_aged":
        mean += 1.5
    elif age_bucket == "elderly":
        mean += 0.8

    bmi = random.gauss(mean, std)
    return round(max(14.0, min(55.0, bmi)), 1)


def _bmi_to_weight_height(bmi: float, age: int, gender: str) -> Tuple[float, float]:
    """Derive consistent weight/height from BMI."""
    if age < 18:
        # Pediatric height approximation
        height_cm = 50 + age * 6.0 + random.gauss(0, 4)
    elif gender == "male":
        height_cm = random.gauss(175, 7)
    else:
        height_cm = random.gauss(162, 6)
    height_cm = max(50, min(210, height_cm))
    height_m = height_cm / 100.0
    weight_kg = bmi * (height_m ** 2)
    return round(weight_kg, 1), round(height_cm, 1)


# ── Patient Generation ────────────────────────────────────────────────────────

def generate_patient() -> SyntheticPatient:
    """Create a single synthetic patient with demographics and conditions."""
    age_bucket = _weighted_choice(AGE_BUCKETS, [AGE_BUCKET_WEIGHTS[b] for b in AGE_BUCKETS])
    gender = _weighted_choice(GENDERS, [GENDER_WEIGHTS[g] for g in GENDERS])
    ethnicity = _weighted_choice(ETHNICITIES, [ETHNICITY_WEIGHTS[e] for e in ETHNICITIES])
    age = _sample_age(age_bucket)

    # Assign conditions based on prevalence
    assigned = []
    for cond in CONDITIONS:
        if cond == "healthy":
            continue
        prev = get_condition_prevalence(cond, age_bucket, gender, ethnicity, assigned)
        if random.random() < prev:
            assigned.append(cond)

    if not assigned:
        assigned = ["healthy"]

    # Primary data source
    source = _weighted_choice(SOURCES, SOURCE_WEIGHTS)

    # BMI / weight / height
    has_obesity = "obesity" in assigned
    bmi = _sample_bmi(age_bucket, gender, has_obesity)
    weight, height = _bmi_to_weight_height(bmi, age, gender)

    return SyntheticPatient(
        patient_id=str(uuid.uuid4()),
        age=age,
        age_bucket=age_bucket,
        gender=gender,
        ethnicity=ethnicity,
        conditions=assigned,
        primary_device=source,
        bmi_baseline=bmi,
        weight_baseline=weight,
        height_cm=height,
    )


# ── Vital Generation ─────────────────────────────────────────────────────────

def _generate_single_vital(
    patient: SyntheticPatient,
    vital_type: str,
    timestamp: datetime,
    discrepancy_rate: float = 0.03,
) -> Optional[VitalReading]:
    """Generate a single vital reading for a patient at a given time."""
    profile = get_vital_profile(
        vital_type, patient.age_bucket, patient.gender, patient.conditions,
    )
    if profile is None:
        return None

    device = DEVICE_PROFILES[patient.primary_device]

    # Check if reading is missing (device unreliability)
    if random.random() < device.missing_rate:
        return None

    # Diurnal-adjusted mean
    hour = timestamp.hour + timestamp.minute / 60.0
    mean = profile.adjusted_mean(hour)

    # Generate value with device noise
    noise_std = profile.std + (mean * device.noise_std_fraction)
    value = random.gauss(mean, noise_std)

    # Special overrides for weight/bmi (slow-changing)
    if vital_type == "weight":
        value = patient.weight_baseline + random.gauss(0, 0.3)
    elif vital_type == "bmi":
        value = patient.bmi_baseline + random.gauss(0, 0.2)

    tags = []

    # Inject discrepancy (exaggerated/impossible values)
    if random.random() < discrepancy_rate:
        # Create a value that's physiologically implausible but not insane
        if random.random() < 0.5:
            value = profile.phys_max * random.uniform(1.05, 1.5)
        else:
            value = profile.phys_min * random.uniform(0.3, 0.9)
        tags.append("INJECTED_DISCREPANCY")

    # Clamp to hard physical limits (leave discrepancy tag for validator to catch)
    value = round(value, 2)

    # Source selection (mostly primary device, sometimes others)
    source = patient.primary_device
    if random.random() < 0.15:
        source = random.choice(SOURCES)

    return VitalReading(
        record_id=str(uuid.uuid4()),
        patient_id=patient.patient_id,
        vital_type=vital_type,
        value=value,
        unit=profile.unit,
        source=source,
        timestamp=timestamp.isoformat(),
        age_bucket=patient.age_bucket,
        gender=patient.gender,
        conditions=patient.conditions,
        tags=tags,
    )


def generate_patient_vitals(
    patient: SyntheticPatient,
    days: int = 365,
    readings_per_day: int = 4,
    discrepancy_rate: float = 0.03,
    start_date: Optional[datetime] = None,
) -> List[VitalReading]:
    """Generate longitudinal vital data for one patient."""
    if start_date is None:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

    vitals: List[VitalReading] = []

    for day_offset in range(days):
        day = start_date + timedelta(days=day_offset)

        for slot in range(readings_per_day):
            # Spread readings across waking hours (6am - 10pm)
            hour = 6 + (slot * 16 // readings_per_day) + random.randint(0, 2)
            minute = random.randint(0, 59)
            ts = day.replace(hour=min(hour, 23), minute=minute, second=0, microsecond=0)

            # Pick 2-3 vitals per slot (not all vitals every time)
            n_vitals = random.randint(2, 4)
            selected = random.sample(VITAL_TYPES_PER_SLOT, min(n_vitals, len(VITAL_TYPES_PER_SLOT)))

            for vt in selected:
                reading = _generate_single_vital(patient, vt, ts, discrepancy_rate)
                if reading:
                    vitals.append(reading)

        # Weekly vitals (weight, BMI) — only on some days
        if day_offset % 7 == 0:
            ts = day.replace(hour=7, minute=random.randint(0, 30))
            for vt in WEEKLY_VITALS:
                reading = _generate_single_vital(patient, vt, ts, discrepancy_rate)
                if reading:
                    vitals.append(reading)

    return vitals


# ── Full Population Generation ────────────────────────────────────────────────

def generate_population(
    n_patients: int = 5000,
    days: int = 365,
    readings_per_day: int = 4,
    discrepancy_rate: float = 0.03,
    seed: int = 42,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Generate a complete synthetic population dataset.

    Returns metadata dict with counts and paths.
    """
    random.seed(seed)
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    patients: List[Dict] = []
    all_vitals: List[Dict] = []
    all_conditions: List[Dict] = []

    print(f"[GEN] Generating {n_patients} patients x {days} days...")
    print(f"   Discrepancy rate: {discrepancy_rate:.1%}")
    print(f"   Output: {out.resolve()}\n")

    for i in range(n_patients):
        patient = generate_patient()
        patients.append(patient.to_dict())

        # Condition records
        start = datetime.now(timezone.utc) - timedelta(days=days)
        for cond in patient.conditions:
            if cond != "healthy":
                onset = start - timedelta(days=random.randint(30, 3650))
                all_conditions.append(ConditionRecord(
                    patient_id=patient.patient_id,
                    condition=cond,
                    onset_date=onset.isoformat(),
                ).to_dict())

        # Generate vitals
        vitals = generate_patient_vitals(
            patient, days=days,
            readings_per_day=readings_per_day,
            discrepancy_rate=discrepancy_rate,
        )
        all_vitals.extend([v.to_dict() for v in vitals])

        # Progress reporting
        if (i + 1) % 500 == 0 or i + 1 == n_patients:
            print(f"   [{i+1:>5}/{n_patients}] patients generated "
                  f"({len(all_vitals):,} vitals so far)")

    # ── Write outputs ─────────────────────────────────────────────────────────
    print(f"\n[SAVE] Writing output files...")

    _write_json(out / "patients.json", patients)
    print(f"   [OK] patients.json        ({len(patients):,} patients)")

    _write_json(out / "conditions.json", all_conditions)
    print(f"   [OK] conditions.json      ({len(all_conditions):,} condition records)")

    # Write vitals in chunks to avoid memory issues with very large datasets
    _write_json(out / "vitals.json", all_vitals)
    print(f"   [OK] vitals.json          ({len(all_vitals):,} vital readings)")

    # Metadata
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": "2.0.0",
        "seed": seed,
        "n_patients": n_patients,
        "n_days": days,
        "readings_per_day": readings_per_day,
        "discrepancy_rate": discrepancy_rate,
        "total_vital_readings": len(all_vitals),
        "total_conditions": len(all_conditions),
        "demographic_summary": _compute_demographic_summary(patients),
        "vital_summary": _compute_vital_summary(all_vitals),
    }
    _write_json(out / "metadata.json", metadata)
    print(f"   [OK] metadata.json")

    # Also write a flattened version compatible with existing generate.py format
    # (for backward compatibility with existing ingestion pipeline)
    compat_records = _to_compat_format(all_vitals)
    _write_json(Path("./data/synthetic_records.json"), compat_records)
    print(f"   [OK] synthetic_records.json (compat, {len(compat_records):,} records)")

    print(f"\n[DONE] Generation complete!")
    print(f"   Patients:  {len(patients):,}")
    print(f"   Vitals:    {len(all_vitals):,}")
    print(f"   Conditions: {len(all_conditions):,}")

    return metadata


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _to_compat_format(vitals: List[Dict]) -> List[Dict]:
    """Convert to the format expected by existing ingestion pipeline."""
    return [
        {
            "source": v["source"],
            "vital_type": v["vital_type"],
            "value": v["value"],
            "unit": v["unit"],
            "timestamp": v["timestamp"],
            "stream_id": "scaled_generator",
            "user_id": v["patient_id"],
        }
        for v in vitals
    ]


def _compute_demographic_summary(patients: List[Dict]) -> Dict:
    """Compute demographic distribution counts."""
    summary = {
        "by_age_bucket": {},
        "by_gender": {},
        "by_ethnicity": {},
        "by_condition": {},
    }
    for p in patients:
        ab = p["age_bucket"]
        summary["by_age_bucket"][ab] = summary["by_age_bucket"].get(ab, 0) + 1

        g = p["gender"]
        summary["by_gender"][g] = summary["by_gender"].get(g, 0) + 1

        e = p["ethnicity"]
        summary["by_ethnicity"][e] = summary["by_ethnicity"].get(e, 0) + 1

        for c in p["conditions"]:
            summary["by_condition"][c] = summary["by_condition"].get(c, 0) + 1

    return summary


def _compute_vital_summary(vitals: List[Dict]) -> Dict:
    """Compute basic stats per vital type."""
    by_type: Dict[str, List[float]] = {}
    for v in vitals:
        vt = v["vital_type"]
        by_type.setdefault(vt, []).append(v["value"])

    summary = {}
    for vt, values in by_type.items():
        n = len(values)
        mean = sum(values) / n
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 0.0
        summary[vt] = {
            "count": n,
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
        }
    return summary


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Relay-med scaled dataset generator")
    parser.add_argument("--patients", type=int, default=5000, help="Number of patients")
    parser.add_argument("--days", type=int, default=365, help="Days of history per patient")
    parser.add_argument("--readings", type=int, default=4, help="Readings per day")
    parser.add_argument("--discrepancy", type=float, default=0.03, help="Discrepancy injection rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    parser.add_argument("--quick", action="store_true", help="Quick mode: 500 patients × 90 days")
    args = parser.parse_args()

    if args.quick:
        args.patients = 500
        args.days = 90

    out_dir = Path(args.output) if args.output else None
    generate_population(
        n_patients=args.patients,
        days=args.days,
        readings_per_day=args.readings,
        discrepancy_rate=args.discrepancy,
        seed=args.seed,
        output_dir=out_dir,
    )
