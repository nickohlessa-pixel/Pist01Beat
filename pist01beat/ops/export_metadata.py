from __future__ import annotations

import hashlib
import json
import platform as _platform
import sys
from datetime import datetime, timezone
from typing import Any, Dict


EXPORT_METADATA_VERSION = "export_metadata_v1_readonly"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _deterministic_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def attach_export_metadata(export_obj: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(export_obj, dict):
        raise TypeError("attach_export_metadata expects export_obj to be a dict")

    payload_bytes = _deterministic_json_bytes(export_obj)
    payload_hash = _sha256_hex(payload_bytes)

    export_version = export_obj.get("version", "unknown")

    metadata = {
        "export_version": export_version,
        "metadata_version": EXPORT_METADATA_VERSION,
        "created_utc": _utc_now_iso(),
        "python_version": sys.version.split(" ")[0],
        "platform": _platform.platform(),
        "payload_hash": payload_hash,
    }

    return {"metadata": metadata, "payload": export_obj}
