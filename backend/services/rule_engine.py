"""
Rule Engine — Evaluates clinical YAML rules against Health_Graph data.
Phase 1 implementation: threshold and trend-based rule evaluation.
"""

import statistics
from datetime import datetime
from pathlib import Path
from typing import List

import yaml

from backend.models.risk_finding import RiskFinding, VitalRef
from backend.services.health_graph import health_graph
from backend.services.audit_logger import audit_logger, AuditEventType
import uuid


RULES_PATH = Path(__file__).parent.parent / "rules" / "clinical_rules.yaml"


class RuleEngine:
    def __init__(self):
        self._rules = self._load_rules()

    def _load_rules(self) -> list:
        try:
            with open(RULES_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("rules", [])
        except Exception as e:
            print(f"[RuleEngine] Failed to load rules: {e}")
            return []

    def evaluate(self) -> List[RiskFinding]:
        findings: List[RiskFinding] = []
        for rule in self._rules:
            finding = self._evaluate_rule(rule)
            if finding:
                findings.append(finding)
        return findings

    def _evaluate_rule(self, rule: dict) -> RiskFinding | None:
        vital_types: List[str] = rule.get("vital_types", [])
        condition: str = rule.get("condition", "")
        days = self._extract_days(condition)

        all_values = []
        contributing_vitals = []
        all_records = []
        for vt in vital_types:
            records = health_graph.get_recent_values(vt, days=days)
            all_records.extend(records)
            all_values.extend([r["value"] for r in records])
            contributing_vitals.extend([VitalRef(vital_id=r["id"], vital_type=vt) for r in records])

        if not all_values:
            return None

        mean_val = statistics.mean(all_values)
        trend_val = self._compute_trend(all_values)

        triggered = self._evaluate_condition(condition, mean_val, trend_val)
        if not triggered:
            return None

        # Optimized: use already fetched records for trust calculation
        avg_trust = statistics.mean(
            [r.get("trust_score", 0.5) for r in all_records]
        ) if all_records else 0.5

        finding = RiskFinding(
            id=str(uuid.uuid4()),
            source="rule_engine",
            rule_id=rule["id"],
            severity=rule.get("severity", "info"),
            contributing_vitals=contributing_vitals,
            trust_score=avg_trust,
            confidence=0.75,
            plain_language_summary=rule.get("description", ""),
            recommendations=[rule.get("recommendation", "")],
            timestamp=datetime.utcnow(),
        )

        audit_logger.log(
            AuditEventType.YELLOW_FLAG_ALERT if finding.severity == "yellow_flag" else AuditEventType.REPORT_GENERATED,
            {"rule_id": rule["id"], "severity": finding.severity},
        )
        return finding

    def _compute_trend(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        return numerator / denominator if denominator != 0 else 0.0

    def _evaluate_condition(self, condition: str, mean_val: float, trend_val: float) -> bool:
        """Simple parser for the DSL used in clinical_rules.yaml."""
        cond = condition
        # Replace DSL tokens with Python-evaluable expressions
        cond = cond.replace("AND", " and ").replace("OR", " or ")

        import re
        cond = re.sub(r"mean\(last_\d+[d]\)", str(mean_val), cond)
        cond = re.sub(r"mean\(last_\d+[d],\s*\w+\)", str(mean_val), cond)
        cond = re.sub(r"trend\(last_\d+[d]\)", str(trend_val), cond)

        try:
            return bool(eval(cond, {"__builtins__": {}}, {}))
        except Exception:
            return False

    def _extract_days(self, condition: str) -> int:
        import re
        match = re.search(r"last_(\d+)d", condition)
        return int(match.group(1)) if match else 7


rule_engine = RuleEngine()
