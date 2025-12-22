
"""
Deterministic ops tooling index (read-only).

Goal:
- Single source of truth for which infra-only ops tools exist and their versions
- JSON-safe, stable ordering
- No engine imports, no model authority, no writes
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

OPS_INDEX_VERSION = "ops_index_v1_readonly"


def build_ops_index() -> Dict:
    """
    Returns a JSON-safe dict describing available ops tools and versions.

    Properties:
      - deterministic ordering
      - warn-only if a tool/version cannot be imported
    """
    warnings: List[str] = []

    tools: List[Dict[str, Optional[str]]] = []

    # (key, module, attr_version_name)
    targets: List[Tuple[str, str, str]] = [
        ("repo_snapshot", "pist01beat.ops.repo_snapshot", "REPO_SNAPSHOT_VERSION"),
        ("repo_snapshot_cli", "pist01beat.ops.repo_snapshot_cli", "REPO_SNAPSHOT_CLI_VERSION"),
        ("preflight_cli", "pist01beat.ops.preflight_cli", "PREFLIGHT_CLI_VERSION"),
        ("ops_dispatch", "pist01beat.ops.__main__", "OPS_DISPATCH_VERSION"),
        ("ops_index", "pist01beat.ops.ops_index", "OPS_INDEX_VERSION"),
    ]

    for key, mod_name, ver_attr in targets:
        version_val: Optional[str] = None
        try:
            mod = __import__(mod_name, fromlist=[ver_attr])
            version_val = getattr(mod, ver_attr, None)
            if version_val is None:
                warnings.append(f"missing_version_attr: {mod_name}.{ver_attr}")
        except Exception as e:
            warnings.append(f"import_failed: {mod_name}: {type(e).__name__}")

        tools.append(
            {
                "key": key,
                "module": mod_name,
                "version_attr": ver_attr,
                "version": version_val,
            }
        )

    # Deterministic ordering
    tools.sort(key=lambda x: (x.get("key") or ""))

    return {
        "version": OPS_INDEX_VERSION,
        "warnings": warnings,
        "tools": tools,
    }
