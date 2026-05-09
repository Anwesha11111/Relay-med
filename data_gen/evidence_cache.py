"""
evidence_cache.py — SQLite-backed cache for PubMed and clinical evidence queries.

Avoids repeated API calls and enables fully offline dataset generation
once evidence has been fetched at least once.

Auto-expires entries older than 90 days.
"""

import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

CACHE_DB_PATH = Path("./data/pubmed_cache.db")
EXPIRY_DAYS = 90


class EvidenceCache:
    """Thread-safe SQLite cache for external evidence queries."""

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or CACHE_DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = self._connect()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence_cache (
                    query_hash   TEXT PRIMARY KEY,
                    query_text   TEXT NOT NULL,
                    result_json  TEXT NOT NULL,
                    pubmed_ids   TEXT,
                    source       TEXT DEFAULT 'pubmed',
                    created_at   TEXT NOT NULL,
                    expires_at   TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clinical_ranges (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    condition    TEXT NOT NULL,
                    vital_type   TEXT NOT NULL,
                    demographic  TEXT,
                    mean         REAL,
                    std          REAL,
                    range_low    REAL,
                    range_high   REAL,
                    evidence_level TEXT DEFAULT 'C',
                    pubmed_id    TEXT,
                    source_title TEXT,
                    cached_at    TEXT NOT NULL,
                    UNIQUE(condition, vital_type, demographic)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    condition     TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    evidence_level TEXT DEFAULT 'C',
                    pubmed_id     TEXT,
                    source_title  TEXT,
                    cached_at     TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._db_path))

    @staticmethod
    def _hash_query(query: str) -> str:
        return hashlib.sha256(query.strip().lower().encode()).hexdigest()

    # ── Generic cache ─────────────────────────────────────────────────────────

    def get(self, query: str) -> Optional[Dict]:
        """Get cached result for a query. Returns None if expired or absent."""
        qhash = self._hash_query(query)
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT result_json, pubmed_ids FROM evidence_cache "
                "WHERE query_hash = ? AND expires_at > ?",
                (qhash, now),
            ).fetchone()
            conn.close()
        if row:
            return {
                "result": json.loads(row[0]),
                "pubmed_ids": json.loads(row[1]) if row[1] else [],
            }
        return None

    def put(self, query: str, result: Any, pubmed_ids: Optional[List[str]] = None):
        """Store a query result in the cache."""
        qhash = self._hash_query(query)
        now = datetime.now(timezone.utc)
        expires = now.replace(year=now.year if now.month + 3 <= 12 else now.year + 1)
        # Simple expiry: +90 days
        from datetime import timedelta
        expires = now + timedelta(days=EXPIRY_DAYS)

        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO evidence_cache "
                "(query_hash, query_text, result_json, pubmed_ids, created_at, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    qhash, query,
                    json.dumps(result, default=str),
                    json.dumps(pubmed_ids or []),
                    now.isoformat(),
                    expires.isoformat(),
                ),
            )
            conn.commit()
            conn.close()

    def get_or_fetch(self, query: str, fetch_fn) -> Dict:
        """Get from cache or call fetch_fn(query) and cache the result."""
        cached = self.get(query)
        if cached:
            return cached["result"]
        result = fetch_fn(query)
        self.put(query, result)
        return result

    # ── Clinical ranges ───────────────────────────────────────────────────────

    def get_clinical_range(
        self, condition: str, vital_type: str, demographic: str = "general"
    ) -> Optional[Dict]:
        """Get a cached clinical range."""
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT mean, std, range_low, range_high, evidence_level, pubmed_id "
                "FROM clinical_ranges WHERE condition = ? AND vital_type = ? AND demographic = ?",
                (condition, vital_type, demographic),
            ).fetchone()
            conn.close()
        if row:
            return {
                "mean": row[0], "std": row[1],
                "range_low": row[2], "range_high": row[3],
                "evidence_level": row[4], "pubmed_id": row[5],
            }
        return None

    def put_clinical_range(
        self, condition: str, vital_type: str,
        mean: float, std: float, range_low: float, range_high: float,
        evidence_level: str = "C", pubmed_id: str = "",
        source_title: str = "", demographic: str = "general",
    ):
        """Store a clinical range."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO clinical_ranges "
                "(condition, vital_type, demographic, mean, std, range_low, range_high, "
                " evidence_level, pubmed_id, source_title, cached_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (condition, vital_type, demographic, mean, std,
                 range_low, range_high, evidence_level, pubmed_id, source_title, now),
            )
            conn.commit()
            conn.close()

    def get_all_clinical_ranges(self) -> List[Dict]:
        """Get all cached clinical ranges."""
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                "SELECT condition, vital_type, demographic, mean, std, "
                "range_low, range_high, evidence_level, pubmed_id, source_title "
                "FROM clinical_ranges"
            ).fetchall()
            conn.close()
        return [
            {
                "condition": r[0], "vital_type": r[1], "demographic": r[2],
                "mean": r[3], "std": r[4], "range_low": r[5], "range_high": r[6],
                "evidence_level": r[7], "pubmed_id": r[8], "source_title": r[9],
            }
            for r in rows
        ]

    # ── Recommendations ───────────────────────────────────────────────────────

    def put_recommendation(
        self, condition: str, recommendation: str,
        evidence_level: str = "C", pubmed_id: str = "", source_title: str = "",
    ):
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT INTO recommendations "
                "(condition, recommendation, evidence_level, pubmed_id, source_title, cached_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (condition, recommendation, evidence_level, pubmed_id, source_title, now),
            )
            conn.commit()
            conn.close()

    def get_recommendations(self, condition: str) -> List[Dict]:
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                "SELECT recommendation, evidence_level, pubmed_id, source_title "
                "FROM recommendations WHERE condition = ?",
                (condition,),
            ).fetchall()
            conn.close()
        return [
            {"recommendation": r[0], "evidence_level": r[1],
             "pubmed_id": r[2], "source_title": r[3]}
            for r in rows
        ]

    # ── Maintenance ───────────────────────────────────────────────────────────

    def purge_expired(self) -> int:
        """Remove expired cache entries. Returns count of purged rows."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._connect()
            cursor = conn.execute(
                "DELETE FROM evidence_cache WHERE expires_at <= ?", (now,)
            )
            count = cursor.rowcount
            conn.commit()
            conn.close()
        return count

    def stats(self) -> Dict:
        """Return cache statistics."""
        with self._lock:
            conn = self._connect()
            total = conn.execute("SELECT COUNT(*) FROM evidence_cache").fetchone()[0]
            ranges = conn.execute("SELECT COUNT(*) FROM clinical_ranges").fetchone()[0]
            recs = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
            conn.close()
        return {
            "cached_queries": total,
            "clinical_ranges": ranges,
            "recommendations": recs,
            "db_path": str(self._db_path),
        }


# Singleton
evidence_cache = EvidenceCache()
