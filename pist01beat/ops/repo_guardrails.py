"""
repo_guardrails.py

Read-only guardrail to detect accidental basketball-related content
in coder-thread artifacts. Warn-only. Deterministic. No side effects.

This file has ZERO decision authority.
"""

FILE_VERSION = "repo_guardrails_v1_readonly"

from typing import Dict, List

BASKETBALL_KEYWORDS = {
    "nba", "basketball", "points", "rebounds", "assists",
    "fg%", "3p%", "spread", "total", "over", "under",
    "roster", "lineup", "injury", "minutes", "pace",
    "offense", "defense", "player", "coach", "matchup",
}

def scan_text_for_basketball(text: str) -> List[str]:
    if not isinstance(text, str):
        return []
    lower = text.lower()
    hits = {kw for kw in BASKETBALL_KEYWORDS if kw in lower}
    return sorted(hits)

def scan_object(obj) -> Dict[str, List[str]]:
    findings: Dict[str, List[str]] = {}

    def _scan(node, path: str) -> None:
        if isinstance(node, str):
            hits = scan_text_for_basketball(node)
            if hits:
                findings[path] = hits
        elif isinstance(node, dict):
            for k, v in node.items():
                _scan(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                _scan(v, f"{path}[{i}]")

    _scan(obj, "$")
    return findings

def guardrail_check(payload) -> Dict[str, object]:
    findings = scan_object(payload)
    return {
        "version": FILE_VERSION,
        "violations_found": bool(findings),
        "violation_count": len(findings),
        "details": findings,
    }
