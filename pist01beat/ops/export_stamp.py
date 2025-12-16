from __future__ import annotations

from typing import Any, Dict
from datetime import datetime, timezone

from pist01beat.ops.export_hash import hash_export

EXPORT_STAMP_VERSION = "export_stamp_v1_readonly"


def build_export_stamp(export: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a deterministic metadata stamp for an export snapshot.

    Returns stable keys:
      version, export_version, export_hash, created_at_utc

    Notes:
    - created_at_utc reflects runtime wall clock in UTC (not deterministic across runs),
      but format is deterministic and intended for audit metadata.
    - export_hash is deterministic for a given export content.
    """
    export_version = export.get("version") if isinstance(export, dict) else None
    if export_version is not None and not isinstance(export_version, str):
        export_version = str(export_version)

    created_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    export_hash = hash_export(export if isinstance(export, dict) else {"_root": export})

    out: Dict[str, Any] = {}
    out["version"] = EXPORT_STAMP_VERSION
    out["export_version"] = export_version
    out["export_hash"] = export_hash
    out["created_at_utc"] = created_at_utc
    return out
