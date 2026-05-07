"""
Audit Logger — Append-only structured JSON log.
Enforces immutability: log file is opened in append mode only.
Archives when size exceeds threshold.
"""

import json
import os
import threading
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path
import uuid

from backend.models.audit import AuditEntry


class AuditEventType(str, Enum):
    INGEST_SUCCESS = "INGEST_SUCCESS"
    INGEST_FAILURE = "INGEST_FAILURE"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    DUPLICATE_DISCARDED = "DUPLICATE_DISCARDED"
    CONSENT_GRANT = "CONSENT_GRANT"
    CONSENT_REVOKE = "CONSENT_REVOKE"
    CONSENT_CHECK = "CONSENT_CHECK"
    AUTH_FAILURE = "AUTH_FAILURE"
    AUTH_SUCCESS = "AUTH_SUCCESS"
    RED_FLAG_ALERT = "RED_FLAG_ALERT"
    YELLOW_FLAG_ALERT = "YELLOW_FLAG_ALERT"
    EMERGENCY_TRIAGE = "EMERGENCY_TRIAGE"
    CONVERSATION_STARTED = "CONVERSATION_STARTED"
    CONVERSATION_RESPONSE = "CONVERSATION_RESPONSE"
    REPORT_GENERATED = "REPORT_GENERATED"
    PRIVACY_SHIELD_ACTIVATED = "PRIVACY_SHIELD_ACTIVATED"
    SYSTEM_STARTUP = "SYSTEM_STARTUP"


ARCHIVE_THRESHOLD_BYTES = 1 * 1024 * 1024 * 1024  # 1 GB


class AuditLogger:
    def __init__(self, log_dir: str = "./data/audit"):
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._log_dir / "audit.jsonl"
        self._lock = threading.Lock()

    def log(
        self,
        event_type: AuditEventType,
        payload: Dict[str, Any],
        user_id: str = "system",
        source_ip: Optional[str] = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            event_type=event_type.value,
            user_id=user_id,
            source_ip=source_ip,
            timestamp=datetime.utcnow(),
            payload=payload,
        )
        self._write(entry)
        return entry

    def _write(self, entry: AuditEntry) -> None:
        with self._lock:
            self._maybe_archive()
            with open(self._log_file, "a", encoding="utf-8") as f:
                record = {
                    "id": entry.id,
                    "event_type": entry.event_type,
                    "user_id": entry.user_id,
                    "source_ip": entry.source_ip,
                    "timestamp": entry.timestamp.isoformat(),
                    "payload": entry.payload,
                }
                f.write(json.dumps(record) + "\n")

    def _maybe_archive(self) -> None:
        if self._log_file.exists() and self._log_file.stat().st_size > ARCHIVE_THRESHOLD_BYTES:
            archive_name = self._log_dir / f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
            self._log_file.rename(archive_name)

    def query(
        self,
        event_type: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        results = []
        if not self._log_file.exists():
            return results

        with self._lock:
            with open(self._log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        ts = datetime.fromisoformat(record["timestamp"])
                        if event_type and record["event_type"] != event_type:
                            continue
                        if start and ts < start:
                            continue
                        if end and ts > end:
                            continue
                        results.append(
                            AuditEntry(
                                id=record["id"],
                                event_type=record["event_type"],
                                user_id=record["user_id"],
                                source_ip=record.get("source_ip"),
                                timestamp=ts,
                                payload=record.get("payload", {}),
                            )
                        )
                        if len(results) >= limit:
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue
        return results


# Singleton
audit_logger = AuditLogger()
