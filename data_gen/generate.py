"""
generate.py — Synthetic health data generator.
Wraps Synthea-style generation and injects realistic discrepancies
to exercise the Ingestion Service validation pipeline.
"""

import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any

import httpx

# ── Config ────────────────────────────────────────────────────────
API_BASE    = "http://127.0.0.1:9000/api/v1"
USER_ID     = "default"
STREAM_ID   = "manual_input"
DAYS_BACK   = 30
RECORDS_PER_DAY = 4

VITAL_PROFILES: Dict[str, Dict] = {
    "heart_rate": {
        "unit": "bpm", "mean": 72, "std": 8, "min": 40, "max": 180,
        "discrepancy_val": 220,   # Out-of-range value for discrepancy injection
    },
    "spo2": {
        "unit": "%", "mean": 97, "std": 1.5, "min": 85, "max": 100,
        "discrepancy_val": 80,
    },
    "blood_pressure_systolic": {
        "unit": "mmHg", "mean": 118, "std": 12, "min": 80, "max": 200,
        "discrepancy_val": 250,
    },
    "blood_pressure_diastolic": {
        "unit": "mmHg", "mean": 76, "std": 8, "min": 50, "max": 130,
        "discrepancy_val": 160,
    },
    "glucose_fasting": {
        "unit": "mg/dL", "mean": 95, "std": 15, "min": 60, "max": 300,
        "discrepancy_val": 400,
    },
    "steps": {
        "unit": "steps", "mean": 7500, "std": 2500, "min": 0, "max": 30000,
        "discrepancy_val": 150000,
    },
    "sleep_hours": {
        "unit": "hrs", "mean": 7.0, "std": 1.0, "min": 2, "max": 12,
        "discrepancy_val": 25,
    },
}

SOURCES = ["manual", "fitbit", "apple_health"]


def generate_records(
    days: int = DAYS_BACK,
    discrepancy_rate: float = 0.05,
) -> List[Dict[str, Any]]:
    """Generate synthetic vital records for the past `days` days."""
    records = []
    now = datetime.now(timezone.utc)

    for day in range(days, 0, -1):
        base_ts = now - timedelta(days=day)
        for _ in range(RECORDS_PER_DAY):
            # Pick a random vital type
            vt = random.choice(list(VITAL_PROFILES.keys()))
            profile = VITAL_PROFILES[vt]

            inject_discrepancy = random.random() < discrepancy_rate
            if inject_discrepancy:
                value = profile["discrepancy_val"]
            else:
                value = max(profile["min"], min(profile["max"],
                    random.gauss(profile["mean"], profile["std"])))
            value = round(value, 2)

            ts = base_ts + timedelta(
                hours=random.randint(6, 22),
                minutes=random.randint(0, 59),
            )

            records.append({
                "source":     random.choice(SOURCES),
                "vital_type": vt,
                "value":      value,
                "unit":       profile["unit"],
                "timestamp":  ts.isoformat(),
                "stream_id":  STREAM_ID,
                "user_id":    USER_ID,
            })

    return records


async def ingest_records(records: List[Dict]) -> Dict[str, int]:
    """POST each record to the ingest API. Returns summary counters."""
    counters = {"success": 0, "failed": 0, "alerts": 0}
    async with httpx.AsyncClient(timeout=30) as client:
        for rec in records:
            try:
                resp = await client.post(f"{API_BASE}/ingest", json=rec)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    counters["success"] += 1
                    counters["alerts"] += len(data.get("triage_alerts", []))
                else:
                    counters["failed"] += 1
                    print(f"  FAILED {rec['vital_type']}: HTTP {resp.status_code}")
            except Exception as e:
                counters["failed"] += 1
                print(f"  FAILED {rec['vital_type']}: {e}")
    return counters


def save_to_file(records: List[Dict], path: str = "./data/synthetic_records.json"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)
    print(f"Saved {len(records)} records to {path}")


if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(description="SecureMed synthetic data generator")
    parser.add_argument("--days",        type=int,   default=DAYS_BACK,    help="Days of history to generate")
    parser.add_argument("--discard-rate", type=float, default=0.05,        help="Fraction of discrepant records (0–1)")
    parser.add_argument("--save-only",   action="store_true",               help="Save to file without ingesting")
    parser.add_argument("--file",        type=str,   default="./data/synthetic_records.json")
    args = parser.parse_args()

    print(f"Generating {args.days} days of synthetic data (discrepancy rate: {args.discard_rate:.0%})...")
    records = generate_records(days=args.days, discrepancy_rate=args.discard_rate)
    print(f"Generated {len(records)} records.")

    save_to_file(records, args.file)

    if not args.save_only:
        # First grant consent
        async def run():
            async with httpx.AsyncClient() as client:
                await client.post(f"{API_BASE}/consent", json={
                    "user_id": USER_ID, "stream_id": STREAM_ID, "consented": True
                })
            print("Consent granted.")
            counters = await ingest_records(records)
            print(f"\nIngestion complete:")
            print(f"   Success:  {counters['success']}")
            print(f"   Failed:   {counters['failed']}")
            print(f"   Alerts:   {counters['alerts']}")

        asyncio.run(run())
