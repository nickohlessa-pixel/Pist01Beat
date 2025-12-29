"""
Edge Slots Schema (read-only, deterministic)

Purpose:
- Provide a stable, versioned payload schema for daily "Edge Slot" outputs.
- Used for logging + calibration consistency.
- No betting logic. No I/O. Stdlib only.

HB15 constraints:
- Deterministic
- Auditable
- No side effects on import
"""

from __future__ import annotations

from typing import Any, Dict, List


EDGE_SLOTS_SCHEMA_VERSION = "0.1.0"

_ALLOWED_BET_TYPES = {"ML", "SPREAD", "GAME_TOTAL", "TEAM_TOTAL", "1H", "PROP"}
_ALLOWED_CONF = {"B+", "A-", "A", "A+", "A++"}
_ALLOWED_EDGE_TYPES = {"DIRECTION", "SCORING", "TEMPO", "ROLE", "OTHER"}


def _require_str(d: Dict[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"'{key}' must be a non-empty string")
    return v.strip()


def _require_bool(d: Dict[str, Any], key: str) -> bool:
    v = d.get(key)
    if not isinstance(v, bool):
        raise ValueError(f"'{key}' must be a boolean")
    return v


def _require_int(d: Dict[str, Any], key: str) -> int:
    v = d.get(key)
    if not isinstance(v, int):
        raise ValueError(f"'{key}' must be an int")
    return v


def _optional_str(d: Dict[str, Any], key: str) -> str:
    v = d.get(key, "")
    if v is None:
        return ""
    if not isinstance(v, str):
        raise ValueError(f"'{key}' must be a string if provided")
    return v.strip()


def new_edge_slots_payload(
    *,
    date: str,
    slate_id: str,
    edges: List[Dict[str, Any]],
    edge_slots_target: int = 4,
    sport: str = "nba",
) -> Dict[str, Any]:
    """
    Convenience builder. Produces a schema-shaped dict.
    Validation is performed by validate_edge_slots().
    """
    return {
        "version": EDGE_SLOTS_SCHEMA_VERSION,
        "date": date,
        "sport": sport,
        "slate_id": slate_id,
        "edge_slots_target": edge_slots_target,
        "edges": edges,
    }


def validate_edge_slots(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate + normalize a payload. Returns a normalized copy.
    Raises ValueError on schema violations.
    """
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict")

    if payload.get("version") != EDGE_SLOTS_SCHEMA_VERSION:
        raise ValueError(f"version must be '{EDGE_SLOTS_SCHEMA_VERSION}'")

    date = _require_str(payload, "date")
    sport = _require_str(payload, "sport")
    slate_id = _require_str(payload, "slate_id")

    target = _require_int(payload, "edge_slots_target")
    if target <= 0:
        raise ValueError("'edge_slots_target' must be > 0")

    edges = payload.get("edges")
    if not isinstance(edges, list) or not edges:
        raise ValueError("'edges' must be a non-empty list")

    seen_slots = set()
    norm_edges: List[Dict[str, Any]] = []

    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            raise ValueError(f"edges[{i}] must be a dict")

        slot = _require_int(e, "slot")
        if slot <= 0 or slot in seen_slots:
            raise ValueError(f"invalid or duplicate slot '{slot}'")
        seen_slots.add(slot)

        bet_type = _require_str(e, "bet_type").upper()
        if bet_type not in _ALLOWED_BET_TYPES:
            raise ValueError(f"invalid bet_type '{bet_type}'")

        confidence = _require_str(e, "confidence").upper()
        if confidence not in _ALLOWED_CONF:
            raise ValueError(f"invalid confidence '{confidence}'")

        edge_type = _require_str(e, "edge_type").upper()
        if edge_type not in _ALLOWED_EDGE_TYPES:
            raise ValueError(f"invalid edge_type '{edge_type}'")

        loss_paths = e.get("kill_switch_loss_paths")
        if (
            not isinstance(loss_paths, list)
            or len(loss_paths) != 3
            or not all(isinstance(x, str) and x.strip() for x in loss_paths)
        ):
            raise ValueError("kill_switch_loss_paths must be 3 non-empty strings")

        norm_edges.append({
            "slot": slot,
            "bet_type": bet_type,
            "line": _require_str(e, "line"),
            "book": _require_str(e, "book"),
            "confidence": confidence,
            "edge_type": edge_type,
            "why": _require_str(e, "why"),
            "auto_kills_passed": _require_bool(e, "auto_kills_passed"),
            "kill_switch_loss_paths": [x.strip() for x in loss_paths],
            "notes": _optional_str(e, "notes"),
        })

    norm_edges.sort(key=lambda x: x["slot"])

    return {
        "version": EDGE_SLOTS_SCHEMA_VERSION,
        "date": date,
        "sport": sport,
        "slate_id": slate_id,
        "edge_slots_target": target,
        "edges": norm_edges,
    }
