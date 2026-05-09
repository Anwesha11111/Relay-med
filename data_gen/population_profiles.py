"""
population_profiles.py — Evidence-based demographic and clinical profiles.

Sources for reference ranges:
  - CDC National Health Statistics Reports
  - WHO Global Health Observatory
  - AHA/ACC Blood Pressure Guidelines (2017)
  - ADA Diabetes Care Standards (2024)
  - NIH NHLBI Body Mass Index tables
  - Published Synthea™ validation studies

Each profile is stratified by (age_bucket, gender, condition) and includes
mean, std, physiological min/max, and temporal variation patterns.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math

# ── Demographic Enums ─────────────────────────────────────────────────────────

AGE_BUCKETS = ["pediatric", "young_adult", "middle_aged", "elderly"]
AGE_RANGES = {
    "pediatric":   (0, 17),
    "young_adult":  (18, 39),
    "middle_aged":  (40, 64),
    "elderly":      (65, 100),
}

GENDERS = ["male", "female"]

ETHNICITIES = ["white", "black", "hispanic", "asian", "other"]

# US Census-approximate demographic distribution weights
ETHNICITY_WEIGHTS = {
    "white":    0.58,
    "black":    0.13,
    "hispanic": 0.19,
    "asian":    0.06,
    "other":    0.04,
}

AGE_BUCKET_WEIGHTS = {
    "pediatric":   0.22,
    "young_adult":  0.27,
    "middle_aged":  0.26,
    "elderly":      0.25,
}

GENDER_WEIGHTS = {"male": 0.49, "female": 0.51}

# ── Condition Definitions ─────────────────────────────────────────────────────

CONDITIONS = [
    "healthy",
    "hypertension",
    "diabetes_t2",
    "obesity",
    "heart_disease",
    "copd",
]

# Prevalence by (age_bucket, gender) — CDC/WHO approximate rates
# Format: {condition: {(age_bucket, gender): prevalence}}
CONDITION_PREVALENCE: Dict[str, Dict[Tuple[str, str], float]] = {
    "hypertension": {
        ("pediatric", "male"):   0.04, ("pediatric", "female"):   0.03,
        ("young_adult", "male"): 0.12, ("young_adult", "female"): 0.08,
        ("middle_aged", "male"): 0.38, ("middle_aged", "female"): 0.32,
        ("elderly", "male"):     0.58, ("elderly", "female"):     0.55,
    },
    "diabetes_t2": {
        ("pediatric", "male"):   0.005, ("pediatric", "female"):  0.005,
        ("young_adult", "male"): 0.04,  ("young_adult", "female"): 0.03,
        ("middle_aged", "male"): 0.14,  ("middle_aged", "female"): 0.11,
        ("elderly", "male"):     0.22,  ("elderly", "female"):     0.19,
    },
    "obesity": {
        ("pediatric", "male"):   0.19, ("pediatric", "female"):   0.16,
        ("young_adult", "male"): 0.32, ("young_adult", "female"): 0.28,
        ("middle_aged", "male"): 0.40, ("middle_aged", "female"): 0.42,
        ("elderly", "male"):     0.35, ("elderly", "female"):     0.38,
    },
    "heart_disease": {
        ("pediatric", "male"):   0.002, ("pediatric", "female"):  0.001,
        ("young_adult", "male"): 0.02,  ("young_adult", "female"): 0.01,
        ("middle_aged", "male"): 0.08,  ("middle_aged", "female"): 0.04,
        ("elderly", "male"):     0.18,  ("elderly", "female"):     0.12,
    },
    "copd": {
        ("pediatric", "male"):   0.0,  ("pediatric", "female"):   0.0,
        ("young_adult", "male"): 0.01, ("young_adult", "female"): 0.01,
        ("middle_aged", "male"): 0.06, ("middle_aged", "female"): 0.05,
        ("elderly", "male"):     0.12, ("elderly", "female"):     0.10,
    },
}

# Comorbidity multipliers: if patient has condition A, multiply prevalence
# of condition B by this factor.  Source: multiple meta-analyses.
COMORBIDITY_MULTIPLIERS: Dict[Tuple[str, str], float] = {
    ("obesity", "diabetes_t2"):      2.5,
    ("obesity", "hypertension"):     2.0,
    ("obesity", "heart_disease"):    1.8,
    ("diabetes_t2", "hypertension"): 2.0,
    ("diabetes_t2", "heart_disease"): 2.5,
    ("hypertension", "heart_disease"): 2.0,
    ("copd", "heart_disease"):       1.5,
}

# Ethnicity risk modifiers (relative to white baseline=1.0)
ETHNICITY_RISK_MODIFIERS: Dict[str, Dict[str, float]] = {
    "hypertension":  {"white": 1.0, "black": 1.5, "hispanic": 1.1, "asian": 0.9, "other": 1.0},
    "diabetes_t2":   {"white": 1.0, "black": 1.6, "hispanic": 1.7, "asian": 1.4, "other": 1.1},
    "obesity":       {"white": 1.0, "black": 1.3, "hispanic": 1.2, "asian": 0.6, "other": 1.0},
    "heart_disease": {"white": 1.0, "black": 1.2, "hispanic": 0.9, "asian": 0.8, "other": 1.0},
    "copd":          {"white": 1.0, "black": 0.9, "hispanic": 0.8, "asian": 0.7, "other": 1.0},
}


# ── Vital Sign Profiles ──────────────────────────────────────────────────────

@dataclass
class VitalProfile:
    """Statistical profile for generating a single vital sign."""
    mean: float
    std: float
    phys_min: float
    phys_max: float
    unit: str
    diurnal_amplitude: float = 0.0   # Peak-to-trough variation (fraction of mean)
    diurnal_phase_hr: float = 14.0   # Hour of day when value peaks

    def adjusted_mean(self, hour: float = 12.0) -> float:
        """Return mean adjusted for time-of-day (circadian rhythm)."""
        if self.diurnal_amplitude == 0:
            return self.mean
        # Sinusoidal diurnal model
        phase = 2 * math.pi * (hour - self.diurnal_phase_hr) / 24.0
        return self.mean * (1 + self.diurnal_amplitude * math.sin(phase))


# Baseline profiles for HEALTHY adults (young_adult, male)
# Other demographics are derived by applying modifiers below
BASELINE_VITALS: Dict[str, VitalProfile] = {
    "heart_rate": VitalProfile(
        mean=72, std=8, phys_min=40, phys_max=180, unit="bpm",
        diurnal_amplitude=0.08, diurnal_phase_hr=14.0,
    ),
    "spo2": VitalProfile(
        mean=97.5, std=1.0, phys_min=85, phys_max=100, unit="%",
    ),
    "blood_pressure_systolic": VitalProfile(
        mean=118, std=10, phys_min=80, phys_max=200, unit="mmHg",
        diurnal_amplitude=0.05, diurnal_phase_hr=10.0,
    ),
    "blood_pressure_diastolic": VitalProfile(
        mean=76, std=7, phys_min=50, phys_max=130, unit="mmHg",
        diurnal_amplitude=0.04, diurnal_phase_hr=10.0,
    ),
    "glucose_fasting": VitalProfile(
        mean=92, std=8, phys_min=60, phys_max=300, unit="mg/dL",
    ),
    "steps": VitalProfile(
        mean=7500, std=2500, phys_min=0, phys_max=40000, unit="steps",
    ),
    "sleep_hours": VitalProfile(
        mean=7.2, std=0.9, phys_min=2, phys_max=14, unit="hrs",
    ),
    "respiratory_rate": VitalProfile(
        mean=15, std=2, phys_min=8, phys_max=30, unit="breaths/min",
        diurnal_amplitude=0.06, diurnal_phase_hr=15.0,
    ),
    "temperature": VitalProfile(
        mean=36.7, std=0.3, phys_min=35.0, phys_max=40.0, unit="°C",
        diurnal_amplitude=0.008, diurnal_phase_hr=18.0,
    ),
    "weight": VitalProfile(
        mean=80.0, std=12.0, phys_min=30, phys_max=250, unit="kg",
    ),
    "bmi": VitalProfile(
        mean=25.0, std=4.0, phys_min=14, phys_max=60, unit="kg/m²",
    ),
}


# ── Demographic Modifiers ─────────────────────────────────────────────────────
# Applied multiplicatively to (mean, std) of baseline profiles.
# Format: {vital_type: {modifier_key: (mean_multiplier, std_multiplier)}}

AGE_MODIFIERS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "heart_rate": {
        "pediatric": (1.25, 1.3),   # Children have higher resting HR
        "young_adult": (1.0, 1.0),
        "middle_aged": (1.03, 1.1),
        "elderly": (1.0, 1.2),      # Slightly more variable
    },
    "blood_pressure_systolic": {
        "pediatric": (0.85, 0.8),
        "young_adult": (1.0, 1.0),
        "middle_aged": (1.08, 1.15),
        "elderly": (1.18, 1.2),
    },
    "blood_pressure_diastolic": {
        "pediatric": (0.82, 0.8),
        "young_adult": (1.0, 1.0),
        "middle_aged": (1.06, 1.1),
        "elderly": (1.04, 1.15),     # Diastolic doesn't rise as much in elderly
    },
    "glucose_fasting": {
        "pediatric": (0.90, 0.8),
        "young_adult": (1.0, 1.0),
        "middle_aged": (1.06, 1.15),
        "elderly": (1.10, 1.2),
    },
    "steps": {
        "pediatric": (1.3, 1.2),
        "young_adult": (1.0, 1.0),
        "middle_aged": (0.85, 1.1),
        "elderly": (0.55, 1.3),
    },
    "sleep_hours": {
        "pediatric": (1.35, 0.9),     # Children sleep more
        "young_adult": (1.0, 1.0),
        "middle_aged": (0.93, 1.1),
        "elderly": (0.88, 1.2),
    },
    "respiratory_rate": {
        "pediatric": (1.5, 1.3),
        "young_adult": (1.0, 1.0),
        "middle_aged": (1.05, 1.1),
        "elderly": (1.12, 1.2),
    },
    "spo2": {
        "pediatric": (1.0, 0.8),
        "young_adult": (1.0, 1.0),
        "middle_aged": (0.995, 1.1),
        "elderly": (0.985, 1.3),
    },
    "temperature": {
        "pediatric": (1.003, 1.1),
        "young_adult": (1.0, 1.0),
        "middle_aged": (0.998, 1.0),
        "elderly": (0.994, 1.1),
    },
    "weight": {
        "pediatric": (0.45, 0.6),
        "young_adult": (1.0, 1.0),
        "middle_aged": (1.08, 1.1),
        "elderly": (0.95, 1.15),
    },
    "bmi": {
        "pediatric": (0.75, 0.7),
        "young_adult": (1.0, 1.0),
        "middle_aged": (1.10, 1.1),
        "elderly": (1.05, 1.15),
    },
}

GENDER_MODIFIERS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "heart_rate": {
        "male": (1.0, 1.0),
        "female": (1.05, 1.05),    # Females have slightly higher resting HR
    },
    "blood_pressure_systolic": {
        "male": (1.0, 1.0),
        "female": (0.95, 0.95),
    },
    "blood_pressure_diastolic": {
        "male": (1.0, 1.0),
        "female": (0.96, 0.95),
    },
    "weight": {
        "male": (1.0, 1.0),
        "female": (0.82, 0.85),
    },
    "bmi": {
        "male": (1.0, 1.0),
        "female": (1.02, 1.05),
    },
    "steps": {
        "male": (1.0, 1.0),
        "female": (0.92, 1.0),
    },
}

# Condition modifiers — how a diagnosed condition shifts vital distributions
CONDITION_MODIFIERS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "hypertension": {
        "blood_pressure_systolic":  (1.22, 1.3),   # Mean ~144 mmHg
        "blood_pressure_diastolic": (1.18, 1.25),   # Mean ~90 mmHg
        "heart_rate":               (1.06, 1.1),
    },
    "diabetes_t2": {
        "glucose_fasting":          (1.55, 1.8),    # Mean ~143 mg/dL
        "weight":                   (1.10, 1.1),
        "bmi":                      (1.15, 1.1),
        "heart_rate":               (1.04, 1.05),
    },
    "obesity": {
        "weight":                   (1.35, 1.2),
        "bmi":                      (1.40, 1.2),    # Mean BMI ~35
        "blood_pressure_systolic":  (1.08, 1.1),
        "blood_pressure_diastolic": (1.06, 1.08),
        "steps":                    (0.70, 1.2),
        "sleep_hours":              (0.92, 1.15),
    },
    "heart_disease": {
        "heart_rate":               (1.10, 1.3),
        "blood_pressure_systolic":  (1.05, 1.2),
        "spo2":                     (0.98, 1.5),
        "steps":                    (0.60, 1.3),
        "respiratory_rate":         (1.12, 1.3),
    },
    "copd": {
        "spo2":                     (0.96, 2.0),    # Lower SpO2, much more variable
        "respiratory_rate":         (1.30, 1.5),
        "heart_rate":               (1.08, 1.2),
        "steps":                    (0.50, 1.4),
    },
}


# ── Wearable Device Noise Profiles ───────────────────────────────────────────

@dataclass
class DeviceNoiseProfile:
    """Models measurement accuracy of different data sources."""
    name: str
    noise_std_fraction: float   # Noise as fraction of the true value
    missing_rate: float         # Probability of a missing reading per slot
    duplicate_rate: float       # Probability of sending a duplicate
    source_reliability: float   # Trust scorer weight (matches trust_scorer.py)

DEVICE_PROFILES: Dict[str, DeviceNoiseProfile] = {
    "fitbit":       DeviceNoiseProfile("fitbit",       0.02, 0.05, 0.01, 1.0),
    "apple_health": DeviceNoiseProfile("apple_health", 0.015, 0.03, 0.005, 1.0),
    "manual":       DeviceNoiseProfile("manual",       0.05, 0.15, 0.02, 0.7),
    "ehr":          DeviceNoiseProfile("ehr",          0.005, 0.02, 0.001, 0.5),
}


# ── Helper: Build a complete profile for a specific patient ──────────────────

def get_vital_profile(
    vital_type: str,
    age_bucket: str,
    gender: str,
    conditions: List[str],
) -> Optional[VitalProfile]:
    """
    Build a VitalProfile for a given (vital_type, age, gender, conditions)
    by stacking demographic and condition modifiers on the baseline.
    """
    baseline = BASELINE_VITALS.get(vital_type)
    if baseline is None:
        return None

    mean = baseline.mean
    std = baseline.std

    # Apply age modifier
    age_mod = AGE_MODIFIERS.get(vital_type, {}).get(age_bucket, (1.0, 1.0))
    mean *= age_mod[0]
    std *= age_mod[1]

    # Apply gender modifier
    gen_mod = GENDER_MODIFIERS.get(vital_type, {}).get(gender, (1.0, 1.0))
    mean *= gen_mod[0]
    std *= gen_mod[1]

    # Apply condition modifiers (multiplicative stacking)
    for cond in conditions:
        if cond == "healthy":
            continue
        cond_mod = CONDITION_MODIFIERS.get(cond, {}).get(vital_type, (1.0, 1.0))
        mean *= cond_mod[0]
        std *= cond_mod[1]

    return VitalProfile(
        mean=round(mean, 2),
        std=round(std, 2),
        phys_min=baseline.phys_min,
        phys_max=baseline.phys_max,
        unit=baseline.unit,
        diurnal_amplitude=baseline.diurnal_amplitude,
        diurnal_phase_hr=baseline.diurnal_phase_hr,
    )


def get_condition_prevalence(
    condition: str,
    age_bucket: str,
    gender: str,
    ethnicity: str,
    existing_conditions: List[str],
) -> float:
    """
    Get prevalence for a condition adjusted by demographics and comorbidities.
    """
    base = CONDITION_PREVALENCE.get(condition, {}).get((age_bucket, gender), 0.0)

    # Ethnicity modifier
    eth_mod = ETHNICITY_RISK_MODIFIERS.get(condition, {}).get(ethnicity, 1.0)
    base *= eth_mod

    # Comorbidity multipliers
    for existing in existing_conditions:
        multiplier = COMORBIDITY_MULTIPLIERS.get((existing, condition), 1.0)
        base *= multiplier

    return min(base, 0.95)  # Cap at 95% to avoid certainty
