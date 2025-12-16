from __future__ import annotations

from typing import Any, Dict, List

DIFF_SUMMARY_VERSION = "diff_summary_v1_readonly"


def summarize_diff(diff: Dict[str, Any], max_paths: int = 25) -> Dict[str, Any]:
    """
    Summarize a diff dict produced by pist01beat.ops.export_diff.diff_exports.

    Deterministic:
    - sorted paths
    - stable keys
    - JSON-serializable return
    """
    if not isinstance(diff, dict):
        return {
            "version": DIFF_SUMMARY_VERSION,
            "counts": {"changed": 0, "added": 0, "removed": 0},
            "headline": "Invalid diff object",
            "changed_paths": [],
            "added_paths": [],
            "removed_paths": [],
            "warnings": ["diff input is not a dict"],
        }

    changed = diff.get("changed") or {}
    added = diff.get("added") or {}
    removed = diff.get("removed") or {}
    warns = diff.get("warnings") or []

    if not isinstance(changed, dict):
        changed = {}
        warns = list(warns) + ["diff.changed is not a dict"]
    if not isinstance(added, dict):
        added = {}
        warns = list(warns) + ["diff.added is not a dict"]
    if not isinstance(removed, dict):
        removed = {}
        warns = list(warns) + ["diff.removed is not a dict"]

    c_paths = sorted([str(k) for k in changed.keys()])[: max(0, int(max_paths))]
    a_paths = sorted([str(k) for k in added.keys()])[: max(0, int(max_paths))]
    r_paths = sorted([str(k) for k in removed.keys()])[: max(0, int(max_paths))]

    counts = {"changed": len(changed), "added": len(added), "removed": len(removed)}
    headline = _headline(counts)

    return {
        "version": DIFF_SUMMARY_VERSION,
        "counts": counts,
        "headline": headline,
        "changed_paths": c_paths,
        "added_paths": a_paths,
        "removed_paths": r_paths,
        "warnings": sorted(set([str(w) for w in warns])),
    }


def _headline(counts: Dict[str, Any]) -> str:
    c = int(counts.get("changed", 0) or 0)
    a = int(counts.get("added", 0) or 0)
    r = int(counts.get("removed", 0) or 0)

    if c == 0 and a == 0 and r == 0:
        return "No differences"
    parts: List[str] = []
    if c:
        parts.append(f"{c} changed")
    if a:
        parts.append(f"{a} added")
    if r:
        parts.append(f"{r} removed")
    return ", ".join(parts)
