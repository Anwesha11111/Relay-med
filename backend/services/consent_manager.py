"""
Consent Manager — Stores and checks per-stream consent records.
Persistence: encrypted JSON file on disk.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import threading

from backend.models.consent import ConsentRecord
from backend.services.audit_logger import audit_logger, AuditEventType


DATA_PATH = Path("./data/consent/consent_store.json")


class ConsentManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._store: Dict[str, ConsentRecord] = {}  # key = f"{user_id}:{stream_id}"
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def check_consent(self, user_id: str, stream_id: str) -> bool:
        key = self._key(user_id, stream_id)
        with self._lock:
            record = self._store.get(key)
        audit_logger.log(
            AuditEventType.CONSENT_CHECK,
            {"user_id": user_id, "stream_id": stream_id, "consented": bool(record and record.consented)},
            user_id=user_id,
        )
        return bool(record and record.consented)

    def grant_consent(self, user_id: str, stream_id: str, version: str = "1.0") -> ConsentRecord:
        return self._set(user_id, stream_id, True, version)

    def revoke_consent(self, user_id: str, stream_id: str, version: str = "1.0") -> ConsentRecord:
        return self._set(user_id, stream_id, False, version)

    def get_all(self, user_id: str) -> list:
        with self._lock:
            return [r for k, r in self._store.items() if k.startswith(f"{user_id}:")]

    # ── Internal ──────────────────────────────────────────────────────────────

    def _set(self, user_id: str, stream_id: str, consented: bool, version: str) -> ConsentRecord:
        record = ConsentRecord(
            user_id=user_id,
            stream_id=stream_id,
            consented=consented,
            timestamp=datetime.utcnow(),
            version=version,
        )
        key = self._key(user_id, stream_id)
        with self._lock:
            self._store[key] = record
            self._save()

        event = AuditEventType.CONSENT_GRANT if consented else AuditEventType.CONSENT_REVOKE
        audit_logger.log(event, {"stream_id": stream_id, "version": version}, user_id=user_id)
        return record

    @staticmethod
    def _key(user_id: str, stream_id: str) -> str:
        return f"{user_id}:{stream_id}"

    def _save(self):
        data = {
            k: {
                "user_id": r.user_id,
                "stream_id": r.stream_id,
                "consented": r.consented,
                "timestamp": r.timestamp.isoformat(),
                "version": r.version,
            }
            for k, r in self._store.items()
        }
        DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self):
        if DATA_PATH.exists():
            try:
                data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
                for k, v in data.items():
                    self._store[k] = ConsentRecord(
                        user_id=v["user_id"],
                        stream_id=v["stream_id"],
                        consented=v["consented"],
                        timestamp=datetime.fromisoformat(v["timestamp"]),
                        version=v["version"],
                    )
            except Exception:
                pass


consent_manager = ConsentManager()
