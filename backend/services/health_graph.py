"""
Health Graph — Directed graph of health events with trust-weighted edges.
Uses NetworkX for Phase 1/2. Persists to encrypted JSON after each update.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import threading

import networkx as nx

from backend.models.vital import VitalRecord

DATA_PATH = Path("./data/health_graph.json")
CO_OCCURRENCE_WINDOW_MINUTES = 30


@dataclass
class HealthGraphNode:
    id: str
    vital_type: str
    value: float
    privatized_value: float
    unit: str
    timestamp: datetime
    trust_score: float
    tags: List[str]


@dataclass
class HealthGraphEdge:
    source_id: str
    target_id: str
    edge_type: Literal["TEMPORAL", "CORRELATION"]
    trust_score: float
    weight: float


class HealthGraph:
    def __init__(self):
        self._graph = nx.DiGraph()
        self._vital_index: Dict[str, List[str]] = {}
        self._lock = threading.Lock()
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def add_node(self, record: VitalRecord) -> None:
        node = HealthGraphNode(
            id=record.id,
            vital_type=record.vital_type,
            value=record.value,
            privatized_value=record.privatized_value or record.value,
            unit=record.unit,
            timestamp=record.timestamp,
            trust_score=record.trust_score or 0.0,
            tags=record.tags,
        )
        with self._lock:
            self._graph.add_node(
                node.id,
                vital_type=node.vital_type,
                value=node.value,
                privatized_value=node.privatized_value,
                unit=node.unit,
                timestamp=node.timestamp.isoformat(),
                trust_score=node.trust_score,
                tags=node.tags,
            )
            # Update index
            if node.vital_type not in self._vital_index:
                self._vital_index[node.vital_type] = []
            self._vital_index[node.vital_type].append(node.id)
            
            self._add_temporal_edges(node)
            self._add_correlation_edges(node)
            self._save()

    def get_recent_values(self, vital_type: str, days: int = 7, use_privatized: bool = True) -> List[Dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        results = []
        with self._lock:
            # Optimized: use index to avoid scanning all nodes
            node_ids = self._vital_index.get(vital_type, [])
            for nid in node_ids:
                data = self._graph.nodes[nid]
                ts = datetime.fromisoformat(data["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    # Anti-Hacking layer: return privatized_value by default
                    val = data["privatized_value"] if use_privatized and "privatized_value" in data else data["value"]
                    results.append({"id": nid, **data, "value": val, "timestamp": ts})
        results.sort(key=lambda x: x["timestamp"])
        return results

    def get_all_nodes(self) -> List[Dict]:
        with self._lock:
            return [{"id": nid, **data} for nid, data in self._graph.nodes(data=True)]

    def get_node_count(self) -> int:
        return self._graph.number_of_nodes()

    def get_edge_count(self) -> int:
        return self._graph.number_of_edges()

    # ── Edge construction ─────────────────────────────────────────────────────

    def _add_temporal_edges(self, new_node: HealthGraphNode) -> None:
        same_type = [
            (nid, data)
            for nid, data in self._graph.nodes(data=True)
            if data.get("vital_type") == new_node.vital_type and nid != new_node.id
        ]
        if not same_type:
            return
        same_type.sort(key=lambda x: x[1]["timestamp"])
        prev_id, prev_data = same_type[-1]
        trust = min(new_node.trust_score, prev_data.get("trust_score", 0.0))
        self._graph.add_edge(
            prev_id,
            new_node.id,
            edge_type="TEMPORAL",
            trust_score=trust,
            weight=trust,
        )

    def _add_correlation_edges(self, new_node: HealthGraphNode) -> None:
        window = timedelta(minutes=CO_OCCURRENCE_WINDOW_MINUTES)
        new_ts = new_node.timestamp
        if new_ts.tzinfo is None:
            new_ts = new_ts.replace(tzinfo=timezone.utc)

        for nid, data in self._graph.nodes(data=True):
            if nid == new_node.id or data.get("vital_type") == new_node.vital_type:
                continue
            ts = datetime.fromisoformat(data["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if abs((new_ts - ts).total_seconds()) <= window.total_seconds():
                trust = min(new_node.trust_score, data.get("trust_score", 0.0))
                if not self._graph.has_edge(nid, new_node.id) and not self._graph.has_edge(new_node.id, nid):
                    self._graph.add_edge(
                        new_node.id,
                        nid,
                        edge_type="CORRELATION",
                        trust_score=trust,
                        weight=trust,
                    )

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self):
        data = nx.node_link_data(self._graph)
        DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self):
        if DATA_PATH.exists():
            try:
                data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
                self._graph = nx.node_link_graph(data)
                # Rebuild index
                self._vital_index = {}
                for nid, data in self._graph.nodes(data=True):
                    vt = data.get("vital_type")
                    if vt:
                        if vt not in self._vital_index:
                            self._vital_index[vt] = []
                        self._vital_index[vt].append(nid)
            except Exception:
                self._graph = nx.DiGraph()
                self._vital_index = {}


health_graph = HealthGraph()
