from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


MODEL_EXPORT_VERSION = "model_export_v1_readonly"


def _deterministic_json_bytes(obj: Any) -> bytes:
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_model_export() -> Dict[str, Any]:
    warnings: List[str] = []

    payload: Dict[str, Any] = {
        "version": MODEL_EXPORT_VERSION,
        "warnings": warnings,
        "context_snapshot": {"model_export_version": MODEL_EXPORT_VERSION},
        "decision_log": {"available": False, "audit": None, "tail": []},
        "decision_timeline": {"available": False, "items": []},
        "team_pack_audit": {"available": False, "summary": None},
    }

    payload["decision_hash"] = _sha256_hex(_deterministic_json_bytes(payload))
    return payload
